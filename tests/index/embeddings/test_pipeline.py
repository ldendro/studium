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
    enumerate_embedding_work,
    merge_embedding_work,
    pack_vector,
    process_embedding_work,
    sync_and_embed,
    sync_vault,
    unpack_vector,
)
from studium.index.repositories import embeddings as embeddings_repo
from studium.index.sync.embedding_inputs import truncate_module_body
from studium.index.sync.models import EmbeddingWorkRequest
from studium.vault import Vault
from tests.index.sync.helpers import write_concept_note

_MODULES_ONE = (
    "scaffold_modules:\n"
    "  - id: module_sgd_update\n"
    "    type: derivation\n"
    "    title: Update Rule\n"
    "    status: scaffolded\n"
    "    origin:\n"
    "    focus: gradient step\n"
)


def _upsert_minimal_concept(engine: Engine, concept_id: str, title: str = "A") -> None:
    from studium.index.repositories import concepts

    with begin_connection(engine) as connection:
        concepts.upsert_concept(
            connection,
            {
                "concept_id": concept_id,
                "canonical_title": title,
                "concept_type": "atomic_concept",
                "status": "active",
                "review_status": "draft",
                "vault_status": "active",
                "file_path": f"concepts/{concept_id}.md",
                "note_schema_version": 2,
                "validity_state": "valid",
                "indexed_revision": 1,
                "note_created_at": "2026-01-01T00:00:00Z",
                "note_updated_at": "2026-01-01T00:00:00Z",
            },
        )


def test_dimension_mismatch_fails_without_reembed_loop(
    initialized_engine: Engine,
) -> None:
    from studium.index.embeddings.protocol import EmbeddingModelMetadata

    class WrongDimProvider:
        def __init__(self) -> None:
            self.documents_calls: list[list[str]] = []

        def model_metadata(self) -> EmbeddingModelMetadata:
            return EmbeddingModelMetadata(
                model_id="wrong-dim",
                model_revision="test",
                dimension=4,
                normalizes_embeddings=True,
            )

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            self.documents_calls.append(list(texts))
            return [[0.1, 0.2] for _ in texts]  # dim 2, not 4

        def embed_query(self, text: str) -> list[float]:
            return self.embed_documents([text])[0]

    _upsert_minimal_concept(initialized_engine, "concept_dim", title="Dim")
    work = [
        EmbeddingWorkRequest(
            owner_type="concept",
            owner_id="concept_dim",
            embedding_type="concept_identity",
            input_hash="hash-dim",
            input_text="Title: Dim\nAliases: ",
            parent_concept_id="concept_dim",
        )
    ]
    provider = WrongDimProvider()
    first = process_embedding_work(initialized_engine, work, provider, indexed_revision=1)
    assert first.failed == 1
    assert first.embedded == 0
    assert first.written == 0
    assert first.errors
    assert len(provider.documents_calls) == 1

    second = process_embedding_work(initialized_engine, work, provider, indexed_revision=2)
    assert second.skipped == 1
    assert second.failed == 0
    assert second.embedded == 0
    assert len(provider.documents_calls) == 1


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
    _upsert_minimal_concept(initialized_engine, "concept_a")

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
    assert bool(row["normalizes_embeddings"]) is True
    assert int(row["dimension"]) == 4
    assert unpack_vector(bytes(row["vector"]), dimension=4)


def test_model_change_regenerates(initialized_engine: Engine) -> None:
    _upsert_minimal_concept(initialized_engine, "concept_b", title="B")
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


def test_normalize_flag_change_regenerates(initialized_engine: Engine) -> None:
    _upsert_minimal_concept(initialized_engine, "concept_norm", title="Norm")
    work = [
        EmbeddingWorkRequest(
            owner_type="concept",
            owner_id="concept_norm",
            embedding_type="concept_identity",
            input_hash="hash-norm",
            input_text="Title: Norm\nAliases: ",
            parent_concept_id="concept_norm",
        )
    ]
    process_embedding_work(
        initialized_engine,
        work,
        FakeEmbeddingProvider(dimension=4, normalizes_embeddings=True),
        indexed_revision=1,
    )
    report = process_embedding_work(
        initialized_engine,
        work,
        FakeEmbeddingProvider(dimension=4, normalizes_embeddings=False),
        indexed_revision=2,
    )
    assert report.skipped == 0
    assert report.written == 1
    with begin_connection(initialized_engine) as connection:
        row = embeddings_repo.get_embedding_for_key(
            connection,
            owner_type="concept",
            owner_id="concept_norm",
            embedding_type="concept_identity",
        )
    assert row is not None
    assert bool(row["normalizes_embeddings"]) is False


def test_model_revision_change_regenerates(initialized_engine: Engine) -> None:
    _upsert_minimal_concept(initialized_engine, "concept_rev", title="Rev")
    work = [
        EmbeddingWorkRequest(
            owner_type="concept",
            owner_id="concept_rev",
            embedding_type="concept_identity",
            input_hash="hash-rev",
            input_text="Title: Rev\nAliases: ",
            parent_concept_id="concept_rev",
        )
    ]
    process_embedding_work(
        initialized_engine,
        work,
        FakeEmbeddingProvider(dimension=4, model_revision="aaa"),
        indexed_revision=1,
    )
    report = process_embedding_work(
        initialized_engine,
        work,
        FakeEmbeddingProvider(dimension=4, model_revision="bbb"),
        indexed_revision=2,
    )
    assert report.written == 1
    with begin_connection(initialized_engine) as connection:
        row = embeddings_repo.get_embedding_for_key(
            connection,
            owner_type="concept",
            owner_id="concept_rev",
            embedding_type="concept_identity",
        )
    assert row is not None
    assert row["model_revision"] == "bbb"


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


