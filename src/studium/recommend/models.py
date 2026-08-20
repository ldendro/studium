"""Discriminated ConceptRecommendation models and failures."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from studium.schemas.enums import (
    LearningRole,
    RelationshipType,
    ScaffoldModuleOrigin,
    ScaffoldModuleType,
    SourceType,
)


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CompletionStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FALLBACK = "fallback"


class ReasoningMode(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    FALLBACK = "fallback"


class FailureStage(StrEnum):
    SEARCH = "search"
    CANDIDATE_ASSEMBLY = "candidate_assembly"
    REASONING = "reasoning"
    STRUCTURED_OUTPUT_VALIDATION = "structured_output_validation"
    DETERMINISTIC_VERIFICATION = "deterministic_verification"
    RECOMMENDATION_ASSEMBLY = "recommendation_assembly"
    TIMEOUT = "timeout"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _empty_strings() -> list[str]:
    return []


def _empty_dict() -> dict[str, Any]:
    return {}


class AliasSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alias: str
    target_concept_id: str
    classification: str
    confidence: ConfidenceLevel
    evidence: list[str] = Field(default_factory=_empty_strings)


class BacklogCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    reason: str
    related_concept_id: str | None = None


def _empty_alias_suggestions() -> list[AliasSuggestion]:
    return []


def _empty_backlog() -> list[BacklogCandidate]:
    return []


class GraphPositionSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_type: RelationshipType
    target_concept_id: str | None = None
    target_title: str
    learning_role: LearningRole
    direction_note: str = ""


def _empty_graph_positions() -> list[GraphPositionSuggestion]:
    return []


class MetadataSuggestions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aliases_to_add: list[AliasSuggestion] = Field(default_factory=_empty_alias_suggestions)
    domains_to_add: list[str] = Field(default_factory=_empty_strings)
    notes: list[str] = Field(default_factory=_empty_strings)


class RecommendationEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=_now)
    confidence: ConfidenceLevel
    completion_status: CompletionStatus
    reasoning_mode: ReasoningMode
    index_revision: int
    evidence: list[str] = Field(default_factory=_empty_strings)
    warnings: list[str] = Field(default_factory=_empty_strings)
    diagnostics: dict[str, Any] = Field(default_factory=_empty_dict)
    metadata_suggestions: MetadataSuggestions = Field(default_factory=MetadataSuggestions)


class UseExistingConceptRecommendation(RecommendationEnvelope):
    action: Literal["use_existing_concept"] = "use_existing_concept"
    target_concept_id: str
    match_classification: str
    matching_module_ids: list[str] = Field(default_factory=_empty_strings)


class CreateNewConceptRecommendation(RecommendationEnvelope):
    action: Literal["create_new_concept"] = "create_new_concept"
    suggested_title: str
    suggested_concept_type: str
    suggested_domains: list[str] = Field(default_factory=_empty_strings)
    scope_summary: str = ""
    backlog_candidates: list[BacklogCandidate] = Field(default_factory=_empty_backlog)
    possible_match_ids: list[str] = Field(default_factory=_empty_strings)
    graph_positions: list[GraphPositionSuggestion] = Field(default_factory=_empty_graph_positions)


class AddLearningEncounterRecommendation(RecommendationEnvelope):
    action: Literal["add_learning_encounter"] = "add_learning_encounter"
    target_concept_id: str
    source_type: SourceType
    source_title: str
    unit: str | None = None
    comparison_outcome: str


class UpdateLearningEncounterRecommendation(RecommendationEnvelope):
    action: Literal["update_learning_encounter"] = "update_learning_encounter"
    target_concept_id: str
    existing_encounter_id: int
    enrichment_fields: list[str] = Field(default_factory=_empty_strings)
    enrichment_values: dict[str, str | None] = Field(default_factory=_empty_dict)
    comparison_outcome: str


class AddScaffoldModuleRecommendation(RecommendationEnvelope):
    action: Literal["add_scaffold_module"] = "add_scaffold_module"
    target_concept_id: str
    module_type: ScaffoldModuleType
    module_title: str
    focus: str | None = None
    origin: ScaffoldModuleOrigin = ScaffoldModuleOrigin.AGENT_RECOMMENDED


class MarkRedundantRecommendation(RecommendationEnvelope):
    action: Literal["mark_redundant"] = "mark_redundant"
    target_concept_id: str | None = None
    target_module_id: str | None = None
    reason: str


class RequestClarificationRecommendation(RecommendationEnvelope):
    action: Literal["request_clarification"] = "request_clarification"
    ambiguity_type: str
    candidate_interpretations: list[str] = Field(default_factory=_empty_strings)
    clarification_message: str


ConceptRecommendation = Annotated[
    UseExistingConceptRecommendation
    | CreateNewConceptRecommendation
    | AddLearningEncounterRecommendation
    | UpdateLearningEncounterRecommendation
    | AddScaffoldModuleRecommendation
    | MarkRedundantRecommendation
    | RequestClarificationRecommendation,
    Field(discriminator="action"),
]


class RecommendationFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    failure_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=_now)
    query: str
    index_revision: int
    failure_stage: FailureStage
    error_code: str
    message: str
    evidence: list[str] = Field(default_factory=_empty_strings)
    diagnostics: dict[str, Any] = Field(default_factory=_empty_dict)
    recoverable: bool = True
    fallback_search_result: dict[str, Any] | None = None
