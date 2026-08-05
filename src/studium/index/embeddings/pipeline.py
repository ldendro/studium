"""Consume embedding work requests and persist vectors."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Engine

from studium.index.config import DEFAULT_EMBEDDING_BATCH_SIZE
from studium.index.embeddings.protocol import EmbeddingModelMetadata, EmbeddingProvider
from studium.index.embeddings.serialize import pack_vector
from studium.index.engine import begin_connection
from studium.index.repositories import embeddings as embeddings_repo
from studium.index.sync.models import EmbeddingWorkRequest


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_strings() -> list[str]:
    return []


class EmbeddingProcessReport(BaseModel):
    """Outcome of ``process_embedding_work``."""

    model_config = ConfigDict(extra="forbid")

    requested: int = 0
    skipped: int = 0
    embedded: int = 0
    written: int = 0
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
    metadata. Provider calls happen before short DB write transactions.
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
            if existing is not None and _row_matches(existing, item, meta):
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
            continue
        if len(vectors) != len(batch):
            report.errors.append(f"Provider returned {len(vectors)} vectors for {len(batch)} texts")
            continue
        report.embedded += len(batch)
        now = _utc_now_iso()
        with begin_connection(engine) as connection:
            for item, vector in zip(batch, vectors, strict=True):
                if len(vector) != meta.dimension:
                    report.errors.append(
                        f"{item.owner_id}/{item.embedding_type}: "
                        f"got dim {len(vector)}, expected {meta.dimension}"
                    )
                    continue
                embeddings_repo.upsert_embedding(
                    connection,
                    {
                        "owner_type": item.owner_type,
                        "owner_id": item.owner_id,
                        "parent_concept_id": item.parent_concept_id,
                        "segment_id": item.segment_id,
                        "embedding_type": item.embedding_type,
                        "vector": pack_vector(vector),
                        "dimension": meta.dimension,
                        "model_id": meta.model_id,
                        "model_revision": meta.model_revision,
                        "input_hash": item.input_hash,
                        "created_at": now,
                        "indexed_revision": indexed_revision,
                    },
                )
                report.written += 1
    return report


def _row_matches(
    existing: dict[str, Any],
    item: EmbeddingWorkRequest,
    meta: EmbeddingModelMetadata,
) -> bool:
    return (
        str(existing.get("input_hash")) == item.input_hash
        and str(existing.get("model_id")) == meta.model_id
        and int(existing.get("dimension") or 0) == meta.dimension
        and (existing.get("model_revision") == meta.model_revision)
    )
