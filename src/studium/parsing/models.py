"""Parser output models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from studium.parsing.markdown_sections import ParsedMarkdownSections
from studium.schemas import ConceptNoteMetadata, ValidationIssue


def _empty_validation_issues() -> list[ValidationIssue]:
    return []


class ParsedConceptNote(BaseModel):
    """Structured result of parsing a concept note Markdown file.

    ``critical_errors`` and ``warnings`` are embedded here for B4. B6 composes
    them into a ``ValidationResult`` with operation-specific strictness.

    H1 heading vs ``canonical_title`` mismatch checks are deferred to B6.
    """

    model_config = ConfigDict(extra="forbid")

    raw_markdown: str
    frontmatter_text: str
    body: str
    raw_metadata: dict[str, Any]
    metadata: ConceptNoteMetadata | None
    unknown_metadata_fields: list[str]
    sections: ParsedMarkdownSections
    critical_errors: list[ValidationIssue] = Field(default_factory=_empty_validation_issues)
    warnings: list[ValidationIssue] = Field(default_factory=_empty_validation_issues)

    @property
    def is_parseable(self) -> bool:
        """Return whether parsing produced valid metadata with no critical errors."""
        return self.metadata is not None and not self.critical_errors
