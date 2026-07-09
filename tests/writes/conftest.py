"""Shared helpers for write layer tests."""

from __future__ import annotations

from pathlib import Path

from studium.vault import Vault


def make_vault(tmp_path: Path) -> tuple[Path, Vault]:
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    return vault_root, Vault(vault_root)


def seed_note(vault_root: Path, relative_path: str, content: str) -> None:
    target = vault_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
