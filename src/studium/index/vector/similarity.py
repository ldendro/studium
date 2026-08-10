"""L2 normalization and cosine similarity helpers (scores in [-1, 1])."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray


def l2_normalize_vector(values: list[float] | NDArray[np.floating]) -> NDArray[np.float32]:
    """Return a unit-length float32 vector; zeros stay zeros."""
    arr = np.asarray(values, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(arr))
    if norm == 0.0 or not math.isfinite(norm):
        return arr
    return arr / np.float32(norm)


def l2_normalize_matrix(matrix: NDArray[np.floating]) -> NDArray[np.float32]:
    """Row-wise L2 normalize a 2-D float matrix."""
    mat = np.asarray(matrix, dtype=np.float32)
    if mat.ndim != 2:
        msg = f"Expected 2-D matrix, got shape {mat.shape}"
        raise ValueError(msg)
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    safe = np.where(norms > 0.0, norms, 1.0)
    return mat / safe.astype(np.float32)


def cosine_scores(
    corpus: list[list[float]] | NDArray[np.floating],
    query: list[float] | NDArray[np.floating],
    *,
    corpus_already_normalized: bool = False,
    query_already_normalized: bool = False,
) -> NDArray[np.float32]:
    """Cosine similarity of each corpus row to ``query`` (values in approx [-1, 1])."""
    mat = np.asarray(corpus, dtype=np.float32)
    q = np.asarray(query, dtype=np.float32).reshape(-1)
    if mat.ndim != 2:
        msg = f"Expected 2-D corpus, got shape {mat.shape}"
        raise ValueError(msg)
    if mat.shape[1] != q.shape[0]:
        msg = f"Corpus dim {mat.shape[1]} != query dim {q.shape[0]}"
        raise ValueError(msg)
    if not corpus_already_normalized:
        mat = l2_normalize_matrix(mat)
    if not query_already_normalized:
        q = l2_normalize_vector(q)
    return mat @ q
