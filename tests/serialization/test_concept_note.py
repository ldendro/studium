"""Tests for full concept note serialization."""

from __future__ import annotations

from pathlib import Path

from studium.parsing import parse_concept_note
from studium.serialization import (
    build_concept_note_metadata,
    create_concept_note_markdown,
    serialize_concept_note,
)
from tests.serialization.helpers import build_sample_metadata

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "parsing"


def test_serialize_preserves_body_bytes() -> None:
    metadata = build_sample_metadata()
    body = "# Custom Body\n\nPreserves this text exactly.  \n"
    markdown = serialize_concept_note(metadata, body)

    parsed = parse_concept_note(markdown)
    assert parsed.body == body


def test_round_trip_valid_fixture_metadata_and_body() -> None:
    original = (FIXTURES_DIR / "valid_concept_note.md").read_text(encoding="utf-8")
    parsed = parse_concept_note(original)
    assert parsed.metadata is not None

    reserialized = serialize_concept_note(parsed.metadata, parsed.body)
    reparsed = parse_concept_note(reserialized)

    assert reparsed.metadata == parsed.metadata
    assert reparsed.body == parsed.body
    assert not reparsed.critical_errors


def test_create_concept_note_markdown_is_parseable() -> None:
    markdown = create_concept_note_markdown("New Concept")
    parsed = parse_concept_note(markdown)

    assert parsed.metadata is not None
    assert parsed.metadata.canonical_title == "New Concept"
    assert parsed.metadata.id.startswith("concept_new_concept_")
    assert not parsed.critical_errors
    assert parsed.sections.canonical_missing == []


def test_build_concept_note_metadata_uses_defaults() -> None:
    metadata = build_concept_note_metadata("Defaults Test")

    assert metadata.canonical_title == "Defaults Test"
    assert metadata.learning_encounters[0].source.title == "Studium"
    assert metadata.status.value == "scaffolded"
