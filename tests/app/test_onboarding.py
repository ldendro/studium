"""Onboarding inspection, vault memory, and archive import."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from studium.app.config import load_last_workspace, remember_last_workspace
from studium.app.onboarding import create_workspace, import_vault_archive, inspect_vault
from studium.app.workspace import WorkspaceRegistry


def test_inspect_missing_and_valid_paths(tmp_path: Path) -> None:
    missing = inspect_vault(tmp_path / "nope")
    assert missing["exists"] is False
    assert missing["ready"] is False
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "hello.md").write_text("# Hello\n", encoding="utf-8")
    report = inspect_vault(vault)
    assert report["ready"] is True
    assert report["markdown_files"] == 1


def test_remember_last_workspace(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    app_data = tmp_path / "app-data"
    remember_last_workspace(vault, app_data)
    loaded = load_last_workspace(app_data)
    assert loaded is not None
    assert loaded[0] == vault.resolve()


def test_create_empty_workspace(tmp_path: Path) -> None:
    registry = WorkspaceRegistry()
    try:
        workspace, seeded = create_workspace(
            registry,
            vault_path=tmp_path / "new-vault",
            app_data_dir=tmp_path / "app-data",
            demo=False,
        )
        assert seeded is None
        health = workspace.health()
        assert health["workspace_open"] is True
        assert health["status"] == "ok"
        assert (tmp_path / "new-vault" / "concepts").is_dir()
    finally:
        registry.close()


def test_import_archive_into_new_vault(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("vault/readme.md", "# Imported\n")
        archive.writestr("vault/concepts/note.md", "# Note\n")
    registry = WorkspaceRegistry()
    try:
        workspace, report = import_vault_archive(
            registry,
            archive_bytes=buffer.getvalue(),
            vault_path=tmp_path / "imported",
            app_data_dir=tmp_path / "app-data",
        )
        assert report["imported_files"] == 2
        assert workspace.vault.exists("readme.md")
    finally:
        registry.close()


def test_import_rejects_path_escape(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../escape.md", "nope")
    registry = WorkspaceRegistry()
    with pytest.raises(ValueError, match="Unsafe archive member"):
        import_vault_archive(
            registry,
            archive_bytes=buffer.getvalue(),
            vault_path=tmp_path / "imported",
            app_data_dir=tmp_path / "app-data",
        )
    registry.close()
