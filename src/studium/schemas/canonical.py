"""Shared canonical ordering constants for concept note metadata and Markdown."""

from __future__ import annotations

from studium.schemas.enums import RelationshipType

CANONICAL_SECTION_TITLES: tuple[str, ...] = (
    "Concept Overview",
    "Prerequisites",
    "Module Index",
    "Scaffold Modules",
    "Related Concepts",
    "Open Questions / Gaps",
)

CANONICAL_YAML_TOP_LEVEL_KEYS: tuple[str, ...] = (
    "id",
    "schema_version",
    "note_type",
    "concept_type",
    "concept_domains",
    "canonical_title",
    "aliases",
    "status",
    "review_status",
    "vault_status",
    "learning_encounters",
    "scaffold_modules",
    "relationships",
    "created_at",
    "updated_at",
)

SOURCE_FIELD_ORDER: tuple[str, ...] = (
    "type",
    "title",
    "unit_type",
    "unit",
    "section",
    "link",
)

LEARNING_ENCOUNTER_FIELD_ORDER: tuple[str, ...] = (
    "source",
    "role",
    "contribution_status",
    "content_attached",
    "content_id",
)

SCAFFOLD_MODULE_FIELD_ORDER: tuple[str, ...] = (
    "id",
    "type",
    "title",
    "status",
    "origin",
    "focus",
)

RELATIONSHIP_FIELD_ORDER: tuple[str, ...] = (
    "relationship_type",
    "target_id",
    "target_title",
    "vault_status",
)

PREREQUISITE_RELATIONSHIP_TYPES: frozenset[RelationshipType] = frozenset(
    {RelationshipType.DEPENDS_ON}
)
