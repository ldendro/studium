"""Integration tests for concept note validation."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from studium.parsing import parse_concept_note
from studium.parsing.markdown_sections import ParsedMarkdownSections
from studium.parsing.models import ParsedConceptNote
from studium.schemas import ValidationIssue, ValidationOperation, ValidationSeverity
from studium.serialization import (
    build_canonical_concept_body,
    build_concept_note_metadata,
    create_concept_note_markdown,
)
from studium.validation import (
    parse_and_validate,
    validate_generated_concept_note,
    validate_parsed_concept_note,
)
from studium.validation.concept_note import metadata_equivalent_after_round_trip
from tests.parsing.conftest import load_fixture
from tests.parsing.helpers import build_canonical_body, build_valid_concept_note_markdown
from tests.serialization.helpers import build_sample_metadata


def test_valid_fixture_parse_validation_is_valid_with_warnings() -> None:
    parsed = parse_concept_note(load_fixture("valid_concept_note.md"))
    result = validate_parsed_concept_note(parsed, operation=ValidationOperation.PARSE)

    assert result.is_valid is True
    assert result.operation == ValidationOperation.PARSE


def test_validate_parsed_independently_checks_unknown_fields_and_sections() -> None:
    """B6 must validate even when B4 warnings are not forwarded."""
    unknown_parsed = parse_concept_note(load_fixture("unknown_metadata_field.md"))
    unknown_stripped = unknown_parsed.model_copy(update={"warnings": []})
    unknown_result = validate_parsed_concept_note(
        unknown_stripped,
        operation=ValidationOperation.PARSE,
    )

    assert any(issue.code == "unknown_field" for issue in unknown_result.warnings)

    missing_section_parsed = parse_concept_note(load_fixture("missing_canonical_section.md"))
    missing_stripped = missing_section_parsed.model_copy(update={"warnings": []})
    section_result = validate_parsed_concept_note(
        missing_stripped,
        operation=ValidationOperation.PARSE,
    )

    assert any(issue.code == "missing_canonical_section" for issue in section_result.warnings)


def test_validate_parsed_does_not_duplicate_semantic_issues() -> None:
    parsed = parse_concept_note(load_fixture("unknown_metadata_field.md"))
    result = validate_parsed_concept_note(parsed, operation=ValidationOperation.PARSE)

    unknown_field_issues = [issue for issue in result.warnings if issue.code == "unknown_field"]
    assert len(unknown_field_issues) == 1


def test_unknown_field_warns_on_parse_and_fails_on_write() -> None:
    parsed = parse_concept_note(load_fixture("unknown_metadata_field.md"))

    parse_result = validate_parsed_concept_note(parsed, operation=ValidationOperation.PARSE)
    write_result = validate_parsed_concept_note(parsed, operation=ValidationOperation.WRITE)

    assert parse_result.is_valid is True
    assert any(issue.code == "unknown_field" for issue in parse_result.warnings)
    assert write_result.is_valid is False
    assert any(issue.code == "unknown_field" for issue in write_result.critical_errors)


def test_missing_section_warns_on_parse_and_fails_on_create() -> None:
    parsed = parse_concept_note(load_fixture("missing_canonical_section.md"))

    parse_result = validate_parsed_concept_note(parsed, operation=ValidationOperation.PARSE)
    create_result = validate_parsed_concept_note(parsed, operation=ValidationOperation.CREATE)

    assert parse_result.is_valid is True
    assert any(issue.code == "missing_canonical_section" for issue in parse_result.warnings)
    assert create_result.is_valid is False
    assert any(issue.code == "missing_canonical_section" for issue in create_result.critical_errors)


def test_unknown_concept_type_warns_on_parse() -> None:
    markdown = build_valid_concept_note_markdown(concept_type="future_concept_kind")
    parsed = parse_concept_note(markdown)

    assert parsed.metadata is None
    result = validate_parsed_concept_note(parsed, operation=ValidationOperation.PARSE)

    assert result.is_valid is True
    assert any(issue.code == "unknown_concept_type" for issue in result.warnings)
    assert not any(issue.field == "concept_type" for issue in result.critical_errors)


def test_unknown_concept_type_critical_on_write() -> None:
    markdown = build_valid_concept_note_markdown(concept_type="future_concept_kind")
    parsed = parse_concept_note(markdown)
    result = validate_parsed_concept_note(parsed, operation=ValidationOperation.WRITE)

    assert result.is_valid is False
    assert any(issue.code == "unknown_concept_type" for issue in result.critical_errors)


def test_multiple_primary_warns_on_parse_and_fails_on_write() -> None:
    metadata = build_sample_metadata()
    encounter = metadata.learning_encounters[0]
    metadata = metadata.model_copy(
        update={"learning_encounters": [encounter, encounter.model_copy()]}
    )
    from studium.serialization import serialize_concept_note

    body = build_canonical_body("Stochastic Gradient Descent")
    markdown = serialize_concept_note(metadata, body)
    parsed = parse_concept_note(markdown)

    parse_result = validate_parsed_concept_note(parsed, operation=ValidationOperation.PARSE)
    write_result = validate_parsed_concept_note(parsed, operation=ValidationOperation.WRITE)

    assert parsed.metadata is not None
    assert parse_result.is_valid is True
    assert any(issue.code == "multiple_primary_encounters" for issue in parse_result.warnings)
    assert write_result.is_valid is False
    assert any(
        issue.code == "multiple_primary_encounters" for issue in write_result.critical_errors
    )


def test_create_generated_note_passes_create_validation() -> None:
    markdown = create_concept_note_markdown("Generated Concept")
    parsed, result = parse_and_validate(markdown, operation=ValidationOperation.CREATE)

    assert parsed.metadata is not None
    assert result.is_valid is True


def test_validate_generated_concept_note_with_microsecond_timestamps() -> None:
    """Fresh metadata from build_concept_note_metadata should pass CREATE validation."""
    now = datetime.now(UTC)
    metadata = build_concept_note_metadata(
        "Fresh Concept",
        created_at=now,
        updated_at=now,
    )
    body = build_canonical_concept_body(metadata)
    result = validate_generated_concept_note(
        metadata,
        body,
        operation=ValidationOperation.CREATE,
    )

    assert result.is_valid is True
    assert not any(issue.code == "round_trip_metadata_mismatch" for issue in result.critical_errors)


def test_metadata_equivalent_after_round_trip_normalizes_microseconds() -> None:
    now = datetime.now(UTC)
    metadata = build_concept_note_metadata("Fresh Concept", created_at=now, updated_at=now)
    truncated = metadata.model_copy(
        update={
            "created_at": now.replace(microsecond=0),
            "updated_at": now.replace(microsecond=0),
        }
    )

    assert metadata != truncated
    assert metadata_equivalent_after_round_trip(metadata, truncated) is True


def test_validate_generated_concept_note_round_trip() -> None:
    metadata = build_sample_metadata()
    body = build_canonical_body("Stochastic Gradient Descent")
    result = validate_generated_concept_note(
        metadata,
        body,
        operation=ValidationOperation.CREATE,
    )

    assert result.is_valid is True


def test_parse_and_validate_invalid_yaml_is_critical() -> None:
    parsed, result = parse_and_validate(
        load_fixture("invalid_yaml_note.md"),
        operation=ValidationOperation.PARSE,
    )

    assert parsed.metadata is None
    assert result.is_valid is False
    assert any(issue.code == "invalid_yaml" for issue in result.critical_errors)


def test_round_trip_skips_metadata_mismatch_when_reparse_fails() -> None:
    metadata = build_sample_metadata()
    body = build_canonical_body("Stochastic Gradient Descent")
    failed_reparse = ParsedConceptNote(
        raw_markdown="",
        frontmatter_text="",
        body="",
        raw_metadata={},
        metadata=None,
        unknown_metadata_fields=[],
        sections=ParsedMarkdownSections(
            headings=[],
            h1_title=None,
            canonical_present=[],
            canonical_missing=[],
        ),
        critical_errors=[
            ValidationIssue(
                message="Invalid YAML frontmatter",
                severity=ValidationSeverity.CRITICAL,
                code="invalid_yaml",
            )
        ],
    )

    with patch(
        "studium.validation.concept_note.parse_concept_note",
        return_value=failed_reparse,
    ):
        result = validate_generated_concept_note(
            metadata,
            body,
            operation=ValidationOperation.CREATE,
        )

    codes = [issue.code for issue in result.critical_errors]
    assert codes == ["round_trip_parse_errors"]
