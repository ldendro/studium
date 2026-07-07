"""Concept note schema models (branch P1-B3).

Pydantic models for concept note metadata, learning encounters, scaffold
modules, relationships, validation results, and write proposals.
"""

from studium.schemas.canonical import (
    CANONICAL_SECTION_TITLES,
    CANONICAL_YAML_TOP_LEVEL_KEYS,
    PREREQUISITE_RELATIONSHIP_TYPES,
)
from studium.schemas.concept_note import ConceptNoteMetadata
from studium.schemas.enums import (
    ConceptType,
    ContributionStatus,
    EncounterRole,
    NoteStatus,
    NoteVaultStatus,
    RelationshipType,
    RelationshipVaultStatus,
    ReviewStatus,
    ScaffoldModuleOrigin,
    ScaffoldModuleStatus,
    ScaffoldModuleType,
    SourceType,
    ValidationOperation,
    ValidationSeverity,
    WriteOperation,
)
from studium.schemas.learning_encounter import LearningEncounter, default_studium_learning_encounter
from studium.schemas.relationship import RelationshipMetadata
from studium.schemas.scaffold_module import ScaffoldModuleMetadata
from studium.schemas.source import SourceMetadata
from studium.schemas.validation import ValidationIssue, ValidationResult
from studium.schemas.write_proposal import WriteProposal

__all__ = [
    "CANONICAL_SECTION_TITLES",
    "CANONICAL_YAML_TOP_LEVEL_KEYS",
    "PREREQUISITE_RELATIONSHIP_TYPES",
    "ConceptNoteMetadata",
    "ConceptType",
    "ContributionStatus",
    "EncounterRole",
    "LearningEncounter",
    "NoteStatus",
    "NoteVaultStatus",
    "RelationshipMetadata",
    "RelationshipType",
    "RelationshipVaultStatus",
    "ReviewStatus",
    "ScaffoldModuleMetadata",
    "ScaffoldModuleOrigin",
    "ScaffoldModuleStatus",
    "ScaffoldModuleType",
    "SourceMetadata",
    "SourceType",
    "ValidationIssue",
    "ValidationOperation",
    "ValidationResult",
    "ValidationSeverity",
    "WriteOperation",
    "WriteProposal",
    "default_studium_learning_encounter",
]
