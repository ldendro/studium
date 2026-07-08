"""Tests for validation rules."""

from __future__ import annotations

from studium.schemas import ConceptType, SourceType
from studium.validation.rules import (
    check_h1_title_match,
    check_multiple_primary_encounters,
    validate_raw_metadata_enums,
)
from tests.serialization.helpers import build_sample_metadata


def test_validate_raw_metadata_enums_detects_unknown_concept_type() -> None:
    issues = validate_raw_metadata_enums({"concept_type": "future_concept_kind"})

    assert len(issues) == 1
    assert issues[0].code == "unknown_concept_type"
    assert issues[0].field == "concept_type"


def test_validate_raw_metadata_enums_detects_unknown_source_type() -> None:
    issues = validate_raw_metadata_enums(
        {
            "learning_encounters": [
                {"source": {"type": "newsletter", "title": "Example"}, "role": "primary"}
            ]
        }
    )

    assert len(issues) == 1
    assert issues[0].code == "unknown_source_type"
    assert issues[0].field == "learning_encounters.0.source.type"


def test_validate_raw_metadata_enums_ignores_known_values() -> None:
    issues = validate_raw_metadata_enums(
        {
            "concept_type": ConceptType.ALGORITHM.value,
            "learning_encounters": [
                {
                    "source": {"type": SourceType.STUDIUM.value, "title": "Studium"},
                    "role": "primary",
                }
            ],
            "scaffold_modules": [
                {"type": "derivation", "id": "m1", "title": "T", "status": "scaffolded"}
            ],
        }
    )

    assert issues == []


def test_check_multiple_primary_encounters() -> None:
    metadata = build_sample_metadata()
    encounter = metadata.learning_encounters[0].model_copy()
    metadata = metadata.model_copy(
        update={"learning_encounters": [encounter, encounter.model_copy()]}
    )

    issues = check_multiple_primary_encounters(metadata.learning_encounters)

    assert len(issues) == 1
    assert issues[0].code == "multiple_primary_encounters"


def test_check_h1_title_match() -> None:
    from studium.parsing.markdown_sections import parse_markdown_sections

    metadata = build_sample_metadata(canonical_title="Canonical Title")
    sections = parse_markdown_sections("# Different Title\n\n## Concept Overview\n")

    issues = check_h1_title_match(metadata, sections)

    assert len(issues) == 1
    assert issues[0].code == "h1_title_mismatch"
