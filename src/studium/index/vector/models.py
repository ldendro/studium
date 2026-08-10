"""Typed models for vector search results and model-space filtering."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True, slots=True)
class ModelSpaceFilter:
    """Identity of the embedding space allowed in a search."""

    model_id: str
    dimension: int
    model_revision: str | None = None
    normalizes_embeddings: bool = True

    def __post_init__(self) -> None:
        if self.dimension <= 0:
            msg = "ModelSpaceFilter.dimension must be positive"
            raise ValueError(msg)


class VectorConceptHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    canonical_title: str
    embedding_type: str
    rank: int
    score: float
    model_id: str
    model_revision: str | None = None


class VectorModuleHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: str
    concept_id: str
    module_title: str
    parent_canonical_title: str
    embedding_type: str
    segment_id: str
    rank: int
    score: float
    model_id: str
    model_revision: str | None = None
    heading: str | None = None
    anchor: str | None = None
