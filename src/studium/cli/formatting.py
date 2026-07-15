"""Human-readable CLI output formatters."""

from __future__ import annotations

from studium.schemas import ValidationIssue, ValidationResult, WriteProposal


def format_validation_issue(issue: ValidationIssue) -> str:
    """Format a single validation issue for CLI output."""
    parts = [issue.severity.value.upper()]
    if issue.code:
        parts.append(f"[{issue.code}]")
    if issue.field:
        parts.append(f"({issue.field})")
    parts.append(issue.message)
    return " ".join(parts)


def format_validation_result(path: str, result: ValidationResult) -> str:
    """Format a validation result for a single note path."""
    status = "valid" if result.is_valid else "invalid"
    lines = [
        f"{path}: {status}",
        f"  operation={result.operation.value}",
    ]
    if result.critical_errors:
        lines.append(f"  critical errors ({len(result.critical_errors)}):")
        lines.extend(f"    - {format_validation_issue(issue)}" for issue in result.critical_errors)
    if result.warnings:
        lines.append(f"  warnings ({len(result.warnings)}):")
        lines.extend(f"    - {format_validation_issue(issue)}" for issue in result.warnings)
    if not result.critical_errors and not result.warnings:
        lines.append("  no issues")
    return "\n".join(lines)


def format_write_proposal(proposal: WriteProposal, *, dry_run: bool = False) -> str:
    """Format a write proposal for create-concept output."""
    lines = [
        "Write proposal:",
        f"  operation={proposal.operation.value}",
        f"  target_path={proposal.target_path}",
        f"  would_create={proposal.would_create}",
        f"  would_update={proposal.would_update}",
        f"  would_overwrite={proposal.would_overwrite}",
    ]
    if proposal.critical_errors:
        lines.append(f"  critical errors ({len(proposal.critical_errors)}):")
        lines.extend(
            f"    - {format_validation_issue(issue)}" for issue in proposal.critical_errors
        )
    if proposal.warnings:
        lines.append(f"  warnings ({len(proposal.warnings)}):")
        lines.extend(f"    - {format_validation_issue(issue)}" for issue in proposal.warnings)
    if not proposal.critical_errors and not proposal.warnings:
        lines.append("  no validation issues")

    preview = proposal.after_content
    if len(preview) > 500:
        preview = preview[:500] + "\n... (truncated)"
    lines.append("  after_content preview:")
    lines.extend(f"    {line}" for line in preview.splitlines() or [""])

    if dry_run:
        lines.append("  status=dry-run (not committed)")
    return "\n".join(lines)


def format_create_committed(target_path: str) -> str:
    """Format a successful create commit message."""
    return f"Committed: {target_path}"
