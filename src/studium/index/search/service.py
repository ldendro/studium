"""Thin lexical search facade: deterministic lookup first, then weighted FTS."""

from __future__ import annotations

from sqlalchemy import Engine

from studium.index.search.fts import search_concepts_fts, search_modules_fts
from studium.index.search.lookup import resolve_concept_identity
from studium.index.search.models import LexicalSearchResult, ResolutionState


def search_concepts_lexical(
    engine: Engine,
    query_text: str,
    *,
    concept_limit: int = 20,
    module_limit: int = 20,
    include_modules: bool = True,
) -> LexicalSearchResult:
    """Run Tier 0 identity lookup, then optional weighted FTS.

    Does not fuse vectors or invoke LLM reasoning (those belong to later branches).
    """
    identity = resolve_concept_identity(engine, query_text)
    warnings: list[str] = []
    diagnostics: dict[str, object] = {
        "deterministic_match_count": len(identity.matches),
        "normalized_query": identity.normalized_query,
    }

    if identity.is_unique:
        return LexicalSearchResult(
            query=query_text,
            resolution_state=ResolutionState.EXACT_MATCH,
            identity=identity,
            concept_hits=[],
            module_hits=[],
            warnings=warnings,
            diagnostics=diagnostics,
        )

    if identity.is_ambiguous:
        warnings.append(
            "Multiple concepts share this normalized title or approved alias; "
            "identity is ambiguous."
        )
        return LexicalSearchResult(
            query=query_text,
            resolution_state=ResolutionState.AMBIGUOUS_RESULTS,
            identity=identity,
            concept_hits=[],
            module_hits=[],
            warnings=warnings,
            diagnostics=diagnostics,
        )

    concept_hits = search_concepts_fts(engine, query_text, limit=concept_limit)
    module_hits = (
        search_modules_fts(engine, query_text, limit=module_limit) if include_modules else []
    )
    diagnostics["concept_fts_count"] = len(concept_hits)
    diagnostics["module_fts_count"] = len(module_hits)

    if not concept_hits and not module_hits:
        state = ResolutionState.NO_RESULTS
    else:
        state = ResolutionState.RELATED_RESULTS

    return LexicalSearchResult(
        query=query_text,
        resolution_state=state,
        identity=identity,
        concept_hits=concept_hits,
        module_hits=module_hits,
        warnings=warnings,
        diagnostics=diagnostics,
    )
