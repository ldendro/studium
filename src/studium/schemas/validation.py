"""Validation result models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from studium.schemas.enums import ValidationOperation, ValidationSeverity


class ValidationIssue(BaseModel):
    """A single validation finding with optional field path and machine-readable code."""

    model_config = ConfigDict(extra="forbid")

    message: str
    severity: ValidationSeverity
    field: str | None = None
    code: str | None = None


class ValidationResult(BaseModel):
    """Structured validation output for parse, create, update, and write operations."""

    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    critical_errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    operation: ValidationOperation
