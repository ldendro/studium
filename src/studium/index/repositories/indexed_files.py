"""Indexed files repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Connection

from studium.index.repositories._util import mapping
from studium.index.schema import indexed_files


def upsert_indexed_file(connection: Connection, values: dict[str, Any]) -> None:
    stmt = insert(indexed_files).values(**values)
    update_cols = {key: stmt.excluded[key] for key in values if key != "file_path"}
    connection.execute(stmt.on_conflict_do_update(index_elements=["file_path"], set_=update_cols))


def get_indexed_file(connection: Connection, file_path: str) -> dict[str, Any] | None:
    row = connection.execute(
        select(indexed_files).where(indexed_files.c.file_path == file_path)
    ).first()
    return None if row is None else mapping(row)


def delete_indexed_file(connection: Connection, file_path: str) -> None:
    connection.execute(delete(indexed_files).where(indexed_files.c.file_path == file_path))


def list_indexed_files(connection: Connection) -> list[dict[str, Any]]:
    rows = connection.execute(select(indexed_files).order_by(indexed_files.c.file_path)).all()
    return [mapping(row) for row in rows]


def list_indexed_files_for_concept(connection: Connection, concept_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(indexed_files)
        .where(indexed_files.c.concept_id == concept_id)
        .order_by(indexed_files.c.file_path)
    ).all()
    return [mapping(row) for row in rows]
