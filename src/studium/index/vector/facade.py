"""Engine-facing vector search facades (library API)."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from studium.index.vector.factory import create_vector_backend
from studium.index.vector.models import ModelSpaceFilter, VectorConceptHit, VectorModuleHit
from studium.index.vector.protocol import VectorSearchBackend


def search_concept_identity_vectors(
    engine: Engine,
    query_vector: list[float],
    model_filter: ModelSpaceFilter,
    *,
    limit: int = 20,
    backend: VectorSearchBackend | None = None,
) -> list[VectorConceptHit]:
    """Rank concepts by identity-embedding cosine similarity."""
    active = backend if backend is not None else create_vector_backend(engine)
    return active.search_concept_identity(query_vector, model_filter, limit=limit)


def search_concept_semantic_vectors(
    engine: Engine,
    query_vector: list[float],
    model_filter: ModelSpaceFilter,
    *,
    limit: int = 20,
    backend: VectorSearchBackend | None = None,
) -> list[VectorConceptHit]:
    """Rank concepts by semantic-embedding cosine similarity."""
    active = backend if backend is not None else create_vector_backend(engine)
    return active.search_concept_semantic(query_vector, model_filter, limit=limit)


def search_module_semantic_vectors(
    engine: Engine,
    query_vector: list[float],
    model_filter: ModelSpaceFilter,
    *,
    limit: int = 20,
    backend: VectorSearchBackend | None = None,
) -> list[VectorModuleHit]:
    """Rank scaffold modules by module-semantic cosine similarity."""
    active = backend if backend is not None else create_vector_backend(engine)
    return active.search_module_semantic(query_vector, model_filter, limit=limit)
