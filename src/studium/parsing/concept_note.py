"""High-level concept note parsing."""

from __future__ import annotations

from studium.parsing.errors import FrontmatterError, YamlParseError
from studium.parsing.frontmatter import split_frontmatter
from studium.parsing.markdown_sections import ParsedMarkdownSections, parse_markdown_sections
from studium.parsing.models import ParsedConceptNote
from studium.parsing.yaml_frontmatter import parse_yaml_frontmatter
from studium.schemas import ValidationIssue, ValidationSeverity
from studium.schemas.canonical import CANONICAL_SECTION_TITLES


def parse_concept_note(raw_markdown: str) -> ParsedConceptNote:
    """Parse raw Markdown into frontmatter, body, metadata, and detected sections."""
    try:
        split = split_frontmatter(raw_markdown)
    except FrontmatterError as exc:
        return _failed_parse(
            raw_markdown=raw_markdown,
            critical_errors=[
                ValidationIssue(
                    message=str(exc),
                    severity=ValidationSeverity.CRITICAL,
                    code="missing_frontmatter",
                )
            ],
        )

    critical_errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    try:
        yaml_result = parse_yaml_frontmatter(split.frontmatter_text)
    except YamlParseError as exc:
        return _failed_parse(
            raw_markdown=raw_markdown,
            frontmatter_text=split.frontmatter_text,
            body=split.body,
            critical_errors=[
                ValidationIssue(
                    message=str(exc),
                    severity=ValidationSeverity.CRITICAL,
                    code="invalid_yaml",
                )
            ],
            sections=parse_markdown_sections(split.body),
        )

    for unknown_field in yaml_result.unknown_fields:
        warnings.append(
            ValidationIssue(
                message=f"Unknown metadata field: {unknown_field}",
                severity=ValidationSeverity.WARNING,
                field=unknown_field,
                code="unknown_field",
            )
        )

    for validation_issue in yaml_result.metadata_issues:
        critical_errors.append(validation_issue)

    sections = parse_markdown_sections(split.body)
    for missing_section in sections.canonical_missing:
        warnings.append(
            ValidationIssue(
                message=f"Missing canonical section: {missing_section}",
                severity=ValidationSeverity.WARNING,
                field=f"sections.{missing_section}",
                code="missing_canonical_section",
            )
        )

    return ParsedConceptNote(
        raw_markdown=raw_markdown,
        frontmatter_text=split.frontmatter_text,
        body=split.body,
        raw_metadata=yaml_result.raw_metadata,
        metadata=yaml_result.metadata,
        unknown_metadata_fields=yaml_result.unknown_fields,
        sections=sections,
        critical_errors=critical_errors,
        warnings=warnings,
    )


def _failed_parse(
    *,
    raw_markdown: str,
    critical_errors: list[ValidationIssue],
    frontmatter_text: str = "",
    body: str = "",
    sections: ParsedMarkdownSections | None = None,
) -> ParsedConceptNote:
    return ParsedConceptNote(
        raw_markdown=raw_markdown,
        frontmatter_text=frontmatter_text,
        body=body,
        raw_metadata={},
        metadata=None,
        unknown_metadata_fields=[],
        sections=sections
        or ParsedMarkdownSections(
            headings=[],
            h1_title=None,
            canonical_present=[],
            canonical_missing=list(CANONICAL_SECTION_TITLES),
        ),
        critical_errors=critical_errors,
        warnings=[],
    )
