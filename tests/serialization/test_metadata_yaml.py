"""Tests for metadata YAML serialization."""

from __future__ import annotations

from studium.schemas.canonical import CANONICAL_YAML_TOP_LEVEL_KEYS
from studium.serialization import metadata_to_ordered_dict, serialize_metadata_to_yaml
from tests.serialization.helpers import build_sample_metadata


def test_metadata_yaml_uses_canonical_top_level_order() -> None:
    ordered = metadata_to_ordered_dict(build_sample_metadata())

    assert list(ordered.keys()) == list(CANONICAL_YAML_TOP_LEVEL_KEYS)


def test_metadata_yaml_formats_datetimes_with_z_suffix() -> None:
    yaml_text = serialize_metadata_to_yaml(build_sample_metadata())

    assert "created_at:" in yaml_text
    assert "updated_at:" in yaml_text
    assert "2026-06-25T00:00:00Z" in yaml_text


def test_metadata_yaml_renders_optional_null_source_fields() -> None:
    yaml_text = serialize_metadata_to_yaml(build_sample_metadata())

    assert "unit_type:" in yaml_text
    assert "content_id:" in yaml_text


def test_metadata_yaml_includes_relationship_target_id_null() -> None:
    metadata = build_sample_metadata(
        relationships=[
            {
                "relationship_type": "depends_on",
                "target_title": "Chain Rule",
                "vault_status": "unresolved",
                "target_id": None,
            }
        ]
    )
    yaml_text = serialize_metadata_to_yaml(metadata)

    assert "target_id:" in yaml_text
    assert "target_title: Chain Rule" in yaml_text
