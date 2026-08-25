"""Recommendation assembly, scaffold generation, drafts, previews, and commits."""

from __future__ import annotations

import difflib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert

from studium.app.database import app_transaction, draft_snapshots, row_dict
from studium.app.migrations import utc_now
from studium.app.workspace import WorkspaceContext
from studium.create.models import (
    CreateIntent,
    CreateProposal,
    DraftCommitResult,
    DraftPreview,
    EncounterProposal,
    GeneratedDraft,
    ModuleProposal,
    PossibleMatch,
    RelationshipProposal,
)
from studium.create.scaffolds import (
    insert_modules,
    module_proposal,
    recommend_modules,
    render_new_concept_body,
    update_module_index,
)
from studium.index.repositories import concepts
from studium.index.search import (
    ConceptSearchLimits,
    ConceptSearchQuery,
    HybridSearchOptions,
    search_concepts,
)
from studium.index.vector.models import ModelSpaceFilter
from studium.parsing import parse_concept_note
from studium.recommend import recommend
from studium.schemas import (
    ConceptNoteMetadata,
    ConceptType,
    ContributionStatus,
    EncounterRole,
    LearningEncounter,
    LearningRole,
    NoteVaultStatus,
    RelationshipConfidence,
    RelationshipMetadata,
    RelationshipStatus,
    RelationshipVaultStatus,
    ReviewStatus,
    ScaffoldModuleMetadata,
    ScaffoldModuleStatus,
    ScaffoldModuleType,
    SourceMetadata,
    SourceType,
    default_studium_learning_encounter,
)
from studium.serialization import build_concept_note_metadata, serialize_concept_note
from studium.serialization.concept_id import generate_concept_id, slugify_title
from studium.writes import (
    build_create_note_proposal,
    build_update_note_proposal,
    proposal_can_be_committed,
)

_DOMAIN_SANITIZE = re.compile(r"[^a-z0-9_]+")


def propose_create(workspace: WorkspaceContext, intent: CreateIntent) -> CreateProposal:
    search_query = ConceptSearchQuery(
        text=intent.intent,
        limits=ConceptSearchLimits(concepts=12, modules=12, channel=50),
        include_modules=True,
    )
    metadata = workspace.embedding_provider.model_metadata()
    search = search_concepts(
        workspace.index_engine,
        search_query,
        options=HybridSearchOptions(
            embedding_provider=workspace.embedding_provider,
            model_filter=ModelSpaceFilter(
                model_id=metadata.model_id,
                model_revision=metadata.model_revision,
                dimension=metadata.dimension,
                normalizes_embeddings=metadata.normalizes_embeddings,
            ),
        ),
    )
    recommendation = recommend(
        workspace.index_engine,
        search=search,
        provider=workspace.llm_provider,
        source_type=None if intent.source_type is None else intent.source_type.value,
        source_title=intent.source_title,
        unit=intent.source_unit,
        module_intent=bool(intent.requested_module_type or intent.target_concept_id),
    )
    raw = recommendation.model_dump(mode="json")
    action = str(raw.get("action") or "create_new_concept")
    target_id = intent.target_concept_id or _optional_string(raw.get("target_concept_id"))
    target = _load_concept(workspace, target_id) if target_id else None

    suggested_title = _optional_string(raw.get("suggested_title")) or intent.intent.strip()
    canonical_title = str(target["canonical_title"]) if target else suggested_title
    concept_type = (
        ConceptType(str(target["concept_type"]))
        if target
        else _concept_type(raw.get("suggested_concept_type"), intent.intent)
    )
    domains = (
        _domains_for_concept(workspace, target_id)
        if target_id and target
        else _clean_domains(raw.get("suggested_domains"), intent.intent)
    )

    if target is not None:
        target_path = str(target["file_path"])
    else:
        target_path = f"{_concept_directory(workspace)}/{slugify_title(canonical_title).replace('_', '-')}.md"

    modules = _proposal_modules(intent, raw, concept_type, action)
    relationships = _proposal_relationships(raw)
    aliases_to_add = _proposal_aliases(raw)
    encounter = _encounter_from_intent(intent)
    possible_matches = [
        PossibleMatch(
            concept_id=candidate.concept_id,
            title=candidate.canonical_title,
            evidence=_candidate_evidence(candidate.model_dump(mode="json")),
            vault_status=candidate.vault_status,
        )
        for candidate in search.ranked_concepts[:5]
        if candidate.concept_id != target_id
    ]
    confidence = str(raw.get("confidence") or "low")
    reasoning_mode = str(raw.get("reasoning_mode") or "fallback")
    evidence = [str(item) for item in cast(list[Any], raw.get("evidence") or [])]
    warnings = [str(item) for item in cast(list[Any], raw.get("warnings") or [])]
    if action == "request_clarification":
        message = _optional_string(raw.get("clarification_message"))
        if message:
            warnings.append(message)
    if action == "use_existing_concept" and not modules and encounter is None:
        evidence.append("An accepted identity match already covers this learning intent.")

    return CreateProposal(
        proposal_id=f"proposal_{uuid4().hex}",
        action=action,
        canonical_title=canonical_title,
        target_concept_id=target_id,
        target_path=target_path,
        concept_type=concept_type,
        domains=domains,
        aliases_to_add=aliases_to_add,
        modules=modules,
        relationships=relationships,
        encounter=encounter,
        possible_matches=possible_matches,
        backlog_candidates=_dict_list(raw.get("backlog_candidates")),
        evidence=evidence,
        warnings=warnings,
        confidence=confidence,
        reasoning_mode=reasoning_mode,
        index_revision=search.index_revision,
        intent=intent,
        raw_recommendation=raw,
    )


