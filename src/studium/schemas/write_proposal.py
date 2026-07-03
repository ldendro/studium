"""Write proposal models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from studium.schemas.enums import WriteOperation
from studium.schemas.validation import ValidationIssue


class WriteProposal(BaseModel):
    """A file write represented before it is committed to the vault."""

    model_config = ConfigDict(extra="forbid")

    operation: WriteOperation
    target_path: str
    before_content: str | None
    after_content: str
    warnings: list[ValidationIssue]
    critical_errors: list[ValidationIssue]
    would_create: bool
    would_update: bool
    would_overwrite: bool
    expected_existing_hash: str | None
