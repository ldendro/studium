"""Tests for reciprocal rank fusion and hybrid concept search."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.engine import Engine

from studium.index import (
    ConceptSearchFilters,
    ConceptSearchQuery,
    FakeEmbeddingProvider,
    HybridSearchOptions,
    IndexConfig,
    ModelSpaceFilter,
    ResolutionState,
    SearchStatus,
    begin_connection,
    pack_vector,
    search_concepts,
    sync_and_embed,
)
from studium.index.repositories import concepts
from studium.index.repositories import embeddings as embeddings_repo
from studium.index.search.models import ConceptSearchLimits
from studium.index.search.rrf import fuse_ranked_lists, reciprocal_rank_score
from studium.vault import Vault
from tests.index.sync.helpers import write_concept_note


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def test_reciprocal_rank_score() -> None:
    assert reciprocal_rank_score(1, constant=60.0, weight=1.0) == pytest.approx(1.0 / 61.0)
    with pytest.raises(ValueError):
        reciprocal_rank_score(0, constant=60.0)


def test_fuse_ranked_lists_order() -> None:
    fused = fuse_ranked_lists(
        {
            "fts": {"a": 1, "b": 2},
            "semantic_vector": {"b": 1, "c": 2},
        },
        channel_weights={"fts": 1.0, "semantic_vector": 1.0},
        constant=60.0,
    )
    ids = [item[0] for item in fused]
    assert ids[0] == "b"  # appears in both channels
    assert set(ids) == {"a", "b", "c"}


def _upsert_concept(engine: Engine, concept_id: str, title: str, **extra: object) -> None:
    payload = {
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
        **extra,
    }
    with begin_connection(engine) as connection:
        concepts.upsert_concept(connection, payload)


def test_tier0_exact_match(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_exact_aaaaaa", "Exact Title")
    result = search_concepts(initialized_engine, "Exact Title", options=HybridSearchOptions())
    assert result.resolution_state == ResolutionState.EXACT_MATCH
    assert result.search_status == SearchStatus.COMPLETE
    assert result.exact_matches[0].concept_id == "concept_exact_aaaaaa"
    assert result.ranked_concepts[0].concept_id == "concept_exact_aaaaaa"
    assert result.diagnostics == {}


def test_tier0_exact_match_honors_zero_concept_limit(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_exact_zero", "Exact Zero")
    result = search_concepts(
        initialized_engine,
        ConceptSearchQuery(
            text="Exact Zero",
            limits=ConceptSearchLimits(concepts=0),
        ),
    )

    assert result.resolution_state == ResolutionState.EXACT_MATCH
    assert result.exact_matches[0].concept_id == "concept_exact_zero"
    assert result.ranked_concepts == []


def test_tier1_fts_only_partial(
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/sgd.md",
        id="concept_sgd_hybrid1",
        canonical_title="Stochastic Gradient Descent",
        overview="An iterative optimizer for machine learning.",
    )
    from studium.index import sync_vault

    sync_vault(Vault(vault_root), initialized_engine, index_config)
    result = search_concepts(
        initialized_engine,
        ConceptSearchQuery(text="iterative optimizer", include_diagnostics=True),
    )
    assert result.resolution_state in {
        ResolutionState.RELATED_RESULTS,
        ResolutionState.NO_RESULTS,
    }
    assert result.search_status == SearchStatus.PARTIAL
    assert any("Vector channels skipped" in w for w in result.warnings)


def test_tier1_with_fake_embeddings(
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/sgd.md",
        id="concept_sgd_hybrid2",
        canonical_title="Stochastic Gradient Descent",
        aliases=["SGD"],
        overview="An iterative optimizer.",
    )
    provider = FakeEmbeddingProvider(dimension=8)
    sync_and_embed(Vault(vault_root), initialized_engine, index_config, provider)
    meta = provider.model_metadata()
    model = ModelSpaceFilter(
        model_id=meta.model_id,
        model_revision=meta.model_revision,
        dimension=meta.dimension,
        normalizes_embeddings=meta.normalizes_embeddings,
    )
    result = search_concepts(
        initialized_engine,
        ConceptSearchQuery(text="gradient descent optimizer", include_diagnostics=True),
        options=HybridSearchOptions(embedding_provider=provider, model_filter=model),
    )
    assert result.search_status == SearchStatus.COMPLETE
    assert result.diagnostics.get("vector_channels") == "ok"
    assert result.ranked_concepts
    assert any(c.concept_id == "concept_sgd_hybrid2" for c in result.ranked_concepts)


def test_filter_by_concept_type(initialized_engine: Engine) -> None:
    _upsert_concept(
        initialized_engine,
        "concept_atom_bbbbbb",
        "Atomic Thing",
        concept_type="atomic_concept",
    )
    _upsert_concept(
        initialized_engine,
        "concept_comp_cccccc",
        "Composite Thing",
        concept_type="composite_concept",
    )
    with begin_connection(initialized_engine) as connection:
        for concept_id, vector in (
            ("concept_atom_bbbbbb", [1.0, 0.0]),
            ("concept_comp_cccccc", [0.9, 0.1]),
        ):
            embeddings_repo.insert_embedding(
                connection,
                {
                    "owner_type": "concept",
                    "owner_id": concept_id,
                    "parent_concept_id": concept_id,
                    "segment_id": "",
                    "embedding_type": "concept_semantic",
                    "vector": pack_vector(vector),
                    "dimension": 2,
                    "model_id": "fake-embedding",
                    "model_revision": "test",
                    "normalizes_embeddings": True,
                    "input_hash": f"h-{concept_id}",
                    "created_at": _now(),
                    "indexed_revision": 1,
                },
            )
            embeddings_repo.insert_embedding(
                connection,
                {
                    "owner_type": "concept",
                    "owner_id": concept_id,
                    "parent_concept_id": concept_id,
                    "segment_id": "",
                    "embedding_type": "concept_identity",
                    "vector": pack_vector(vector),
                    "dimension": 2,
                    "model_id": "fake-embedding",
                    "model_revision": "test",
                    "normalizes_embeddings": True,
                    "input_hash": f"hi-{concept_id}",
                    "created_at": _now(),
                    "indexed_revision": 1,
                },
            )
    model = ModelSpaceFilter(
        model_id="fake-embedding",
        model_revision="test",
        dimension=2,
    )
    result = search_concepts(
        initialized_engine,
        ConceptSearchQuery(
            text="Thing",
            filters=ConceptSearchFilters(concept_types=["atomic_concept"]),
        ),
        options=HybridSearchOptions(
            query_identity_vector=[1.0, 0.0],
            query_semantic_vector=[1.0, 0.0],
            model_filter=model,
        ),
    )
    assert all(c.concept_type == "atomic_concept" for c in result.ranked_concepts)


def test_filtered_channels_incrementally_overfetch_with_a_fixed_cap(
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    for index in range(1, 10):
        write_concept_note(
            vault_root,
            f"concepts/{index}.md",
            id=f"concept_filter_{index:06d}",
            canonical_title=f"Filter Candidate {index}",
            concept_type=("algorithm" if index == 9 else "general_concept"),
            overview="boundedfilterterm",
        )
    from studium.index import sync_vault

    sync_vault(Vault(vault_root), initialized_engine, index_config)
    result = search_concepts(
        initialized_engine,
        ConceptSearchQuery(
            text="boundedfilterterm",
            filters=ConceptSearchFilters(concept_types=["algorithm"]),
            limits=ConceptSearchLimits(channel=2),
            include_modules=False,
            include_diagnostics=True,
        ),
    )

    assert [candidate.concept_id for candidate in result.ranked_concepts] == [
        "concept_filter_000009"
    ]
    assert "filter_overfetch_capped" not in result.diagnostics


def test_empty_query_no_crash(initialized_engine: Engine) -> None:
    result = search_concepts(initialized_engine, "zzzz-nonexistent-query-xyz")
    assert result.resolution_state == ResolutionState.NO_RESULTS
