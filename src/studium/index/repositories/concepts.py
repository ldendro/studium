"""Concepts repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Connection

from studium.index.normalize import normalize_title
from studium.index.repositories._util import mapping
from studium.index.schema import concepts


def upsert_concept(connection: Connection, values: dict[str, Any]) -> None:
    payload = dict(values)
    if "normalized_title" not in payload and "canonical_title" in payload:
        payload["normalized_title"] = normalize_title(str(payload["canonical_title"]))
    stmt = insert(concepts).values(**payload)
    update_cols = {key: stmt.excluded[key] for key in payload if key != "concept_id"}
    connection.execute(stmt.on_conflict_do_update(index_elements=["concept_id"], set_=update_cols))


def get_concept(connection: Connection, concept_id: str) -> dict[str, Any] | None:
    row = connection.execute(select(concepts).where(concepts.c.concept_id == concept_id)).first()
    return None if row is None else mapping(row)


def list_concepts_by_normalized_title(
    connection: Connection, normalized_title: str
) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(concepts)
        .where(concepts.c.normalized_title == normalized_title)
        .order_by(concepts.c.concept_id)
    ).all()
    return [mapping(row) for row in rows]


def delete_concept(connection: Connection, concept_id: str) -> None:
    connection.execute(delete(concepts).where(concepts.c.concept_id == concept_id))


def list_concepts(connection: Connection) -> list[dict[str, Any]]:
    rows = connection.execute(select(concepts).order_by(concepts.c.concept_id)).all()
    return [mapping(row) for row in rows]
