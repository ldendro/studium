"""Configuration for the derived SQLite concept index."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from studium.index.paths import (
    derive_vault_identifier,
    index_db_path,
    resolve_application_data_dir,
)

INDEX_SCHEMA_VERSION = 5
DEFAULT_BUSY_TIMEOUT_MS = 5000

# Phase 2 module embedding input cap (tune after memory benchmarks).
MAX_MODULE_EMBED_CHARS = 4000

DEFAULT_EMBEDDING_BATCH_SIZE = 32
DEFAULT_EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

# Empirically selected default (see P2-B06 Implementation Notes).
DEFAULT_VECTOR_BACKEND = "numpy"

# Weighted reciprocal rank fusion (B07; tunable via evaluation harness).
DEFAULT_RRF_CONSTANT = 60.0
DEFAULT_RRF_WEIGHTS: dict[str, float] = {
    "fts": 1.0,
    "identity_vector": 1.0,
    "semantic_vector": 1.2,
    "module_vector": 0.8,
}

# Default OpenAI-compatible local reasoning model (B10).
DEFAULT_REASONING_MODEL = "llama3.2:3b"
DEFAULT_LLM_BASE_URL = "http://127.0.0.1:11434/v1"


@dataclass(frozen=True, slots=True)
class IndexConfig:
    """Runtime configuration for opening or creating a vault index."""

    vault_root: Path
    app_data_dir: Path | None = None
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS

    @property
    def resolved_vault_root(self) -> Path:
        return self.vault_root.expanduser().resolve()

    @property
    def resolved_app_data_dir(self) -> Path:
        return resolve_application_data_dir(self.app_data_dir)

    @property
    def vault_identifier(self) -> str:
        return derive_vault_identifier(self.resolved_vault_root)

    @property
    def database_path(self) -> Path:
        return index_db_path(self.resolved_app_data_dir, self.vault_identifier)
