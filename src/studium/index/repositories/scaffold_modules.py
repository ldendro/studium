"""Scaffold modules repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Connection

from studium.index.normalize import normalize_title
from studium.index.repositories._util import mapping
from studium.index.schema import scaffold_modules


def upsert_scaffold_module(connection: Connection, values: dict[str, Any]) -> None:
    payload = dict(values)
    if "normalized_title" not in payload and "title" in payload:
        payload["normalized_title"] = normalize_title(str(payload["title"]))
    stmt = insert(scaffold_modules).values(**payload)
    update_cols = {key: stmt.excluded[key] for key in payload if key != "module_id"}
    connection.execute(stmt.on_conflict_do_update(index_elements=["module_id"], set_=update_cols))


def get_scaffold_module(connection: Connection, module_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        select(scaffold_modules).where(scaffold_modules.c.module_id == module_id)
    ).first()
    return None if row is None else mapping(row)


def list_modules_for_concept(connection: Connection, concept_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(scaffold_modules)
        .where(scaffold_modules.c.concept_id == concept_id)
        .order_by(scaffold_modules.c.module_id)
    ).all()
    return [mapping(row) for row in rows]


def delete_scaffold_module(connection: Connection, module_id: str) -> None:
    connection.execute(delete(scaffold_modules).where(scaffold_modules.c.module_id == module_id))
