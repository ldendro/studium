"""Typed models for the Phase 4 Create workflow."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from studium.schemas import (
    ConceptType,
    LearningRole,
    RelationshipConfidence,
    RelationshipType,
    ScaffoldModuleOrigin,
    ScaffoldModuleType,
    SourceType,
)


def _empty_module_types() -> list[ScaffoldModuleType]:
    return []


def _empty_modules() -> list[ModuleProposal]:
    return []


def _empty_relationships() -> list[RelationshipProposal]:
    return []


def _empty_matches() -> list[PossibleMatch]:
    return []


def _empty_dicts() -> list[dict[str, Any]]:
    return []


def _empty_dict() -> dict[str, Any]:
    return {}


def _empty_strings() -> list[str]:
    return []


class CreateIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str
    learning_goal: str = ""
    user_context: str = ""
    source_type: SourceType | None = None
    source_title: str | None = None
    source_unit: str | None = None
    source_section: str | None = None
    source_link: str | None = None
    source_id: str | None = None
    target_concept_id: str | None = None
    target_module_id: str | None = None
    requested_module_type: ScaffoldModuleType | None = None
    scaffold_preferences: list[ScaffoldModuleType] = Field(
        default_factory=_empty_module_types
    )
    search_context: dict[str, Any] = Field(default_factory=_empty_dict)

    @field_validator("intent")
    @classmethod
    def validate_intent(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("intent must not be empty")
        return value


class ModuleProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: ScaffoldModuleType
    title: str
    focus: str | None = None
    selected: bool = True
    reason: str
    origin: ScaffoldModuleOrigin = ScaffoldModuleOrigin.AGENT_RECOMMENDED


class RelationshipProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_type: RelationshipType
    target_title: str
    target_id: str | None = None
    learning_role: LearningRole
    confidence: RelationshipConfidence = RelationshipConfidence.MEDIUM
    selected: bool = True
    evidence: str = ""


class EncounterProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    source_title: str
    unit: str | None = None
    section: str | None = None
    link: str | None = None
    source_id: str | None = None
    selected: bool = True


class PossibleMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    title: str
    evidence: list[str] = Field(default_factory=list)
    vault_status: str | None = None


class CreateProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    action: str
    canonical_title: str
    target_concept_id: str | None = None
    target_path: str
    concept_type: ConceptType
    domains: list[str] = Field(default_factory=list)
    aliases_to_add: list[str] = Field(default_factory=list)
    modules: list[ModuleProposal] = Field(default_factory=_empty_modules)
    relationships: list[RelationshipProposal] = Field(default_factory=_empty_relationships)
    encounter: EncounterProposal | None = None
    possible_matches: list[PossibleMatch] = Field(default_factory=_empty_matches)
    backlog_candidates: list[dict[str, Any]] = Field(default_factory=_empty_dicts)
    evidence: list[str] = Field(default_factory=_empty_strings)
    warnings: list[str] = Field(default_factory=_empty_strings)
    confidence: str
    reasoning_mode: str
    index_revision: int
    intent: CreateIntent
    raw_recommendation: dict[str, Any] = Field(default_factory=_empty_dict)


class GeneratedDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    operation: Literal["create", "update", "no_change"]
    concept_id: str
    target_path: str
    markdown: str
    selected_modules: list[str] = Field(default_factory=_empty_strings)
    warnings: list[str] = Field(default_factory=_empty_strings)


class DraftPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: str
    target_path: str
    would_create: bool
    would_update: bool
    can_commit: bool
    diff: str
    warnings: list[dict[str, Any]] = Field(default_factory=_empty_dicts)
    critical_errors: list[dict[str, Any]] = Field(default_factory=_empty_dicts)


class DraftCommitResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    target_path: str
    index_revision: int
    sync_status: str
    review_status: str
    vault_status: str
