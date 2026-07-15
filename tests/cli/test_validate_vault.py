"""Tests for validate-vault CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from studium.cli.main import main
from studium.serialization import create_concept_note_markdown
from tests.cli.conftest import FIXTURE_VAULT, make_temp_vault


def test_validate_fixture_vault_exits_nonzero_due_to_invalids(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["validate-vault", str(FIXTURE_VAULT)])
    captured = capsys.readouterr()
    assert code == 1
    assert "Summary:" in captured.out
    assert "critical" in captured.out
    assert "invalid_yaml_note.md" in captured.out


def test_validate_vault_only_valid_notes_exits_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault_root = make_temp_vault(tmp_path)
    note = vault_root / "concepts" / "ok.md"
    note.parent.mkdir(parents=True)
    note.write_text(create_concept_note_markdown("Only Valid"), encoding="utf-8")

    code = main(["validate-vault", str(vault_root)])
    captured = capsys.readouterr()
    assert code == 0
    assert "Summary: 1 files, 0 critical" in captured.out


def test_validate_empty_vault_exits_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault_root = make_temp_vault(tmp_path)
    code = main(["validate-vault", str(vault_root)])
    captured = capsys.readouterr()
    assert code == 0
    assert "Summary: 0 files, 0 critical, 0 warnings" in captured.out
