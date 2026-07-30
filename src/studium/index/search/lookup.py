"""Deterministic concept identity lookup (Tier 0)."""

from __future__ import annotations

from sqlalchemy import Engine

from studium.index.normalize import normalize_for_lookup
from studium.index.repositories import aliases, concepts
from studium.index.search.models import ExactMatchType, IdentityMatch, IdentityResolution


def resolve_concept_identity(engine: Engine, query_text: str) -> IdentityResolution:
    """Resolve a query to concept identity without FTS.

    Order:
    1. Exact ``concept_id`` match
    2. Normalized canonical-title equality
    3. Approved-alias equality on ``normalized_alias``

    Multiple alias/title hits are returned as ambiguous (no winner).
    """
    normalized = normalize_for_lookup(query_text)
    with engine.connect() as connection:
        by_id = concepts.get_concept(connection, query_text.strip())
        if by_id is not None:
            return IdentityResolution(
                query=query_text,
                normalized_query=normalized,
                matches=[
                    IdentityMatch(
                        concept_id=str(by_id["concept_id"]),
                        canonical_title=str(by_id["canonical_title"]),
                        match_type=ExactMatchType.STABLE_ID,
                    )
                ],
                is_ambiguous=False,
            )

        if not normalized:
            return IdentityResolution(
                query=query_text,
                normalized_query=normalized,
                matches=[],
                is_ambiguous=False,
            )

        title_rows = concepts.list_concepts_by_normalized_title(connection, normalized)
        if title_rows:
            matches = [
                IdentityMatch(
                    concept_id=str(row["concept_id"]),
                    canonical_title=str(row["canonical_title"]),
                    match_type=ExactMatchType.CANONICAL_TITLE,
                )
                for row in title_rows
            ]
            return IdentityResolution(
                query=query_text,
                normalized_query=normalized,
                matches=matches,
                is_ambiguous=len(matches) > 1,
            )

        alias_rows = aliases.list_aliases_by_normalized_alias(connection, normalized)
        if not alias_rows:
            return IdentityResolution(
                query=query_text,
                normalized_query=normalized,
                matches=[],
                is_ambiguous=False,
            )

        matches: list[IdentityMatch] = []
        seen: set[str] = set()
        for alias_row in alias_rows:
            concept_id = str(alias_row["concept_id"])
            if concept_id in seen:
                continue
            seen.add(concept_id)
            concept = concepts.get_concept(connection, concept_id)
            if concept is None:
                continue
            matches.append(
                IdentityMatch(
                    concept_id=concept_id,
                    canonical_title=str(concept["canonical_title"]),
                    match_type=ExactMatchType.APPROVED_ALIAS,
                    matched_alias=str(alias_row["alias"]),
                )
            )
        return IdentityResolution(
            query=query_text,
            normalized_query=normalized,
            matches=matches,
            is_ambiguous=len(matches) > 1,
        )
