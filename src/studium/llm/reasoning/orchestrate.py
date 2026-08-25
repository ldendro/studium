"""Identity-first reasoning orchestration over search/graph context."""

from __future__ import annotations

import json
from typing import Any

from studium.index.search.models import ConceptSearchResult, ResolutionState
from studium.llm.protocol import LLMProvider, StructuredGenerationResult
from studium.llm.reasoning.registry import (
    CLARIFICATION_TASK,
    IDENTITY_TASK,
    MODULE_INTENT_TASK,
    NEW_CONCEPT_TASK,
    RELATIONSHIP_TASK,
)
from studium.llm.reasoning.schemas import (
    ClarificationDecision,
    ConceptIdentityDecision,
    ConfidenceLevel,
    IdentityClassification,
)
from studium.llm.runner import run_reasoning_task


def _candidates_json(search: ConceptSearchResult, *, limit: int = 8) -> str:
    rows: list[dict[str, Any]] = []
    for hit in search.ranked_concepts[:limit]:
        rows.append(
            {
                "concept_id": hit.concept_id,
                "canonical_title": hit.canonical_title,
                "concept_type": hit.concept_type,
                "domains": hit.domains,
                "fused_rank": hit.fused_rank,
                "fused_score": hit.fused_score,
            }
        )
    for match in search.exact_matches:
        rows.insert(
            0,
            {
                "concept_id": match.concept_id,
                "canonical_title": match.canonical_title,
                "match_type": match.match_type.value,
            },
        )
    return json.dumps(rows)


def reason_identity(
    provider: LLMProvider,
    search: ConceptSearchResult,
) -> StructuredGenerationResult:
    """Skip LLM when Tier 0 unique exact match; otherwise run identity task."""
    if search.resolution_state == ResolutionState.EXACT_MATCH and len(search.exact_matches) == 1:
        match = search.exact_matches[0]
        decision = ConceptIdentityDecision(
            classification=IdentityClassification.SAME_CONCEPT,
            selected_concept_id=match.concept_id,
            confidence=ConfidenceLevel.HIGH,
            rationale="Deterministic exact identity match",
            evidence=[match.match_type.value],
        )
        return StructuredGenerationResult(
            ok=True,
            data=decision.model_dump(mode="json"),
            diagnostics={"path": "deterministic_identity", "privacy": "prompt_omitted"},
        )
    return run_reasoning_task(
        provider,
        IDENTITY_TASK,
        {
            "query": search.query.text,
            "candidates_json": _candidates_json(search),
        },
    )


def reason_new_concept(
    provider: LLMProvider,
    search: ConceptSearchResult,
    *,
    extra_context: dict[str, Any] | None = None,
) -> StructuredGenerationResult:
    context = {
        "candidates": json.loads(_candidates_json(search)),
        "extra": extra_context or {},
    }
    return run_reasoning_task(
        provider,
        NEW_CONCEPT_TASK,
        {"query": search.query.text, "context_json": json.dumps(context)},
    )


def reason_module_intent(
    provider: LLMProvider,
    search: ConceptSearchResult,
) -> StructuredGenerationResult:
    return run_reasoning_task(
        provider,
        MODULE_INTENT_TASK,
        {
            "query": search.query.text,
            "candidates_json": _candidates_json(search),
        },
    )


def reason_relationships(
    provider: LLMProvider,
    search: ConceptSearchResult,
    *,
    graph_context: dict[str, Any] | None = None,
) -> StructuredGenerationResult:
    context = {
        "candidates": json.loads(_candidates_json(search)),
        "graph": graph_context or {},
    }
    return run_reasoning_task(
        provider,
        RELATIONSHIP_TASK,
        {"query": search.query.text, "context_json": json.dumps(context)},
    )


def reason_clarification(
    provider: LLMProvider,
    search: ConceptSearchResult,
) -> StructuredGenerationResult:
    return run_reasoning_task(
        provider,
        CLARIFICATION_TASK,
        {
            "query": search.query.text,
            "resolution_state": search.resolution_state.value,
        },
    )


def parse_identity_decision(result: StructuredGenerationResult) -> ConceptIdentityDecision | None:
    if not result.ok or result.data is None:
        return None
    return ConceptIdentityDecision.model_validate(result.data)


def parse_clarification(result: StructuredGenerationResult) -> ClarificationDecision | None:
    if not result.ok or result.data is None:
        return None
    return ClarificationDecision.model_validate(result.data)
