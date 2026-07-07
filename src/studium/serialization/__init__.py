"""Concept note serialization (branch P1-B5).

Generates full Markdown concept notes from metadata, including concept ID
generation, canonical YAML/Markdown ordering, and relationship projection.
"""

from studium.serialization.body import build_canonical_concept_body
from studium.serialization.concept_id import generate_concept_id, slugify_title
from studium.serialization.concept_note import (
    build_concept_note_metadata,
    create_concept_note_markdown,
    serialize_concept_note,
)
from studium.serialization.metadata_yaml import metadata_to_ordered_dict, serialize_metadata_to_yaml
from studium.serialization.relationships import project_relationship_bullets

__all__ = [
    "build_canonical_concept_body",
    "build_concept_note_metadata",
    "create_concept_note_markdown",
    "generate_concept_id",
    "metadata_to_ordered_dict",
    "project_relationship_bullets",
    "serialize_concept_note",
    "serialize_metadata_to_yaml",
    "slugify_title",
]
