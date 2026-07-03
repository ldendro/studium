"""Tests for ConceptNoteMetadata."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from schemas.helpers import build_minimal_concept_note_data
from studium.schemas import ConceptNoteMetadata, ConceptType


def test_valid_full_metadata_constructs(valid_concept_note_data: dict[str, Any]) -> None:
    note = ConceptNoteMetadata.model_validate(valid_concept_note_data)

    assert note.id == "concept_stochastic_gradient_descent_a1b2c3"
    assert note.schema_version == 1
    assert note.note_type == "concept"
    assert note.concept_type == ConceptType.ALGORITHM
    assert note.concept_domains == ["machine_learning", "optimization"]
    assert note.canonical_title == "Stochastic Gradient Descent"
    assert len(note.learning_encounters) == 1


def test_missing_required_field_raises() -> None:
    data = build_minimal_concept_note_data()
    del data["canonical_title"]

    with pytest.raises(ValidationError):
        ConceptNoteMetadata.model_validate(data)


def test_invalid_schema_version_raises() -> None:
    data = build_minimal_concept_note_data(schema_version=2)

    with pytest.raises(ValidationError):
        ConceptNoteMetadata.model_validate(data)


def test_invalid_note_type_raises() -> None:
    data = build_minimal_concept_note_data(note_type="source")

    with pytest.raises(ValidationError):
        ConceptNoteMetadata.model_validate(data)


def test_empty_canonical_title_raises() -> None:
    data = build_minimal_concept_note_data(canonical_title="")

    with pytest.raises(ValidationError):
        ConceptNoteMetadata.model_validate(data)


def test_empty_learning_encounters_raises() -> None:
    data = build_minimal_concept_note_data(learning_encounters=[])

    with pytest.raises(ValidationError):
        ConceptNoteMetadata.model_validate(data)


def test_duplicate_scaffold_module_ids_raises() -> None:
    module = {
        "id": "module_dup_001",
        "type": "derivation",
        "title": "First Module",
        "status": "scaffolded",
    }
    data = build_minimal_concept_note_data(scaffold_modules=[module, module])

    with pytest.raises(ValidationError, match="duplicate scaffold module id"):
        ConceptNoteMetadata.model_validate(data)


def test_unknown_top_level_field_raises() -> None:
    data = build_minimal_concept_note_data(extra_field="not_allowed")

    with pytest.raises(ValidationError):
        ConceptNoteMetadata.model_validate(data)


def test_invalid_concept_domain_pattern_raises() -> None:
    data = build_minimal_concept_note_data(concept_domains=["MachineLearning"])

    with pytest.raises(ValidationError):
        ConceptNoteMetadata.model_validate(data)


def test_model_dump_round_trip(valid_concept_note: ConceptNoteMetadata) -> None:
    dumped = valid_concept_note.model_dump(mode="json")
    restored = ConceptNoteMetadata.model_validate(dumped)

    assert restored == valid_concept_note


def test_default_concept_type_is_general_concept() -> None:
    data = build_minimal_concept_note_data()
    del data["concept_type"]

    note = ConceptNoteMetadata.model_validate(data)
    assert note.concept_type == ConceptType.GENERAL_CONCEPT


def test_multiple_primary_encounters_allowed_in_b3() -> None:
    """Multiple primary encounters are deferred to B6 write-mode validation."""
    encounter = {
        "source": {"type": "studium", "title": "Studium"},
        "role": "primary",
        "contribution_status": "pending",
        "content_attached": False,
        "content_id": None,
    }
    data = build_minimal_concept_note_data(learning_encounters=[encounter, encounter])

    note = ConceptNoteMetadata.model_validate(data)
    assert len(note.learning_encounters) == 2
    assert all(e.role.value == "primary" for e in note.learning_encounters)
