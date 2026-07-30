"""Typed models for deterministic lookup and lexical FTS results."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
