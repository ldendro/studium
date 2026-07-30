"""Create, inspect, and rebuild derived index databases."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, delete, inspect, select
from sqlalchemy.engine import Connection

from studium.index.config import INDEX_SCHEMA_VERSION, IndexConfig
from studium.index.engine import begin_connection, create_index_engine
from studium.index.errors import IndexNotInitializedError, IndexSchemaMismatchError
from studium.index.repositories.fts import clear_fts_tables, create_fts_tables
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
    """Create all tables and write the index metadata row.

    Does not migrate existing DDL. If metadata already records an incompatible
    schema version, raise and require ``rebuild_index`` instead of rewriting the
    stored version.
    """
    with engine.connect() as connection:
        found_version = _read_schema_version(connection)
    if found_version is not None and found_version != INDEX_SCHEMA_VERSION:
        raise IndexSchemaMismatchError(found=found_version, expected=INDEX_SCHEMA_VERSION)

    metadata.create_all(engine)
    now = _utc_now_iso()
    with begin_connection(engine) as connection:
        create_fts_tables(connection)
        existing = connection.execute(select(index_metadata.c.id).limit(1)).first()
        if existing is None:
            connection.execute(
                index_metadata.insert().values(
                    schema_version=INDEX_SCHEMA_VERSION,
                    vault_path=str(config.resolved_vault_root),
                    vault_identifier=config.vault_identifier,
                    index_revision=0,
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


def rebuild_index(
    config: IndexConfig,
    existing_engine: Engine | None = None,
) -> Engine:
    """Delete the existing index database and recreate it from scratch.

    Pass any engine previously opened against this database as
    ``existing_engine`` so its connection pool is closed before the SQLite
    files are unlinked. Leaving pooled handles open can fail on Windows
    (file in use) or leave POSIX connections attached to a deleted inode.
    """
    if existing_engine is not None:
        existing_engine.dispose()

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
    """Delete all rows from application tables (keeps schema).

    FTS5 virtual tables are outside SQLAlchemy metadata, so they are cleared
    explicitly; otherwise lexical search would keep stale hits after a reset.
    """
    with begin_connection(engine) as connection:
        clear_fts_tables(connection)
        for table in reversed(metadata.sorted_tables):
            connection.execute(delete(table))


def get_index_revision(engine: Engine) -> int:
    """Return the current index revision, or raise if metadata is missing."""
    with engine.connect() as connection:
        row = connection.execute(
            select(index_metadata.c.index_revision).order_by(index_metadata.c.id).limit(1)
        ).first()
    if row is None:
        raise IndexNotInitializedError("Index metadata is missing; initialize or rebuild.")
    return int(row.index_revision)


def increment_index_revision(engine: Engine) -> int:
    """Bump index_revision by one and return the new value."""
    now = _utc_now_iso()
    with begin_connection(engine) as connection:
        meta = connection.execute(
            select(index_metadata).order_by(index_metadata.c.id).limit(1)
        ).first()
        if meta is None:
            raise IndexNotInitializedError("Index metadata is missing; initialize or rebuild.")
        new_revision = int(meta.index_revision) + 1
        connection.execute(
            index_metadata.update()
            .where(index_metadata.c.id == meta.id)
            .values(index_revision=new_revision, updated_at=now)
        )
    return new_revision
