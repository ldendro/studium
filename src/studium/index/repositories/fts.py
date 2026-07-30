"""FTS5 virtual-table DDL and row sync helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

# FTS tokenizer lives here (not in search.weights) to avoid importing the search
# package from repositories — that cycle broke package import.
FTS_TOKENIZER = "unicode61"

CONCEPT_FTS_TABLE = "concept_fts"
MODULE_FTS_TABLE = "module_fts"

_CREATE_CONCEPT_FTS = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS {CONCEPT_FTS_TABLE} USING fts5(
    concept_id UNINDEXED,
    title,
    aliases,
    domains,
    overview,
    tokenize='{FTS_TOKENIZER}'
)
"""

_CREATE_MODULE_FTS = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS {MODULE_FTS_TABLE} USING fts5(
    module_id UNINDEXED,
    concept_id UNINDEXED,
    title,
    type,
    focus,
    body,
    tokenize='{FTS_TOKENIZER}'
)
"""


def create_fts_tables(connection: Connection) -> None:
    """Create concept and module FTS5 virtual tables if missing."""
    connection.execute(text(_CREATE_CONCEPT_FTS))
    connection.execute(text(_CREATE_MODULE_FTS))


def delete_concept_fts(connection: Connection, concept_id: str) -> None:
    connection.execute(
        text(f"DELETE FROM {CONCEPT_FTS_TABLE} WHERE concept_id = :concept_id"),
        {"concept_id": concept_id},
    )


def delete_module_fts_for_concept(connection: Connection, concept_id: str) -> None:
    connection.execute(
        text(f"DELETE FROM {MODULE_FTS_TABLE} WHERE concept_id = :concept_id"),
        {"concept_id": concept_id},
    )


def delete_all_fts_for_concept(connection: Connection, concept_id: str) -> None:
    """Remove concept + module FTS rows for one concept (two scans max)."""
    delete_concept_fts(connection, concept_id)
    delete_module_fts_for_concept(connection, concept_id)


def insert_concept_fts(
    connection: Connection,
    *,
    concept_id: str,
    title: str,
    aliases: str,
    domains: str,
    overview: str,
) -> None:
    """Insert one concept FTS row. Caller must have deleted any prior row."""
    connection.execute(
        text(
            f"""
            INSERT INTO {CONCEPT_FTS_TABLE}
                (concept_id, title, aliases, domains, overview)
            VALUES
                (:concept_id, :title, :aliases, :domains, :overview)
            """
        ),
        {
            "concept_id": concept_id,
            "title": title,
            "aliases": aliases,
            "domains": domains,
            "overview": overview,
        },
    )


def insert_module_fts(
    connection: Connection,
    *,
    module_id: str,
    concept_id: str,
    title: str,
    module_type: str,
    focus: str,
    body: str,
) -> None:
    """Insert one module FTS row. Caller must have deleted any prior rows."""
    connection.execute(
        text(
            f"""
            INSERT INTO {MODULE_FTS_TABLE}
                (module_id, concept_id, title, type, focus, body)
            VALUES
                (:module_id, :concept_id, :title, :type, :focus, :body)
            """
        ),
        {
            "module_id": module_id,
            "concept_id": concept_id,
            "title": title,
            "type": module_type,
            "focus": focus,
            "body": body,
        },
    )


def sync_concept_projection_fts(
    connection: Connection,
    *,
    concept_id: str,
    title: str,
    aliases: list[str],
    domains: list[str],
    overview: str,
    module_rows: list[dict[str, Any]],
) -> None:
    """Replace FTS rows for one concept and its modules.

    Performs a single concept-scoped delete pair, then inserts. Identifier
    columns are UNINDEXED, so each ``DELETE ... WHERE id = ...`` scans the
    virtual table — avoid per-row deletes during rebuild.
    """
    delete_all_fts_for_concept(connection, concept_id)
    insert_concept_fts(
        connection,
        concept_id=concept_id,
        title=title,
        aliases=" ".join(aliases),
        domains=" ".join(domains),
        overview=overview,
    )
    for module in module_rows:
        insert_module_fts(
            connection,
            module_id=str(module["module_id"]),
            concept_id=concept_id,
            title=str(module["title"]),
            module_type=str(module["type"]),
            focus="" if module.get("focus") is None else str(module["focus"]),
            body="",
        )
