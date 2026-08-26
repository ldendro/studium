"""Shared API request and response models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OpenWorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vault_path: str
    app_data_path: str | None = None

    @field_validator("vault_path")
    @classmethod
    def validate_vault_path(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("vault_path must not be empty")
        return value

    def vault(self) -> Path:
        return Path(self.vault_path).expanduser()

    def app_data(self) -> Path | None:
        return None if self.app_data_path is None else Path(self.app_data_path).expanduser()


class CreateWorkspaceRequest(OpenWorkspaceRequest):
    model_config = ConfigDict(extra="forbid")

    demo: bool = False


class SyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    embeddings: bool = True
    background: bool = False


class ApiMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    details: dict[str, Any] = Field(default_factory=dict)
