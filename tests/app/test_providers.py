"""Provider routing and privacy-gate tests."""

from __future__ import annotations

import pytest

from studium.app.providers import (
    LocalHashEmbeddingProvider,
    ProviderSettings,
    build_embedding_provider,
    provider_route,
    validate_provider_settings,
)


def test_local_hash_embeddings_are_normalized_and_stable() -> None:
    provider = LocalHashEmbeddingProvider(dimension=32)
    first = provider.embed_query("gradient descent learning rate")
    second = provider.embed_query("gradient descent learning rate")
    assert first == second
    assert len(first) == 32
    assert pytest.approx(sum(value * value for value in first), rel=1e-5) == 1.0


def test_loopback_endpoints_are_local() -> None:
    assert provider_route("http://127.0.0.1:11434/v1") == "local"
    assert provider_route("http://localhost:1234/v1") == "local"
    assert provider_route("https://api.example.com/v1") == "remote"


def test_remote_routing_requires_explicit_permission() -> None:
    with pytest.raises(ValueError, match="Remote model routing"):
        validate_provider_settings(
            ProviderSettings(
                llm_provider="openai_compatible",
                llm_base_url="https://api.example.com/v1",
                remote_data_allowed=False,
            )
        )


def test_local_openai_compatible_routing_is_allowed() -> None:
    settings = validate_provider_settings(
        ProviderSettings(
            llm_provider="openai_compatible",
            llm_base_url="http://127.0.0.1:11434/v1",
            remote_data_allowed=False,
        )
    )
    assert settings.llm_provider == "openai_compatible"
    assert build_embedding_provider(settings).model_metadata().model_id == "studium/local-feature-hash"
