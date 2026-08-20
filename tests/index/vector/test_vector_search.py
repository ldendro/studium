"""Unit tests for vector similarity and search backends."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.engine import Engine

from studium.index import (
    FakeEmbeddingProvider,
    IndexConfig,
    ModelSpaceFilter,
    NumpyVectorSearchBackend,
    begin_connection,
    create_vector_backend,
    pack_vector,
    search_concept_identity_vectors,
    search_concept_semantic_vectors,
    search_module_semantic_vectors,
    sync_and_embed,
    unpack_vector,
)
from studium.index.repositories import concepts, scaffold_modules
from studium.index.repositories import embeddings as embeddings_repo
from studium.index.vector.similarity import cosine_scores, l2_normalize_vector
from studium.vault import Vault
from tests.index.sync.helpers import write_concept_note


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _upsert_concept(engine: Engine, concept_id: str, title: str) -> None:
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


def _insert_embedding(
    engine: Engine,
    *,
    owner_type: str,
    owner_id: str,
    embedding_type: str,
    vector: list[float],
    model_id: str = "fake-embedding",
    model_revision: str | None = "test",
    normalizes: bool = True,
    parent_concept_id: str | None = None,
    segment_id: str = "",
    dimension: int | None = None,
) -> None:
    dim = len(vector) if dimension is None else dimension
    with begin_connection(engine) as connection:
        embeddings_repo.insert_embedding(
            connection,
            {
                "owner_type": owner_type,
                "owner_id": owner_id,
                "parent_concept_id": parent_concept_id
                or (owner_id if owner_type == "concept" else None),
                "segment_id": segment_id,
                "embedding_type": embedding_type,
                "vector": pack_vector(vector) if dim > 0 else b"",
                "dimension": dim,
                "model_id": model_id,
                "model_revision": model_revision,
                "normalizes_embeddings": normalizes,
                "input_hash": f"hash-{owner_id}-{embedding_type}",
                "created_at": _now(),
                "indexed_revision": 1,
            },
        )


def test_cosine_known_vectors() -> None:
    identical = cosine_scores([[1.0, 0.0]], [1.0, 0.0])
    assert identical[0] == pytest.approx(1.0)
    orthogonal = cosine_scores([[1.0, 0.0]], [0.0, 1.0])
    assert orthogonal[0] == pytest.approx(0.0)
    opposite = cosine_scores([[1.0, 0.0]], [-1.0, 0.0])
    assert opposite[0] == pytest.approx(-1.0)


def test_l2_normalize_zero_vector() -> None:
    out = l2_normalize_vector([0.0, 0.0, 0.0])
    assert out.tolist() == [0.0, 0.0, 0.0]


def test_model_space_filter_rejects_nonpositive_dimension() -> None:
    with pytest.raises(ValueError, match="positive"):
        ModelSpaceFilter(model_id="m", dimension=0)


def test_top_k_order_and_tiebreak(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_a", "Alpha")
    _upsert_concept(initialized_engine, "concept_b", "Beta")
    _upsert_concept(initialized_engine, "concept_c", "Gamma")
    _insert_embedding(
        initialized_engine,
        owner_type="concept",
        owner_id="concept_b",
        embedding_type="concept_identity",
        vector=[1.0, 0.0],
    )
    _insert_embedding(
        initialized_engine,
        owner_type="concept",
        owner_id="concept_a",
        embedding_type="concept_identity",
        vector=[1.0, 0.0],
    )
    _insert_embedding(
        initialized_engine,
        owner_type="concept",
        owner_id="concept_c",
        embedding_type="concept_identity",
        vector=[0.0, 1.0],
    )
    model = ModelSpaceFilter(
        model_id="fake-embedding",
        model_revision="test",
        dimension=2,
        normalizes_embeddings=True,
    )
    hits = search_concept_identity_vectors(initialized_engine, [1.0, 0.0], model, limit=2)
    assert [h.concept_id for h in hits] == ["concept_a", "concept_b"]
    assert hits[0].score == pytest.approx(1.0)
    assert hits[0].rank == 1
    assert hits[0].canonical_title == "Alpha"


def test_model_filter_excludes_mismatched_space(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_ok", "Ok")
    _upsert_concept(initialized_engine, "concept_other", "Other")
    _insert_embedding(
        initialized_engine,
        owner_type="concept",
        owner_id="concept_ok",
        embedding_type="concept_semantic",
        vector=[1.0, 0.0],
        model_id="fake-embedding",
    )
    _insert_embedding(
        initialized_engine,
        owner_type="concept",
        owner_id="concept_other",
        embedding_type="concept_semantic",
        vector=[1.0, 0.0],
        model_id="other-model",
    )
    model = ModelSpaceFilter(
        model_id="fake-embedding",
        model_revision="test",
        dimension=2,
    )
    hits = search_concept_semantic_vectors(initialized_engine, [1.0, 0.0], model)
    assert [h.concept_id for h in hits] == ["concept_ok"]


def test_model_spaces_prefer_corpus_coverage_over_recency(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_covered_a", "Covered A")
    _upsert_concept(initialized_engine, "concept_covered_b", "Covered B")
    for concept_id in ("concept_covered_a", "concept_covered_b"):
        _insert_embedding(
            initialized_engine,
            owner_type="concept",
            owner_id=concept_id,
            embedding_type="concept_identity",
            vector=[1.0, 0.0],
            model_id="complete-model",
        )
    _insert_embedding(
        initialized_engine,
        owner_type="concept",
        owner_id="concept_covered_a",
        embedding_type="concept_semantic",
        vector=[1.0, 0.0],
        model_id="new-partial-model",
    )

    with initialized_engine.connect() as connection:
        spaces = embeddings_repo.list_model_spaces(connection)

    assert spaces[0]["model_id"] == "complete-model"
    assert int(spaces[0]["concept_count"]) == 2


def test_rejection_rows_excluded(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_live", "Live")
    _upsert_concept(initialized_engine, "concept_reject", "Reject")
    _insert_embedding(
        initialized_engine,
        owner_type="concept",
        owner_id="concept_live",
        embedding_type="concept_identity",
        vector=[1.0, 0.0],
    )
    _insert_embedding(
        initialized_engine,
        owner_type="concept",
        owner_id="concept_reject",
        embedding_type="concept_identity",
        vector=[],
        dimension=0,
    )
    model = ModelSpaceFilter(
        model_id="fake-embedding",
        model_revision="test",
        dimension=2,
    )
    hits = search_concept_identity_vectors(initialized_engine, [1.0, 0.0], model)
    assert [h.concept_id for h in hits] == ["concept_live"]


def test_type_isolation(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_x", "X")
    _insert_embedding(
        initialized_engine,
        owner_type="concept",
        owner_id="concept_x",
        embedding_type="concept_semantic",
        vector=[1.0, 0.0],
    )
    model = ModelSpaceFilter(
        model_id="fake-embedding",
        model_revision="test",
        dimension=2,
    )
    assert search_concept_identity_vectors(initialized_engine, [1.0, 0.0], model) == []
    assert len(search_concept_semantic_vectors(initialized_engine, [1.0, 0.0], model)) == 1


def test_module_hits_include_location_fields(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_parent", "Parent")
    with begin_connection(initialized_engine) as connection:
        scaffold_modules.upsert_scaffold_module(
            connection,
            {
                "module_id": "module_one",
                "concept_id": "concept_parent",
                "type": "derivation",
                "title": "Module One",
                "status": "scaffolded",
                "heading": "Update Rule",
                "anchor": "update-rule",
                "indexed_revision": 1,
            },
        )
    _insert_embedding(
        initialized_engine,
        owner_type="scaffold_module",
        owner_id="module_one",
        embedding_type="module_semantic",
        vector=[0.0, 1.0],
        parent_concept_id="concept_parent",
        segment_id="",
    )
    model = ModelSpaceFilter(
        model_id="fake-embedding",
        model_revision="test",
        dimension=2,
    )
    hits = search_module_semantic_vectors(initialized_engine, [0.0, 1.0], model)
    assert len(hits) == 1
    hit = hits[0]
    assert hit.module_id == "module_one"
    assert hit.concept_id == "concept_parent"
    assert hit.parent_canonical_title == "Parent"
    assert hit.module_type == "derivation"
    assert hit.heading == "Update Rule"
    assert hit.anchor == "update-rule"
    assert hit.segment_id == ""


def test_empty_corpus(initialized_engine: Engine) -> None:
    model = ModelSpaceFilter(
        model_id="fake-embedding",
        model_revision="test",
        dimension=2,
    )
    assert search_concept_identity_vectors(initialized_engine, [1.0, 0.0], model) == []


def test_query_dimension_mismatch(initialized_engine: Engine) -> None:
    model = ModelSpaceFilter(
        model_id="fake-embedding",
        model_revision="test",
        dimension=2,
    )
    with pytest.raises(ValueError, match="query_vector length"):
        search_concept_identity_vectors(initialized_engine, [1.0, 0.0, 0.0], model)


def test_create_vector_backend_default_is_numpy(initialized_engine: Engine) -> None:
    backend = create_vector_backend(initialized_engine)
    assert isinstance(backend, NumpyVectorSearchBackend)


def test_fake_end_to_end_search(
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/sgd.md",
        id="concept_sgd_vec001",
        canonical_title="Stochastic Gradient Descent",
        aliases=["SGD"],
        overview="Iterative optimizer.",
    )
    provider = FakeEmbeddingProvider(dimension=8)
    report = sync_and_embed(
        Vault(vault_root),
        initialized_engine,
        index_config,
        provider,
    )
    assert report.embeddings.written >= 2

    meta = provider.model_metadata()
    model = ModelSpaceFilter(
        model_id=meta.model_id,
        model_revision=meta.model_revision,
        dimension=meta.dimension,
        normalizes_embeddings=meta.normalizes_embeddings,
    )
    with begin_connection(initialized_engine) as connection:
        stored = embeddings_repo.get_embedding_for_key(
            connection,
            owner_type="concept",
            owner_id="concept_sgd_vec001",
            embedding_type="concept_identity",
        )
    assert stored is not None
    query = unpack_vector(bytes(stored["vector"]), dimension=meta.dimension)
    hits = search_concept_identity_vectors(initialized_engine, query, model, limit=5)
    assert hits
    assert hits[0].concept_id == "concept_sgd_vec001"
    assert hits[0].score == pytest.approx(1.0, abs=1e-5)
