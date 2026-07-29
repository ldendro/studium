"""Invalid index records repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.engine import Connection

from studium.index.repositories._util import inserted_int_pk, mapping
from studium.index.schema import invalid_index_records


def insert_invalid_record(connection: Connection, values: dict[str, Any]) -> int:
    result = connection.execute(invalid_index_records.insert().values(**values))
    return inserted_int_pk(result)


def list_invalid_records(connection: Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(invalid_index_records).order_by(invalid_index_records.c.id)
    ).all()
    return [mapping(row) for row in rows]


def delete_invalid_records_for_path(connection: Connection, file_path: str) -> None:
    connection.execute(
        delete(invalid_index_records).where(invalid_index_records.c.file_path == file_path)
    )
