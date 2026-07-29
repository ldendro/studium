"""Application-data and vault-index path helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path

from platformdirs import user_data_dir


def resolve_application_data_dir(override: Path | None = None) -> Path:
    """Return the Studium application data directory."""
    if override is not None:
        return override.expanduser().resolve()
    return Path(user_data_dir("studium", appauthor=False)).resolve()


def derive_vault_identifier(vault_root: Path) -> str:
    """Derive a filesystem-safe vault identifier from the resolved vault path."""
    resolved = str(vault_root.expanduser().resolve())
    digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()
    return digest[:32]


def index_db_path(app_data: Path, vault_id: str) -> Path:
    """Return the SQLite path for a vault's derived concept index."""
    return app_data / "indexes" / vault_id / "concept-index.sqlite"
