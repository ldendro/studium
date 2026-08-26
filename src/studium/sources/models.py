"""Typed source processing contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _empty_dict() -> dict[str, Any]:
    return {}


def _empty_strings() -> list[str]:
    return []


class SourceStatus(StrEnum):
    QUEUED = "queued"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class SourceKind(StrEnum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    TRANSCRIPT = "transcript"


class ExtractedUnit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    section: str | None = None
    page: int | None = None
    timestamp_start: float | None = None
    timestamp_end: float | None = None
    metadata: dict[str, Any] = Field(default_factory=_empty_dict)


class SourceChunkModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str
    ordinal: int
    text: str
    section: str | None = None
    page: int | None = None
    timestamp_start: float | None = None
    timestamp_end: float | None = None
    char_start: int | None = None
    char_end: int | None = None
    token_count: int
    embedding: list[float] | None = None
    embedding_model: str | None = None


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_title: str
    chunk_id: str
    locator: str
    quote: str
    section: str | None = None
    page: int | None = None
    timestamp_start: float | None = None
    timestamp_end: float | None = None


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    source_id: str
    source_title: str
    text: str
    score: float
    semantic_score: float
    lexical_score: float
    citation: Citation


class ContributionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str
    concept_id: str
    classification: str
    summary: str
    evidence: list[Citation]
    proposed_module: dict[str, Any] | None = None
    status: str = "proposed"
    warnings: list[str] = Field(default_factory=_empty_strings)
