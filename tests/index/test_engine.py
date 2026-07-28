"""Tests for engine PRAGMA configuration."""

from __future__ import annotations

from studium.index import IndexConfig, begin_connection, create_engine_for_config, read_pragma
from studium.index.schema_manager import initialize_index


def test_sqlite_pragmas_are_applied(index_config: IndexConfig) -> None:
    engine = create_engine_for_config(index_config)
    initialize_index(engine, index_config)

    with begin_connection(engine) as connection:
        assert read_pragma(connection, "foreign_keys") == "1"
        assert read_pragma(connection, "journal_mode").lower() == "wal"
        assert read_pragma(connection, "synchronous") in {"1", "NORMAL", "normal"}
        assert read_pragma(connection, "busy_timeout") == str(index_config.busy_timeout_ms)
