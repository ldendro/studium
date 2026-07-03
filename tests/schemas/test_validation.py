"""Tests for ValidationIssue and ValidationResult."""

from __future__ import annotations

from studium.schemas import (
    ValidationIssue,
    ValidationOperation,
    ValidationResult,
    ValidationSeverity,
)


def test_critical_errors_make_result_invalid() -> None:
    issue = ValidationIssue(
        message="canonical_title is required",
        severity=ValidationSeverity.CRITICAL,
        field="canonical_title",
        code="missing_field",
    )
    result = ValidationResult(
        is_valid=False,
        critical_errors=[issue],
        warnings=[],
        operation=ValidationOperation.WRITE,
    )

    assert result.is_valid is False
    assert len(result.critical_errors) == 1
    assert result.critical_errors[0].code == "missing_field"


def test_warnings_only_result_constructible() -> None:
    warning = ValidationIssue(
        message="Unknown source type in parsed note",
        severity=ValidationSeverity.WARNING,
        field="learning_encounters.0.source.type",
    )
    result = ValidationResult(
        is_valid=True,
        critical_errors=[],
        warnings=[warning],
        operation=ValidationOperation.PARSE,
    )

    assert result.is_valid is True
    assert len(result.warnings) == 1
    assert result.warnings[0].field == "learning_encounters.0.source.type"
