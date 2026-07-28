"""Relationships repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.engine import Connection

from studium.index.repositories._util import inserted_int_pk, mapping
from studium.index.schema import relationships


def insert_relationship(connection: Connection, values: dict[str, Any]) -> int:
    result = connection.execute(relationships.insert().values(**values))
    return inserted_int_pk(result)


def list_relationships_for_source(
    connection: Connection, source_concept_id: str
) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(relationships)
        .where(relationships.c.source_concept_id == source_concept_id)
        .order_by(relationships.c.id)
    ).all()
    return [mapping(row) for row in rows]


def delete_relationships_for_source(connection: Connection, source_concept_id: str) -> None:
    connection.execute(
        delete(relationships).where(relationships.c.source_concept_id == source_concept_id)
    )
