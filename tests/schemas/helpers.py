"""Shared helpers for schema tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_minimal_concept_note_data(**overrides: Any) -> dict[str, Any]:
    """Build minimal valid concept note metadata with optional field overrides."""
    base: dict[str, Any] = {
        "id": "concept_test_abc123",
        "schema_version": 1,
        "note_type": "concept",
        "concept_type": "general_concept",
        "concept_domains": [],
        "canonical_title": "Test Concept",
        "aliases": [],
        "status": "scaffolded",
        "review_status": "not_submitted",
        "vault_status": "draft",
        "learning_encounters": [
            {
                "source": {"type": "studium", "title": "Studium"},
                "role": "primary",
                "contribution_status": "pending",
                "content_attached": False,
                "content_id": None,
            }
        ],
        "scaffold_modules": [],
        "relationships": [],
        "created_at": datetime(2026, 6, 25, tzinfo=UTC),
        "updated_at": datetime(2026, 6, 25, tzinfo=UTC),
    }
    base.update(overrides)
    return base
