"""Build Markdown concept note strings for parsing tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from schemas.helpers import build_minimal_concept_note_data


def build_valid_frontmatter_yaml(**overrides: Any) -> str:
    """Return YAML frontmatter text without delimiters."""
    data = build_minimal_concept_note_data(**overrides)
    data["created_at"] = datetime(2026, 6, 25, tzinfo=UTC)
    data["updated_at"] = datetime(2026, 6, 25, tzinfo=UTC)

    lines = [
        f"id: {data['id']}",
        "schema_version: 1",
        "note_type: concept",
        f"concept_type: {data['concept_type']}",
        "concept_domains: []",
        f"canonical_title: {data['canonical_title']}",
        "aliases: []",
        "status: scaffolded",
        "review_status: not_submitted",
        "vault_status: draft",
        "learning_encounters:",
        "  - source:",
        "      type: studium",
        "      title: Studium",
        "    role: primary",
        "    contribution_status: pending",
        "    content_attached: false",
        "    content_id:",
        "scaffold_modules: []",
        "relationships: []",
        "created_at: 2026-06-25T00:00:00Z",
        "updated_at: 2026-06-25T00:00:00Z",
    ]
    return "\n".join(lines)


def build_canonical_body(title: str = "Test Concept", *, include_module_index: bool = True) -> str:
    """Return canonical Markdown body sections for a concept note."""
    sections = [
        f"# {title}",
        "",
        "## Concept Overview",
        "",
        "## Prerequisites",
        "",
    ]
    if include_module_index:
        sections.extend(["## Module Index", ""])
    sections.extend(
        [
            "## Scaffold Modules",
            "",
            "## Related Concepts",
            "",
            "## Open Questions / Gaps",
            "",
        ]
    )
    return "\n".join(sections)


def build_valid_concept_note_markdown(**metadata_overrides: Any) -> str:
    """Return a full concept note Markdown document."""
    title = metadata_overrides.get("canonical_title", "Test Concept")
    yaml_block = build_valid_frontmatter_yaml(**metadata_overrides)
    body = build_canonical_body(title)
    return f"---\n{yaml_block}\n---\n{body}"
