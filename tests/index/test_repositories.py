"""Repository CRUD, foreign-key, cascade, and transaction tests."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError

from studium.index import begin_connection
from studium.index.repositories import (
    aliases,
    concepts,
    domains,
    embeddings,
    indexed_files,
    invalid_records,
    learning_encounters,
    relationships,
    scaffold_modules,
    search_documents,
)


def _sample_concept(concept_id: str = "concept_sgd_a1b2c3") -> dict[str, object]:
    return {
        "concept_id": concept_id,
        "canonical_title": "Stochastic Gradient Descent",
        "concept_type": "algorithm",
        "status": "scaffolded",
        "review_status": "not_submitted",
        "vault_status": "draft",
        "file_path": "concepts/stochastic-gradient-descent.md",
        "note_schema_version": 2,
        "validity_state": "valid",
        "indexed_revision": 1,
    }


def test_concept_crud_round_trip(initialized_engine: Engine) -> None:
    with begin_connection(initialized_engine) as connection:
        concepts.upsert_concept(connection, _sample_concept())
        row = concepts.get_concept(connection, "concept_sgd_a1b2c3")
        assert row is not None
        assert row["canonical_title"] == "Stochastic Gradient Descent"
        assert row["normalized_title"] == "stochastic gradient descent"

        concepts.delete_concept(connection, "concept_sgd_a1b2c3")
        assert concepts.get_concept(connection, "concept_sgd_a1b2c3") is None


def test_child_rows_and_cascade_delete(initialized_engine: Engine) -> None:
    with begin_connection(initialized_engine) as connection:
        concepts.upsert_concept(connection, _sample_concept())
        aliases.insert_alias(connection, concept_id="concept_sgd_a1b2c3", alias="SGD")
        domains.insert_domain(
            connection, concept_id="concept_sgd_a1b2c3", domain="machine_learning"
        )
        learning_encounters.insert_learning_encounter(
            connection,
            {
                "concept_id": "concept_sgd_a1b2c3",
                "source_type": "paper",
                "source_title": "Example Paper",
                "external_id_type": "doi",
                "external_id_value": "10.1234/example",
                "role": "primary",
                "contribution_status": "pending",
                "content_attached": False,
                "content_id": None,
            },
        )
        relationships.insert_relationship(
            connection,
            {
                "source_concept_id": "concept_sgd_a1b2c3",
                "relationship_type": "depends_on",
                "target_title": "Partial Derivatives",
                "vault_status": "missing",
                "learning_role": "mathematical_prerequisite",
                "confidence": "high",
                "status": "agent_suggested",
            },
        )
        scaffold_modules.upsert_scaffold_module(
            connection,
            {
                "module_id": "module_sgd_001",
                "concept_id": "concept_sgd_a1b2c3",
                "type": "derivation",
                "title": "Update Rule",
                "status": "scaffolded",
                "segment_count": 1,
                "indexed_revision": 1,
            },
        )
        search_documents.upsert_concept_search_document(
            connection,
            {
                "concept_id": "concept_sgd_a1b2c3",
                "document_text": "Stochastic Gradient Descent SGD",
                "indexed_revision": 1,
            },
        )
        search_documents.upsert_module_search_document(
            connection,
            {
                "module_id": "module_sgd_001",
                "concept_id": "concept_sgd_a1b2c3",
                "document_text": "Update Rule derivation",
                "indexed_revision": 1,
            },
        )
        embedding_id = embeddings.insert_embedding(
            connection,
            {
                "owner_type": "concept",
                "owner_id": "concept_sgd_a1b2c3",
                "parent_concept_id": "concept_sgd_a1b2c3",
                "embedding_type": "identity",
                "vector": b"\x00\x01\x02\x03",
                "dimension": 4,
                "model_id": "test-model",
                "input_hash": "abc",
                "created_at": "2026-07-28T00:00:00Z",
                "indexed_revision": 1,
            },
        )
        assert embeddings.get_embedding(connection, embedding_id) is not None
        assert aliases.list_aliases_for_concept(connection, "concept_sgd_a1b2c3")
        assert domains.list_domains_for_concept(connection, "concept_sgd_a1b2c3")
        assert learning_encounters.list_encounters_for_concept(connection, "concept_sgd_a1b2c3")
        assert relationships.list_relationships_for_source(connection, "concept_sgd_a1b2c3")
        assert scaffold_modules.list_modules_for_concept(connection, "concept_sgd_a1b2c3")
        assert search_documents.get_concept_search_document(connection, "concept_sgd_a1b2c3")
        assert search_documents.get_module_search_document(connection, "module_sgd_001")

        concepts.delete_concept(connection, "concept_sgd_a1b2c3")
        assert aliases.list_aliases_for_concept(connection, "concept_sgd_a1b2c3") == []
        assert domains.list_domains_for_concept(connection, "concept_sgd_a1b2c3") == []
        assert (
            learning_encounters.list_encounters_for_concept(connection, "concept_sgd_a1b2c3") == []
        )
        assert relationships.list_relationships_for_source(connection, "concept_sgd_a1b2c3") == []
        assert scaffold_modules.list_modules_for_concept(connection, "concept_sgd_a1b2c3") == []
        assert (
            search_documents.get_concept_search_document(connection, "concept_sgd_a1b2c3") is None
        )
        assert search_documents.get_module_search_document(connection, "module_sgd_001") is None
        assert embeddings.get_embedding(connection, embedding_id) is None


def test_foreign_key_rejects_orphan_alias(initialized_engine: Engine) -> None:
    with begin_connection(initialized_engine) as connection, pytest.raises(IntegrityError):
        aliases.insert_alias(connection, concept_id="missing_concept", alias="X")


def test_transaction_rollback(initialized_engine: Engine) -> None:
    try:
        with begin_connection(initialized_engine) as connection:
            concepts.upsert_concept(connection, _sample_concept())
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass

    with begin_connection(initialized_engine) as connection:
        assert concepts.get_concept(connection, "concept_sgd_a1b2c3") is None


def test_indexed_files_and_invalid_records(initialized_engine: Engine) -> None:
    with begin_connection(initialized_engine) as connection:
        indexed_files.upsert_indexed_file(
            connection,
            {
                "file_path": "concepts/bad.md",
                "index_state": "invalid",
                "validation_errors_json": '["parse error"]',
                "indexed_at": "2026-07-28T00:00:00Z",
            },
        )
        invalid_records.insert_invalid_record(
            connection,
            {
                "file_path": "concepts/bad.md",
                "reason_code": "parse_error",
                "message": "Invalid YAML",
                "recorded_at": "2026-07-28T00:00:00Z",
            },
        )
        assert indexed_files.get_indexed_file(connection, "concepts/bad.md") is not None
        assert len(invalid_records.list_invalid_records(connection)) == 1
        invalid_records.delete_invalid_records_for_path(connection, "concepts/bad.md")
        indexed_files.delete_indexed_file(connection, "concepts/bad.md")
        assert indexed_files.get_indexed_file(connection, "concepts/bad.md") is None
        assert invalid_records.list_invalid_records(connection) == []
