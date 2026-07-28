"""Create, inspect, and rebuild derived index databases."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, delete, inspect, select
from sqlalchemy.engine import Connection

from studium.index.config import INDEX_SCHEMA_VERSION, IndexConfig
from studium.index.engine import begin_connection, create_index_engine
from studium.index.errors import IndexNotInitializedError, IndexSchemaMismatchError
from studium.index.schema import index_metadata, metadata


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_engine_for_config(config: IndexConfig) -> Engine:
    """Create an engine for the configured vault index path."""
    return create_index_engine(
        config.database_path,
        busy_timeout_ms=config.busy_timeout_ms,
    )


def initialize_index(engine: Engine, config: IndexConfig) -> None:
    """Create all tables and write the index metadata row."""
    metadata.create_all(engine)
    now = _utc_now_iso()
    with begin_connection(engine) as connection:
        existing = connection.execute(select(index_metadata.c.id).limit(1)).first()
        if existing is None:
            connection.execute(
                index_metadata.insert().values(
                    schema_version=INDEX_SCHEMA_VERSION,
                    vault_path=str(config.resolved_vault_root),
                    vault_identifier=config.vault_identifier,
                    created_at=now,
                    updated_at=now,
                    last_rebuild_at=None,
                )
            )
        else:
            connection.execute(
                index_metadata.update()
                .where(index_metadata.c.id == existing.id)
                .values(
                    schema_version=INDEX_SCHEMA_VERSION,
                    vault_path=str(config.resolved_vault_root),
                    vault_identifier=config.vault_identifier,
                    updated_at=now,
                )
            )


def read_index_schema_version(engine: Engine) -> int | None:
    """Return the stored index schema version, or None if missing."""
    with engine.connect() as connection:
        return _read_schema_version(connection)


def _read_schema_version(connection: Connection) -> int | None:
    inspector = inspect(connection)
    if "index_metadata" not in inspector.get_table_names():
        return None
    row = connection.execute(
        select(index_metadata.c.schema_version).order_by(index_metadata.c.id).limit(1)
    ).first()
    if row is None:
        return None
    return int(row.schema_version)


def ensure_compatible_index(engine: Engine) -> int:
    """Assert the on-disk schema version matches the code expectation."""
    found = read_index_schema_version(engine)
    if found is None:
        raise IndexNotInitializedError("Index metadata is missing; initialize or rebuild.")
    if found != INDEX_SCHEMA_VERSION:
        raise IndexSchemaMismatchError(found=found, expected=INDEX_SCHEMA_VERSION)
    return found


def delete_index_files(db_path: Path) -> None:
    """Delete the SQLite database and companion WAL/SHM files if present."""
    for path in (db_path, Path(f"{db_path}-wal"), Path(f"{db_path}-shm")):
        if path.exists():
            path.unlink()


def rebuild_index(config: IndexConfig) -> Engine:
    """Delete the existing index database and recreate it from scratch."""
    db_path = config.database_path
    delete_index_files(db_path)
    engine = create_engine_for_config(config)
    initialize_index(engine, config)
    now = _utc_now_iso()
    with begin_connection(engine) as connection:
        row = connection.execute(select(index_metadata.c.id).limit(1)).first()
        if row is None:
            raise IndexNotInitializedError("Index metadata is missing after rebuild initialize.")
        connection.execute(
            index_metadata.update()
            .where(index_metadata.c.id == row.id)
            .values(last_rebuild_at=now, updated_at=now)
        )
    return engine


def set_schema_version_for_tests(engine: Engine, version: int) -> None:
    """Overwrite schema_version (test helper for mismatch scenarios)."""
    with begin_connection(engine) as connection:
        row = connection.execute(select(index_metadata.c.id).limit(1)).first()
        if row is None:
            raise IndexNotInitializedError("Cannot set schema version on an empty index.")
        connection.execute(
            index_metadata.update()
            .where(index_metadata.c.id == row.id)
            .values(schema_version=version, updated_at=_utc_now_iso())
        )


def clear_all_tables(engine: Engine) -> None:
    """Delete all rows from application tables (keeps schema)."""
    with begin_connection(engine) as connection:
        for table in reversed(metadata.sorted_tables):
            connection.execute(delete(table))
