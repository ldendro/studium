"""Tests for canonical Markdown body generation."""

from __future__ import annotations

from studium.schemas.canonical import CANONICAL_SECTION_TITLES
from studium.serialization import build_canonical_concept_body
from tests.serialization.helpers import (
    build_metadata_with_relationships,
    build_metadata_with_scaffold_modules,
    build_sample_metadata,
)


def test_build_canonical_body_includes_all_sections_in_order() -> None:
    body = build_canonical_concept_body(build_sample_metadata())

    assert body.startswith("# Stochastic Gradient Descent\n")
    section_positions = [body.index(f"## {title}") for title in CANONICAL_SECTION_TITLES]
    assert section_positions == sorted(section_positions)


def test_build_canonical_body_projects_prerequisites_and_related_sections() -> None:
    body = build_canonical_concept_body(build_metadata_with_relationships())

    prerequisites_index = body.index("## Prerequisites")
    related_index = body.index("## Related Concepts")
    assert prerequisites_index < related_index
    assert "- [[Partial Derivatives]]" in body
    assert "- [[Gradient Descent]]" in body


def test_build_canonical_body_lists_scaffold_module_titles_in_module_index() -> None:
    body = build_canonical_concept_body(build_metadata_with_scaffold_modules())

    assert "- Gradient Update Formula Derivation" in body
