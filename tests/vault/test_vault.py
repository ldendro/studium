"""Tests for the Vault access API."""

import os
from pathlib import Path

import pytest

from studium.vault import Vault
from studium.vault.errors import VaultNotFoundError, VaultPathError, VaultTypeError


def _make_vault(tmp_path: Path) -> tuple[Path, Vault]:
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    return vault_root, Vault(vault_root)


def test_vault_requires_existing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(VaultNotFoundError, match="does not exist"):
        Vault(missing)

    not_dir = tmp_path / "file"
    not_dir.write_text("x", encoding="utf-8")

    with pytest.raises(VaultNotFoundError, match="not a directory"):
        Vault(not_dir)


def test_read_markdown_returns_content(tmp_path: Path) -> None:
    vault_root, vault = _make_vault(tmp_path)
    note = vault_root / "notes" / "concept.md"
    note.parent.mkdir()
    note.write_text("# Concept\n\nBody.", encoding="utf-8")

    assert vault.read_markdown("notes/concept.md") == "# Concept\n\nBody."


def test_read_markdown_missing_file_raises(tmp_path: Path) -> None:
    _, vault = _make_vault(tmp_path)

    with pytest.raises(VaultNotFoundError, match="not found"):
        vault.read_markdown("missing.md")


def test_read_markdown_rejects_non_markdown_extension(tmp_path: Path) -> None:
    vault_root, vault = _make_vault(tmp_path)
    text_file = vault_root / "notes.txt"
    text_file.write_text("plain", encoding="utf-8")

    with pytest.raises(VaultTypeError, match="Expected a Markdown file"):
        vault.read_markdown("notes.txt")


def test_exists_reports_file_presence(tmp_path: Path) -> None:
    vault_root, vault = _make_vault(tmp_path)
    note = vault_root / "present.md"
    note.write_text("content", encoding="utf-8")

    assert vault.exists("present.md") is True
    assert vault.exists("absent.md") is False


def test_exists_propagates_path_traversal_errors(tmp_path: Path) -> None:
    _, vault = _make_vault(tmp_path)

    with pytest.raises(VaultPathError, match="escapes vault root"):
        vault.exists("../outside.md")


def test_list_markdown_files_recursive_and_relative(tmp_path: Path) -> None:
    vault_root, vault = _make_vault(tmp_path)
    (vault_root / "top.md").write_text("top", encoding="utf-8")
    nested = vault_root / "concepts" / "nested"
    nested.mkdir(parents=True)
    (nested / "note.md").write_text("nested", encoding="utf-8")
    (vault_root / "readme.txt").write_text("txt", encoding="utf-8")

    assert vault.list_markdown_files() == ["concepts/nested/note.md", "top.md"]


def test_list_markdown_files_empty_vault(tmp_path: Path) -> None:
    _, vault = _make_vault(tmp_path)

    assert vault.list_markdown_files() == []


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_read_markdown_blocks_symlink_outside_vault(tmp_path: Path) -> None:
    vault_root, vault = _make_vault(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    link = vault_root / "link.md"
    link.symlink_to(outside)

    with pytest.raises(VaultPathError, match="escapes vault root"):
        vault.read_markdown("link.md")


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_list_markdown_files_excludes_symlinks_outside_vault(tmp_path: Path) -> None:
    vault_root, vault = _make_vault(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    real = vault_root / "real.md"
    real.write_text("real", encoding="utf-8")
    link = vault_root / "escape.md"
    link.symlink_to(outside)

    assert vault.list_markdown_files() == ["real.md"]


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_read_markdown_allows_symlink_within_vault(tmp_path: Path) -> None:
    vault_root, vault = _make_vault(tmp_path)
    target = vault_root / "target.md"
    target.write_text("linked content", encoding="utf-8")
    link = vault_root / "link.md"
    link.symlink_to(target)

    assert vault.read_markdown("link.md") == "linked content"
