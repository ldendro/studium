"""Tests for committing write proposals."""

from __future__ import annotations

from pathlib import Path

import pytest

from studium.schemas import ValidationOperation
from studium.serialization import create_concept_note_markdown
from studium.validation import parse_and_validate
from studium.writes import (
    CollisionError,
    StaleFileError,
    WriteProposalBlockedError,
    build_create_note_proposal,
    build_create_note_proposal_from_title,
    build_metadata_update_proposal,
    build_update_note_proposal,
    commit_write_proposal,
)
from tests.parsing.conftest import load_fixture
from tests.serialization.helpers import build_sample_metadata
from tests.writes.conftest import make_vault, seed_note


def test_commit_create_writes_file(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)
    proposal = build_create_note_proposal_from_title(
        vault,
        "concepts/new-note.md",
        "Committed Concept",
    )

    commit_write_proposal(vault, proposal)

    written = vault.read_markdown("concepts/new-note.md")
    assert written == proposal.after_content


def test_commit_create_creates_parent_directories(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    proposal = build_create_note_proposal_from_title(
        vault,
        "concepts/nested/new-note.md",
        "Nested Concept",
    )

    commit_write_proposal(vault, proposal)

    assert (vault_root / "concepts/nested/new-note.md").is_file()


def test_commit_update_writes_new_content(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    before = load_fixture("valid_concept_note.md")
    seed_note(vault_root, "concepts/existing.md", before)
    metadata = build_sample_metadata(status="in_progress")
    proposal = build_metadata_update_proposal(vault, "concepts/existing.md", metadata)

    commit_write_proposal(vault, proposal)

    assert vault.read_markdown("concepts/existing.md") == proposal.after_content


def test_commit_create_end_to_end_validate(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)
    proposal = build_create_note_proposal_from_title(
        vault,
        "concepts/e2e.md",
        "End To End Concept",
    )

    commit_write_proposal(vault, proposal)

    raw = vault.read_markdown("concepts/e2e.md")
    _, result = parse_and_validate(raw, operation=ValidationOperation.PARSE)
    assert result.is_valid is True


def test_commit_blocks_proposal_with_critical_errors(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    seed_note(vault_root, "concepts/taken.md", "# Taken\n")
    proposal = build_create_note_proposal(
        vault,
        "concepts/taken.md",
        create_concept_note_markdown("Collision Concept"),
    )

    with pytest.raises(WriteProposalBlockedError):
        commit_write_proposal(vault, proposal)

    assert vault.read_markdown("concepts/taken.md") == "# Taken\n"


def test_commit_create_raises_collision_if_file_appears(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    proposal = build_create_note_proposal_from_title(
        vault,
        "concepts/race.md",
        "Race Concept",
    )
    seed_note(vault_root, "concepts/race.md", "# Appeared\n")

    with pytest.raises(CollisionError, match="already exists"):
        commit_write_proposal(vault, proposal)


def test_commit_update_raises_stale_if_file_changed(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    before = load_fixture("valid_concept_note.md")
    seed_note(vault_root, "concepts/existing.md", before)
    after = before.replace("scaffolded", "in_progress")
    proposal = build_update_note_proposal(vault, "concepts/existing.md", after)

    mutated = before.replace("Stochastic Gradient Descent", "Mutated Title")
    seed_note(vault_root, "concepts/existing.md", mutated)

    with pytest.raises(StaleFileError, match="changed since proposal"):
        commit_write_proposal(vault, proposal)


def test_commit_update_raises_when_file_deleted(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    before = load_fixture("valid_concept_note.md")
    seed_note(vault_root, "concepts/existing.md", before)
    proposal = build_update_note_proposal(vault, "concepts/existing.md", before)

    (vault_root / "concepts/existing.md").unlink()

    with pytest.raises(WriteProposalBlockedError, match="not found"):
        commit_write_proposal(vault, proposal)


def test_commit_allows_warnings_only_proposal(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)
    proposal = build_create_note_proposal_from_title(
        vault,
        "concepts/warnings-only.md",
        "Warnings Only Concept",
        concept_domains=[],
    )

    assert proposal.warnings
    assert proposal.critical_errors == []

    commit_write_proposal(vault, proposal)
    assert vault.exists("concepts/warnings-only.md")