def build_draft(workspace: WorkspaceContext, proposal: CreateProposal) -> GeneratedDraft:
    if proposal.target_concept_id:
        return _build_existing_draft(workspace, proposal)
    selected = [module for module in proposal.modules if module.selected]
    encounters = [_learning_encounter(proposal.encounter)] if proposal.encounter else [
        default_studium_learning_encounter()
    ]
    module_metadata = [_module_metadata(module) for module in selected]
    relationships = [
        _relationship_metadata(item)
        for item in proposal.relationships
        if item.selected
    ]
    metadata = build_concept_note_metadata(
        proposal.canonical_title,
        concept_type=proposal.concept_type,
        concept_domains=proposal.domains,
        aliases=proposal.aliases_to_add,
        learning_encounters=encounters,
        scaffold_modules=module_metadata,
        relationships=relationships,
    )
    body = render_new_concept_body(proposal.canonical_title, selected)
    return GeneratedDraft(
        proposal_id=proposal.proposal_id,
        operation="create",
        concept_id=metadata.id,
        target_path=proposal.target_path,
        markdown=serialize_concept_note(metadata, body),
        selected_modules=[item.id for item in selected],
        warnings=list(proposal.warnings),
    )


def _build_existing_draft(
    workspace: WorkspaceContext,
    proposal: CreateProposal,
) -> GeneratedDraft:
    before = workspace.vault.read_markdown(proposal.target_path)
    parsed = parse_concept_note(before)
    if parsed.metadata is None:
        raise ValueError("The target concept can no longer be parsed.")
    selected = [module for module in proposal.modules if module.selected]
    has_changes = bool(
        selected
        or proposal.aliases_to_add
        or any(item.selected for item in proposal.relationships)
        or (proposal.encounter and proposal.encounter.selected)
    )
    if not has_changes:
        return GeneratedDraft(
            proposal_id=proposal.proposal_id,
            operation="no_change",
            concept_id=parsed.metadata.id,
            target_path=proposal.target_path,
            markdown=before,
            warnings=[
                *proposal.warnings,
                "No mutation is proposed. Open the existing concept or select an expansion.",
            ],
        )

    existing_module_ids = {module.id for module in parsed.metadata.scaffold_modules}
    new_modules = [
        _module_metadata(module) for module in selected if module.id not in existing_module_ids
    ]
    aliases = list(dict.fromkeys([*parsed.metadata.aliases, *proposal.aliases_to_add]))
    relationships = list(parsed.metadata.relationships)
    relationship_keys = {
        (item.relationship_type, item.target_id, item.target_title.casefold())
        for item in relationships
    }
    for item in proposal.relationships:
        if not item.selected:
            continue
        converted = _relationship_metadata(item)
        key = (
            converted.relationship_type,
            converted.target_id,
            converted.target_title.casefold(),
        )
        if key not in relationship_keys:
            relationships.append(converted)
            relationship_keys.add(key)
    encounters = list(parsed.metadata.learning_encounters)
    if proposal.encounter and proposal.encounter.selected:
        encounters.append(_learning_encounter(proposal.encounter))
    updated = parsed.metadata.model_copy(
        update={
            "aliases": aliases,
            "scaffold_modules": [*parsed.metadata.scaffold_modules, *new_modules],
            "relationships": relationships,
            "learning_encounters": encounters,
            "review_status": ReviewStatus.NOT_SUBMITTED,
            "vault_status": NoteVaultStatus.DRAFT,
            "updated_at": datetime.now(UTC).replace(microsecond=0),
        }
    )
    body = insert_modules(parsed.body, selected)
    body = update_module_index(body, selected)
    return GeneratedDraft(
        proposal_id=proposal.proposal_id,
        operation="update",
        concept_id=updated.id,
        target_path=proposal.target_path,
        markdown=serialize_concept_note(updated, body),
        selected_modules=[item.id for item in selected],
        warnings=list(proposal.warnings),
    )


