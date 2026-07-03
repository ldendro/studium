"""Scaffold module metadata."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from studium.schemas.enums import ScaffoldModuleOrigin, ScaffoldModuleStatus, ScaffoldModuleType


class ScaffoldModuleMetadata(BaseModel):
    """Metadata for a scaffold module container within a concept note."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: ScaffoldModuleType
    title: str = Field(min_length=1)
    status: ScaffoldModuleStatus
    origin: ScaffoldModuleOrigin | None = None
    focus: str | None = None
