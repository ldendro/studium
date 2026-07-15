"""Shared helpers for CLI tests."""

from __future__ import annotations

from pathlib import Path

FIXTURE_VAULT = Path(__file__).resolve().parents[1] / "fixtures" / "test_vault"


def make_temp_vault(tmp_path: Path) -> Path:
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    return vault_root
