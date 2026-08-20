"""Deterministic recommendation assembly and verification."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy.engine import Engine

from studium.index.graph.encounters import compare_learning_encounter, normalize_source_identity
from studium.index.graph.models import EncounterOutcome
from studium.index.repositories import aliases, concepts
from studium.index.search.models import (
    ConceptSearchResult,
    ExactMatchType,
    IdentityMatch,
    ResolutionState,
)
from studium.llm.protocol import LLMProvider
from studium.llm.reasoning.orchestrate import (
    parse_clarification,
    parse_identity_decision,
    reason_clarification,
    reason_identity,
    reason_new_concept,
)
from studium.llm.reasoning.schemas import IdentityClassification
from studium.recommend.models import (
    AddLearningEncounterRecommendation,
    AddScaffoldModuleRecommendation,
    AliasSuggestion,
    BacklogCandidate,
    CompletionStatus,
    ConfidenceLevel,
    CreateNewConceptRecommendation,
    FailureStage,
    GraphPositionSuggestion,
    MarkRedundantRecommendation,
    ReasoningMode,
    RecommendationFailure,
    RequestClarificationRecommendation,
    UpdateLearningEncounterRecommendation,
    UseExistingConceptRecommendation,
)


def _concept_exists(engine: Engine, concept_id: str) -> bool:
    with engine.connect() as connection:
        return concepts.get_concept(connection, concept_id) is not None


def _alias_collision(engine: Engine, alias: str, *, target_concept_id: str) -> list[str]:
    from studium.index.normalize import normalize_title

    normalized = normalize_title(alias)
    with engine.connect() as connection:
        rows = aliases.list_aliases_by_normalized_alias(connection, normalized)
        title_rows = concepts.list_concepts_by_normalized_title(connection, normalized)
    ids = {
        str(row["concept_id"])
        for row in [*rows, *title_rows]
        if str(row["concept_id"]) != target_concept_id
    }
    return sorted(ids)


def assemble_recommendation_failure(
    *,
    query: str,
    index_revision: int,
    stage: FailureStage,
    error_code: str,
    message: str,
    search: ConceptSearchResult | None = None,
) -> RecommendationFailure:
    return RecommendationFailure(
        query=query,
        index_revision=index_revision,
        failure_stage=stage,
        error_code=error_code,
        message=message,
        fallback_search_result=None if search is None else search.model_dump(mode="json"),
    )


def recommend(
    engine: Engine,
    *,
    search: ConceptSearchResult,
    provider: LLMProvider | None = None,
    source_type: str | None = None,
    source_title: str | None = None,
    unit: str | None = None,
    module_intent: bool = False,
) -> (
    UseExistingConceptRecommendation
    | CreateNewConceptRecommendation
    | AddLearningEncounterRecommendation
    | UpdateLearningEncounterRecommendation
    | AddScaffoldModuleRecommendation
    | MarkRedundantRecommendation
    | RequestClarificationRecommendation
    | RecommendationFailure
):
    """Assemble a recommendation from search (+ optional LLM), without mutating notes."""
    query_text = search.query.text
    revision = search.index_revision

    has_source_intent = bool(source_type or source_title or unit)
    if has_source_intent and not (source_type and source_title):
        return RequestClarificationRecommendation(
            confidence=ConfidenceLevel.LOW,
            completion_status=CompletionStatus.COMPLETE,
            reasoning_mode=ReasoningMode.DETERMINISTIC,
            index_revision=revision,
            evidence=["incomplete_source_intent"],
            ambiguity_type="incomplete_source_intent",
            candidate_interpretations=[],
            clarification_message=(
                "Learning encounter intent requires both source_type and source_title."
            ),
        )

    exact_match = (
        search.exact_matches[0]
        if search.resolution_state == ResolutionState.EXACT_MATCH and len(search.exact_matches) == 1
        else None
    )
    intent_target_id = exact_match.concept_id if exact_match is not None else None

    # Explicit source intent takes precedence over generic exact reuse.
    if (
        source_type
        and source_title
        and intent_target_id
        and _concept_exists(engine, intent_target_id)
    ):
        candidate = normalize_source_identity(
            source_type=source_type, source_title=source_title, unit=unit
        )
        comparison = compare_learning_encounter(
            engine, concept_id=intent_target_id, candidate=candidate
        )
        if comparison.outcome == EncounterOutcome.EXACT_SAME_ENCOUNTER:
            return MarkRedundantRecommendation(
                confidence=ConfidenceLevel.HIGH,
                completion_status=CompletionStatus.COMPLETE,
                reasoning_mode=ReasoningMode.DETERMINISTIC,
                index_revision=revision,
                evidence=["exact_same_encounter"],
                target_concept_id=intent_target_id,
                reason="Learning encounter already indexed",
            )
        if comparison.outcome == EncounterOutcome.SAME_SOURCE_ENRICH_EXISTING:
            assert comparison.matched_encounter_id is not None
            return UpdateLearningEncounterRecommendation(
                confidence=ConfidenceLevel.HIGH,
                completion_status=CompletionStatus.COMPLETE,
                reasoning_mode=ReasoningMode.DETERMINISTIC,
                index_revision=revision,
                evidence=["same_source_enrich_existing"],
                target_concept_id=intent_target_id,
                existing_encounter_id=comparison.matched_encounter_id,
                enrichment_fields=["unit"] if unit else [],
                comparison_outcome=comparison.outcome.value,
            )
        if comparison.outcome == EncounterOutcome.AMBIGUOUS:
            return RequestClarificationRecommendation(
                confidence=ConfidenceLevel.LOW,
                completion_status=CompletionStatus.COMPLETE,
                reasoning_mode=ReasoningMode.DETERMINISTIC,
                index_revision=revision,
                evidence=["ambiguous_learning_encounter"],
                ambiguity_type="learning_encounter_collision",
                candidate_interpretations=[intent_target_id],
                clarification_message=(
                    "Multiple existing learning encounters conflict with the supplied "
                    "source metadata."
                ),
            )
        return AddLearningEncounterRecommendation(
            confidence=ConfidenceLevel.MEDIUM,
            completion_status=CompletionStatus.COMPLETE,
            reasoning_mode=ReasoningMode.DETERMINISTIC,
            index_revision=revision,
            evidence=[comparison.outcome.value],
            target_concept_id=intent_target_id,
            source_type=source_type,
            source_title=source_title,
            unit=unit,
            comparison_outcome=comparison.outcome.value,
        )

    # Explicit module intent also takes precedence over generic exact reuse.
    if module_intent and intent_target_id and _concept_exists(engine, intent_target_id):
        return AddScaffoldModuleRecommendation(
            confidence=ConfidenceLevel.MEDIUM,
            completion_status=CompletionStatus.COMPLETE,
            reasoning_mode=ReasoningMode.DETERMINISTIC,
            index_revision=revision,
            evidence=["module_intent_target"],
            target_concept_id=intent_target_id,
            module_type="derivation",
            module_title=query_text[:80] or "New module",
            focus=None,
        )

    # Exact identity → use existing
    if search.resolution_state == ResolutionState.EXACT_MATCH and search.exact_matches:
        match = search.exact_matches[0]
        if not _concept_exists(engine, match.concept_id):
            return assemble_recommendation_failure(
                query=query_text,
                index_revision=revision,
                stage=FailureStage.DETERMINISTIC_VERIFICATION,
                error_code="missing_target_concept",
                message=f"Exact match concept {match.concept_id} not in index",
                search=search,
            )
        return UseExistingConceptRecommendation(
            confidence=ConfidenceLevel.HIGH,
            completion_status=CompletionStatus.COMPLETE,
            reasoning_mode=ReasoningMode.DETERMINISTIC,
            index_revision=revision,
            evidence=[f"exact:{match.match_type.value}"],
            target_concept_id=match.concept_id,
            match_classification="exact_identity",
            matching_module_ids=[m.module_id for m in search.module_hits[:5]],
        )

    # Ambiguous identity → clarification
    if search.resolution_state == ResolutionState.AMBIGUOUS_RESULTS:
        return RequestClarificationRecommendation(
            confidence=ConfidenceLevel.MEDIUM,
            completion_status=CompletionStatus.COMPLETE,
            reasoning_mode=ReasoningMode.DETERMINISTIC,
            index_revision=revision,
            evidence=["ambiguous_identity"],
            ambiguity_type="identity_collision",
            candidate_interpretations=[m.concept_id for m in search.exact_matches],
            clarification_message="Multiple concepts match this title or alias.",
        )

    # LLM path when provider supplied
    if provider is not None:
        identity = reason_identity(provider, search)
        decision = parse_identity_decision(identity)
        if decision is None:
            return assemble_recommendation_failure(
                query=query_text,
                index_revision=revision,
                stage=FailureStage.STRUCTURED_OUTPUT_VALIDATION,
                error_code=identity.error_code or "identity_failed",
                message=identity.message or "Identity reasoning failed",
                search=search,
            )
        if (
            decision.classification == IdentityClassification.SAME_CONCEPT
            and decision.selected_concept_id
            and decision.selected_concept_id
            in {m.concept_id for m in search.exact_matches}
            | {candidate.concept_id for candidate in search.ranked_concepts}
            and _concept_exists(engine, decision.selected_concept_id)
        ):
            if (source_type and source_title) or module_intent:
                verified = search.model_copy(
                    update={
                        "resolution_state": ResolutionState.EXACT_MATCH,
                        "exact_matches": [
                            IdentityMatch(
                                concept_id=decision.selected_concept_id,
                                canonical_title=next(
                                    candidate.canonical_title
                                    for candidate in search.ranked_concepts
                                    if candidate.concept_id == decision.selected_concept_id
                                ),
                                match_type=ExactMatchType.CANONICAL_TITLE,
                            )
                        ],
                    }
                )
                return recommend(
                    engine,
                    search=verified,
                    provider=None,
                    source_type=source_type,
                    source_title=source_title,
                    unit=unit,
                    module_intent=module_intent,
                )
            return UseExistingConceptRecommendation(
                confidence=ConfidenceLevel(decision.confidence.value),
                completion_status=CompletionStatus.COMPLETE,
                reasoning_mode=ReasoningMode.LLM,
                index_revision=revision,
                evidence=[*list(decision.evidence), decision.rationale],
                target_concept_id=decision.selected_concept_id,
                match_classification=decision.classification.value,
            )

        clarification = reason_clarification(provider, search)
        clar = parse_clarification(clarification)
        if clar is not None and clar.needs_clarification:
            return RequestClarificationRecommendation(
                confidence=ConfidenceLevel(clar.confidence.value),
                completion_status=CompletionStatus.COMPLETE,
                reasoning_mode=ReasoningMode.LLM,
                index_revision=revision,
                evidence=list(clar.evidence),
                ambiguity_type=clar.ambiguity_type,
                candidate_interpretations=list(clar.candidate_interpretations),
                clarification_message=clar.clarification_message,
            )

        analysis = reason_new_concept(provider, search)
        if not analysis.ok or analysis.data is None:
            # Fallback: create-new with search evidence only
            return _fallback_create_new(search, query_text, revision)

        data = analysis.data
        backlog = [
            BacklogCandidate(title=title, reason="missing_prerequisite")
            for title in data.get("prerequisite_titles", [])
        ]
        candidate_ids = {candidate.concept_id for candidate in search.ranked_concepts}
        graph_positions: list[GraphPositionSuggestion] = []
        for raw in data.get("graph_positions", []):
            if not isinstance(raw, dict):
                continue
            position = cast(dict[str, Any], raw)
            target_id = position.get("target_concept_id")
            if target_id is not None and str(target_id) not in candidate_ids:
                continue
            graph_positions.append(GraphPositionSuggestion.model_validate(position))
        return CreateNewConceptRecommendation(
            confidence=ConfidenceLevel(str(data.get("confidence", "medium"))),
            completion_status=CompletionStatus.COMPLETE,
            reasoning_mode=ReasoningMode.LLM,
            index_revision=revision,
            evidence=list(data.get("evidence", [])),
            suggested_title=query_text,
            suggested_concept_type=str(data.get("suggested_concept_type", "general_concept")),
            suggested_domains=[str(d) for d in data.get("suggested_domains", [])],
            scope_summary=str(data.get("scope_summary", "")),
            backlog_candidates=backlog,
            possible_match_ids=[c.concept_id for c in search.ranked_concepts[:5]],
            graph_positions=graph_positions,
        )

    # No provider: deterministic fallbacks from search state
    if search.resolution_state == ResolutionState.NO_RESULTS:
        return _fallback_create_new(search, query_text, revision)
    if search.ranked_concepts:
        top = search.ranked_concepts[0]
        if _concept_exists(engine, top.concept_id) and top.channels:
            return UseExistingConceptRecommendation(
                confidence=ConfidenceLevel.LOW,
                completion_status=CompletionStatus.FALLBACK,
                reasoning_mode=ReasoningMode.FALLBACK,
                index_revision=revision,
                evidence=["top_hybrid_candidate_without_llm"],
                warnings=["LLM provider not supplied; low-confidence reuse suggestion"],
                target_concept_id=top.concept_id,
                match_classification="related_candidate",
            )
    return _fallback_create_new(search, query_text, revision)


def _fallback_create_new(
    search: ConceptSearchResult,
    query_text: str,
    revision: int,
) -> CreateNewConceptRecommendation:
    return CreateNewConceptRecommendation(
        confidence=ConfidenceLevel.LOW,
        completion_status=CompletionStatus.FALLBACK,
        reasoning_mode=ReasoningMode.FALLBACK,
        index_revision=revision,
        evidence=["no_strong_match"],
        warnings=["Created without LLM analysis"],
        suggested_title=query_text,
        suggested_concept_type="general_concept",
        suggested_domains=[],
        scope_summary="",
        backlog_candidates=[],
        possible_match_ids=[c.concept_id for c in search.ranked_concepts[:5]],
    )


def assemble_alias_suggestion(
    engine: Engine,
    *,
    alias: str,
    target_concept_id: str,
    classification: str,
    confidence: ConfidenceLevel,
    evidence: list[str] | None = None,
) -> AliasSuggestion | RecommendationFailure:
    """Verify alias collisions before accepting a suggestion."""
    if not alias.strip():
        return assemble_recommendation_failure(
            query=alias,
            index_revision=0,
            stage=FailureStage.DETERMINISTIC_VERIFICATION,
            error_code="empty_alias",
            message="Alias must be non-empty",
        )
    if not _concept_exists(engine, target_concept_id):
        return assemble_recommendation_failure(
            query=alias,
            index_revision=0,
            stage=FailureStage.DETERMINISTIC_VERIFICATION,
            error_code="missing_target_concept",
            message=f"Target concept {target_concept_id} not found",
        )
    from studium.index.normalize import normalize_title

    with engine.connect() as connection:
        target = concepts.get_concept(connection, target_concept_id)
    assert target is not None
    if normalize_title(alias) == str(target["normalized_title"]):
        return assemble_recommendation_failure(
            query=alias,
            index_revision=0,
            stage=FailureStage.DETERMINISTIC_VERIFICATION,
            error_code="alias_matches_target_title",
            message="Alias must differ from the target concept's canonical title",
        )
    collisions = _alias_collision(engine, alias, target_concept_id=target_concept_id)
    warnings_evidence = list(evidence or [])
    if collisions:
        warnings_evidence.append(f"alias_collision:{','.join(collisions)}")
    return AliasSuggestion(
        alias=alias,
        target_concept_id=target_concept_id,
        classification=classification,
        confidence=confidence if not collisions else ConfidenceLevel.LOW,
        evidence=warnings_evidence,
    )


def calculate_recommendation_confidence(
    *,
    base: ConfidenceLevel,
    downgrade_steps: int = 0,
) -> ConfidenceLevel:
    order = [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
    index = order.index(base)
    return order[min(len(order) - 1, index + max(0, downgrade_steps))]
