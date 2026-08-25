"""Typed models for deterministic lookup and lexical FTS results."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExactMatchType(StrEnum):
    STABLE_ID = "stable_id"
    CANONICAL_TITLE = "canonical_title"
    APPROVED_ALIAS = "approved_alias"


class ResolutionState(StrEnum):
    EXACT_MATCH = "exact_match"
    RELATED_RESULTS = "related_results"
    AMBIGUOUS_RESULTS = "ambiguous_results"
    NO_RESULTS = "no_results"


class IdentityMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    canonical_title: str
    match_type: ExactMatchType
    matched_alias: str | None = None


def _empty_identity_matches() -> list[IdentityMatch]:
    return []


def _empty_strings() -> list[str]:
    return []


def _empty_concept_hits() -> list[LexicalConceptHit]:
    return []


def _empty_module_hits() -> list[LexicalModuleHit]:
    return []


def _empty_diagnostics() -> dict[str, Any]:
    return {}


class IdentityResolution(BaseModel):
    """Outcome of Tier 0 deterministic identity lookup."""

    model_config = ConfigDict(extra="forbid")

    query: str
    normalized_query: str
    matches: list[IdentityMatch] = Field(default_factory=_empty_identity_matches)
    is_ambiguous: bool = False

    @property
    def is_unique(self) -> bool:
        return len(self.matches) == 1 and not self.is_ambiguous

    @property
    def unique_match(self) -> IdentityMatch | None:
        if not self.is_unique:
            return None
        return self.matches[0]


class LexicalConceptHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    canonical_title: str
    rank: int
    score: float
    matched_fields: list[str] = Field(default_factory=_empty_strings)
    overview_excerpt: str | None = None
    concept_type: str | None = None
    domains: list[str] = Field(default_factory=_empty_strings)


class LexicalModuleHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: str
    concept_id: str
    title: str
    module_type: str | None = None
    focus: str | None = None
    heading: str | None = None
    anchor: str | None = None
    rank: int
    score: float
    matched_fields: list[str] = Field(default_factory=_empty_strings)
    parent_canonical_title: str | None = None


class LexicalSearchResult(BaseModel):
    """Thin lexical-only search facade result (B04; B07 wraps/extends later)."""

    model_config = ConfigDict(extra="forbid")

    query: str
    resolution_state: ResolutionState
    identity: IdentityResolution
    concept_hits: list[LexicalConceptHit] = Field(default_factory=_empty_concept_hits)
    module_hits: list[LexicalModuleHit] = Field(default_factory=_empty_module_hits)
    warnings: list[str] = Field(default_factory=_empty_strings)
    diagnostics: dict[str, Any] = Field(default_factory=_empty_diagnostics)


class SearchStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FALLBACK = "fallback"


class SearchChannel(StrEnum):
    FTS = "fts"
    IDENTITY_VECTOR = "identity_vector"
    SEMANTIC_VECTOR = "semantic_vector"
    MODULE_VECTOR = "module_vector"


class ConceptSearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domains: list[str] = Field(default_factory=_empty_strings)
    concept_types: list[str] = Field(default_factory=_empty_strings)
    vault_statuses: list[str] = Field(default_factory=_empty_strings)
    review_statuses: list[str] = Field(default_factory=_empty_strings)


class ConceptSearchLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concepts: int = Field(default=20, ge=0)
    modules: int = Field(default=20, ge=0)
    channel: int = Field(default=50, ge=0)


class ConceptSearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    filters: ConceptSearchFilters = Field(default_factory=ConceptSearchFilters)
    limits: ConceptSearchLimits = Field(default_factory=ConceptSearchLimits)
    include_modules: bool = True
    include_diagnostics: bool = False

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("search text must not be empty")
        return value


class ChannelContribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: SearchChannel
    rank: int
    score: float | None = None


class SearchEvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_type: str
    summary: str
    concept_id: str | None = None
    module_id: str | None = None
    details: dict[str, Any] = Field(default_factory=_empty_diagnostics)


def _empty_channels() -> list[ChannelContribution]:
    return []


def _empty_evidence() -> list[SearchEvidenceItem]:
    return []


class RankedModuleMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: str
    title: str
    module_type: str | None = None
    segment_id: str = ""
    heading: str | None = None
    anchor: str | None = None
    channels: list[ChannelContribution] = Field(default_factory=_empty_channels)
    fused_score: float = 0.0


def _empty_module_matches() -> list[RankedModuleMatch]:
    return []


class RankedConceptCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    canonical_title: str
    aliases: list[str] = Field(default_factory=_empty_strings)
    concept_type: str | None = None
    domains: list[str] = Field(default_factory=_empty_strings)
    overview_excerpt: str | None = None
    status: str | None = None
    vault_status: str | None = None
    review_status: str | None = None
    channels: list[ChannelContribution] = Field(default_factory=_empty_channels)
    matched_fields: list[str] = Field(default_factory=_empty_strings)
    fused_rank: int
    fused_score: float
    matching_modules: list[RankedModuleMatch] = Field(default_factory=_empty_module_matches)
    evidence: list[SearchEvidenceItem] = Field(default_factory=_empty_evidence)


class HybridModuleHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: str
    concept_id: str
    parent_canonical_title: str | None = None
    title: str
    module_type: str | None = None
    segment_id: str = ""
    heading: str | None = None
    anchor: str | None = None
    channels: list[ChannelContribution] = Field(default_factory=_empty_channels)
    fused_rank: int
    fused_score: float
    snippet: str | None = None


def _empty_ranked_concepts() -> list[RankedConceptCandidate]:
    return []


def _empty_hybrid_modules() -> list[HybridModuleHit]:
    return []


class ConceptSearchResult(BaseModel):
    """Stable hybrid search contract for Phase 3 and recommendations (B07)."""

    model_config = ConfigDict(extra="forbid")

    query: ConceptSearchQuery
    index_revision: int
    search_status: SearchStatus
    resolution_state: ResolutionState
    exact_matches: list[IdentityMatch] = Field(default_factory=_empty_identity_matches)
    ranked_concepts: list[RankedConceptCandidate] = Field(default_factory=_empty_ranked_concepts)
    module_hits: list[HybridModuleHit] = Field(default_factory=_empty_hybrid_modules)
    evidence: list[SearchEvidenceItem] = Field(default_factory=_empty_evidence)
    warnings: list[str] = Field(default_factory=_empty_strings)
    diagnostics: dict[str, Any] = Field(default_factory=_empty_diagnostics)
