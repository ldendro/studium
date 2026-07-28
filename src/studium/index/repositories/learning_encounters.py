"""Learning encounters repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.engine import Connection

from studium.index.repositories._util import inserted_int_pk, mapping
from studium.index.schema import learning_encounters


def insert_learning_encounter(connection: Connection, values: dict[str, Any]) -> int:
    result = connection.execute(learning_encounters.insert().values(**values))
    return inserted_int_pk(result)


def list_encounters_for_concept(connection: Connection, concept_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(learning_encounters)
        .where(learning_encounters.c.concept_id == concept_id)
        .order_by(learning_encounters.c.id)
    ).all()
    return [mapping(row) for row in rows]


def delete_encounters_for_concept(connection: Connection, concept_id: str) -> None:
    connection.execute(
        delete(learning_encounters).where(learning_encounters.c.concept_id == concept_id)
    )
