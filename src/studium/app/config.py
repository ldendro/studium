"""Paths and runtime configuration for one local Studium workspace."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

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

    @property
    def logs_dir(self) -> Path:
        return self.resolved_app_data_dir / "logs"

    def ensure_directories(self) -> None:
        for directory in (
            self.workspace_dir,
            self.source_assets_dir,
            self.backups_dir,
            self.exports_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def last_workspace_path(app_data_dir: Path | None = None) -> Path:
    return resolve_application_data_dir(app_data_dir) / "last-workspace.json"


def remember_last_workspace(vault_root: Path, app_data_dir: Path | None = None) -> None:
    payload = {
        "vault_path": str(vault_root.expanduser().resolve()),
        "app_data_path": (
            None if app_data_dir is None else str(Path(app_data_dir).expanduser().resolve())
        ),
    }
    path = last_workspace_path(app_data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_last_workspace(app_data_dir: Path | None = None) -> tuple[Path, Path | None] | None:
    path = last_workspace_path(app_data_dir)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    mapping = cast(dict[str, Any], payload)
    vault = Path(str(mapping.get("vault_path") or "")).expanduser()
    if not vault.is_dir():
        return None
    raw_app = mapping.get("app_data_path")
    app_data = None if raw_app in {None, ""} else Path(str(raw_app)).expanduser()
    return vault.resolve(), None if app_data is None else app_data.resolve()