def test_sync_and_embed_repairs_missing_when_vault_unchanged(
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/repair.md",
        id="concept_repair_bbbbbb",
        canonical_title="Repair Target",
        overview="Needs embeddings.",
    )
    vault = Vault(vault_root)
    first = sync_and_embed(
        vault, initialized_engine, index_config, FakeEmbeddingProvider(dimension=4)
    )
    assert first.embeddings.written >= 2

    with begin_connection(initialized_engine) as connection:
        for row in embeddings_repo.list_embeddings_for_owner(
            connection, owner_type="concept", owner_id="concept_repair_bbbbbb"
        ):
            embeddings_repo.delete_embedding(connection, int(row["id"]))

    second = sync_and_embed(
        vault, initialized_engine, index_config, FakeEmbeddingProvider(dimension=4)
    )
    assert second.sync.embedding_work == []
    assert second.embeddings.written >= 2


def test_enumerate_embedding_work_covers_modules(
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/mod.md",
        id="concept_mod_cccccc",
        canonical_title="Module Host",
        modules_yaml=_MODULES_ONE,
    )
    sync_vault(Vault(vault_root), initialized_engine, index_config)
    work = enumerate_embedding_work(initialized_engine)
    types = {(item.owner_type, item.embedding_type, item.owner_id) for item in work}
    assert ("concept", "concept_identity", "concept_mod_cccccc") in types
    assert ("concept", "concept_semantic", "concept_mod_cccccc") in types
    assert ("scaffold_module", "module_semantic", "module_sgd_update") in types


def test_removed_module_embedding_is_pruned(
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/prune.md",
        id="concept_prune_dddddd",
        canonical_title="Prune Host",
        modules_yaml=_MODULES_ONE,
    )
    vault = Vault(vault_root)
    sync_and_embed(vault, initialized_engine, index_config, FakeEmbeddingProvider(dimension=4))
    with begin_connection(initialized_engine) as connection:
        before = embeddings_repo.get_embedding_for_key(
            connection,
            owner_type="scaffold_module",
            owner_id="module_sgd_update",
            embedding_type="module_semantic",
            segment_id="module_sgd_update:0",
        )
    assert before is not None

    write_concept_note(
        vault_root,
        "concepts/prune.md",
        id="concept_prune_dddddd",
        canonical_title="Prune Host",
        modules_yaml="scaffold_modules: []\n",
    )
    sync_vault(vault, initialized_engine, index_config)
    with begin_connection(initialized_engine) as connection:
        after = embeddings_repo.get_embedding_for_key(
            connection,
            owner_type="scaffold_module",
            owner_id="module_sgd_update",
            embedding_type="module_semantic",
            segment_id="module_sgd_update:0",
        )
        orphans = embeddings_repo.list_module_embeddings_for_parent(
            connection, parent_concept_id="concept_prune_dddddd"
        )
    assert after is None
    assert orphans == []


def test_sync_and_enumerate_agree_on_deduped_aliases(
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    path = write_concept_note(
        vault_root,
        "concepts/alias.md",
        id="concept_alias_eeeeee",
        canonical_title="Alias Host",
    )
    note_path = vault_root / path
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(
        text.replace("aliases: []", "aliases:\n  - foo-bar\n  - foo_bar"),
        encoding="utf-8",
    )
    vault = Vault(vault_root)
    sync_report = sync_vault(vault, initialized_engine, index_config)
    sync_identity = next(
        item for item in sync_report.embedding_work if item.embedding_type == "concept_identity"
    )
    enumerated = enumerate_embedding_work(initialized_engine)
    enum_identity = next(
        item
        for item in enumerated
        if item.owner_id == "concept_alias_eeeeee" and item.embedding_type == "concept_identity"
    )
    assert sync_identity.input_text == enum_identity.input_text
    assert sync_identity.input_hash == enum_identity.input_hash
    assert "foo-bar" in sync_identity.input_text
    assert "foo_bar" not in sync_identity.input_text

    merged = merge_embedding_work(enumerated, sync_report.embedding_work)
    merged_identity = next(
        item
        for item in merged
        if item.owner_id == "concept_alias_eeeeee" and item.embedding_type == "concept_identity"
    )
    assert merged_identity.input_hash == sync_identity.input_hash


def test_sync_and_embed_skips_on_failed_sync(
    vault_root: Path,
    tmp_path: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/ok.md",
        id="concept_ok_ffffff",
        canonical_title="Already Indexed",
    )
    vault = Vault(vault_root)
    sync_and_embed(vault, initialized_engine, index_config, FakeEmbeddingProvider(dimension=4))

    other_root = tmp_path / "other_vault"
    other_root.mkdir()
    provider = FakeEmbeddingProvider(dimension=4)
    report = sync_and_embed(
        Vault(other_root),
        initialized_engine,
        index_config,
        provider,
    )
    assert report.sync.status.value == "failed"
    assert report.embeddings.requested == 0
    assert report.embeddings.written == 0
    assert provider.documents_calls == []
