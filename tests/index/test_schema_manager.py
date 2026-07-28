"""Tests for index schema manager and version handling."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine

from studium.index import (
    INDEX_SCHEMA_VERSION,
    IndexConfig,
    IndexNotInitializedError,
    IndexSchemaMismatchError,
    begin_connection,
    create_engine_for_config,
    ensure_compatible_index,
    read_index_schema_version,
    rebuild_index,
)
from studium.index.repositories import concepts, index_metadata
from studium.index.schema_manager import set_schema_version_for_tests


def test_initialize_index_writes_metadata(
    index_config: IndexConfig, initialized_engine: Engine
) -> None:
    assert read_index_schema_version(initialized_engine) == INDEX_SCHEMA_VERSION
    ensure_compatible_index(initialized_engine)

    with begin_connection(initialized_engine) as connection:
        meta = index_metadata.get_index_metadata(connection)
        assert meta is not None
        assert meta["schema_version"] == INDEX_SCHEMA_VERSION
        assert meta["vault_identifier"] == index_config.vault_identifier
        assert meta["vault_path"] == str(index_config.resolved_vault_root)


def test_ensure_compatible_rejects_mismatch(
    index_config: IndexConfig, initialized_engine: Engine
) -> None:
    set_schema_version_for_tests(initialized_engine, 999)
    with pytest.raises(IndexSchemaMismatchError) as exc_info:
        ensure_compatible_index(initialized_engine)
    assert exc_info.value.found == 999
    assert exc_info.value.expected == INDEX_SCHEMA_VERSION


def test_rebuild_index_recreates_database(
    index_config: IndexConfig, initialized_engine: Engine
) -> None:
    with begin_connection(initialized_engine) as connection:
        concepts.upsert_concept(
            connection,
            {
                "concept_id": "concept_temp_abc123",
                "canonical_title": "Temp",
                "concept_type": "general_concept",
                "status": "scaffolded",
                "review_status": "not_submitted",
                "vault_status": "draft",
                "file_path": "concepts/temp.md",
                "note_schema_version": 2,
                "validity_state": "valid",
                "indexed_revision": 1,
            },
        )

    set_schema_version_for_tests(initialized_engine, 999)
    initialized_engine.dispose()
    rebuilt = rebuild_index(index_config)

    assert read_index_schema_version(rebuilt) == INDEX_SCHEMA_VERSION
    ensure_compatible_index(rebuilt)
    with begin_connection(rebuilt) as connection:
        assert concepts.get_concept(connection, "concept_temp_abc123") is None
        meta = index_metadata.get_index_metadata(connection)
        assert meta is not None
        assert meta["last_rebuild_at"] is not None


def test_ensure_compatible_uninitialized(index_config: IndexConfig) -> None:
    engine = create_engine_for_config(index_config)
    with pytest.raises(IndexNotInitializedError):
        ensure_compatible_index(engine)
