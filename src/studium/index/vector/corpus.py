"""Load and rank embedding rows for vector search backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sqlalchemy.engine import Connection, Engine

from studium.index.embeddings.serialize import unpack_vector
from studium.index.repositories import concepts, scaffold_modules
from studium.index.repositories import embeddings as embeddings_repo
from studium.index.vector.models import ModelSpaceFilter, VectorConceptHit, VectorModuleHit
from studium.index.vector.similarity import cosine_scores, l2_normalize_vector


@dataclass(frozen=True, slots=True)
class CorpusRow:
    """One searchable embedding row with unpacked vector."""

    owner_id: str
    parent_concept_id: str | None
    segment_id: str
    embedding_type: str
    model_id: str
    model_revision: str | None
    normalizes_embeddings: bool
    vector: list[float]


def validate_query_vector(query_vector: list[float], model_filter: ModelSpaceFilter) -> None:
    if len(query_vector) != model_filter.dimension:
        msg = (
            f"query_vector length {len(query_vector)} does not match "
            f"ModelSpaceFilter.dimension {model_filter.dimension}"
        )
        raise ValueError(msg)


def load_corpus(
    connection: Connection,
    *,
    embedding_type: str,
    model_filter: ModelSpaceFilter,
) -> list[CorpusRow]:
    rows = embeddings_repo.list_embeddings_for_search(
        connection,
        embedding_type=embedding_type,
        model_id=model_filter.model_id,
        dimension=model_filter.dimension,
        model_revision=model_filter.model_revision,
        normalizes_embeddings=model_filter.normalizes_embeddings,
    )
    corpus: list[CorpusRow] = []
    for row in rows:
        raw_blob = row["vector"]
        if isinstance(raw_blob, memoryview):
            blob = raw_blob.tobytes()
        elif isinstance(raw_blob, bytes):
            blob = raw_blob
        else:
            continue
        vector = unpack_vector(blob, dimension=int(row["dimension"]))
        parent = row.get("parent_concept_id")
        corpus.append(
            CorpusRow(
                owner_id=str(row["owner_id"]),
                parent_concept_id=None if parent is None else str(parent),
                segment_id=str(row.get("segment_id") or ""),
                embedding_type=str(row["embedding_type"]),
                model_id=str(row["model_id"]),
                model_revision=(
                    None if row.get("model_revision") is None else str(row["model_revision"])
                ),
                normalizes_embeddings=bool(row["normalizes_embeddings"]),
                vector=vector,
            )
        )
    return corpus


def corpus_matrix(corpus: list[CorpusRow]) -> NDArray[np.float32]:
    if not corpus:
        return np.zeros((0, 0), dtype=np.float32)
    return np.asarray([row.vector for row in corpus], dtype=np.float32)


def top_k_indices(
    scores: NDArray[np.floating],
    corpus: list[CorpusRow],
    *,
    limit: int,
) -> list[int]:
    """Return indices of top-K scores with stable owner_id / segment_id tie-break."""
    if limit <= 0 or not corpus:
        return []
    order = sorted(
        range(len(corpus)),
        key=lambda i: (-float(scores[i]), corpus[i].owner_id, corpus[i].segment_id),
    )
    return order[:limit]


def rank_concept_hits(
    engine: Engine,
    corpus: list[CorpusRow],
    scores: NDArray[np.floating],
    *,
    limit: int,
) -> list[VectorConceptHit]:
    indices = top_k_indices(scores, corpus, limit=limit)
    if not indices:
        return []
    hits: list[VectorConceptHit] = []
    with engine.connect() as connection:
        for rank, index in enumerate(indices, start=1):
            row = corpus[index]
            concept = concepts.get_concept(connection, row.owner_id)
            title = str(concept["canonical_title"]) if concept is not None else row.owner_id
            hits.append(
                VectorConceptHit(
                    concept_id=row.owner_id,
                    canonical_title=title,
                    embedding_type=row.embedding_type,
                    rank=rank,
                    score=float(scores[index]),
                    model_id=row.model_id,
                    model_revision=row.model_revision,
                )
            )
    return hits


def rank_module_hits(
    engine: Engine,
    corpus: list[CorpusRow],
    scores: NDArray[np.floating],
    *,
    limit: int,
) -> list[VectorModuleHit]:
    indices = top_k_indices(scores, corpus, limit=limit)
    if not indices:
        return []
    hits: list[VectorModuleHit] = []
    with engine.connect() as connection:
        for rank, index in enumerate(indices, start=1):
            row = corpus[index]
            module = scaffold_modules.get_scaffold_module(connection, row.owner_id)
            concept_id = row.parent_concept_id or (
                str(module["concept_id"]) if module is not None else ""
            )
            parent = concepts.get_concept(connection, concept_id) if concept_id else None
            hits.append(
                VectorModuleHit(
                    module_id=row.owner_id,
                    concept_id=concept_id,
                    module_title=(str(module["title"]) if module is not None else row.owner_id),
                    parent_canonical_title=(
                        str(parent["canonical_title"]) if parent is not None else concept_id
                    ),
                    embedding_type=row.embedding_type,
                    segment_id=row.segment_id,
                    rank=rank,
                    score=float(scores[index]),
                    model_id=row.model_id,
                    model_revision=row.model_revision,
                    heading=None if module is None else _optional_str(module.get("heading")),
                    anchor=None if module is None else _optional_str(module.get("anchor")),
                )
            )
    return hits


def score_corpus_numpy(
    corpus: list[CorpusRow],
    query_vector: list[float],
    *,
    normalizes_embeddings: bool,
) -> NDArray[np.float32]:
    """Compute cosine scores; normalize at search time when corpus is not unit-normalized."""
    matrix = corpus_matrix(corpus)
    if matrix.size == 0:
        return np.zeros(0, dtype=np.float32)
    return cosine_scores(
        matrix,
        query_vector,
        corpus_already_normalized=normalizes_embeddings,
        query_already_normalized=False,
    )


def prepare_query_blob(query_vector: list[float]) -> bytes:
    """Pack an L2-normalized query for sqlite-vec distance functions."""
    from studium.index.embeddings.serialize import pack_vector

    normalized = l2_normalize_vector(query_vector)
    return pack_vector(normalized.tolist())


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None
