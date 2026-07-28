"""Index metadata repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import Connection

from studium.index.repositories._util import mapping
from studium.index.schema import index_metadata


def get_index_metadata(connection: Connection) -> dict[str, Any] | None:
    row = connection.execute(select(index_metadata).order_by(index_metadata.c.id).limit(1)).first()
    return None if row is None else mapping(row)
