"""Write proposal builders."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from studium.parsing import parse_concept_note
from studium.schemas import (
    ConceptNoteMetadata,
    ValidationIssue,
    ValidationOperation,
    ValidationSeverity,
    WriteOperation,
    WriteProposal,
)
from studium.serialization import (
    build_canonical_concept_body,
    create_concept_note_markdown,
    serialize_concept_note,
)
from studium.validation import parse_and_validate
from studium.vault.vault import Vault
from studium.writes.hashing import hash_file_content


def proposal_can_be_committed(proposal: WriteProposal) -> bool:
    """Return whether a proposal has no blocking critical errors."""
    return not proposal.critical_errors


def _storage_critical_issue(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        message=message,
        severity=ValidationSeverity.CRITICAL,
        code=code,
    )


def _has_markdown_extension(target_path: str) -> bool:
    return Path(target_path).suffix.lower() == ".md"


def _extension_issue(target_path: str) -> ValidationIssue | None:
    if not _has_markdown_extension(target_path):
        return _storage_critical_issue(
            "invalid_target_extension",
            f"Expected a Markdown file (.md): {target_path}",
        )
    return None


def _read_vault_file_content(vault: Vault, target_path: str) -> str:
    """Read vault file bytes as UTF-8 text without enforcing a Markdown extension."""
    return vault.resolve_path(target_path).read_text(encoding="utf-8")


def _build_write_proposal(
    *,
    operation: WriteOperation,
    target_path: str,
    before_content: str | None,
    after_content: str,
    warnings: list[ValidationIssue],
    critical_errors: list[ValidationIssue],
    would_create: bool,
    would_update: bool,
    would_overwrite: bool,
    expected_existing_hash: str | None,
) -> WriteProposal:
    return WriteProposal(
        operation=operation,
        target_path=target_path,
        before_content=before_content,
        after_content=after_content,
        warnings=warnings,
        critical_errors=critical_errors,
        would_create=would_create,
        would_update=would_update,
        would_overwrite=would_overwrite,
        expected_existing_hash=expected_existing_hash,
    )


def build_create_note_proposal(
    vault: Vault,
    target_path: str,
    after_content: str,
) -> WriteProposal:
    """Build a create-note proposal with collision detection and CREATE validation."""
    vault.resolve_path(target_path)

    critical_errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    extension_error = _extension_issue(target_path)
    if extension_error is not None:
        critical_errors.append(extension_error)

    target_exists = vault.exists(target_path)
    if target_exists:
        critical_errors.append(
            _storage_critical_issue(
                "target_file_exists",
                f"Target file already exists: {target_path}",
            )
        )

    _, validation = parse_and_validate(after_content, operation=ValidationOperation.CREATE)
    warnings.extend(validation.warnings)
    critical_errors.extend(validation.critical_errors)

    return _build_write_proposal(
        operation=WriteOperation.CREATE_NOTE,
        target_path=target_path,
        before_content=None,
        after_content=after_content,
        warnings=warnings,
        critical_errors=critical_errors,
        would_create=not target_exists,
        would_update=False,
        would_overwrite=target_exists,
        expected_existing_hash=None,
    )


def build_create_note_proposal_from_title(
    vault: Vault,
    target_path: str,
    canonical_title: str,
    **metadata_overrides: Any,
) -> WriteProposal:
    """Build a create-note proposal from a title via the B5 note generator."""
    after_content = create_concept_note_markdown(canonical_title, **metadata_overrides)
    return build_create_note_proposal(vault, target_path, after_content)


def build_update_note_proposal(
    vault: Vault,
    target_path: str,
    after_content: str,
    *,
    before_content: str | None = None,
) -> WriteProposal:
    """Build an update-note proposal with before/after content and stale-write hash.

    When ``before_content`` is provided, the vault file is not read again and
    existence is assumed from the caller's prior read.
    """
    vault.resolve_path(target_path)

    critical_errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    extension_error = _extension_issue(target_path)
    if extension_error is not None:
        critical_errors.append(extension_error)

    resolved_before_content: str | None
    expected_existing_hash: str | None
    has_valid_extension = extension_error is None

    if before_content is not None:
        target_exists = True
        resolved_before_content = before_content
        expected_existing_hash = hash_file_content(before_content)
    elif has_valid_extension and vault.exists(target_path):
        target_exists = True
        resolved_before_content = vault.read_markdown(target_path)
        expected_existing_hash = hash_file_content(resolved_before_content)
    elif vault.exists(target_path):
        target_exists = True
        resolved_before_content = _read_vault_file_content(vault, target_path)
        expected_existing_hash = hash_file_content(resolved_before_content)
    else:
        target_exists = False
        resolved_before_content = None
        expected_existing_hash = None
        critical_errors.append(
            _storage_critical_issue(
                "target_file_missing",
                f"Target file not found: {target_path}",
            )
        )

    _, validation = parse_and_validate(after_content, operation=ValidationOperation.UPDATE)
    warnings.extend(validation.warnings)
    critical_errors.extend(validation.critical_errors)

    return _build_write_proposal(
        operation=WriteOperation.UPDATE_NOTE,
        target_path=target_path,
        before_content=resolved_before_content,
        after_content=after_content,
        warnings=warnings,
        critical_errors=critical_errors,
        would_create=not target_exists,
        would_update=target_exists,
        would_overwrite=target_exists,
        expected_existing_hash=expected_existing_hash,
    )


def build_metadata_update_proposal(
    vault: Vault,
    target_path: str,
    metadata: ConceptNoteMetadata,
    *,
    body: str | None = None,
) -> WriteProposal:
    """Build an update proposal from structured metadata and an optional body override."""
    updated_metadata = metadata.model_copy(
        update={"updated_at": datetime.now(UTC).replace(microsecond=0)}
    )

    existing_content: str | None = None
    has_valid_extension = _has_markdown_extension(target_path)

    if has_valid_extension and vault.exists(target_path):
        existing_content = vault.read_markdown(target_path)
        parsed = parse_concept_note(existing_content)
        effective_body = body if body is not None else (parsed.body or "")
    elif vault.exists(target_path):
        existing_content = _read_vault_file_content(vault, target_path)
        effective_body = (
            body if body is not None else build_canonical_concept_body(updated_metadata)
        )
    else:
        effective_body = (
            body if body is not None else build_canonical_concept_body(updated_metadata)
        )

    after_content = serialize_concept_note(updated_metadata, effective_body)
    return build_update_note_proposal(
        vault,
        target_path,
        after_content,
        before_content=existing_content,
    )
