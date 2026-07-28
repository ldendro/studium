"""Source metadata for learning encounters."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from studium.schemas.enums import SourceType


class ExternalId(BaseModel):
    """Typed optional external identifier for a source."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    value: str = Field(min_length=1)


class SourceMetadata(BaseModel):
    """Structured source reference attached to a learning encounter."""

    model_config = ConfigDict(extra="forbid")

    type: SourceType
    title: str = Field(min_length=1)
    unit_type: str | None = None
    unit: str | None = None
    section: str | None = None
    link: str | None = None
    external_id: ExternalId | None = None
