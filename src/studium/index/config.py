"""Configuration for the derived SQLite concept index."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from studium.index.paths import (
    derive_vault_identifier,
    index_db_path,
    resolve_application_data_dir,
)

INDEX_SCHEMA_VERSION = 3
DEFAULT_BUSY_TIMEOUT_MS = 5000


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