def build_preview(workspace: WorkspaceContext, draft: GeneratedDraft) -> DraftPreview:
    write = _write_proposal(workspace, draft)
    before_lines = [] if write.before_content is None else write.before_content.splitlines(keepends=True)
    after_lines = write.after_content.splitlines(keepends=True)
    diff = "".join(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{write.target_path}",
            tofile=f"b/{write.target_path}",
            n=3,
        )
    )
    return DraftPreview(
        operation=write.operation.value,
        target_path=write.target_path,
        would_create=write.would_create,
        would_update=write.would_update,
        can_commit=proposal_can_be_committed(write),
        diff=diff,
        warnings=[issue.model_dump(mode="json") for issue in write.warnings],
        critical_errors=[
            issue.model_dump(mode="json") for issue in write.critical_errors
        ],
    )


def commit_draft(workspace: WorkspaceContext, draft: GeneratedDraft) -> DraftCommitResult:
    if draft.operation == "no_change":
        parsed = parse_concept_note(draft.markdown)
        if parsed.metadata is None:
            raise ValueError("Existing note is not parseable.")
        return DraftCommitResult(
            concept_id=draft.concept_id,
            target_path=draft.target_path,
            index_revision=workspace.health()["index_revision"],
            sync_status="no_changes",
            review_status=parsed.metadata.review_status.value,
            vault_status=parsed.metadata.vault_status.value,
        )
    write = _write_proposal(workspace, draft)
    result = workspace.commit(write)
    parsed = parse_concept_note(draft.markdown)
    if parsed.metadata is None:
        raise ValueError("Committed draft did not parse.")
    return DraftCommitResult(
        concept_id=draft.concept_id,
        target_path=draft.target_path,
        index_revision=result.index_revision,
        sync_status=result.sync.status.value,
        review_status=parsed.metadata.review_status.value,
        vault_status=parsed.metadata.vault_status.value,
    )


def save_draft_snapshot(
    workspace: WorkspaceContext,
    draft: GeneratedDraft,
    *,
    title: str,
    recommendation: dict[str, Any] | None = None,
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    identifier = snapshot_id or f"draft_{uuid4().hex}"
    now = utc_now()
    statement = insert(draft_snapshots).values(
        id=identifier,
        concept_id=draft.concept_id,
        title=title,
        target_path=draft.target_path,
        operation=draft.operation,
        markdown=draft.markdown,
        recommendation_json=(
            None if recommendation is None else json.dumps(recommendation, sort_keys=True)
        ),
        created_at=now,
        updated_at=now,
    )
    with app_transaction(workspace.app_engine) as connection:
        connection.execute(
            statement.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "concept_id": draft.concept_id,
                    "title": title,
                    "target_path": draft.target_path,
                    "operation": draft.operation,
                    "markdown": draft.markdown,
                    "recommendation_json": (
                        None
                        if recommendation is None
                        else json.dumps(recommendation, sort_keys=True)
                    ),
                    "updated_at": now,
                },
            )
        )
    return get_draft(workspace, identifier)


def list_drafts(workspace: WorkspaceContext) -> list[dict[str, Any]]:
    with workspace.app_engine.connect() as connection:
        rows = connection.execute(
            select(draft_snapshots).order_by(draft_snapshots.c.updated_at.desc())
        ).all()
    return [_decode_draft(row_dict(row)) for row in rows]


def get_draft(workspace: WorkspaceContext, draft_id: str) -> dict[str, Any]:
    with workspace.app_engine.connect() as connection:
        row = connection.execute(
            select(draft_snapshots).where(draft_snapshots.c.id == draft_id)
        ).first()
    if row is None:
        raise KeyError(draft_id)
    return _decode_draft(row_dict(row))


