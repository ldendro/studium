"""Tests for vault-relative path resolution."""

from pathlib import Path

import pytest

from studium.vault.errors import VaultNotFoundError, VaultPathError
from studium.vault.paths import resolve_vault_path


def test_resolve_valid_relative_path(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    note = notes / "concept.md"
    note.write_text("# Concept", encoding="utf-8")

    resolved = resolve_vault_path(vault, "notes/concept.md")
    assert resolved == note.resolve()


def test_rejects_path_traversal(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(VaultPathError, match="escapes vault root"):
        resolve_vault_path(vault, "../outside.md")


def test_rejects_nested_path_traversal(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(VaultPathError, match="escapes vault root"):
        resolve_vault_path(vault, "notes/../../outside.md")


def test_rejects_absolute_path(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    absolute = tmp_path / "absolute.md"
    absolute.write_text("content", encoding="utf-8")

    with pytest.raises(VaultPathError, match="Absolute paths are not allowed"):
        resolve_vault_path(vault, str(absolute))


def test_missing_vault_root_raises_not_found(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"

    with pytest.raises(VaultNotFoundError, match="does not exist"):
        resolve_vault_path(missing_root, "notes/concept.md")


def test_vault_root_file_raises_not_found(tmp_path: Path) -> None:
    vault_file = tmp_path / "not-a-dir"
    vault_file.write_text("content", encoding="utf-8")

    with pytest.raises(VaultNotFoundError, match="not a directory"):
        resolve_vault_path(vault_file, "notes/concept.md")


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="symlinks unavailable")
def test_rejects_symlink_escaping_vault_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    escape_link = vault / "escape.md"
    escape_link.symlink_to(outside)

    with pytest.raises(VaultPathError, match="escapes vault root"):
        resolve_vault_path(vault, "escape.md")
