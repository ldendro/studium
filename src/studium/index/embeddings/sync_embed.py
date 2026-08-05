"""Optional sync+embed convenience wrapper."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine

from studium.index.config import DEFAULT_EMBEDDING_BATCH_SIZE, IndexConfig
from studium.index.embeddings.enumerate import enumerate_embedding_work
from studium.index.embeddings.pipeline import EmbeddingProcessReport, process_embedding_work
from studium.index.embeddings.protocol import EmbeddingProvider
from studium.index.sync.models import EmbeddingWorkRequest, SyncReport, SyncStatus
from studium.index.sync.synchronizer import sync_vault
from studium.vault import Vault


@dataclass(frozen=True, slots=True)
class SyncAndEmbedReport:
    sync: SyncReport
    embeddings: EmbeddingProcessReport


def _work_key(item: EmbeddingWorkRequest) -> tuple[str, str, str, str]:
    return (
        item.owner_type,
        item.owner_id,
        item.embedding_type,
        "" if item.segment_id is None else item.segment_id,
    )


def merge_embedding_work(
    enumerated: list[EmbeddingWorkRequest],
    sync_work: list[EmbeddingWorkRequest],
) -> list[EmbeddingWorkRequest]:
    """Prefer sync-emitted texts for changed projections; fill the rest from enumeration."""
    by_key = {_work_key(item): item for item in enumerated}
    for item in sync_work:
        by_key[_work_key(item)] = item
    return list(by_key.values())


def sync_and_embed(
    vault: Vault,
    engine: Engine,
    config: IndexConfig,
    provider: EmbeddingProvider,
    *,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    from_current_projections: bool = True,
) -> SyncAndEmbedReport:
    """Run ``sync_vault`` then embed work.

    By default, work is enumerated from current index projections so unchanged
    vaults still repair missing rows and regenerate on model/metadata changes.
    Sync-emitted items override enumeration for the same owner/type/segment so
    just-synced projection texts win. Set ``from_current_projections=False`` to
    process only sync-emitted deltas.

    When sync status is ``FAILED``, embedding is skipped (no provider/upsert side
    effects on an index the sync explicitly rejected).
    """
    sync_report = sync_vault(vault, engine, config)
    if sync_report.status == SyncStatus.FAILED:
        meta = provider.model_metadata()
        return SyncAndEmbedReport(
            sync=sync_report,
            embeddings=EmbeddingProcessReport(
                model_id=meta.model_id,
                dimension=meta.dimension,
            ),
        )

    if from_current_projections:
        work = merge_embedding_work(
            enumerate_embedding_work(engine),
            sync_report.embedding_work,
        )
    else:
        work = sync_report.embedding_work

    embed_report = process_embedding_work(
        engine,
        work,
        provider,
        indexed_revision=sync_report.revision_after,
        batch_size=batch_size,
    )
    return SyncAndEmbedReport(sync=sync_report, embeddings=embed_report)
