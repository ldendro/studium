"""Tests for WriteProposal."""

from __future__ import annotations

from studium.schemas import ValidationIssue, ValidationSeverity, WriteOperation, WriteProposal


def test_create_proposal_flags() -> None:
    proposal = WriteProposal(
        operation=WriteOperation.CREATE_NOTE,
        target_path="concepts/test.md",
        before_content=None,
        after_content="# Test\n",
        warnings=[],
        critical_errors=[],
        would_create=True,
        would_update=False,
        would_overwrite=False,
        expected_existing_hash=None,
    )

    assert proposal.operation == WriteOperation.CREATE_NOTE
    assert proposal.would_create is True
    assert proposal.would_update is False
    assert proposal.expected_existing_hash is None


def test_update_proposal_with_hash_and_warnings() -> None:
    warning = ValidationIssue(
        message="Scaffold section missing in body",
        severity=ValidationSeverity.WARNING,
    )
    proposal = WriteProposal(
        operation=WriteOperation.UPDATE_NOTE,
        target_path="concepts/existing.md",
        before_content="# Existing\n",
        after_content="# Updated\n",
        warnings=[warning],
        critical_errors=[],
        would_create=False,
        would_update=True,
        would_overwrite=True,
        expected_existing_hash="abc123",
    )

    assert proposal.operation == WriteOperation.UPDATE_NOTE
    assert proposal.would_update is True
    assert proposal.would_overwrite is True
    assert proposal.expected_existing_hash == "abc123"
    assert len(proposal.warnings) == 1
