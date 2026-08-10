"""Optional sqlite-vec backend contract tests (marker: vector_ext)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.engine import Engine

from studium.index import (
    ModelSpaceFilter,
    begin_connection,
    create_vector_backend,
    pack_vector,
    search_concept_identity_vectors,
)
from studium.index.repositories import concepts
from studium.index.repositories import embeddings as embeddings_repo

pytestmark = pytest.mark.vector_ext


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def test_sqlite_vec_agrees_with_numpy(initialized_engine: Engine) -> None:
    with begin_connection(initialized_engine) as connection:
        for concept_id, title, vector in (
            ("concept_a", "A", [1.0, 0.0]),
            ("concept_b", "B", [0.0, 1.0]),
            ("concept_c", "C", [0.7071, 0.7071]),
        ):
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
                    "input_hash": f"hash-{concept_id}",
                    "created_at": _now(),
                    "indexed_revision": 1,
                },
            )

    model = ModelSpaceFilter(
        model_id="fake-embedding",
        model_revision="test",
        dimension=2,
    )
    query = [1.0, 0.0]
    numpy_hits = search_concept_identity_vectors(
        initialized_engine,
        query,
        model,
        backend=create_vector_backend(initialized_engine, name="numpy"),
    )
    vec_hits = search_concept_identity_vectors(
        initialized_engine,
        query,
        model,
        backend=create_vector_backend(initialized_engine, name="sqlite_vec"),
    )
    assert [h.concept_id for h in numpy_hits] == [h.concept_id for h in vec_hits]
    for left, right in zip(numpy_hits, vec_hits, strict=True):
        assert left.score == pytest.approx(right.score, abs=1e-5)
