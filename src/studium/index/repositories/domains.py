"""Concept domains repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.engine import Connection

from studium.index.repositories._util import inserted_int_pk, mapping
from studium.index.schema import concept_domains


def insert_domain(connection: Connection, *, concept_id: str, domain: str) -> int:
    result = connection.execute(
        concept_domains.insert().values(concept_id=concept_id, domain=domain)
    )
    return inserted_int_pk(result)


def list_domains_for_concept(connection: Connection, concept_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(concept_domains)
        .where(concept_domains.c.concept_id == concept_id)
        .order_by(concept_domains.c.id)
    ).all()
    return [mapping(row) for row in rows]


def delete_domains_for_concept(connection: Connection, concept_id: str) -> None:
    connection.execute(delete(concept_domains).where(concept_domains.c.concept_id == concept_id))
