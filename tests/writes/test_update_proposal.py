"""Tests for update-note write proposals."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from studium.serialization import create_concept_note_markdown, serialize_concept_note
from studium.writes import (
    build_metadata_update_proposal,
    build_update_note_proposal,
    hash_file_content,
)
from tests.parsing.conftest import load_fixture
from tests.serialization.helpers import build_sample_metadata
from tests.writes.conftest import make_vault, seed_note


def test_update_proposal_captures_before_and_hash(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    before = load_fixture("valid_concept_note.md")
    seed_note(vault_root, "concepts/existing.md", before)
    after = before.replace("scaffolded", "in_progress")

    proposal = build_update_note_proposal(vault, "concepts/existing.md", after)

    assert proposal.before_content == before
    assert proposal.after_content == after
    assert proposal.expected_existing_hash is not None
    assert proposal.would_update is True
    assert proposal.would_overwrite is True
    assert proposal.critical_errors == []


def test_update_proposal_uses_provided_before_content_without_rereading(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    before = load_fixture("valid_concept_note.md")
    seed_note(vault_root, "concepts/existing.md", before)
    after = before.replace("scaffolded", "in_progress")

    with patch.object(vault, "read_markdown") as mock_read:
        proposal = build_update_note_proposal(
            vault,
            "concepts/existing.md",
            after,
            before_content=before,
        )

    mock_read.assert_not_called()
    assert proposal.before_content == before
    assert proposal.expected_existing_hash is not None


def test_metadata_update_proposal_reads_file_once(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    before = load_fixture("valid_concept_note.md")
    seed_note(vault_root, "concepts/existing.md", before)
    metadata = build_sample_metadata(status="in_progress")

    with patch.object(vault, "read_markdown", wraps=vault.read_markdown) as mock_read:
        build_metadata_update_proposal(vault, "concepts/existing.md", metadata)

    assert mock_read.call_count == 1


def test_metadata_update_proposal_defaults_none_body_to_empty_string(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    before = load_fixture("valid_concept_note.md")
    seed_note(vault_root, "concepts/existing.md", before)
    metadata = build_sample_metadata(status="in_progress")

    with (
        patch("studium.writes.proposal.parse_concept_note") as mock_parse,
        patch(
            "studium.writes.proposal.serialize_concept_note",
            wraps=serialize_concept_note,
        ) as mock_serialize,
    ):
        mock_parsed = MagicMock()
        mock_parsed.body = None
        mock_parse.return_value = mock_parsed
        build_metadata_update_proposal(vault, "concepts/existing.md", metadata)

    mock_serialize.assert_called_once()
    assert mock_serialize.call_args[0][1] == ""


def test_update_proposal_missing_file_returns_critical(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)
    after_content = create_concept_note_markdown("Missing Target")

    proposal = build_update_note_proposal(vault, "concepts/missing.md", after_content)

    assert proposal.before_content is None
    assert proposal.expected_existing_hash is None
    assert proposal.would_create is True
    assert proposal.would_update is False
    assert any(issue.code == "target_file_missing" for issue in proposal.critical_errors)


def test_metadata_update_proposal_changes_metadata_and_preserves_body(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    before = load_fixture("valid_concept_note.md")
    seed_note(vault_root, "concepts/existing.md", before)
    metadata = build_sample_metadata(status="in_progress")

    proposal = build_metadata_update_proposal(
        vault,
        "concepts/existing.md",
        metadata,
    )

    assert proposal.before_content == before
    assert proposal.after_content != before
    assert "in_progress" in proposal.after_content
    assert proposal.critical_errors == []


def test_update_proposal_rejects_non_markdown_target(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)

    proposal = build_update_note_proposal(
        vault,
        "concepts/note.txt",
        create_concept_note_markdown("Test Concept"),
    )

    assert any(issue.code == "invalid_target_extension" for issue in proposal.critical_errors)


def test_update_proposal_existing_non_markdown_target_returns_proposal(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    content = "plain text"
    seed_note(vault_root, "concepts/note.txt", content)

    proposal = build_update_note_proposal(
        vault,
        "concepts/note.txt",
        create_concept_note_markdown("Test Concept"),
    )

    assert any(issue.code == "invalid_target_extension" for issue in proposal.critical_errors)
    assert proposal.before_content == content
    assert proposal.expected_existing_hash == hash_file_content(content)
    assert proposal.would_update is True
    assert proposal.would_overwrite is True


def test_metadata_update_proposal_existing_non_markdown_target_returns_proposal(
    tmp_path: Path,
) -> None:
    vault_root, vault = make_vault(tmp_path)
    content = "plain text"
    seed_note(vault_root, "concepts/note.txt", content)
    metadata = build_sample_metadata()

    proposal = build_metadata_update_proposal(vault, "concepts/note.txt", metadata)

    assert any(issue.code == "invalid_target_extension" for issue in proposal.critical_errors)
    assert proposal.before_content == content
    assert proposal.expected_existing_hash == hash_file_content(content)


def test_metadata_update_proposal_when_file_missing_uses_canonical_body(tmp_path: Path) -> None:
    _, vault = make_vault(tmp_path)
    metadata = build_sample_metadata()

    proposal = build_metadata_update_proposal(vault, "concepts/missing.md", metadata)

    assert any(issue.code == "target_file_missing" for issue in proposal.critical_errors)
    assert metadata.canonical_title in proposal.after_content


def test_update_proposal_includes_validation_critical_errors(tmp_path: Path) -> None:
    vault_root, vault = make_vault(tmp_path)
    before = load_fixture("valid_concept_note.md")
    seed_note(vault_root, "concepts/existing.md", before)

    proposal = build_update_note_proposal(
        vault,
        "concepts/existing.md",
        load_fixture("invalid_yaml_note.md"),
    )

    assert proposal.critical_errors
    assert any(
        issue.code not in {"target_file_missing", "invalid_target_extension"}
        for issue in proposal.critical_errors
    )
