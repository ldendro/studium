"""Integration tests for concept note validation."""

from __future__ import annotations

from studium.parsing import parse_concept_note
from studium.schemas import ValidationOperation
from studium.serialization import create_concept_note_markdown
from studium.validation import (
    parse_and_validate,
    validate_generated_concept_note,
    validate_parsed_concept_note,
)
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
