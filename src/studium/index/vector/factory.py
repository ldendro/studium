"""Construct the configured vector search backend."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from studium.index.config import DEFAULT_VECTOR_BACKEND
from studium.index.vector.numpy_backend import NumpyVectorSearchBackend
from studium.index.vector.protocol import VectorSearchBackend


def create_vector_backend(
    engine: Engine,
    *,
    name: str | None = None,
) -> VectorSearchBackend:
    """Return a vector backend by name (default: ``DEFAULT_VECTOR_BACKEND``)."""
    backend_name = (DEFAULT_VECTOR_BACKEND if name is None else name).strip().lower()
    if backend_name in {"numpy", "exact"}:
        return NumpyVectorSearchBackend(engine)
    if backend_name in {"sqlite_vec", "sqlite-vec", "vec"}:
        from studium.index.vector.sqlite_vec_backend import SqliteVecSearchBackend

        return SqliteVecSearchBackend(engine)
    msg = f"Unknown vector backend {backend_name!r}; expected 'numpy' or 'sqlite_vec'"
    raise ValueError(msg)
