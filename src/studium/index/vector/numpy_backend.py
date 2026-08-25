"""Exact top-K cosine vector search with NumPy."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from studium.index.vector.corpus import (
    load_corpus,
    rank_concept_hits,
    rank_module_hits,
    score_corpus_numpy,
    validate_query_vector,
)
from studium.index.vector.models import ModelSpaceFilter, VectorConceptHit, VectorModuleHit


class NumpyVectorSearchBackend:
    """Exact cosine similarity over embeddings loaded from SQLite BLOBs."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def search_concept_identity(
        self,
        query_vector: list[float],
        model_filter: ModelSpaceFilter,
        *,
        limit: int = 20,
    ) -> list[VectorConceptHit]:
        return self._search_concepts(
            query_vector,
            model_filter,
            embedding_type="concept_identity",
            limit=limit,
        )

    def search_concept_semantic(
        self,
        query_vector: list[float],
        model_filter: ModelSpaceFilter,
        *,
        limit: int = 20,
    ) -> list[VectorConceptHit]:
        return self._search_concepts(
            query_vector,
            model_filter,
            embedding_type="concept_semantic",
            limit=limit,
        )

    def search_module_semantic(
        self,
        query_vector: list[float],
        model_filter: ModelSpaceFilter,
        *,
        limit: int = 20,
    ) -> list[VectorModuleHit]:
        validate_query_vector(query_vector, model_filter)
        if limit <= 0:
            return []
        with self._engine.connect() as connection:
            corpus = load_corpus(
                connection,
                embedding_type="module_semantic",
                model_filter=model_filter,
            )
        scores = score_corpus_numpy(
            corpus,
            query_vector,
            normalizes_embeddings=model_filter.normalizes_embeddings,
        )
        return rank_module_hits(self._engine, corpus, scores, limit=limit)

    def _search_concepts(
        self,
        query_vector: list[float],
        model_filter: ModelSpaceFilter,
        *,
        embedding_type: str,
        limit: int,
    ) -> list[VectorConceptHit]:
        validate_query_vector(query_vector, model_filter)
        if limit <= 0:
            return []
        with self._engine.connect() as connection:
            corpus = load_corpus(
                connection,
                embedding_type=embedding_type,
                model_filter=model_filter,
            )
        scores = score_corpus_numpy(
            corpus,
            query_vector,
            normalizes_embeddings=model_filter.normalizes_embeddings,
        )
        return rank_concept_hits(self._engine, corpus, scores, limit=limit)
