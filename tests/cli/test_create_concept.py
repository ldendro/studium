"""Tests for CLI path helpers and create-concept."""

from __future__ import annotations

from pathlib import Path

import pytest

from studium.cli.main import main
from studium.cli.paths import default_concept_path
from studium.vault import Vault
from tests.cli.conftest import make_temp_vault


def test_default_concept_path_uses_hyphens() -> None:
    assert (
        default_concept_path("Stochastic Gradient Descent")
        == "concepts/stochastic-gradient-descent.md"
    )


def test_create_concept_writes_note(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    vault_root = make_temp_vault(tmp_path)

    code = main(
        [
            "create-concept",
            "Stochastic Gradient Descent",
            "--vault",
            str(vault_root),
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    assert "Write proposal:" in captured.out
    assert "Committed: concepts/stochastic-gradient-descent.md" in captured.out

    vault = Vault(vault_root)
    assert vault.exists("concepts/stochastic-gradient-descent.md")
    content = vault.read_markdown("concepts/stochastic-gradient-descent.md")
    assert "Stochastic Gradient Descent" in content


def test_create_concept_dry_run_does_not_write(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault_root = make_temp_vault(tmp_path)

    code = main(
        [
            "create-concept",
            "Dry Run Concept",
            "--vault",
            str(vault_root),
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    assert "status=dry-run (not committed)" in captured.out
    assert "Committed:" not in captured.out
    assert not Vault(vault_root).exists("concepts/dry-run-concept.md")


def test_create_concept_collision_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault_root = make_temp_vault(tmp_path)
    args = [
        "create-concept",
        "Collision Concept",
        "--vault",
        str(vault_root),
    ]
    assert main(args) == 0
    code = main(args)
    captured = capsys.readouterr()
    assert code == 1
    assert "target_file_exists" in captured.out or "critical" in captured.out.lower()


def test_create_concept_custom_path(tmp_path: Path) -> None:
    vault_root = make_temp_vault(tmp_path)

    code = main(
        [
            "create-concept",
            "Custom Path Concept",
            "--vault",
            str(vault_root),
            "--path",
            "notes/custom.md",
        ]
    )

    assert code == 0
    assert Vault(vault_root).exists("notes/custom.md")
