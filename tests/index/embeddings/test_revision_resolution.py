"""Unit tests for Hub revision → commit SHA resolution (no model download)."""

from __future__ import annotations

from typing import Any

from studium.index.embeddings.sentence_transformers_provider import (
    discover_model_revision,
    is_commit_sha,
    resolve_model_revision,
)


def test_is_commit_sha() -> None:
    assert is_commit_sha("abcdef0")
    assert is_commit_sha("a" * 40)
    assert not is_commit_sha("main")
    assert not is_commit_sha("v1.0.0")
    assert not is_commit_sha("")


def test_resolve_mutable_ref_uses_discovered_sha(monkeypatch: Any) -> None:
    def fake_discover(model_id: str, *, revision: str | None = None) -> str | None:
        assert model_id == "org/model"
        assert revision == "main"
        return "deadbeefcafebabe0123456789abcdef01234567"

    monkeypatch.setattr(
        "studium.index.embeddings.sentence_transformers_provider.discover_model_revision",
        fake_discover,
    )
    assert (
        resolve_model_revision("org/model", revision="main")
        == "deadbeefcafebabe0123456789abcdef01234567"
    )


def test_resolve_falls_back_to_sha_when_discovery_fails(monkeypatch: Any) -> None:
    def no_discover(_model_id: str, *, revision: str | None = None) -> str | None:
        _ = revision
        return None

    monkeypatch.setattr(
        "studium.index.embeddings.sentence_transformers_provider.discover_model_revision",
        no_discover,
    )
    sha = "0123456789abcdef0123456789abcdef01234567"
    assert resolve_model_revision("org/model", revision=sha) == sha
    assert resolve_model_revision("org/model", revision="main") is None


def test_discover_passes_revision_to_model_info(monkeypatch: Any) -> None:
    calls: list[tuple[str, str | None]] = []

    def fake_model_info(model_id: str, revision: str | None = None) -> Any:
        calls.append((model_id, revision))

        class _Info:
            sha = "abc1234"

        return _Info()

    import sys
    from types import ModuleType

    hub = ModuleType("huggingface_hub")
    hub.model_info = fake_model_info  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "huggingface_hub", hub)

    assert discover_model_revision("org/model", revision="main") == "abc1234"
    assert calls == [("org/model", "main")]
