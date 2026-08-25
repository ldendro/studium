"""Bounded reasoning decision schemas (B10)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from studium.schemas.concept_note import ConceptDomain
from studium.schemas.enums import ConceptType, LearningRole, RelationshipType, ScaffoldModuleType


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IdentityClassification(StrEnum):
    SAME_CONCEPT = "same_concept"
    DISTINCT_RELATED_CONCEPT = "distinct_related_concept"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class ConceptIdentityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: IdentityClassification
    selected_concept_id: str | None = None
    confidence: ConfidenceLevel
    rationale: str
    evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_same_concept_target(self) -> ConceptIdentityDecision:
        if self.classification == IdentityClassification.SAME_CONCEPT and not (
            self.selected_concept_id and self.selected_concept_id.strip()
        ):
            raise ValueError("same_concept decisions require selected_concept_id")
        return self


class GraphPositionHint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_type: RelationshipType
    target_concept_id: str | None = None
    target_title: str
    learning_role: LearningRole
    direction_note: str = ""


def _empty_graph_positions() -> list[GraphPositionHint]:
    return []


def _empty_strings() -> list[str]:
    return []


class NewConceptAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggested_concept_type: ConceptType
    suggested_domains: list[ConceptDomain] = Field(default_factory=_empty_strings)
    scope_summary: str
    graph_positions: list[GraphPositionHint] = Field(default_factory=_empty_graph_positions)
    prerequisite_titles: list[str] = Field(default_factory=_empty_strings)
    confidence: ConfidenceLevel
    rationale: str
    evidence: list[str] = Field(default_factory=_empty_strings)


class ModuleIntentClassification(StrEnum):
    ADD_TO_EXISTING = "add_to_existing"
    CREATE_WITH_CONCEPT = "create_with_concept"
    REDUNDANT = "redundant"
    UNCLEAR = "unclear"


class ScaffoldModuleIntentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: ModuleIntentClassification
    target_concept_id: str | None = None
    suggested_module_type: ScaffoldModuleType | None = None
    suggested_title: str | None = None
    suggested_focus: str | None = None
    confidence: ConfidenceLevel
    rationale: str
    evidence: list[str] = Field(default_factory=list)


class RelationshipJudgment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_type: RelationshipType
    learning_role: LearningRole
    target_concept_id: str | None = None
    target_title: str
    confidence: ConfidenceLevel
    rationale: str


def _empty_relationships() -> list[RelationshipJudgment]:
    return []


class RelationshipAndPrerequisiteAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationships: list[RelationshipJudgment] = Field(default_factory=_empty_relationships)
    missing_prerequisite_titles: list[str] = Field(default_factory=_empty_strings)
    confidence: ConfidenceLevel
    rationale: str
    evidence: list[str] = Field(default_factory=_empty_strings)


class SourceAmbiguityResolution(StrEnum):
    TREAT_AS_SAME = "treat_as_same"
    TREAT_AS_ENRICH = "treat_as_enrich"
    TREAT_AS_NEW_UNIT = "treat_as_new_unit"
    TREAT_AS_DIFFERENT = "treat_as_different"
    NEED_CLARIFICATION = "need_clarification"


class SourceEncounterAmbiguityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolution: SourceAmbiguityResolution
    confidence: ConfidenceLevel
    rationale: str
    evidence: list[str] = Field(default_factory=list)


class AliasClassification(StrEnum):
    APPROVED_ALIAS = "approved_alias"
    ACRONYM = "acronym"
    ALTERNATE_SPELLING = "alternate_spelling"
    REJECT = "reject"


class AliasProposalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alias: str
    target_concept_id: str
    classification: AliasClassification
    confidence: ConfidenceLevel
    rationale: str
    evidence: list[str] = Field(default_factory=list)


class ClarificationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    needs_clarification: bool
    ambiguity_type: str
    candidate_interpretations: list[str] = Field(default_factory=list)
    clarification_message: str
    confidence: ConfidenceLevel
    evidence: list[str] = Field(default_factory=list)
