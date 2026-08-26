"""Application-facing search, concept detail, and graph projections."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, cast
from urllib.parse import quote

from sqlalchemy import select

from studium.app.workspace import WorkspaceContext
from studium.index.graph import get_one_hop_neighborhood
from studium.index.repositories import aliases, concepts, domains, scaffold_modules
from studium.index.schema import relationships
from studium.index.search import (
    ConceptSearchFilters,
    ConceptSearchLimits,
    ConceptSearchQuery,
    HybridSearchOptions,
    search_concepts,
)
from studium.index.search.models import RankedConceptCandidate
from studium.index.vector.models import ModelSpaceFilter
from studium.parsing import parse_concept_note
from studium.recommend import recommend

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def search_workspace(
    workspace: WorkspaceContext,
    *,
    text: str,
    filters: ConceptSearchFilters | None = None,
    include_modules: bool = True,
    include_drafts: bool = False,
    diagnostics: bool = False,
) -> dict[str, Any]:
    selected_filters = filters or ConceptSearchFilters()
    if not include_drafts and not selected_filters.vault_statuses:
        selected_filters = selected_filters.model_copy(update={"vault_statuses": ["accepted"]})
    query = ConceptSearchQuery(
        text=text,
        filters=selected_filters,
        limits=ConceptSearchLimits(concepts=30, modules=30, channel=80),
        include_modules=include_modules,
        include_diagnostics=diagnostics,
    )
    model = workspace.embedding_provider.model_metadata()
    result = search_concepts(
        workspace.index_engine,
        query,
        options=HybridSearchOptions(
            embedding_provider=workspace.embedding_provider,
            model_filter=ModelSpaceFilter(
                model_id=model.model_id,
                model_revision=model.model_revision,
                dimension=model.dimension,
                normalizes_embeddings=model.normalizes_embeddings,
            ),
        ),
    )
    payload = result.model_dump(mode="json")
    for candidate in payload["ranked_concepts"]:
        candidate["match_explanations"] = explain_match(candidate)
    for module in payload["module_hits"]:
        module["match_explanations"] = explain_module_match(module)

    recommendation = None
    if result.resolution_state.value in {"no_results", "related_results"}:
        candidate = recommend(
            workspace.index_engine,
            search=result,
            provider=workspace.llm_provider,
        )
        recommendation = candidate.model_dump(mode="json")
    payload["recommendation"] = recommendation
    return payload


def explain_match(candidate: dict[str, Any] | RankedConceptCandidate) -> list[str]:
    raw = (
        candidate.model_dump(mode="json")
        if isinstance(candidate, RankedConceptCandidate)
        else candidate
    )
    explanations: list[str] = []
    fields = [str(item) for item in raw.get("matched_fields", [])]
    if "canonical_title" in fields:
        explanations.append("Exact title match")
    if "approved_alias" in fields:
        explanations.append("Approved alias match")
    if "stable_id" in fields:
        explanations.append("Stable concept ID match")
    modules = raw.get("matching_modules", [])
    for module in modules[:2]:
        explanations.append(f"Matched module: {module['title']}")
    channels = _channel_names(raw.get("channels"))
    if "semantic_vector" in channels:
        explanations.append("Semantically related")
    if "identity_vector" in channels and not explanations:
        explanations.append("Similar concept identity")
    if "fts" in channels and not explanations:
        explanations.append("Matched note text")
    return explanations or ["Related concept"]


def explain_module_match(module: dict[str, Any]) -> list[str]:
    channels = _channel_names(module.get("channels"))
    explanations: list[str] = []
    if "fts" in channels:
        explanations.append("Matched module title or focus")
    if "module_vector" in channels:
        explanations.append("Semantically related module")
    return explanations or ["Matching scaffold module"]


def search_facets(workspace: WorkspaceContext, *, include_drafts: bool = False) -> dict[str, Any]:
    domain_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    review_counts: Counter[str] = Counter()
    vault_counts: Counter[str] = Counter()
    with workspace.index_engine.connect() as connection:
        rows = concepts.list_concepts(connection)
        for row in rows:
            if not include_drafts and str(row["vault_status"]) != "accepted":
                continue
            type_counts[str(row["concept_type"])] += 1
            review_counts[str(row["review_status"])] += 1
            vault_counts[str(row["vault_status"])] += 1
            for item in domains.list_domains_for_concept(connection, str(row["concept_id"])):
                domain_counts[str(item["domain"])] += 1
    return {
        "domains": _counter_options(domain_counts),
        "concept_types": _counter_options(type_counts),
        "review_statuses": _counter_options(review_counts),
        "vault_statuses": _counter_options(vault_counts),
    }


def concept_detail(workspace: WorkspaceContext, concept_id: str) -> dict[str, Any]:
    with workspace.index_engine.connect() as connection:
        concept = concepts.get_concept(connection, concept_id)
        if concept is None:
            raise KeyError(concept_id)
        alias_rows = aliases.list_aliases_for_concept(connection, concept_id)
        domain_rows = domains.list_domains_for_concept(connection, concept_id)
        module_rows = scaffold_modules.list_modules_for_concept(connection, concept_id)

    file_path = str(concept["file_path"])
    markdown = workspace.vault.read_markdown(file_path)
    parsed = parse_concept_note(markdown)
    metadata = parsed.metadata
    if metadata is None:
        raise ValueError(f"Indexed note is no longer parseable: {file_path}")
    sections = split_markdown_sections(parsed.body)
    module_sections = _match_module_sections(module_rows, sections)
    neighborhood = get_one_hop_neighborhood(workspace.index_engine, concept_id)
    rels = [
        *neighborhood.outgoing,
        *neighborhood.incoming_derived,
    ]
    return {
        "concept_id": concept_id,
        "canonical_title": str(concept["canonical_title"]),
        "aliases": [str(row["alias"]) for row in alias_rows],
        "concept_type": str(concept["concept_type"]),
        "domains": [str(row["domain"]) for row in domain_rows],
        "status": str(concept["status"]),
        "review_status": str(concept["review_status"]),
        "vault_status": str(concept["vault_status"]),
        "file_path": file_path,
        "updated_at": concept.get("note_updated_at"),
        "overview_markdown": concept.get("overview_markdown") or "",
        "body_markdown": parsed.body,
        "raw_markdown": markdown,
        "sections": sections,
        "modules": module_sections,
        "relationships": [rel.model_dump(mode="json") for rel in rels],
        "learning_encounters": [
            encounter.model_dump(mode="json") for encounter in metadata.learning_encounters
        ],
        "warnings": [issue.model_dump(mode="json") for issue in parsed.warnings],
        "obsidian_uri": f"obsidian://open?path={quote(str(workspace.vault.resolve_path(file_path)))}",
    }


def graph_projection(
    workspace: WorkspaceContext,
    *,
    center: str | None = None,
    domain: str | None = None,
    include_drafts: bool = False,
) -> dict[str, Any]:
    allowed_ids: set[str] | None = None
    if center:
        neighborhood = get_one_hop_neighborhood(workspace.index_engine, center)
        allowed_ids = {center}
        for rel in [*neighborhood.outgoing, *neighborhood.incoming_derived]:
            if rel.target_id:
                allowed_ids.add(rel.target_id)

    nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    with workspace.index_engine.connect() as connection:
        for row in concepts.list_concepts(connection):
            concept_id = str(row["concept_id"])
            if allowed_ids is not None and concept_id not in allowed_ids:
                continue
            if not include_drafts and str(row["vault_status"]) != "accepted":
                continue
            concept_domains = [
                str(item["domain"])
                for item in domains.list_domains_for_concept(connection, concept_id)
            ]
            if domain and domain not in concept_domains:
                continue
            nodes.append(
                {
                    "id": concept_id,
                    "title": str(row["canonical_title"]),
                    "concept_type": str(row["concept_type"]),
                    "domains": concept_domains,
                    "status": str(row["status"]),
                    "vault_status": str(row["vault_status"]),
                    "review_status": str(row["review_status"]),
                    "selected": concept_id == center,
                }
            )
            node_ids.add(concept_id)

        edge_rows = connection.execute(select(relationships)).mappings().all()

    edges: list[dict[str, Any]] = []
    for row in edge_rows:
        source = str(row["source_concept_id"])
        target = None if row["target_id"] is None else str(row["target_id"])
        if target is None or source not in node_ids or target not in node_ids:
            continue
        edges.append(
            {
                "id": f"relationship_{row['id']}",
                "source": source,
                "target": target,
                "relationship_type": str(row["relationship_type"]),
                "learning_role": str(row["learning_role"]),
                "confidence": str(row["confidence"]),
                "status": str(row["status"]),
            }
        )

    return {
        "center": center,
        "nodes": nodes,
        "edges": edges,
        "legend": {
            "depends_on": "Prerequisite",
            "related_to": "Related",
            "variant_of": "Variant",
            "parent_of": "Parent / child",
            "contrasts_with": "Contrast",
        },
    }


def split_markdown_sections(body: str) -> list[dict[str, Any]]:
    matches = list(_HEADING_RE.finditer(body))
    sections: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        title = match.group(2).strip()
        markdown = body[start:end].strip()
        sections.append(
            {
                "id": slugify_heading(title),
                "title": title,
                "level": len(match.group(1)),
                "markdown": markdown,
                "line": body.count("\n", 0, start) + 1,
            }
        )
    return sections


def slugify_heading(title: str) -> str:
    return _NON_SLUG.sub("-", title.casefold()).strip("-")


def _match_module_sections(
    module_rows: list[dict[str, Any]],
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_title = {str(section["title"]).casefold(): section for section in sections}
    result: list[dict[str, Any]] = []
    for module in module_rows:
        section = by_title.get(str(module["title"]).casefold())
        result.append(
            {
                "id": str(module["module_id"]),
                "type": str(module["type"]),
                "title": str(module["title"]),
                "status": str(module["status"]),
                "origin": module.get("origin"),
                "focus": module.get("focus"),
                "anchor": module.get("anchor") or (None if section is None else section["id"]),
                "markdown": "" if section is None else section["markdown"],
            }
        )
    return result


def _counter_options(counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {"value": value, "label": value.replace("_", " ").title(), "count": count}
        for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def _channel_names(value: Any) -> set[str]:
    names: set[str] = set()
    if not isinstance(value, list):
        return names
    for item in cast(list[Any], value):
        if isinstance(item, dict):
            channel = cast(dict[str, Any], item).get("channel")
            if channel is not None:
                names.add(str(channel))
    return names
