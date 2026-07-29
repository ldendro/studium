"""Typed models for vault → index synchronization."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class FileSyncClass(StrEnum):
    NEW = "new"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    MOVED = "moved"
    REMOVED = "removed"
    INVALID = "invalid"
    DUPLICATE_ID_CONFLICT = "duplicate_id_conflict"


class SyncStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    NO_CHANGES = "no_changes"


class EmbeddingWorkRequest(BaseModel):
    """Deferred embedding work discovered during sync (no provider call)."""

    model_config = ConfigDict(extra="forbid")

    owner_type: Literal["concept", "scaffold_module"]
    owner_id: str
    embedding_type: Literal["concept_identity", "concept_semantic", "module_semantic"]
    input_hash: str
    input_text: str
    parent_concept_id: str | None = None
    segment_id: str | None = None


class SyncCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scanned: int = 0
    created: int = 0
    updated: int = 0
    moved: int = 0
    removed: int = 0
    unchanged: int = 0
    invalid: int = 0
    duplicate_conflicts: int = 0


def _empty_embedding_work() -> list[EmbeddingWorkRequest]:
    return []


def _empty_strings() -> list[str]:
    return []


class SyncReport(BaseModel):
    """Outcome of ``sync_vault`` / ``rebuild_vault_index``."""

    model_config = ConfigDict(extra="forbid")

    sync_id: str = Field(default_factory=lambda: str(uuid4()))
    started_at: datetime
    finished_at: datetime
    status: SyncStatus
    revision_before: int
    revision_after: int
    counts: SyncCounts = Field(default_factory=SyncCounts)
    embedding_work: list[EmbeddingWorkRequest] = Field(default_factory=_empty_embedding_work)
    warnings: list[str] = Field(default_factory=_empty_strings)
    errors: list[str] = Field(default_factory=_empty_strings)
