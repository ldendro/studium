"""End-to-end Phase 1 verification via CLI and library APIs."""

from __future__ import annotations

from pathlib import Path

import pytest

from studium.cli.main import main
from studium.schemas import ValidationOperation
from studium.validation import parse_and_validate
from studium.vault import Vault
from studium.writes import build_create_note_proposal_from_title, commit_write_proposal
from tests.cli.conftest import FIXTURE_VAULT, make_temp_vault


def test_e2e_create_then_validate_note(tmp_path: Path) -> None:
    vault_root = make_temp_vault(tmp_path)

    create_code = main(
        [
            "create-concept",
            "End To End Concept",
            "--vault",
            str(vault_root),
        ]
    )
    assert create_code == 0

    validate_code = main(
        [
            "validate-note",
            "concepts/end-to-end-concept.md",
            "--vault",
            str(vault_root),
        ]
    )
    assert validate_code == 0


def test_e2e_library_create_commit_parse_validate(tmp_path: Path) -> None:
    vault_root = make_temp_vault(tmp_path)
    vault = Vault(vault_root)
    proposal = build_create_note_proposal_from_title(
        vault,
        "concepts/library-e2e.md",
        "Library End To End",
    )
    assert proposal.critical_errors == []
    commit_write_proposal(vault, proposal)

    raw = vault.read_markdown("concepts/library-e2e.md")
    _, result = parse_and_validate(raw, operation=ValidationOperation.PARSE)
    assert result.is_valid is True


def test_e2e_fixture_vault_reports_known_invalid(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["validate-vault", str(FIXTURE_VAULT)])
    captured = capsys.readouterr()
    assert code == 1
    assert "concepts/invalid_yaml_note.md" in captured.out
    assert "concepts/valid_concept_note.md" in captured.out
