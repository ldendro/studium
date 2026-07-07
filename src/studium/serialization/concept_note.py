"""High-level concept note serialization."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from studium.schemas import ConceptNoteMetadata, NoteStatus, NoteVaultStatus, ReviewStatus
from studium.schemas.learning_encounter import default_studium_learning_encounter
from studium.serialization.body import build_canonical_concept_body
from studium.serialization.concept_id import generate_concept_id
from studium.serialization.metadata_yaml import serialize_metadata_to_yaml


def serialize_concept_note(metadata: ConceptNoteMetadata, body: str) -> str:
    """Serialize metadata and an existing Markdown body into a full concept note."""
    yaml_text = serialize_metadata_to_yaml(metadata)
    if not yaml_text.endswith("\n"):
        yaml_text += "\n"
    return f"---\n{yaml_text}---\n{body}"


def build_concept_note_metadata(canonical_title: str, **overrides: Any) -> ConceptNoteMetadata:
    """Build valid metadata for a newly generated concept note."""
    now = datetime.now(UTC)
    data: dict[str, Any] = {
        "id": generate_concept_id(canonical_title),
        "canonical_title": canonical_title,
        "learning_encounters": [default_studium_learning_encounter()],
        "status": NoteStatus.SCAFFOLDED,
        "review_status": ReviewStatus.NOT_SUBMITTED,
        "vault_status": NoteVaultStatus.DRAFT,
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return ConceptNoteMetadata.model_validate(data)


def create_concept_note_markdown(canonical_title: str, **overrides: Any) -> str:
    """Generate a full Markdown concept note from a title and optional metadata overrides."""
    metadata = build_concept_note_metadata(canonical_title, **overrides)
    body = build_canonical_concept_body(metadata)
    return serialize_concept_note(metadata, body)
