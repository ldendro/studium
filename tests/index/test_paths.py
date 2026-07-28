"""Tests for index path helpers and title normalization."""

from __future__ import annotations

from pathlib import Path

from studium.index import (
    derive_vault_identifier,
    index_db_path,
    normalize_title,
    resolve_application_data_dir,
)
from studium.index.config import IndexConfig


def test_resolve_application_data_dir_override(tmp_path: Path) -> None:
    override = tmp_path / "custom-data"
    assert resolve_application_data_dir(override) == override.resolve()


def test_derive_vault_identifier_is_stable(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    first = derive_vault_identifier(vault)
    second = derive_vault_identifier(vault)
    assert first == second
    assert len(first) == 32
    assert all(ch in "0123456789abcdef" for ch in first)


def test_index_db_path_layout(tmp_path: Path) -> None:
    path = index_db_path(tmp_path, "abc123")
    assert path == tmp_path / "indexes" / "abc123" / "concept-index.sqlite"


def test_index_config_database_path(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    app_data = tmp_path / "app"
    config = IndexConfig(vault_root=vault, app_data_dir=app_data)
    assert config.database_path == (
        app_data.resolve() / "indexes" / config.vault_identifier / "concept-index.sqlite"
    )


def test_normalize_title_casefold_and_collapse_whitespace() -> None:
    assert normalize_title("  Stochastic   Gradient Descent ") == "stochastic gradient descent"
