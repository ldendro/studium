"""Project YAML relationships into readable Markdown bullets."""

from __future__ import annotations

from studium.schemas import RelationshipMetadata
from studium.schemas.canonical import PREREQUISITE_RELATIONSHIP_TYPES


def project_relationship_bullets(
    relationships: list[RelationshipMetadata],
) -> tuple[list[str], list[str]]:
    """Return prerequisite and related-concept wikilink bullets.

    Only ``depends_on`` relationships appear under Prerequisites so the section
    lists concepts the learner should address before this note. All other
    relationship types project into Related Concepts.
    """
    prerequisite_lines: list[str] = []
    related_lines: list[str] = []

    for relationship in relationships:
        bullet = f"- [[{relationship.target_title}]]"
        if relationship.relationship_type in PREREQUISITE_RELATIONSHIP_TYPES:
            prerequisite_lines.append(bullet)
        else:
            related_lines.append(bullet)

    return prerequisite_lines, related_lines
