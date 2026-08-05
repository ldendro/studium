"""Optional sync+embed convenience wrapper."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine

from studium.index.config import DEFAULT_EMBEDDING_BATCH_SIZE, IndexConfig
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
) -> SyncAndEmbedReport:
    """Run ``sync_vault`` then ``process_embedding_work`` for emitted requests."""
    sync_report = sync_vault(vault, engine, config)
    embed_report = process_embedding_work(
        engine,
        sync_report.embedding_work,
        provider,
        indexed_revision=sync_report.revision_after,
        batch_size=batch_size,
    )
    return SyncAndEmbedReport(sync=sync_report, embeddings=embed_report)
