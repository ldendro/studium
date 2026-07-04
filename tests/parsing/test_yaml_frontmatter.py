"""Tests for YAML frontmatter parsing."""

from __future__ import annotations

import pytest

from studium.parsing import YamlParseError, parse_yaml_frontmatter
from studium.schemas import ValidationSeverity
from tests.parsing.helpers import build_valid_frontmatter_yaml


def test_parse_valid_yaml_metadata() -> None:
    result = parse_yaml_frontmatter(build_valid_frontmatter_yaml())

    assert result.metadata is not None
    assert result.metadata.canonical_title == "Test Concept"
    assert result.unknown_fields == []
    assert result.metadata_issues == []


def test_invalid_yaml_raises() -> None:
    with pytest.raises(YamlParseError, match="Invalid YAML frontmatter"):
        parse_yaml_frontmatter("id: [broken\naliases: ]")


def test_non_mapping_yaml_raises() -> None:
    with pytest.raises(YamlParseError, match="must parse to a mapping"):
        parse_yaml_frontmatter("just a string\n")


def test_empty_frontmatter_parses_to_empty_dict() -> None:
    result = parse_yaml_frontmatter("")

    assert result.raw_metadata == {}
    assert result.metadata is None
    assert result.metadata_issues


def test_unknown_fields_stripped_and_reported() -> None:
    yaml_text = build_valid_frontmatter_yaml() + "\nlegacy_field: old_value\n"
    result = parse_yaml_frontmatter(yaml_text)

    assert result.unknown_fields == ["legacy_field"]
    assert "legacy_field" not in result.known_metadata
    assert result.metadata is not None


def test_empty_strings_normalized_to_none() -> None:
    yaml_text = """id: concept_test_abc123
schema_version: 1
note_type: concept
concept_type: general_concept
concept_domains: []
canonical_title: Test Concept
aliases: []
status: scaffolded
review_status: not_submitted
vault_status: draft
learning_encounters:
  - source:
      type: studium
      title: Studium
      unit_type: ""
      unit: ""
      section: ""
      link: ""
    role: primary
    contribution_status: pending
    content_attached: false
    content_id: ""
scaffold_modules: []
relationships: []
created_at: 2026-06-25T00:00:00Z
updated_at: 2026-06-25T00:00:00Z
"""
    result = parse_yaml_frontmatter(yaml_text)

    assert result.metadata is not None
    encounter = result.metadata.learning_encounters[0]
    assert encounter.content_id is None
    assert encounter.source.unit_type is None
    assert encounter.source.link is None


def test_metadata_issues_are_critical() -> None:
    result = parse_yaml_frontmatter("canonical_title: Missing Required Fields\n")

    assert result.metadata is None
    assert all(issue.severity == ValidationSeverity.CRITICAL for issue in result.metadata_issues)
