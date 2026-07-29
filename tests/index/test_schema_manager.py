"""Tests for index schema manager and version handling."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy import Engine, text

from studium.index import (
    INDEX_SCHEMA_VERSION,
    IndexConfig,
    IndexNotInitializedError,
    IndexSchemaMismatchError,
    begin_connection,
    create_engine_for_config,
    ensure_compatible_index,
    initialize_index,
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


def test_initialize_index_rejects_older_schema_without_rewriting_version(
    index_config: IndexConfig, initialized_engine: Engine
) -> None:
    set_schema_version_for_tests(initialized_engine, 999)
    assert read_index_schema_version(initialized_engine) == 999

    with pytest.raises(IndexSchemaMismatchError) as exc_info:
        initialize_index(initialized_engine, index_config)

    assert exc_info.value.found == 999
    assert exc_info.value.expected == INDEX_SCHEMA_VERSION
    assert read_index_schema_version(initialized_engine) == 999
    with pytest.raises(IndexSchemaMismatchError):
        ensure_compatible_index(initialized_engine)


def test_initialize_index_is_idempotent_for_compatible_schema(
    index_config: IndexConfig, initialized_engine: Engine
) -> None:
    initialize_index(initialized_engine, index_config)
    assert read_index_schema_version(initialized_engine) == INDEX_SCHEMA_VERSION
    ensure_compatible_index(initialized_engine)


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
    # Do not dispose here: rebuild_index must close the existing pool itself.
    rebuilt = rebuild_index(index_config, existing_engine=initialized_engine)

    assert read_index_schema_version(rebuilt) == INDEX_SCHEMA_VERSION
    ensure_compatible_index(rebuilt)
    with begin_connection(rebuilt) as connection:
        assert concepts.get_concept(connection, "concept_temp_abc123") is None
        meta = index_metadata.get_index_metadata(connection)
        assert meta is not None
        assert meta["last_rebuild_at"] is not None


def test_rebuild_index_disposes_existing_engine_before_unlink(
    index_config: IndexConfig, initialized_engine: Engine
) -> None:
    db_path = index_config.database_path
    assert db_path.exists()

    # Return a connection to the pool so dispose must close live handles.
    with initialized_engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar() == 1

    dispose = MagicMock(wraps=initialized_engine.dispose)
    initialized_engine.dispose = dispose  # type: ignore[method-assign]

    rebuilt = rebuild_index(index_config, existing_engine=initialized_engine)

    dispose.assert_called_once_with()
    assert rebuilt is not initialized_engine
    assert db_path.exists()
    assert read_index_schema_version(rebuilt) == INDEX_SCHEMA_VERSION


def test_ensure_compatible_uninitialized(index_config: IndexConfig) -> None:
    engine = create_engine_for_config(index_config)
    with pytest.raises(IndexNotInitializedError):
        ensure_compatible_index(engine)
