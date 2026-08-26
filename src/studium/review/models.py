"""Typed review sessions, findings, patches, and acceptance gates."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def _empty_strings() -> list[str]:
    return []


def _empty_findings() -> list[ReviewFinding]:
    return []


class ReviewReadiness(StrEnum):
    NEEDS_REVISION = "needs_revision"
    APPROVED_WITH_SUGGESTIONS = "approved_with_suggestions"
    APPROVED = "approved"


class ReviewSessionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingSeverity(StrEnum):
    CRITICAL = "critical"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class FindingCategory(StrEnum):
    PREFLIGHT = "preflight"
    COVERAGE = "coverage"
    CONCEPTUAL = "conceptual"
    RELATIONSHIP = "relationship"
    SOURCE_GROUNDING = "source_grounding"


class FindingStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    APPLIED = "applied"
    REJECTED = "rejected"


class ReviewAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: str = "section"
    module_id: str | None = None
    heading: str | None = None
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)


class ReviewFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    review_id: str
    concept_id: str
    module_id: str | None = None
    category: FindingCategory
    severity: FindingSeverity
    message: str
    anchor: ReviewAnchor | None = None
    quoted_text: str | None = None
    proposed_patch: str | None = None
    status: FindingStatus = FindingStatus.OPEN
    decision_note: str | None = None
    created_at: str
    resolved_at: str | None = None


class ReviewSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    critical_count: int = 0
    recommended_count: int = 0
    optional_count: int = 0
    open_critical_count: int = 0
    open_recommended_count: int = 0
    missing_essential_modules: list[str] = Field(default_factory=_empty_strings)
    content_hash: str
    agent_mode: str = "deterministic"
    can_accept: bool = False
    blockers: list[str] = Field(default_factory=_empty_strings)


class ReviewSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    concept_id: str
    file_path: str
    status: ReviewSessionStatus
    readiness: ReviewReadiness
    summary: ReviewSummary
    created_at: str
    completed_at: str | None = None
    findings: list[ReviewFinding] = Field(default_factory=_empty_findings)


class PatchPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    target_path: str
    replacement: str
    diff: str
    can_commit: bool
    warnings: list[dict[str, object]]
    critical_errors: list[dict[str, object]]


class AcceptanceGate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    review_id: str | None = None
    readiness: ReviewReadiness | None = None
    can_accept: bool
    requires_acknowledgement: bool = False
    blockers: list[str] = Field(default_factory=_empty_strings)
    recommendations: list[str] = Field(default_factory=_empty_strings)
    preview_diff: str = ""
