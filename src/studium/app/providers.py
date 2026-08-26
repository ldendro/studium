"""Default local providers and user-configurable provider construction."""

from __future__ import annotations

import hashlib
import ipaddress
import math
import os
import re
from dataclasses import dataclass
from itertools import pairwise
from typing import Any
from urllib.parse import urlparse

from studium.index.embeddings.protocol import EmbeddingModelMetadata, EmbeddingProvider
from studium.llm.openai_compat import OpenAICompatibleProvider
from studium.llm.protocol import LLMProvider

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_ENV_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
EMBEDDING_PROVIDERS = ("local_hash", "sentence_transformers")
LLM_PROVIDERS = ("disabled", "openai_compatible")


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
    llm_provider: str = "disabled"
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_model: str = "llama3.2:3b"
    llm_api_key_env: str = "STUDIUM_LLM_API_KEY"
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
        api_key=os.environ.get(settings.llm_api_key_env, "ollama"),
    )


def provider_settings_from_mapping(values: dict[str, Any]) -> ProviderSettings:
    allowed = {key: values[key] for key in ProviderSettings.__dataclass_fields__ if key in values}
    return validate_provider_settings(ProviderSettings(**allowed))


def validate_provider_settings(settings: ProviderSettings) -> ProviderSettings:
    if settings.embedding_provider not in EMBEDDING_PROVIDERS:
        raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
    if settings.llm_provider not in LLM_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    if not settings.embedding_model.strip():
        raise ValueError("Embedding model must not be empty.")
    if not settings.llm_model.strip():
        raise ValueError("LLM model must not be empty.")
    if not _ENV_NAME_RE.fullmatch(settings.llm_api_key_env.strip()):
        raise ValueError("API-key environment variable must be an uppercase shell name.")
    if settings.llm_provider != "disabled":
        parsed = urlparse(settings.llm_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("LLM base URL must be a complete HTTP or HTTPS URL.")
        if parsed.username or parsed.password:
            raise ValueError("Do not place credentials in the LLM base URL.")
        if provider_route(settings.llm_base_url) == "remote" and not settings.remote_data_allowed:
            raise ValueError(
                "Remote model routing requires explicit permission to send note content."
            )
    return settings


def provider_route(base_url: str) -> str:
    hostname = urlparse(base_url).hostname
    if hostname is None:
        return "invalid"
    normalized = hostname.casefold().rstrip(".")
    if normalized == "localhost" or normalized.endswith(".localhost"):
        return "local"
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return "remote"
    return "local" if address.is_loopback else "remote"


def api_key_is_configured(settings: ProviderSettings) -> bool:
    return bool(os.environ.get(settings.llm_api_key_env))
