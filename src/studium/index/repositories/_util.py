"""Repository helpers shared across index repositories."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from sqlalchemy.engine import CursorResult, Row

from studium.index.errors import IndexIntegrityError


def mapping(row: Row[Any]) -> dict[str, Any]:
    """Convert a SQLAlchemy row to a plain dict."""
    row_mapping = cast(Mapping[str, Any], cast(Any, row)._mapping)
    return dict(row_mapping)


def inserted_int_pk(result: CursorResult[Any]) -> int:
    """Return the integer primary key from an insert result."""
    primary_key = result.inserted_primary_key
    if primary_key is None or primary_key[0] is None:
        msg = "Insert did not return a primary key"
        raise IndexIntegrityError(msg)
    return int(primary_key[0])
