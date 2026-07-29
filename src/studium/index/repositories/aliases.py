"""Concept aliases repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.engine import Connection

from studium.index.normalize import normalize_title
from studium.index.repositories._util import inserted_int_pk, mapping
from studium.index.schema import concept_aliases


def insert_alias(
    connection: Connection,
    *,
    concept_id: str,
    alias: str,
    normalized_alias: str | None = None,
) -> int:
    result = connection.execute(
        concept_aliases.insert().values(
            concept_id=concept_id,
            alias=alias,
            normalized_alias=normalized_alias or normalize_title(alias),
        )
    )
    return inserted_int_pk(result)


def list_aliases_for_concept(connection: Connection, concept_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(concept_aliases)
        .where(concept_aliases.c.concept_id == concept_id)
        .order_by(concept_aliases.c.id)
    ).all()
    return [mapping(row) for row in rows]


def delete_aliases_for_concept(connection: Connection, concept_id: str) -> None:
    connection.execute(delete(concept_aliases).where(concept_aliases.c.concept_id == concept_id))
