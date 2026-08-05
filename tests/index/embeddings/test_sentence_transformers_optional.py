"""Optional real-model smoke test (requires ``uv sync --extra embeddings``)."""

from __future__ import annotations

import pytest

pytest.importorskip("sentence_transformers")

from studium.index.embeddings.sentence_transformers_provider import (
    SentenceTransformersEmbeddingProvider,
)


@pytest.mark.embedding
def test_sentence_transformers_provider_smoke() -> None:
    provider = SentenceTransformersEmbeddingProvider(
        "sentence-transformers/all-MiniLM-L6-v2",
        batch_size=2,
    )
    meta = provider.model_metadata()
    assert meta.dimension > 0
    vectors = provider.embed_documents(["gradient descent", "neural network"])
    assert len(vectors) == 2
    assert len(vectors[0]) == meta.dimension
    query = provider.embed_query("optimizer")
    assert len(query) == meta.dimension
