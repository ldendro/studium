"""Tests for high-level concept note parsing."""

from __future__ import annotations

from studium.parsing import parse_concept_note, split_frontmatter
from studium.schemas import ValidationSeverity
from tests.parsing.conftest import load_fixture
from tests.parsing.helpers import build_valid_concept_note_markdown


def test_parse_valid_fixture_note() -> None:
    parsed = parse_concept_note(load_fixture("valid_concept_note.md"))

    assert parsed.metadata is not None
    assert parsed.metadata.canonical_title == "Stochastic Gradient Descent"
    assert parsed.critical_errors == []
    assert parsed.is_parseable


def test_body_preserved_exactly() -> None:
    markdown = load_fixture("valid_concept_note.md")
    parsed = parse_concept_note(markdown)

    assert parsed.body == split_frontmatter(markdown).body


def test_invalid_yaml_fixture_has_critical_error() -> None:
    parsed = parse_concept_note(load_fixture("invalid_yaml_note.md"))

    assert parsed.metadata is None
    assert any(issue.code == "invalid_yaml" for issue in parsed.critical_errors)


def test_missing_frontmatter_is_critical_error() -> None:
    parsed = parse_concept_note("# Body without frontmatter\n")

    assert parsed.metadata is None
    assert any(issue.code == "missing_frontmatter" for issue in parsed.critical_errors)


def test_empty_frontmatter_yields_metadata_critical_errors() -> None:
    parsed = parse_concept_note(load_fixture("empty_frontmatter.md"))

    assert parsed.metadata is None
    assert parsed.critical_errors
    assert all(issue.severity == ValidationSeverity.CRITICAL for issue in parsed.critical_errors)


def test_unknown_metadata_field_warning() -> None:
    parsed = parse_concept_note(load_fixture("unknown_metadata_field.md"))

    assert parsed.metadata is not None
    assert parsed.unknown_metadata_fields == ["legacy_field"]
    assert any(issue.code == "unknown_field" for issue in parsed.warnings)


def test_missing_canonical_section_warning() -> None:
    parsed = parse_concept_note(load_fixture("missing_canonical_section.md"))

    assert parsed.metadata is not None
    assert any(
        issue.code == "missing_canonical_section" and issue.field == "sections.Module Index"
        for issue in parsed.warnings
    )


def test_inline_markdown_round_trip_metadata() -> None:
    parsed = parse_concept_note(build_valid_concept_note_markdown())

    assert parsed.metadata is not None
    assert parsed.sections.canonical_missing == []
    assert not parsed.critical_errors


def test_metadata_with_embedded_dashes_parses_via_high_level() -> None:
    markdown = build_valid_concept_note_markdown().replace(
        "      title: Studium",
        "      title: Studium\n      link: https://example/a---b",
    )
    parsed = parse_concept_note(markdown)

    assert parsed.metadata is not None
    assert parsed.metadata.learning_encounters[0].source.link == "https://example/a---b"
    assert not parsed.critical_errors
