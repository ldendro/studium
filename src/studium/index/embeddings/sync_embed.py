"""Optional sync+embed convenience wrapper."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine

from studium.index.config import DEFAULT_EMBEDDING_BATCH_SIZE, IndexConfig
from studium.index.embeddings.enumerate import enumerate_embedding_work
from studium.index.embeddings.pipeline import EmbeddingProcessReport, process_embedding_work
from studium.index.embeddings.protocol import EmbeddingProvider
from studium.index.sync.models import SyncReport
from studium.index.sync.synchronizer import sync_vault
from studium.vault import Vault


@dataclass(frozen=True, slots=True)
class SyncAndEmbedReport:
    sync: SyncReport
    embeddings: EmbeddingProcessReport


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
    Set ``from_current_projections=False`` to process only sync-emitted deltas.
    """
    sync_report = sync_vault(vault, engine, config)
    work = (
        enumerate_embedding_work(engine) if from_current_projections else sync_report.embedding_work
    )
    embed_report = process_embedding_work(
        engine,
        work,
        provider,
        indexed_revision=sync_report.revision_after,
        batch_size=batch_size,
    )
    return SyncAndEmbedReport(sync=sync_report, embeddings=embed_report)
