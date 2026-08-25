"""Typed application-state models for Studium's ongoing learning loop."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _empty_strings() -> list[str]:
    return []


def _empty_dicts() -> list[dict[str, Any]]:
    return []


def _empty_mapping() -> dict[str, Any]:
    return {}


class BacklogStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DEFERRED = "deferred"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class BacklogItemType(StrEnum):
    NEW_CONCEPT = "new_concept"
    MISSING_PREREQUISITE = "missing_prerequisite"
    CONCEPT_EXPANSION = "concept_expansion"
    OPEN_QUESTION = "open_question"


class BacklogOrigin(StrEnum):
    SEARCH = "search"
    CREATE = "create"
    GRAPH = "graph"
    REVIEW = "review"
    RETENTION = "retention"
    MANUAL = "manual"


class RetentionCardState(StrEnum):
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    RELEARNING = "relearning"
    SUSPENDED = "suspended"


class RetentionEvaluation(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


class MasteryState(StrEnum):
    UNASSESSED = "unassessed"
    FRAGILE = "fragile"
    DEVELOPING = "developing"
    STRONG = "strong"


class ProfileObservationStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISABLED = "disabled"


class ProfileCategory(StrEnum):
    GOAL = "goal"
    ACTIVE_CONTEXT = "active_context"
    LEARNING_PREFERENCE = "learning_preference"
    STRENGTH = "strength"
    GAP = "gap"
    TOPIC_PRIORITY = "topic_priority"


class BacklogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    item_type: BacklogItemType
    status: BacklogStatus
    priority: int = Field(ge=0, le=100)
    reason: str
    origin: BacklogOrigin
    related_concept_id: str | None = None
    required_by: list[str] = Field(default_factory=_empty_strings)
    source_query: str | None = None
    metadata: dict[str, Any] = Field(default_factory=_empty_mapping)
    resolution_candidate: dict[str, Any] | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None


class RetentionCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    concept_id: str
    concept_title: str
    module_id: str | None = None
    module_type: str | None = None
    prompt: str
    expected_components: list[str] = Field(default_factory=_empty_strings)
    state: RetentionCardState
    interval_days: int
    ease_factor: float
    repetitions: int
    lapses: int
    difficulty: float
    stability: float
    last_reviewed_at: str | None = None
    next_review_at: str
    pinned: bool
    queue: str = "upcoming"
    priority_score: float = 0.0
    prerequisite_context: list[str] = Field(default_factory=_empty_strings)
    created_at: str
    updated_at: str


class RetentionReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    card: RetentionCard
    evaluation: RetentionEvaluation
    score: float
    expected_components: list[str] = Field(default_factory=_empty_strings)
    feedback: list[str] = Field(default_factory=_empty_strings)
    next_interval_days: int


class MasteryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    concept_title: str
    module_id: str | None = None
    module_title: str | None = None
    score: float = Field(ge=0.0, le=1.0)
    state: MasteryState
    signals: dict[str, Any] = Field(default_factory=_empty_mapping)
    trend: list[dict[str, Any]] = Field(default_factory=_empty_dicts)
    domains: list[str] = Field(default_factory=_empty_strings)
    weak_prerequisites: list[dict[str, Any]] = Field(default_factory=_empty_dicts)
    recommendations: list[str] = Field(default_factory=_empty_strings)
    updated_at: str


class ProfileObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    category: ProfileCategory
    statement: str
    evidence: list[dict[str, Any]] = Field(default_factory=_empty_dicts)
    confidence: float = Field(ge=0.0, le=1.0)
    status: ProfileObservationStatus
    pinned: bool
    source: str
    created_at: str
    updated_at: str

