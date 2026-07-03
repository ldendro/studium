"""Relationship metadata."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from studium.schemas.enums import RelationshipType, RelationshipVaultStatus


class RelationshipMetadata(BaseModel):
    """Structured concept relationship stored in YAML frontmatter."""

    model_config = ConfigDict(extra="forbid")

    relationship_type: RelationshipType
    target_title: str = Field(min_length=1)
    vault_status: RelationshipVaultStatus
    target_id: str | None = None
