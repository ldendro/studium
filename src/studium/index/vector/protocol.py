"""Provider-independent vector search protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from studium.index.vector.models import ModelSpaceFilter, VectorConceptHit, VectorModuleHit


@runtime_checkable
class VectorSearchBackend(Protocol):
    """Backend-independent vector retrieval (Technical Plan §4.14)."""

    def search_concept_identity(
        self,
        query_vector: list[float],
        model_filter: ModelSpaceFilter,
        *,
        limit: int = 20,
    ) -> list[VectorConceptHit]:
        """Rank concepts by identity-embedding cosine similarity."""
        ...

    def search_concept_semantic(
        self,
        query_vector: list[float],
        model_filter: ModelSpaceFilter,
        *,
        limit: int = 20,
    ) -> list[VectorConceptHit]:
        """Rank concepts by semantic-embedding cosine similarity."""
        ...

    def search_module_semantic(
        self,
        query_vector: list[float],
        model_filter: ModelSpaceFilter,
        *,
        limit: int = 20,
    ) -> list[VectorModuleHit]:
        """Rank scaffold modules by module-semantic cosine similarity."""
        ...
