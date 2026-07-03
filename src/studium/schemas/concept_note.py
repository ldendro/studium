"""Concept note metadata model."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from studium.schemas.enums import ConceptType, NoteStatus, NoteVaultStatus, ReviewStatus
from studium.schemas.learning_encounter import LearningEncounter
from studium.schemas.relationship import RelationshipMetadata
from studium.schemas.scaffold_module import ScaffoldModuleMetadata

ConceptDomain = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]


def _empty_scaffold_modules() -> list[ScaffoldModuleMetadata]:
    return []


def _empty_relationships() -> list[RelationshipMetadata]:
    return []


class ConceptNoteMetadata(BaseModel):
    """YAML frontmatter model for a Studium concept note."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    schema_version: Literal[1] = 1
    note_type: Literal["concept"] = "concept"
    concept_type: ConceptType = ConceptType.GENERAL_CONCEPT
    concept_domains: list[ConceptDomain] = Field(default_factory=list)
    canonical_title: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    status: NoteStatus
    review_status: ReviewStatus
    vault_status: NoteVaultStatus
    learning_encounters: list[LearningEncounter]
    scaffold_modules: list[ScaffoldModuleMetadata] = Field(default_factory=_empty_scaffold_modules)
    relationships: list[RelationshipMetadata] = Field(default_factory=_empty_relationships)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_learning_encounters_and_scaffold_modules(self) -> ConceptNoteMetadata:
        if len(self.learning_encounters) < 1:
            msg = "learning_encounters must contain at least one encounter"
            raise ValueError(msg)

        seen_module_ids: set[str] = set()
        for module in self.scaffold_modules:
            if module.id in seen_module_ids:
                msg = f"duplicate scaffold module id: {module.id}"
                raise ValueError(msg)
            seen_module_ids.add(module.id)

        return self
