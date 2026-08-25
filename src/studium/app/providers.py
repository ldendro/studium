"""Default local providers and user-configurable provider construction."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from studium.index.embeddings.protocol import EmbeddingModelMetadata, EmbeddingProvider
from studium.llm.openai_compat import OpenAICompatibleProvider
from studium.llm.protocol import LLMProvider

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class LocalHashEmbeddingProvider:
    """Dependency-free feature-hashing embeddings for an always-available baseline.

    This is intentionally modest but useful: shared words and word bigrams map to
    shared dimensions, unlike opaque whole-document hashes. Users can select a
    sentence-transformer provider for stronger semantic retrieval.
    """

    def __init__(self, *, dimension: int = 384) -> None:
        self._dimension = dimension

    def model_metadata(self) -> EmbeddingModelMetadata:
        return EmbeddingModelMetadata(
            model_id="studium/local-feature-hash",
            model_revision="1",
            dimension=self._dimension,
            normalizes_embeddings=True,
            batch_size_hint=64,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        tokens = _TOKEN_RE.findall(text.casefold())
        features = [*tokens, *(f"{a}_{b}" for a, b in pairwise(tokens))]
        values = [0.0] * self._dimension
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            values[bucket] += sign
        norm = math.sqrt(sum(value * value for value in values))
        return values if norm == 0.0 else [value / norm for value in values]


@dataclass(frozen=True, slots=True)
class ProviderSettings:
    embedding_provider: str = "local_hash"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_provider: str = "local_openai"
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_model: str = "llama3.2:3b"
    remote_data_allowed: bool = False


def build_embedding_provider(settings: ProviderSettings) -> EmbeddingProvider:
    if settings.embedding_provider == "sentence_transformers":
        from studium.index.embeddings.sentence_transformers_provider import (
            SentenceTransformersEmbeddingProvider,
        )

        return SentenceTransformersEmbeddingProvider(model_id=settings.embedding_model)
    return LocalHashEmbeddingProvider()


def build_llm_provider(settings: ProviderSettings) -> LLMProvider | None:
    if settings.llm_provider == "disabled":
        return None
    return OpenAICompatibleProvider(
        base_url=settings.llm_base_url,
        model_id=settings.llm_model,
    )


def provider_settings_from_mapping(values: dict[str, Any]) -> ProviderSettings:
    allowed = {
        key: values[key]
        for key in ProviderSettings.__dataclass_fields__
        if key in values
    }
    return ProviderSettings(**allowed)
