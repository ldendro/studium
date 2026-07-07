"""Canonical Markdown body generation for concept notes."""

from __future__ import annotations

from studium.schemas import ConceptNoteMetadata
from studium.schemas.canonical import CANONICAL_SECTION_TITLES
from studium.serialization.relationships import project_relationship_bullets


def build_canonical_concept_body(
    metadata: ConceptNoteMetadata,
    *,
    project_relationships: bool = True,
) -> str:
    """Build a canonical Markdown body with section containers for a concept note."""
    prerequisite_lines, related_lines = (
        project_relationship_bullets(metadata.relationships) if project_relationships else ([], [])
    )
    module_index_lines = [f"- {module.title}" for module in metadata.scaffold_modules]

    sections: list[str] = [f"# {metadata.canonical_title}", ""]
    for title in CANONICAL_SECTION_TITLES:
        sections.extend([f"## {title}", ""])
        if title == "Prerequisites" and prerequisite_lines:
            sections.extend([*prerequisite_lines, ""])
        elif title == "Module Index" and module_index_lines:
            sections.extend([*module_index_lines, ""])
        elif title == "Related Concepts" and related_lines:
            sections.extend([*related_lines, ""])

    return "\n".join(sections).rstrip() + "\n"
