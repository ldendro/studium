"""Concept note validation orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from studium.parsing import parse_concept_note
from studium.parsing.markdown_sections import ParsedMarkdownSections, parse_markdown_sections
from studium.parsing.models import ParsedConceptNote
from studium.schemas import (
    ConceptNoteMetadata,
    ValidationIssue,
    ValidationOperation,
    ValidationResult,
    ValidationSeverity,
)
from studium.serialization import serialize_concept_note
from studium.validation.result import build_validation_result
from studium.validation.rules import (
    collect_metadata_validation_issues,
    collect_raw_metadata_validation_issues,
    filter_parse_enum_critical_errors,
    validate_raw_metadata_enums,
)
from studium.validation.severity import is_strict_operation


def validate_parsed_concept_note(
    parsed: ParsedConceptNote,
    operation: ValidationOperation = ValidationOperation.PARSE,
) -> ValidationResult:
    """Validate a parsed concept note with operation-specific strictness."""
    issues: list[ValidationIssue] = list(parsed.critical_errors)
    issues = filter_parse_enum_critical_errors(issues, parsed.raw_metadata, operation)

    if parsed.metadata is not None:
        issues.extend(
            collect_metadata_validation_issues(
                parsed.metadata,
                sections=parsed.sections,
                unknown_fields=parsed.unknown_metadata_fields,
            )
        )
    else:
        issues.extend(
            collect_raw_metadata_validation_issues(
                parsed.raw_metadata,
                sections=parsed.sections,
                unknown_fields=parsed.unknown_metadata_fields,
            )
        )

    return build_validation_result(issues, operation)


def validate_concept_metadata(
    metadata: ConceptNoteMetadata,
    *,
    operation: ValidationOperation,
    sections: ParsedMarkdownSections | None = None,
    unknown_fields: list[str] | None = None,
    raw_metadata: Mapping[str, Any] | None = None,
) -> ValidationResult:
    """Validate structured metadata and optional section context."""
    issues = collect_metadata_validation_issues(
        metadata,
        sections=sections,
        unknown_fields=unknown_fields,
    )
    if raw_metadata is not None:
        issues.extend(validate_raw_metadata_enums(raw_metadata))
    return build_validation_result(issues, operation)


def validate_generated_concept_note(
    metadata: ConceptNoteMetadata,
    body: str,
    operation: ValidationOperation = ValidationOperation.CREATE,
) -> ValidationResult:
    """Validate proposed note content and serialization round-trip integrity."""
    sections = parse_markdown_sections(body)
    base_result = validate_concept_metadata(
        metadata,
        operation=operation,
        sections=sections,
    )
    issues: list[ValidationIssue] = [
        *base_result.critical_errors,
        *base_result.warnings,
    ]
    issues.extend(_round_trip_issues(metadata, body, operation))
    return build_validation_result(issues, operation)


def parse_and_validate(
    raw_markdown: str,
    operation: ValidationOperation = ValidationOperation.PARSE,
) -> tuple[ParsedConceptNote, ValidationResult]:
    """Parse raw Markdown and return both the parse result and validation output."""
    parsed = parse_concept_note(raw_markdown)
    result = validate_parsed_concept_note(parsed, operation=operation)
    return parsed, result


def _round_trip_issues(
    metadata: ConceptNoteMetadata,
    body: str,
    operation: ValidationOperation,
) -> list[ValidationIssue]:
    """Check serialize -> parse preserves metadata for strict operations."""
    if not is_strict_operation(operation):
        return []

    serialized = serialize_concept_note(metadata, body)
    reparsed = parse_concept_note(serialized)

    issues: list[ValidationIssue] = []
    if reparsed.metadata != metadata:
        issues.append(
            ValidationIssue(
                message="Serialization round-trip changed metadata",
                severity=ValidationSeverity.CRITICAL,
                code="round_trip_metadata_mismatch",
            )
        )
    if reparsed.critical_errors:
        issues.append(
            ValidationIssue(
                message="Serialization round-trip introduced parse critical errors",
                severity=ValidationSeverity.CRITICAL,
                code="round_trip_parse_errors",
            )
        )
    return issues
