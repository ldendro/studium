"""Tests for LLM provider framework and reasoning tasks."""

from __future__ import annotations

from studium.index.search.models import (
    ConceptSearchQuery,
    ConceptSearchResult,
    ExactMatchType,
    IdentityMatch,
    ResolutionState,
    SearchStatus,
)
from studium.llm import (
    DeterministicLLMProvider,
    extract_json_object,
    reason_identity,
    run_reasoning_task,
)
from studium.llm.reasoning.registry import IDENTITY_TASK
from studium.llm.reasoning.schemas import IdentityClassification


def test_extract_json_object_fenced() -> None:
    text = '```json\n{"classification": "same_concept"}\n```'
    assert extract_json_object(text)["classification"] == "same_concept"


def test_extract_json_object_ignores_later_braces_and_objects() -> None:
    text = '{"message": "brace } in string", "ok": true} commentary {"example": false}'
    assert extract_json_object(text) == {"message": "brace } in string", "ok": True}


def test_run_reasoning_task_validates_and_repairs() -> None:
    calls = {"n": 0}

    def handler(_system: str, _user: str) -> dict[str, object]:
        calls["n"] += 1
        if calls["n"] == 1:
            return {"classification": "nope"}  # invalid
        return {
            "classification": "distinct_related_concept",
            "selected_concept_id": None,
            "confidence": "medium",
            "rationale": "related but distinct",
            "evidence": ["title overlap"],
        }

    provider = DeterministicLLMProvider(handler=handler)
    result = run_reasoning_task(
        provider,
        IDENTITY_TASK,
        {"query": "foo", "candidates_json": "[]"},
    )
    assert result.ok
    assert result.repaired is True
    assert result.data is not None
    assert result.data["classification"] == "distinct_related_concept"
    assert calls["n"] == 2


def test_unhealthy_provider_fails_fast() -> None:
    provider = DeterministicLLMProvider(healthy=False)
    result = run_reasoning_task(
        provider,
        IDENTITY_TASK,
        {"query": "foo", "candidates_json": "[]"},
    )
    assert result.ok is False
    assert result.error_code == "provider_unavailable"


def test_reason_identity_skips_llm_on_exact_match() -> None:
    provider = DeterministicLLMProvider(default_response={})
    search = ConceptSearchResult(
        query=ConceptSearchQuery(text="SGD"),
        index_revision=1,
        search_status=SearchStatus.COMPLETE,
        resolution_state=ResolutionState.EXACT_MATCH,
        exact_matches=[
            IdentityMatch(
                concept_id="concept_sgd",
                canonical_title="Stochastic Gradient Descent",
                match_type=ExactMatchType.APPROVED_ALIAS,
            )
        ],
    )
    result = reason_identity(provider, search)
    assert result.ok
    assert result.diagnostics.get("path") == "deterministic_identity"
    assert provider.calls == []
    assert result.data is not None
    assert result.data["classification"] == IdentityClassification.SAME_CONCEPT.value


def test_openai_compat_importable() -> None:
    from studium.llm import OpenAICompatibleProvider

    provider = OpenAICompatibleProvider(model_id="llama3.2:3b")
    assert provider.model_id() == "llama3.2:3b"
