"""Relationship metadata."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from studium.schemas.enums import (
    LearningRole,
    RelationshipConfidence,
    RelationshipStatus,
    RelationshipType,
    RelationshipVaultStatus,
)


class RelationshipMetadata(BaseModel):
    """Structured concept relationship stored in YAML frontmatter."""

    model_config = ConfigDict(extra="forbid")

    relationship_type: RelationshipType
    target_title: str = Field(min_length=1)
    vault_status: RelationshipVaultStatus
    learning_role: LearningRole
    confidence: RelationshipConfidence
    status: RelationshipStatus
    target_id: str | None = None
