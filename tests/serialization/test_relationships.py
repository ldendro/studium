"""Tests for relationship Markdown projection."""

from __future__ import annotations

from studium.serialization import project_relationship_bullets
from tests.serialization.helpers import build_metadata_with_relationships


def test_depends_on_projects_to_prerequisites_only() -> None:
    metadata = build_metadata_with_relationships()
    prerequisites, related = project_relationship_bullets(metadata.relationships)

    assert prerequisites == ["- [[Partial Derivatives]]"]
    assert related == ["- [[Gradient Descent]]"]


def test_missing_target_still_renders_wikilink_bullet() -> None:
    metadata = build_metadata_with_relationships()
    prerequisites, _ = project_relationship_bullets(metadata.relationships)

    assert prerequisites[0] == "- [[Partial Derivatives]]"
