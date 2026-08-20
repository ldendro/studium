"""Evaluation case and result models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _empty_strings() -> list[str]:
    return []


def _empty_dict() -> dict[str, Any]:
    return {}


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    query: str
    domain: str = "general"
    acceptable_actions: list[str] = Field(default_factory=_empty_strings)
    required_candidate_ids: list[str] = Field(default_factory=_empty_strings)
    prohibited_identity_ids: list[str] = Field(default_factory=_empty_strings)
    expected_resolution_states: list[str] = Field(default_factory=_empty_strings)
    notes: str = ""


class RetrievalCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    hit: bool
    reciprocal_rank: float
    ranked_ids: list[str] = Field(default_factory=_empty_strings)
    exact_match_ids: list[str] = Field(default_factory=_empty_strings)
    resolution_state: str
    search_status: str


class RecommendationCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    action: str | None
    action_ok: bool
    structured_ok: bool
    failure_code: str | None = None


def _empty_retrieval_results() -> list[RetrievalCaseResult]:
    return []


def _empty_recommendation_results() -> list[RecommendationCaseResult]:
    return []


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_count: int
    recall_at_5: float
    mrr: float
    exact_lookup_accuracy: float
    action_accuracy: float
    structured_validity: float
    retrieval_results: list[RetrievalCaseResult] = Field(default_factory=_empty_retrieval_results)
    recommendation_results: list[RecommendationCaseResult] = Field(
        default_factory=_empty_recommendation_results
    )
    config: dict[str, Any] = Field(default_factory=_empty_dict)
    thresholds: dict[str, float] = Field(default_factory=_empty_dict)
    thresholds_met: bool = False
