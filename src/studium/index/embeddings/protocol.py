"""Provider-independent embedding types and protocol (P2-B05)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class EmbeddingModelMetadata:
    """Identity of an embedding space used for storage and later search."""

    model_id: str
    dimension: int
    model_revision: str | None = None
    normalizes_embeddings: bool = True
    max_input_chars: int | None = None
    batch_size_hint: int | None = None


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Provider-independent embedding operations (Technical Plan §4.10)."""

    def model_metadata(self) -> EmbeddingModelMetadata:
        """Return model identity and encoding behavior."""
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed documents in order; ``result[i]`` corresponds to ``texts[i]``."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string (not persisted)."""
        ...
