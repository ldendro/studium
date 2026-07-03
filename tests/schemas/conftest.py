"""Shared fixtures for schema tests."""

from __future__ import annotations

from typing import Any

import pytest

from studium.schemas import ConceptNoteMetadata, default_studium_learning_encounter


@pytest.fixture
def valid_concept_note_data() -> dict[str, Any]:
    """Dict matching Technical Plan §5.1 example."""
    return {
        "id": "concept_stochastic_gradient_descent_a1b2c3",
        "schema_version": 1,
        "note_type": "concept",
        "concept_type": "algorithm",
        "concept_domains": ["machine_learning", "optimization"],
        "canonical_title": "Stochastic Gradient Descent",
        "aliases": ["SGD"],
        "status": "scaffolded",
        "review_status": "not_submitted",
        "vault_status": "draft",
        "learning_encounters": [
            {
                "source": {
                    "type": "studium",
                    "title": "Studium",
                    "unit_type": None,
                    "unit": None,
                    "section": None,
                    "link": None,
                },
                "role": "primary",
                "contribution_status": "pending",
                "content_attached": False,
                "content_id": None,
            }
        ],
        "scaffold_modules": [],
        "relationships": [],
        "created_at": "2026-06-25T00:00:00Z",
        "updated_at": "2026-06-25T00:00:00Z",
    }


@pytest.fixture
def valid_concept_note(valid_concept_note_data: dict[str, Any]) -> ConceptNoteMetadata:
    return ConceptNoteMetadata.model_validate(valid_concept_note_data)


@pytest.fixture
def default_encounter() -> Any:
    return default_studium_learning_encounter()
