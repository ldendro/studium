"""Helpers for building validation results."""

from __future__ import annotations

from studium.schemas import (
    ValidationIssue,
    ValidationOperation,
    ValidationResult,
    ValidationSeverity,
)
from studium.validation.severity import apply_operation_severity


def build_validation_result(
    issues: list[ValidationIssue],
    operation: ValidationOperation,
) -> ValidationResult:
    """Partition issues into critical errors and warnings for an operation."""
    adjusted = apply_operation_severity(issues, operation)
    critical_errors = [issue for issue in adjusted if issue.severity == ValidationSeverity.CRITICAL]
    warnings = [issue for issue in adjusted if issue.severity == ValidationSeverity.WARNING]
    return ValidationResult(
        is_valid=not critical_errors,
        critical_errors=critical_errors,
        warnings=warnings,
        operation=operation,
    )