def delete_draft(workspace: WorkspaceContext, draft_id: str) -> None:
    with app_transaction(workspace.app_engine) as connection:
        result = connection.execute(
            draft_snapshots.delete().where(draft_snapshots.c.id == draft_id)
        )
    if result.rowcount == 0:
        raise KeyError(draft_id)


def _write_proposal(workspace: WorkspaceContext, draft: GeneratedDraft) -> Any:
    if draft.operation == "create":
        return build_create_note_proposal(
            workspace.vault,
            draft.target_path,
            draft.markdown,
        )
    if draft.operation == "update":
        return build_update_note_proposal(
            workspace.vault,
            draft.target_path,
            draft.markdown,
        )
    raise ValueError("A no-change draft does not require a write proposal.")


def _proposal_modules(
    intent: CreateIntent,
    raw: dict[str, Any],
    concept_type: ConceptType,
    action: str,
) -> list[ModuleProposal]:
    if action == "add_scaffold_module":
        module_type = ScaffoldModuleType(str(raw.get("module_type") or "custom"))
        return [
            module_proposal(
                module_type,
                title=_optional_string(raw.get("module_title")),
                focus=_optional_string(raw.get("focus")),
                reason="Recommendation targets an unmet module-level learning intent.",
            )
        ]
    if action in {"use_existing_concept", "add_learning_encounter", "update_learning_encounter"}:
        if intent.requested_module_type is None:
            return []
    modules = recommend_modules(
        concept_type,
        intent=f"{intent.intent} {intent.learning_goal}",
        requested=(
            intent.requested_module_type
            or _optional_module_type(raw.get("suggested_module_type"))
        ),
        preferences=intent.scaffold_preferences,
    )
    suggested_title = _optional_string(raw.get("suggested_module_title"))
    suggested_focus = _optional_string(raw.get("suggested_module_focus"))
    if suggested_title and modules:
        modules[0] = modules[0].model_copy(
            update={"title": suggested_title, "focus": suggested_focus}
        )
    return modules


def _proposal_relationships(raw: dict[str, Any]) -> list[RelationshipProposal]:
    result: list[RelationshipProposal] = []
    values = raw.get("graph_positions")
    if not isinstance(values, list):
        return result
    for value in cast(list[Any], values):
        if not isinstance(value, dict):
            continue
        item = cast(dict[str, Any], value)
        try:
            result.append(
                RelationshipProposal(
                    relationship_type=RelationshipMetadata.model_fields[
                        "relationship_type"
                    ].annotation(str(item.get("relationship_type"))),
                    target_title=str(item.get("target_title") or ""),
                    target_id=_optional_string(item.get("target_concept_id")),
                    learning_role=LearningRole(str(item.get("learning_role") or "supporting")),
                    evidence=str(item.get("direction_note") or ""),
                )
            )
        except (TypeError, ValueError):
            continue
    return result


def _proposal_aliases(raw: dict[str, Any]) -> list[str]:
    metadata = raw.get("metadata_suggestions")
    if not isinstance(metadata, dict):
        return []
    aliases = cast(dict[str, Any], metadata).get("aliases_to_add")
    if not isinstance(aliases, list):
        return []
    result: list[str] = []
    for value in cast(list[Any], aliases):
        if isinstance(value, dict):
            alias = _optional_string(cast(dict[str, Any], value).get("alias"))
            if alias:
                result.append(alias)
    return result


def _encounter_from_intent(intent: CreateIntent) -> EncounterProposal | None:
    if intent.source_type is None or not intent.source_title:
        return None
    return EncounterProposal(
        source_type=intent.source_type,
        source_title=intent.source_title,
        unit=intent.source_unit,
        section=intent.source_section,
        link=intent.source_link,
        source_id=intent.source_id,
    )


def _learning_encounter(proposal: EncounterProposal) -> LearningEncounter:
    return LearningEncounter(
        source=SourceMetadata(
            type=proposal.source_type,
            title=proposal.source_title,
            unit=proposal.unit,
            section=proposal.section,
            link=proposal.link,
        ),
        role=EncounterRole.PRIMARY,
        contribution_status=ContributionStatus.PENDING,
        content_attached=proposal.source_id is not None,
        content_id=proposal.source_id,
    )


