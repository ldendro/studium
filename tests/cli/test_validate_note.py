"""Tests for validate-note CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from studium.cli.main import main
from tests.cli.conftest import FIXTURE_VAULT, make_temp_vault


def test_validate_note_valid_fixture(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "validate-note",
            "concepts/valid_concept_note.md",
            "--vault",
            str(FIXTURE_VAULT),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "valid" in captured.out
    assert "concepts/valid_concept_note.md" in captured.out


def test_validate_note_invalid_yaml_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "validate-note",
            "concepts/invalid_yaml_note.md",
            "--vault",
            str(FIXTURE_VAULT),
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "invalid" in captured.out
    assert "critical" in captured.out.lower()


def test_validate_note_missing_section_warns_but_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "validate-note",
            "concepts/missing_canonical_section.md",
            "--vault",
            str(FIXTURE_VAULT),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "valid" in captured.out
    assert "warning" in captured.out.lower() or "missing_canonical_section" in captured.out


def test_validate_note_path_outside_vault(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault_root = make_temp_vault(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")

    code = main(
        [
            "validate-note",
            str(outside),
            "--vault",
            str(vault_root),
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "error:" in captured.out
