"""Deterministic fake embedding provider for unit tests."""

from __future__ import annotations

import hashlib
import math

from studium.index.embeddings.protocol import EmbeddingModelMetadata


class FakeEmbeddingProvider:
    """Hash-based deterministic vectors; no ML dependencies."""

    def __init__(
        self,
        *,
        dimension: int = 8,
        model_id: str = "fake-embedding",
        model_revision: str | None = "test",
        normalizes_embeddings: bool = True,
    ) -> None:
        if dimension <= 0:
            msg = "dimension must be positive"
            raise ValueError(msg)
        self._dimension = dimension
        self._model_id = model_id
        self._model_revision = model_revision
        self._normalizes = normalizes_embeddings
        self.documents_calls: list[list[str]] = []
        self.query_calls: list[str] = []

    def model_metadata(self) -> EmbeddingModelMetadata:
        return EmbeddingModelMetadata(
            model_id=self._model_id,
            model_revision=self._model_revision,
            dimension=self._dimension,
            normalizes_embeddings=self._normalizes,
            max_input_chars=None,
            batch_size_hint=32,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.documents_calls.append(list(texts))
        return [self._embed_one(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        self.query_calls.append(text)
        return self._embed_one(text)

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        while len(values) < self._dimension:
            for byte in digest:
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) >= self._dimension:
                    break
            digest = hashlib.sha256(digest).digest()
        if self._normalizes:
            return _l2_normalize(values)
        return values


def _l2_normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0.0:
        return values
    return [value / norm for value in values]
