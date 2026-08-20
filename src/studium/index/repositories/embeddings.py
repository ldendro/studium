"""Embeddings repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.engine import Connection

from studium.index.repositories._util import inserted_int_pk, mapping
from studium.index.schema import embeddings


def _normalize_segment_id(segment_id: str | None) -> str:
    return "" if segment_id is None else segment_id


def insert_embedding(connection: Connection, values: dict[str, Any]) -> int:
    payload = dict(values)
    raw_segment = payload.get("segment_id")
    payload["segment_id"] = _normalize_segment_id(None if raw_segment is None else str(raw_segment))
    result = connection.execute(embeddings.insert().values(**payload))
    return inserted_int_pk(result)


def get_embedding(connection: Connection, embedding_id: int) -> dict[str, Any] | None:
    row = connection.execute(select(embeddings).where(embeddings.c.id == embedding_id)).first()
    return None if row is None else mapping(row)


def get_embedding_for_key(
    connection: Connection,
    *,
    owner_type: str,
    owner_id: str,
    embedding_type: str,
    segment_id: str | None = None,
) -> dict[str, Any] | None:
    segment = _normalize_segment_id(segment_id)
    row = connection.execute(
        select(embeddings).where(
            embeddings.c.owner_type == owner_type,
            embeddings.c.owner_id == owner_id,
            embeddings.c.embedding_type == embedding_type,
            embeddings.c.segment_id == segment,
        )
    ).first()
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


def list_module_embeddings_for_parent(
    connection: Connection, *, parent_concept_id: str
) -> list[dict[str, Any]]:
    rows = connection.execute(
        select(embeddings)
        .where(
            embeddings.c.parent_concept_id == parent_concept_id,
            embeddings.c.owner_type == "scaffold_module",
            embeddings.c.embedding_type == "module_semantic",
        )
        .order_by(embeddings.c.id)
    ).all()
    return [mapping(row) for row in rows]


def list_embeddings_for_search(
    connection: Connection,
    *,
    owner_type: str,
    embedding_type: str,
    model_id: str,
    dimension: int,
    model_revision: str | None = None,
    normalizes_embeddings: bool = True,
) -> list[dict[str, Any]]:
    """Load searchable embedding rows for one type in a single model space.

    Excludes B05 rejection sentinels (``dimension == 0``) and rows outside the
    requested ``(model_id, model_revision, dimension, normalizes_embeddings)``.
    """
    if dimension <= 0:
        return []
    conditions = [
        embeddings.c.owner_type == owner_type,
        embeddings.c.embedding_type == embedding_type,
        embeddings.c.model_id == model_id,
        embeddings.c.dimension == dimension,
        embeddings.c.dimension > 0,
        embeddings.c.normalizes_embeddings == normalizes_embeddings,
    ]
    if model_revision is None:
        conditions.append(embeddings.c.model_revision.is_(None))
    else:
        conditions.append(embeddings.c.model_revision == model_revision)
    rows = connection.execute(
        select(embeddings)
        .where(*conditions)
        .order_by(embeddings.c.owner_id, embeddings.c.segment_id)
    ).all()
    return [mapping(row) for row in rows]


def list_model_spaces(connection: Connection) -> list[dict[str, Any]]:
    """Return searchable model spaces, newest embedding generation first."""
    rows = connection.execute(
        select(
            embeddings.c.model_id,
            embeddings.c.model_revision,
            embeddings.c.dimension,
            embeddings.c.normalizes_embeddings,
            func.max(embeddings.c.created_at).label("created_at"),
            func.max(embeddings.c.indexed_revision).label("indexed_revision"),
        )
        .where(embeddings.c.dimension > 0)
        .group_by(
            embeddings.c.model_id,
            embeddings.c.model_revision,
            embeddings.c.dimension,
            embeddings.c.normalizes_embeddings,
        )
        .order_by(func.max(embeddings.c.created_at).desc(), embeddings.c.model_id)
    ).all()
    return [mapping(row) for row in rows]


def delete_embedding(connection: Connection, embedding_id: int) -> None:
    connection.execute(delete(embeddings).where(embeddings.c.id == embedding_id))


def delete_embedding_for_key(
    connection: Connection,
    *,
    owner_type: str,
    owner_id: str,
    embedding_type: str,
    segment_id: str | None = None,
) -> None:
    segment = _normalize_segment_id(segment_id)
    connection.execute(
        delete(embeddings).where(
            embeddings.c.owner_type == owner_type,
            embeddings.c.owner_id == owner_id,
            embeddings.c.embedding_type == embedding_type,
            embeddings.c.segment_id == segment,
        )
    )


def delete_stale_module_embeddings(
    connection: Connection,
    *,
    parent_concept_id: str,
    live_module_ids: set[str],
) -> int:
    """Delete module_semantic rows for ``parent_concept_id`` whose owner is not live."""
    deleted = 0
    for row in list_module_embeddings_for_parent(connection, parent_concept_id=parent_concept_id):
        owner_id = str(row["owner_id"])
        if owner_id in live_module_ids:
            continue
        delete_embedding(connection, int(row["id"]))
        deleted += 1
    return deleted


def upsert_embedding(connection: Connection, values: dict[str, Any]) -> int:
    """Replace the row for (owner, type, segment) and insert ``values``."""
    owner_type = str(values["owner_type"])
    owner_id = str(values["owner_id"])
    embedding_type = str(values["embedding_type"])
    segment_id = values.get("segment_id")
    delete_embedding_for_key(
        connection,
        owner_type=owner_type,
        owner_id=owner_id,
        embedding_type=embedding_type,
        segment_id=None if segment_id is None else str(segment_id),
    )
    return insert_embedding(connection, values)
