"""Tests for validation severity policy."""

from __future__ import annotations

from studium.schemas import ValidationIssue, ValidationOperation, ValidationSeverity
from studium.validation.result import build_validation_result
from studium.validation.severity import resolve_issue_severity


def test_unknown_field_warns_on_parse_and_critical_on_write() -> None:
    issue = ValidationIssue(
        message="Unknown metadata field: legacy_field",
        severity=ValidationSeverity.WARNING,
        field="legacy_field",
        code="unknown_field",
    )

    assert resolve_issue_severity(issue, ValidationOperation.PARSE) == ValidationSeverity.WARNING
    assert resolve_issue_severity(issue, ValidationOperation.WRITE) == ValidationSeverity.CRITICAL
    assert resolve_issue_severity(issue, ValidationOperation.UPDATE) == ValidationSeverity.CRITICAL


def test_missing_canonical_section_warns_on_parse_and_critical_on_create() -> None:
    issue = ValidationIssue(
        message="Missing canonical section: Module Index",
        severity=ValidationSeverity.WARNING,
        field="sections.Module Index",
        code="missing_canonical_section",
    )

    assert resolve_issue_severity(issue, ValidationOperation.PARSE) == ValidationSeverity.WARNING
    assert resolve_issue_severity(issue, ValidationOperation.CREATE) == ValidationSeverity.CRITICAL


def test_warnings_only_result_is_valid() -> None:
    result = build_validation_result(
        [
            ValidationIssue(
                message="aliases is empty",
                severity=ValidationSeverity.WARNING,
                field="aliases",
                code="missing_aliases",
            )
        ],
        ValidationOperation.PARSE,
    )

    assert result.is_valid is True
    assert result.critical_errors == []
    assert len(result.warnings) == 1
