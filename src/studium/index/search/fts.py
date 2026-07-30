"""Weighted SQLite FTS5 search for concepts and modules."""

from __future__ import annotations

import re

from sqlalchemy import Engine, text

from studium.index.repositories import concepts, domains, scaffold_modules
from studium.index.repositories.fts import CONCEPT_FTS_TABLE, MODULE_FTS_TABLE
from studium.index.search.models import LexicalConceptHit, LexicalModuleHit
from studium.index.search.weights import CONCEPT_FTS_WEIGHTS, MODULE_FTS_WEIGHTS

_TOKEN_SPLIT = re.compile(r"[^\w]+", re.UNICODE)


def build_fts_match_query(query_text: str) -> str | None:
    """Convert user text into a safe FTS5 MATCH expression (AND of quoted tokens)."""
    tokens: list[str] = []
    for part in _TOKEN_SPLIT.split(query_text):
        token = part.strip()
        if not token:
            continue
        # Escape embedded double quotes for FTS5 phrase/token quoting.
        escaped = token.replace('"', '""')
        tokens.append(f'"{escaped}"')
    if not tokens:
        return None
    return " ".join(tokens)


def search_concepts_fts(
    engine: Engine,
    query_text: str,
    *,
    limit: int = 20,
) -> list[LexicalConceptHit]:
    """Rank concepts with BM25 over weighted FTS columns."""
    match = build_fts_match_query(query_text)
    if match is None or limit <= 0:
        return []

    weight_sql = ", ".join(str(weight) for weight in CONCEPT_FTS_WEIGHTS)
    sql = text(
        f"""
        SELECT concept_id,
               bm25({CONCEPT_FTS_TABLE}, {weight_sql}) AS score,
               title,
               aliases,
               domains,
               overview
        FROM {CONCEPT_FTS_TABLE}
        WHERE {CONCEPT_FTS_TABLE} MATCH :match
        ORDER BY score, concept_id
        LIMIT :limit
        """
    )
    hits: list[LexicalConceptHit] = []
    with engine.connect() as connection:
        rows = connection.execute(sql, {"match": match, "limit": int(limit)}).mappings().all()
        for rank, row in enumerate(rows, start=1):
            concept_id = str(row["concept_id"])
            concept = concepts.get_concept(connection, concept_id)
            domain_rows = domains.list_domains_for_concept(connection, concept_id)
            matched_fields = _matched_concept_fields(query_text, row)
            hits.append(
                LexicalConceptHit(
                    concept_id=concept_id,
                    canonical_title=(
                        str(concept["canonical_title"])
                        if concept is not None
                        else str(row["title"])
                    ),
                    rank=rank,
                    score=float(row["score"]),
                    matched_fields=matched_fields,
                    overview_excerpt=_excerpt(str(row["overview"] or "")),
                    concept_type=None if concept is None else str(concept["concept_type"]),
                    domains=[str(item["domain"]) for item in domain_rows],
                )
            )
    return hits


def search_modules_fts(
    engine: Engine,
    query_text: str,
    *,
    limit: int = 20,
) -> list[LexicalModuleHit]:
    """Rank scaffold modules with BM25; preserve parent concept location."""
    match = build_fts_match_query(query_text)
    if match is None or limit <= 0:
        return []

    weight_sql = ", ".join(str(weight) for weight in MODULE_FTS_WEIGHTS)
    sql = text(
        f"""
        SELECT module_id,
               concept_id,
               bm25({MODULE_FTS_TABLE}, {weight_sql}) AS score,
               title,
               type,
               focus,
               body
        FROM {MODULE_FTS_TABLE}
        WHERE {MODULE_FTS_TABLE} MATCH :match
        ORDER BY score, module_id
        LIMIT :limit
        """
    )
    hits: list[LexicalModuleHit] = []
    with engine.connect() as connection:
        rows = connection.execute(sql, {"match": match, "limit": int(limit)}).mappings().all()
        for rank, row in enumerate(rows, start=1):
            module_id = str(row["module_id"])
            concept_id = str(row["concept_id"])
            module = scaffold_modules.get_scaffold_module(connection, module_id)
            concept = concepts.get_concept(connection, concept_id)
            hits.append(
                LexicalModuleHit(
                    module_id=module_id,
                    concept_id=concept_id,
                    title=str(row["title"]),
                    module_type=str(row["type"]) if row["type"] else None,
                    focus=str(row["focus"]) if row["focus"] else None,
                    heading=None if module is None else module.get("heading"),
                    anchor=None if module is None else module.get("anchor"),
                    rank=rank,
                    score=float(row["score"]),
                    matched_fields=_matched_module_fields(query_text, row),
                    parent_canonical_title=(
                        None if concept is None else str(concept["canonical_title"])
                    ),
                )
            )
    return hits


def _matched_concept_fields(query_text: str, row: object) -> list[str]:
    mapping = {str(key): value for key, value in dict(row).items()}  # type: ignore[arg-type]
    return _fields_containing_tokens(
        query_text,
        {
            "title": str(mapping.get("title") or ""),
            "aliases": str(mapping.get("aliases") or ""),
            "domains": str(mapping.get("domains") or ""),
            "overview": str(mapping.get("overview") or ""),
        },
    )


def _matched_module_fields(query_text: str, row: object) -> list[str]:
    mapping = {str(key): value for key, value in dict(row).items()}  # type: ignore[arg-type]
    return _fields_containing_tokens(
        query_text,
        {
            "title": str(mapping.get("title") or ""),
            "type": str(mapping.get("type") or ""),
            "focus": str(mapping.get("focus") or ""),
            "body": str(mapping.get("body") or ""),
        },
    )


def _fields_containing_tokens(query_text: str, fields: dict[str, str]) -> list[str]:
    tokens = [part.casefold() for part in _TOKEN_SPLIT.split(query_text) if part.strip()]
    if not tokens:
        return []
    matched: list[str] = []
    for name, value in fields.items():
        haystack = value.casefold()
        if any(token in haystack for token in tokens):
            matched.append(name)
    return matched


def _excerpt(text_value: str, *, max_len: int = 160) -> str | None:
    cleaned = " ".join(text_value.split())
    if not cleaned:
        return None
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1] + "…"
