"""Search document repositories."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Connection

from studium.index.repositories._util import mapping
from studium.index.schema import concept_search_documents, module_search_documents


def upsert_concept_search_document(connection: Connection, values: dict[str, Any]) -> None:
    stmt = insert(concept_search_documents).values(**values)
    update_cols = {key: stmt.excluded[key] for key in values if key != "concept_id"}
    connection.execute(stmt.on_conflict_do_update(index_elements=["concept_id"], set_=update_cols))


def get_concept_search_document(connection: Connection, concept_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        select(concept_search_documents).where(concept_search_documents.c.concept_id == concept_id)
    ).first()
    return None if row is None else mapping(row)


def upsert_module_search_document(connection: Connection, values: dict[str, Any]) -> None:
    stmt = insert(module_search_documents).values(**values)
    update_cols = {key: stmt.excluded[key] for key in values if key != "module_id"}
    connection.execute(stmt.on_conflict_do_update(index_elements=["module_id"], set_=update_cols))


def get_module_search_document(connection: Connection, module_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        select(module_search_documents).where(module_search_documents.c.module_id == module_id)
    ).first()
    return None if row is None else mapping(row)


def delete_concept_search_document(connection: Connection, concept_id: str) -> None:
    connection.execute(
        delete(concept_search_documents).where(concept_search_documents.c.concept_id == concept_id)
    )
