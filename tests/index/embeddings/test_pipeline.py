"""Unit tests for embedding serialization, fake provider, and pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Engine

from studium.index import (
    FakeEmbeddingProvider,
    IndexConfig,
    begin_connection,
    embed_query,
    pack_vector,
    process_embedding_work,
    sync_and_embed,
    unpack_vector,
)
from studium.index.repositories import embeddings as embeddings_repo
from studium.index.sync.embedding_inputs import truncate_module_body
from studium.index.sync.models import EmbeddingWorkRequest
from studium.vault import Vault
from tests.index.sync.helpers import write_concept_note


def test_pack_unpack_round_trip() -> None:
    values = [0.0, -1.5, 2.25, 0.125]
    blob = pack_vector(values)
    assert unpack_vector(blob, dimension=4) == pytest.approx(values)


def test_fake_provider_preserves_batch_order() -> None:
    provider = FakeEmbeddingProvider(dimension=4)
    texts = ["alpha", "beta", "gamma"]
    vectors = provider.embed_documents(texts)
    assert len(vectors) == 3
    assert provider.documents_calls == [texts]
    # Distinct inputs → distinct vectors
    assert vectors[0] != vectors[1]
    query = embed_query(provider, "alpha")
    assert query == vectors[0]


def test_truncate_module_body() -> None:
    assert truncate_module_body("abc", max_chars=10) == "abc"
    assert truncate_module_body("abcdefghij", max_chars=4) == "abcd"


def test_process_embedding_work_writes_and_skips(
    initialized_engine: Engine,
) -> None:
    provider = FakeEmbeddingProvider(dimension=4)
    work = [
        EmbeddingWorkRequest(
            owner_type="concept",
            owner_id="concept_a",
            embedding_type="concept_identity",
            input_hash="hash-a",
            input_text="Title: A\nAliases: ",
            parent_concept_id="concept_a",
        )
    ]
    # Need a concept row for FK parent_concept_id
    with begin_connection(initialized_engine) as connection:
        from studium.index.repositories import concepts

        concepts.upsert_concept(
            connection,
            {
                "concept_id": "concept_a",
                "canonical_title": "A",
                "concept_type": "atomic_concept",
                "status": "active",
                "review_status": "draft",
                "vault_status": "active",
                "file_path": "concepts/a.md",
                "note_schema_version": 2,
                "validity_state": "valid",
                "indexed_revision": 1,
                "note_created_at": "2026-01-01T00:00:00Z",
                "note_updated_at": "2026-01-01T00:00:00Z",
            },
        )

    first = process_embedding_work(
        initialized_engine, work, provider, indexed_revision=1, batch_size=8
    )
    assert first.requested == 1
    assert first.embedded == 1
    assert first.written == 1
    assert first.skipped == 0
    assert len(provider.documents_calls) == 1

    second = process_embedding_work(
        initialized_engine, work, provider, indexed_revision=1, batch_size=8
    )
    assert second.skipped == 1
    assert second.embedded == 0
    assert second.written == 0
    assert len(provider.documents_calls) == 1

    with begin_connection(initialized_engine) as connection:
        row = embeddings_repo.get_embedding_for_key(
            connection,
            owner_type="concept",
            owner_id="concept_a",
            embedding_type="concept_identity",
            segment_id=None,
        )
    assert row is not None
    assert row["model_id"] == "fake-embedding"
    assert int(row["dimension"]) == 4
    assert unpack_vector(bytes(row["vector"]), dimension=4)


def test_model_change_regenerates(
    initialized_engine: Engine,
) -> None:
    with begin_connection(initialized_engine) as connection:
        from studium.index.repositories import concepts

        concepts.upsert_concept(
            connection,
            {
                "concept_id": "concept_b",
                "canonical_title": "B",
                "concept_type": "atomic_concept",
                "status": "active",
                "review_status": "draft",
                "vault_status": "active",
                "file_path": "concepts/b.md",
                "note_schema_version": 2,
                "validity_state": "valid",
                "indexed_revision": 1,
                "note_created_at": "2026-01-01T00:00:00Z",
                "note_updated_at": "2026-01-01T00:00:00Z",
            },
        )

    work = [
        EmbeddingWorkRequest(
            owner_type="concept",
            owner_id="concept_b",
            embedding_type="concept_semantic",
            input_hash="hash-b",
            input_text="Title: B\nAliases: \nConcept Type: atomic_concept\nDomains: \nOverview: ",
            parent_concept_id="concept_b",
        )
    ]
    process_embedding_work(
        initialized_engine,
        work,
        FakeEmbeddingProvider(dimension=4, model_id="model-v1"),
        indexed_revision=1,
    )
    process_embedding_work(
        initialized_engine,
        work,
        FakeEmbeddingProvider(dimension=4, model_id="model-v2"),
        indexed_revision=2,
    )
    with begin_connection(initialized_engine) as connection:
        row = embeddings_repo.get_embedding_for_key(
            connection,
            owner_type="concept",
            owner_id="concept_b",
            embedding_type="concept_semantic",
        )
    assert row is not None
    assert row["model_id"] == "model-v2"
    assert int(row["indexed_revision"]) == 2


def test_sync_and_embed_with_fake(
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/sgd.md",
        id="concept_sgd_aaaaaa",
        canonical_title="Stochastic Gradient Descent",
        overview="An iterative optimizer.",
    )
    report = sync_and_embed(
        Vault(vault_root),
        initialized_engine,
        index_config,
        FakeEmbeddingProvider(dimension=8),
    )
    assert report.sync.embedding_work
    assert report.embeddings.written >= 2
    with begin_connection(initialized_engine) as connection:
        rows = embeddings_repo.list_embeddings_for_owner(
            connection, owner_type="concept", owner_id="concept_sgd_aaaaaa"
        )
    assert len(rows) >= 2
