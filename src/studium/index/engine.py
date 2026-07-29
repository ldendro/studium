"""SQLAlchemy engine factory and SQLite runtime PRAGMAs."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import Connection

from studium.index.config import DEFAULT_BUSY_TIMEOUT_MS


def create_index_engine(
    db_path: Path,
    *,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> Engine:
    """Create a SQLAlchemy engine for a derived index database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        future=True,
    )
    _register_sqlite_pragmas(engine, busy_timeout_ms=busy_timeout_ms)
    return engine


def _register_sqlite_pragmas(engine: Engine, *, busy_timeout_ms: int) -> None:
    def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
        cursor.close()

    event.listen(engine, "connect", _set_sqlite_pragma)


@contextmanager
def begin_connection(engine: Engine) -> Generator[Connection]:
    """Yield a connection inside a transaction that commits on success."""
    with engine.begin() as connection:
        yield connection


def read_pragma(connection: Connection, name: str) -> str:
    """Return a PRAGMA value as a string for diagnostics/tests."""
    result = connection.execute(text(f"PRAGMA {name}"))
    value = result.scalar()
    return "" if value is None else str(value)
