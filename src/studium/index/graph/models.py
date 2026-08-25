"""Graph query and source-encounter matching models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EncounterOutcome(StrEnum):
    EXACT_SAME_ENCOUNTER = "exact_same_encounter"
    SAME_SOURCE_ENRICH_EXISTING = "same_source_enrich_existing"
    SAME_SOURCE_NEW_UNIT = "same_source_new_unit"
    DIFFERENT_SOURCE = "different_source"
    AMBIGUOUS = "ambiguous"


class GraphRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    source_concept_id: str
    relationship_type: str
    target_id: str | None = None
    target_title: str
    vault_status: str
    learning_role: str
    confidence: str
    status: str
    derived_inverse: bool = False
    original_relationship_type: str | None = None


def _empty_rels() -> list[GraphRelationship]:
    return []


def _empty_map() -> dict[str, list[GraphRelationship]]:
    return {}


class OneHopNeighborhood(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    outgoing: list[GraphRelationship] = Field(default_factory=_empty_rels)
    incoming_derived: list[GraphRelationship] = Field(default_factory=_empty_rels)
    by_type: dict[str, list[GraphRelationship]] = Field(default_factory=_empty_map)
    by_learning_role: dict[str, list[GraphRelationship]] = Field(default_factory=_empty_map)


class SourceIdentity(BaseModel):
    """Normalized source fields used for encounter comparison."""

    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_title: str
    unit_type: str | None = None
    unit: str | None = None
    section: str | None = None
    link: str | None = None
    external_id_type: str | None = None
    external_id_value: str | None = None


class EncounterComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: EncounterOutcome
    source_fingerprint: str
    encounter_fingerprint: str
    matched_encounter_id: int | None = None
    matched_concept_id: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
