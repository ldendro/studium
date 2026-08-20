"""Consume embedding work requests and persist vectors."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Engine

from studium.index.config import DEFAULT_EMBEDDING_BATCH_SIZE
from studium.index.embeddings.protocol import EmbeddingModelMetadata, EmbeddingProvider
from studium.index.embeddings.serialize import pack_vector, unpack_vector
from studium.index.engine import begin_connection
from studium.index.repositories import embeddings as embeddings_repo
from studium.index.sync.models import EmbeddingWorkRequest

# Persisted sentinel: prior dimension-mismatch rejection for this input/model.
_REJECTION_DIMENSION = 0


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_strings() -> list[str]:
    return []


def _as_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes"}:
            return True
        if lowered in {"0", "false", "no"}:
            return False
    return None


class EmbeddingProcessReport(BaseModel):
    """Outcome of ``process_embedding_work``."""

    model_config = ConfigDict(extra="forbid")

    requested: int = 0
    skipped: int = 0
    embedded: int = 0
    written: int = 0
    failed: int = 0
    model_id: str = ""
    dimension: int = 0
    errors: list[str] = Field(default_factory=_empty_strings)


def embed_query(provider: EmbeddingProvider, text: str) -> list[float]:
    """Embed a query string without persisting it."""
    return provider.embed_query(text)


def process_embedding_work(
    engine: Engine,
    work: list[EmbeddingWorkRequest],
    provider: EmbeddingProvider,
    *,
    indexed_revision: int,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
) -> EmbeddingProcessReport:
    """Batch-generate embeddings for deferred sync work and upsert rows.

    Skips items whose stored row already matches input hash and active model
    metadata (including normalization mode), and items previously rejected for
    a dimension mismatch under the same model identity. Provider calls happen
    before short DB write transactions.
    """
    meta = provider.model_metadata()
    report = EmbeddingProcessReport(
        requested=len(work),
        model_id=meta.model_id,
        dimension=meta.dimension,
    )
    if not work:
        return report

    to_embed: list[EmbeddingWorkRequest] = []
    with engine.connect() as connection:
        for item in work:
            existing = embeddings_repo.get_embedding_for_key(
                connection,
                owner_type=item.owner_type,
                owner_id=item.owner_id,
                embedding_type=item.embedding_type,
                segment_id=item.segment_id,
            )
            if existing is not None and _should_skip(existing, item, meta):
                report.skipped += 1
                continue
            to_embed.append(item)

    if not to_embed:
        return report

    effective_batch = batch_size if batch_size > 0 else len(to_embed)
    for start in range(0, len(to_embed), effective_batch):
        batch = to_embed[start : start + effective_batch]
        texts = [item.input_text for item in batch]
        try:
            vectors = provider.embed_documents(texts)
        except Exception as exc:
            report.errors.append(f"embed_documents failed: {exc}")
            report.failed += len(batch)
            continue
        if len(vectors) != len(batch):
            report.errors.append(f"Provider returned {len(vectors)} vectors for {len(batch)} texts")
            report.failed += len(batch)
            continue
        now = _utc_now_iso()
        with begin_connection(engine) as connection:
            for item, vector in zip(batch, vectors, strict=True):
                parent_concept_id = _resolve_parent_concept_id(item)
                if parent_concept_id is None:
                    report.errors.append(
                        f"{item.owner_id}/{item.embedding_type}: "
                        "parent_concept_id is required for scaffold_module work"
                    )
                    report.failed += 1
                    continue
                if len(vector) != meta.dimension:
                    report.errors.append(
                        f"{item.owner_id}/{item.embedding_type}: "
                        f"got dim {len(vector)}, expected {meta.dimension}"
                    )
                    report.failed += 1
                    # Durable rejection so the same input/model is not re-sent forever.
                    embeddings_repo.upsert_embedding(
                        connection,
                        _embedding_row_values(
                            item,
                            meta,
                            parent_concept_id=parent_concept_id,
                            vector_blob=b"",
                            dimension=_REJECTION_DIMENSION,
                            indexed_revision=indexed_revision,
                            created_at=now,
                        ),
                    )
                    continue
                if not _is_valid_vector(vector, expected_dimension=meta.dimension):
                    report.errors.append(
                        f"{item.owner_id}/{item.embedding_type}: "
                        "vector must contain finite values and have non-zero norm"
                    )
                    report.failed += 1
                    continue
                embeddings_repo.upsert_embedding(
                    connection,
                    _embedding_row_values(
                        item,
                        meta,
                        parent_concept_id=parent_concept_id,
                        vector_blob=pack_vector(vector),
                        dimension=meta.dimension,
                        indexed_revision=indexed_revision,
                        created_at=now,
                    ),
                )
                report.embedded += 1
                report.written += 1
    return report


def _resolve_parent_concept_id(item: EmbeddingWorkRequest) -> str | None:
    """Return a concept id that FK-cascades on concept removal.

    Concept work defaults ``parent_concept_id`` to ``owner_id`` when omitted.
    Module work requires an explicit parent — otherwise the row would orphan.
    """
    if item.parent_concept_id is not None:
        return item.parent_concept_id
    if item.owner_type == "concept":
        return item.owner_id
    return None


def _embedding_row_values(
    item: EmbeddingWorkRequest,
    meta: EmbeddingModelMetadata,
    *,
    parent_concept_id: str,
    vector_blob: bytes,
    dimension: int,
    indexed_revision: int,
    created_at: str,
) -> dict[str, Any]:
    return {
        "owner_type": item.owner_type,
        "owner_id": item.owner_id,
        "parent_concept_id": parent_concept_id,
        "segment_id": item.segment_id,
        "embedding_type": item.embedding_type,
        "vector": vector_blob,
        "dimension": dimension,
        "model_id": meta.model_id,
        "model_revision": meta.model_revision,
        "normalizes_embeddings": meta.normalizes_embeddings,
        "input_hash": item.input_hash,
        "created_at": created_at,
        "indexed_revision": indexed_revision,
    }


def _should_skip(
    existing: dict[str, Any],
    item: EmbeddingWorkRequest,
    meta: EmbeddingModelMetadata,
) -> bool:
    if _row_matches(existing, item, meta):
        return True
    return _is_dimension_rejection(existing, item, meta)


def _row_matches(
    existing: dict[str, Any],
    item: EmbeddingWorkRequest,
    meta: EmbeddingModelMetadata,
) -> bool:
    stored_normalize = _as_bool(existing.get("normalizes_embeddings"))
    if stored_normalize is None:
        return False
    metadata_matches = (
        str(existing.get("input_hash")) == item.input_hash
        and str(existing.get("model_id")) == meta.model_id
        and int(existing.get("dimension") or 0) == meta.dimension
        and (existing.get("model_revision") == meta.model_revision)
        and stored_normalize == meta.normalizes_embeddings
    )
    if not metadata_matches:
        return False
    raw_blob = existing.get("vector")
    if isinstance(raw_blob, memoryview):
        blob = raw_blob.tobytes()
    elif isinstance(raw_blob, bytes):
        blob = raw_blob
    else:
        return False
    try:
        vector = unpack_vector(blob, dimension=meta.dimension)
    except ValueError:
        return False
    return _is_valid_vector(vector, expected_dimension=meta.dimension)


def _is_valid_vector(vector: list[float], *, expected_dimension: int) -> bool:
    if len(vector) != expected_dimension or not all(math.isfinite(value) for value in vector):
        return False
    squared_norm = math.fsum(value * value for value in vector)
    return math.isfinite(squared_norm) and squared_norm > 0.0


def _is_dimension_rejection(
    existing: dict[str, Any],
    item: EmbeddingWorkRequest,
    meta: EmbeddingModelMetadata,
) -> bool:
    """True when a prior dim-mismatch rejection exists for this input/model."""
    stored_normalize = _as_bool(existing.get("normalizes_embeddings"))
    if stored_normalize is None:
        return False
    raw_dim = existing.get("dimension")
    stored_dim = -1 if raw_dim is None else int(raw_dim)
    return (
        stored_dim == _REJECTION_DIMENSION
        and str(existing.get("input_hash")) == item.input_hash
        and str(existing.get("model_id")) == meta.model_id
        and (existing.get("model_revision") == meta.model_revision)
        and stored_normalize == meta.normalizes_embeddings
    )
