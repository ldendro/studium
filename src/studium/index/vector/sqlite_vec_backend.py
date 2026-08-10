"""Optional sqlite-vec backed cosine ranking (exact via scalar distance)."""

from __future__ import annotations

import importlib
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from studium.index.embeddings.serialize import pack_vector
from studium.index.vector.corpus import (
    CorpusRow,
    load_corpus,
    prepare_query_blob,
    rank_concept_hits,
    rank_module_hits,
    validate_query_vector,
)
from studium.index.vector.models import ModelSpaceFilter, VectorConceptHit, VectorModuleHit
from studium.index.vector.similarity import l2_normalize_matrix


def sqlite_vec_available() -> bool:
    try:
        importlib.import_module("sqlite_vec")
    except ImportError:
        return False
    return True


def load_sqlite_vec(connection: Connection) -> None:
    """Load the sqlite-vec extension onto a live DBAPI connection."""
    sqlite_vec = importlib.import_module("sqlite_vec")
    raw = connection.connection.dbapi_connection
    if raw is None:
        msg = "SQLite DBAPI connection is unavailable"
        raise RuntimeError(msg)
    enable = getattr(raw, "enable_load_extension", None)
    if enable is None:
        msg = "SQLite connection does not support loading extensions"
        raise RuntimeError(msg)
    enable(True)
    # sqlite-vec's load() expects a stdlib sqlite3.Connection.
    cast(Any, sqlite_vec).load(raw)
    enable(False)


class SqliteVecSearchBackend:
    """Rank via ``vec_distance_cosine`` after loading sqlite-vec.

    Corpus BLOBs are still read from the embeddings table (no schema bump).
    Vectors are L2-normalized in Python before distance evaluation so scores
    match NumPy cosine similarity (``1 - distance`` for unit vectors).
    """

    def __init__(self, engine: Engine) -> None:
        if not sqlite_vec_available():
            msg = "sqlite-vec is not installed; uv sync --extra vector-ext"
            raise RuntimeError(msg)
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
        corpus, scores = self._score(query_vector, model_filter, "module_semantic", limit)
        return rank_module_hits(self._engine, corpus, scores, limit=limit)

    def _search_concepts(
        self,
        query_vector: list[float],
        model_filter: ModelSpaceFilter,
        *,
        embedding_type: str,
        limit: int,
    ) -> list[VectorConceptHit]:
        corpus, scores = self._score(query_vector, model_filter, embedding_type, limit)
        return rank_concept_hits(self._engine, corpus, scores, limit=limit)

    def _score(
        self,
        query_vector: list[float],
        model_filter: ModelSpaceFilter,
        embedding_type: str,
        limit: int,
    ) -> tuple[list[CorpusRow], NDArray[np.float32]]:
        validate_query_vector(query_vector, model_filter)
        if limit <= 0:
            return [], np.zeros(0, dtype=np.float32)

        with self._engine.connect() as connection:
            load_sqlite_vec(connection)
            corpus = load_corpus(
                connection,
                embedding_type=embedding_type,
                model_filter=model_filter,
            )
            if not corpus:
                return [], np.zeros(0, dtype=np.float32)

            # Normalize stored rows when the model does not guarantee unit vectors.
            if model_filter.normalizes_embeddings:
                unit_rows = corpus
            else:
                raw = np.asarray([r.vector for r in corpus], dtype=np.float32)
                matrix = l2_normalize_matrix(raw)
                unit_rows = [
                    CorpusRow(
                        owner_id=row.owner_id,
                        parent_concept_id=row.parent_concept_id,
                        segment_id=row.segment_id,
                        embedding_type=row.embedding_type,
                        model_id=row.model_id,
                        model_revision=row.model_revision,
                        normalizes_embeddings=True,
                        vector=matrix[i].tolist(),
                    )
                    for i, row in enumerate(corpus)
                ]

            query_blob = prepare_query_blob(query_vector)
            scores = np.zeros(len(unit_rows), dtype=np.float32)
            for i, row in enumerate(unit_rows):
                row_blob = pack_vector(row.vector)
                distance = connection.execute(
                    text("SELECT vec_distance_cosine(:a, :b)"),
                    {"a": row_blob, "b": query_blob},
                ).scalar_one()
                # Cosine distance for unit vectors is 1 - similarity.
                scores[i] = np.float32(1.0 - float(distance))

        # Preserve original corpus metadata order alignment with scores.
        return corpus if model_filter.normalizes_embeddings else unit_rows, scores
