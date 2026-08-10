"""Recommendation assembly tests."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from studium.index import begin_connection
from studium.index.repositories import concepts
from studium.index.search.models import (
    ConceptSearchQuery,
    ConceptSearchResult,
    ExactMatchType,
    IdentityMatch,
    RankedConceptCandidate,
    ResolutionState,
    SearchStatus,
)
from studium.recommend import recommend
from studium.recommend.models import (
    CreateNewConceptRecommendation,
    RequestClarificationRecommendation,
    UseExistingConceptRecommendation,
)


def _upsert(engine: Engine, concept_id: str, title: str) -> None:
    with begin_connection(engine) as connection:
        concepts.upsert_concept(
            connection,
            {
                "concept_id": concept_id,
                "canonical_title": title,
                "concept_type": "atomic_concept",
                "status": "active",
                "review_status": "draft",
                "vault_status": "active",
                "file_path": f"concepts/{concept_id}.md",
                "note_schema_version": 2,
                "validity_state": "valid",
                "indexed_revision": 1,
                "note_created_at": "2026-01-01T00:00:00Z",
                "note_updated_at": "2026-01-01T00:00:00Z",
            },
        )


def test_use_existing_from_exact_match(initialized_engine: Engine) -> None:
    _upsert(initialized_engine, "concept_sgd", "SGD")
    search = ConceptSearchResult(
        query=ConceptSearchQuery(text="SGD"),
        index_revision=1,
        search_status=SearchStatus.COMPLETE,
        resolution_state=ResolutionState.EXACT_MATCH,
        exact_matches=[
            IdentityMatch(
                concept_id="concept_sgd",
                canonical_title="SGD",
                match_type=ExactMatchType.CANONICAL_TITLE,
            )
        ],
    )
    result = recommend(initialized_engine, search=search)
    assert isinstance(result, UseExistingConceptRecommendation)
    assert result.target_concept_id == "concept_sgd"
    assert result.reasoning_mode.value == "deterministic"


def test_ambiguous_requests_clarification(initialized_engine: Engine) -> None:
    search = ConceptSearchResult(
        query=ConceptSearchQuery(text="SGD"),
        index_revision=1,
        search_status=SearchStatus.COMPLETE,
        resolution_state=ResolutionState.AMBIGUOUS_RESULTS,
        exact_matches=[
            IdentityMatch(
                concept_id="a",
                canonical_title="A",
                match_type=ExactMatchType.APPROVED_ALIAS,
            ),
            IdentityMatch(
                concept_id="b",
                canonical_title="B",
                match_type=ExactMatchType.APPROVED_ALIAS,
            ),
        ],
    )
    result = recommend(initialized_engine, search=search)
    assert isinstance(result, RequestClarificationRecommendation)


def test_no_results_create_new_fallback(initialized_engine: Engine) -> None:
    search = ConceptSearchResult(
        query=ConceptSearchQuery(text="Brand New Idea"),
        index_revision=1,
        search_status=SearchStatus.COMPLETE,
        resolution_state=ResolutionState.NO_RESULTS,
    )
    result = recommend(initialized_engine, search=search)
    assert isinstance(result, CreateNewConceptRecommendation)
    assert result.suggested_title == "Brand New Idea"


def test_recommend_does_not_mutate_notes(initialized_engine: Engine) -> None:
    _upsert(initialized_engine, "concept_x", "X")
    search = ConceptSearchResult(
        query=ConceptSearchQuery(text="X"),
        index_revision=1,
        search_status=SearchStatus.COMPLETE,
        resolution_state=ResolutionState.RELATED_RESULTS,
        ranked_concepts=[
            RankedConceptCandidate(
                concept_id="concept_x",
                canonical_title="X",
                fused_rank=1,
                fused_score=0.1,
            )
        ],
    )
    recommend(initialized_engine, search=search)
    with begin_connection(initialized_engine) as connection:
        row = concepts.get_concept(connection, "concept_x")
    assert row is not None
    assert row["canonical_title"] == "X"
