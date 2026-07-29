"""Embeddings repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.engine import Connection

from studium.index.repositories._util import inserted_int_pk, mapping
from studium.index.schema import embeddings


def insert_embedding(connection: Connection, values: dict[str, Any]) -> int:
    result = connection.execute(embeddings.insert().values(**values))
    return inserted_int_pk(result)


def get_embedding(connection: Connection, embedding_id: int) -> dict[str, Any] | None:
    row = connection.execute(select(embeddings).where(embeddings.c.id == embedding_id)).first()
    return None if row is None else mapping(row)


def list_embeddings_for_owner(
    connection: Connection, *, owner_type: str, owner_id: str
) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(embeddings)
        .where(embeddings.c.owner_type == owner_type, embeddings.c.owner_id == owner_id)
        .order_by(embeddings.c.id)
    ).all()
    return [mapping(row) for row in rows]


def delete_embedding(connection: Connection, embedding_id: int) -> None:
    connection.execute(delete(embeddings).where(embeddings.c.id == embedding_id))
