"""Paths and runtime configuration for one local Studium workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from studium.index.paths import derive_vault_identifier, resolve_application_data_dir


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Resolved locations for durable application state around a vault."""

    vault_root: Path
    app_data_dir: Path | None = None

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
    def workspace_dir(self) -> Path:
        return self.resolved_app_data_dir / "workspaces" / self.vault_identifier

    @property
    def database_path(self) -> Path:
        return self.workspace_dir / "studium.sqlite"

    @property
    def source_assets_dir(self) -> Path:
        return self.workspace_dir / "sources"

    @property
    def backups_dir(self) -> Path:
        return self.workspace_dir / "backups"

    @property
    def exports_dir(self) -> Path:
        return self.workspace_dir / "exports"

    def ensure_directories(self) -> None:
        for directory in (
            self.workspace_dir,
            self.source_assets_dir,
            self.backups_dir,
            self.exports_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
