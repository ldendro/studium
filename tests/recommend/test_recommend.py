"""Recommendation assembly tests."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from studium.index import begin_connection
from studium.index.repositories import concepts
from studium.index.search.models import (
    ChannelContribution,
    ConceptSearchQuery,
    ConceptSearchResult,
    ExactMatchType,
    IdentityMatch,
    RankedConceptCandidate,
    ResolutionState,
    SearchChannel,
    SearchStatus,
)
from studium.llm import DeterministicLLMProvider
from studium.recommend import recommend
from studium.recommend.models import (
    AddLearningEncounterRecommendation,
    AddScaffoldModuleRecommendation,
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


def test_source_type_is_normalized_for_encounter_recommendation(
    initialized_engine: Engine,
) -> None:
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

    result = recommend(
        initialized_engine,
        search=search,
        source_type="Book",
        source_title="Hands-On Machine Learning",
    )

    assert isinstance(result, AddLearningEncounterRecommendation)
    assert result.source_type.value == "book"


def test_invalid_source_type_requests_clarification(initialized_engine: Engine) -> None:
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

    result = recommend(
        initialized_engine,
        search=search,
        source_type="unsupported",
        source_title="Source",
    )

    assert isinstance(result, RequestClarificationRecommendation)
    assert result.ambiguity_type == "invalid_source_type"


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


def test_identity_reasoning_failure_uses_deterministic_fallback(
    initialized_engine: Engine,
) -> None:
    _upsert(initialized_engine, "concept_x", "Existing Concept")
    search = ConceptSearchResult(
        query=ConceptSearchQuery(text="Existing related topic"),
        index_revision=1,
        search_status=SearchStatus.COMPLETE,
        resolution_state=ResolutionState.RELATED_RESULTS,
        ranked_concepts=[
            RankedConceptCandidate(
                concept_id="concept_x",
                canonical_title="Existing Concept",
                fused_rank=1,
                fused_score=0.1,
                channels=[ChannelContribution(channel=SearchChannel.FTS, rank=1, score=1.0)],
            )
        ],
    )

    result = recommend(
        initialized_engine,
        search=search,
        provider=DeterministicLLMProvider(default_response={}),
    )

    assert isinstance(result, UseExistingConceptRecommendation)
    assert result.completion_status.value == "fallback"
    assert any("Identity reasoning failed" in warning for warning in result.warnings)


def test_module_intent_uses_module_reasoning(initialized_engine: Engine) -> None:
    _upsert(initialized_engine, "concept_x", "Existing Concept")
    search = ConceptSearchResult(
        query=ConceptSearchQuery(text="Add a derivation module"),
        index_revision=1,
        search_status=SearchStatus.COMPLETE,
        resolution_state=ResolutionState.RELATED_RESULTS,
        ranked_concepts=[
            RankedConceptCandidate(
                concept_id="concept_x",
                canonical_title="Existing Concept",
                fused_rank=1,
                fused_score=0.1,
            )
        ],
    )

    def handler(system_prompt: str, _user_prompt: str) -> dict[str, object]:
        if "whether a query refers" in system_prompt:
            return {
                "classification": "distinct_related_concept",
                "selected_concept_id": None,
                "confidence": "medium",
                "rationale": "Related but distinct.",
                "evidence": [],
            }
        return {
            "classification": "add_to_existing",
            "target_concept_id": "concept_x",
            "suggested_module_type": "derivation",
            "suggested_title": "Derivation",
            "suggested_focus": "Step-by-step derivation",
            "confidence": "high",
            "rationale": "The request targets the existing concept.",
            "evidence": ["module_intent"],
        }

    result = recommend(
        initialized_engine,
        search=search,
        provider=DeterministicLLMProvider(handler=handler),
        module_intent=True,
    )

    assert isinstance(result, AddScaffoldModuleRecommendation)
    assert result.target_concept_id == "concept_x"


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
