"""Shared helpers for serialization tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from studium.schemas import (
    ConceptNoteMetadata,
    ConceptType,
    ContributionStatus,
    EncounterRole,
    LearningEncounter,
    NoteStatus,
    NoteVaultStatus,
    RelationshipMetadata,
    RelationshipType,
    RelationshipVaultStatus,
    ReviewStatus,
    ScaffoldModuleMetadata,
    ScaffoldModuleStatus,
    ScaffoldModuleType,
    SourceMetadata,
    SourceType,
)


def build_sample_metadata(**overrides: Any) -> ConceptNoteMetadata:
    """Build metadata aligned with valid_concept_note fixture defaults."""
    now = datetime(2026, 6, 25, tzinfo=UTC)
    data: dict[str, Any] = {
        "id": "concept_stochastic_gradient_descent_a1b2c3",
        "schema_version": 1,
        "note_type": "concept",
        "concept_type": ConceptType.ALGORITHM,
        "concept_domains": ["machine_learning", "optimization"],
        "canonical_title": "Stochastic Gradient Descent",
        "aliases": ["SGD"],
        "status": NoteStatus.SCAFFOLDED,
        "review_status": ReviewStatus.NOT_SUBMITTED,
        "vault_status": NoteVaultStatus.DRAFT,
        "learning_encounters": [
            LearningEncounter(
                source=SourceMetadata(type=SourceType.STUDIUM, title="Studium"),
                role=EncounterRole.PRIMARY,
                contribution_status=ContributionStatus.PENDING,
                content_attached=False,
                content_id=None,
            )
        ],
        "scaffold_modules": [],
        "relationships": [],
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return ConceptNoteMetadata.model_validate(data)


def build_metadata_with_relationships() -> ConceptNoteMetadata:
    return build_sample_metadata(
        relationships=[
            RelationshipMetadata(
                relationship_type=RelationshipType.DEPENDS_ON,
                target_title="Partial Derivatives",
                vault_status=RelationshipVaultStatus.MISSING,
            ),
            RelationshipMetadata(
                relationship_type=RelationshipType.RELATED_TO,
                target_title="Gradient Descent",
                vault_status=RelationshipVaultStatus.FOUND,
                target_id="concept_gradient_descent_x1y2z3",
            ),
        ]
    )


def build_metadata_with_scaffold_modules() -> ConceptNoteMetadata:
    return build_sample_metadata(
        scaffold_modules=[
            ScaffoldModuleMetadata(
                id="module_sgd_gradient_update_derivation_001",
                type=ScaffoldModuleType.DERIVATION,
                title="Gradient Update Formula Derivation",
                status=ScaffoldModuleStatus.SCAFFOLDED,
            )
        ]
    )