def _module_metadata(proposal: ModuleProposal) -> ScaffoldModuleMetadata:
    return ScaffoldModuleMetadata(
        id=proposal.id,
        type=proposal.type,
        title=proposal.title,
        status=ScaffoldModuleStatus.SCAFFOLDED,
        origin=proposal.origin,
        focus=proposal.focus,
    )


def _relationship_metadata(proposal: RelationshipProposal) -> RelationshipMetadata:
    return RelationshipMetadata(
        relationship_type=proposal.relationship_type,
        target_id=proposal.target_id,
        target_title=proposal.target_title,
        vault_status=(
            RelationshipVaultStatus.FOUND
            if proposal.target_id
            else RelationshipVaultStatus.MISSING
        ),
        learning_role=proposal.learning_role,
        confidence=proposal.confidence,
        status=RelationshipStatus.PROPOSED,
    )


def _load_concept(workspace: WorkspaceContext, concept_id: str | None) -> dict[str, Any] | None:
    if not concept_id:
        return None
    with workspace.index_engine.connect() as connection:
        return concepts.get_concept(connection, concept_id)


def _domains_for_concept(workspace: WorkspaceContext, concept_id: str) -> list[str]:
    from studium.index.repositories import domains

    with workspace.index_engine.connect() as connection:
        rows = domains.list_domains_for_concept(connection, concept_id)
    return [str(row["domain"]) for row in rows]


def _concept_directory(workspace: WorkspaceContext) -> str:
    with workspace.index_engine.connect() as connection:
        rows = concepts.list_concepts(connection)
    parents = Counter(
        str(row["file_path"]).rsplit("/", 1)[0]
        for row in rows
        if "/" in str(row["file_path"])
    )
    return parents.most_common(1)[0][0] if parents else "concepts"


def _concept_type(value: Any, intent: str) -> ConceptType:
    if value is not None:
        try:
            return ConceptType(str(value))
        except ValueError:
            pass
    lower = intent.casefold()
    if any(token in lower for token in ("algorithm", "sort", "search", "gradient descent")):
        return ConceptType.ALGORITHM
    if any(token in lower for token in ("equation", "theorem", "calculus", "probability")):
        return ConceptType.MATHEMATICAL_CONCEPT
    if any(token in lower for token in ("python", "function", "class", "programming")):
        return ConceptType.PROGRAMMING_CONCEPT
    if any(token in lower for token in ("architecture", "distributed", "system design")):
        return ConceptType.SYSTEM_DESIGN_CONCEPT
    return ConceptType.GENERAL_CONCEPT


def _clean_domains(value: Any, intent: str) -> list[str]:
    raw = cast(list[Any], value) if isinstance(value, list) else []
    domains = []
    for item in raw:
        normalized = _DOMAIN_SANITIZE.sub("_", str(item).casefold()).strip("_")
        if normalized and normalized not in domains:
            domains.append(normalized)
    if domains:
        return domains
    lower = intent.casefold()
    heuristics = {
        "machine_learning": ("gradient", "neural", "model", "regression", "embedding"),
        "mathematics": ("equation", "theorem", "calculus", "probability"),
        "computer_science": ("algorithm", "data structure", "complexity"),
        "software_engineering": ("python", "code", "architecture", "testing"),
    }
    return [
        domain
        for domain, tokens in heuristics.items()
        if any(token in lower for token in tokens)
    ] or ["general"]


def _optional_module_type(value: Any) -> ScaffoldModuleType | None:
    if value is None:
        return None
    try:
        return ScaffoldModuleType(str(value))
    except ValueError:
        return None


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [
        cast(dict[str, Any], item)
        for item in cast(list[Any], value)
        if isinstance(item, dict)
    ]


def _candidate_evidence(candidate: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    fields = candidate.get("matched_fields")
    if isinstance(fields, list):
        evidence.extend(str(item).replace("_", " ") for item in cast(list[Any], fields))
    modules = candidate.get("matching_modules")
    if isinstance(modules, list):
        for module in cast(list[Any], modules)[:2]:
            if isinstance(module, dict):
                evidence.append(
                    f"module: {cast(dict[str, Any], module).get('title', 'match')}"
                )
    return evidence or ["hybrid retrieval candidate"]


def _decode_draft(row: dict[str, Any]) -> dict[str, Any]:
    value = dict(row)
    raw = value.pop("recommendation_json", None)
    value["recommendation"] = None if raw is None else json.loads(str(raw))
    return value
