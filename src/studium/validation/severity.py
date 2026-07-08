"""Operation-mode severity policy for validation issues."""

from __future__ import annotations

from studium.schemas import ValidationIssue, ValidationOperation, ValidationSeverity

_STRICT_OPERATIONS = frozenset(
    {
        ValidationOperation.CREATE,
        ValidationOperation.UPDATE,
        ValidationOperation.WRITE,
    }
)

_MODE_SENSITIVE_CODES = frozenset(
    {
        "unknown_field",
        "missing_canonical_section",
        "multiple_primary_encounters",
        "unknown_concept_type",
        "unknown_source_type",
        "unknown_module_type",
    }
)

_ALWAYS_WARNING_CODES = frozenset(
    {
        "h1_title_mismatch",
        "empty_concept_domains",
        "missing_aliases",
        "scaffold_modules_without_section",
    }
)


def is_strict_operation(operation: ValidationOperation) -> bool:
    """Return whether the operation uses create/update/write strictness."""
    return operation in _STRICT_OPERATIONS


def resolve_issue_severity(
    issue: ValidationIssue,
    operation: ValidationOperation,
) -> ValidationSeverity:
    """Apply operation-mode severity rules to a validation issue."""
    code = issue.code
    if code in _ALWAYS_WARNING_CODES:
        return ValidationSeverity.WARNING

    if code in _MODE_SENSITIVE_CODES:
        return (
            ValidationSeverity.CRITICAL
            if is_strict_operation(operation)
            else ValidationSeverity.WARNING
        )

    return issue.severity


def apply_operation_severity(
    issues: list[ValidationIssue],
    operation: ValidationOperation,
) -> list[ValidationIssue]:
    """Return issues with severities adjusted for the validation operation."""
    adjusted: list[ValidationIssue] = []
    for issue in issues:
        severity = resolve_issue_severity(issue, operation)
        if severity == issue.severity:
            adjusted.append(issue)
        else:
            adjusted.append(issue.model_copy(update={"severity": severity}))
    return adjusted
