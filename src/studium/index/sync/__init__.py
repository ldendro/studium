"""Vault → derived index synchronization (Phase 2 / P2-B03)."""

from studium.index.sync.embedding_inputs import (
    build_identity_embedding_input,
    build_module_embedding_input,
    build_semantic_embedding_input,
)
from studium.index.sync.models import (
    EmbeddingWorkRequest,
    FileSyncClass,
    SyncCounts,
    SyncReport,
    SyncStatus,
)
from studium.index.sync.synchronizer import rebuild_vault_index, sync_vault

__all__ = [
    "EmbeddingWorkRequest",
    "FileSyncClass",
    "SyncCounts",
    "SyncReport",
    "SyncStatus",
    "build_identity_embedding_input",
    "build_module_embedding_input",
    "build_semantic_embedding_input",
    "rebuild_vault_index",
    "sync_vault",
]
