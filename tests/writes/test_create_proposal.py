"""Tests for create-note write proposals."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from studium.serialization import create_concept_note_markdown
from studium.vault.errors import VaultPathError
from studium.writes import (
    build_create_note_proposal,
    build_create_note_proposal_from_title,
    proposal_can_be_committed,
)
from tests.parsing.conftest import load_fixture
from tests.writes.conftest import make_vault, seed_note


def test_create_proposal_on_empty_vault(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)
    after_content = create_concept_note_markdown("Test Concept")

    proposal = build_create_note_proposal(vault, "concepts/test.md", after_content)

    assert proposal.operation.value == "create_note"
    assert proposal.before_content is None
    assert proposal.would_create is True
    assert proposal.would_update is False
    assert proposal.would_overwrite is False
    assert proposal.critical_errors == []
    assert proposal_can_be_committed(proposal) is True


def test_create_proposal_from_title(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)

    proposal = build_create_note_proposal_from_title(
        vault,
        "concepts/new-note.md",
        "Gradient Descent",
    )

    assert proposal.would_create is True
    assert proposal.critical_errors == []
    assert "Gradient Descent" in proposal.after_content


def test_create_proposal_detects_collision(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    seed_note(vault_root, "concepts/existing.md", "# Existing\n")

    proposal = build_create_note_proposal(
        vault,
        "concepts/existing.md",
        create_concept_note_markdown("Another Concept"),
    )

    assert proposal.would_overwrite is True
    assert proposal.would_create is False
    assert any(issue.code == "target_file_exists" for issue in proposal.critical_errors)
    assert proposal_can_be_committed(proposal) is False


def test_create_proposal_rejects_non_markdown_target(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)

    proposal = build_create_note_proposal(
        vault,
        "concepts/note.txt",
        create_concept_note_markdown("Test Concept"),
    )

    assert any(issue.code == "invalid_target_extension" for issue in proposal.critical_errors)


def test_create_proposal_includes_validation_critical_errors(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)
    invalid_content = load_fixture("invalid_yaml_note.md")

    proposal = build_create_note_proposal(vault, "concepts/invalid.md", invalid_content)

    assert proposal.critical_errors
    assert proposal_can_be_committed(proposal) is False


def test_create_proposal_propagates_path_traversal_errors(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)

    with pytest.raises(VaultPathError, match="escapes vault root"):
        build_create_note_proposal(
            vault,
            "../outside.md",
            create_concept_note_markdown("Test Concept"),
        )


def test_empty_title_rejected_by_metadata_validation(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)

    with pytest.raises(ValidationError):
        build_create_note_proposal_from_title(vault, "concepts/empty.md", "")
