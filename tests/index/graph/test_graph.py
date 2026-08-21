"""Tests for graph queries and encounter matching."""

from __future__ import annotations

import pytest
from sqlalchemy.engine import Engine

from studium.index import begin_connection
from studium.index.errors import ConceptNotFoundError
from studium.index.graph import (
    EncounterOutcome,
    build_encounter_fingerprint,
    compare_learning_encounter,
    derive_inverse_relationship_type,
    get_one_hop_neighborhood,
    get_parent_child_candidates,
    get_prerequisites,
    normalize_source_identity,
)
from studium.index.graph.encounters import compare_against_rows
from studium.index.repositories import concepts, learning_encounters, relationships


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


def test_inverse_types() -> None:
    assert derive_inverse_relationship_type("depends_on") == "prerequisite_for"
    assert derive_inverse_relationship_type("parent_of") == "child_of"


def test_one_hop_and_prerequisites(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_backprop", "Backpropagation")
    _upsert_concept(initialized_engine, "concept_chain", "Chain Rule")
    with begin_connection(initialized_engine) as connection:
        relationships.insert_relationship(
            connection,
            {
                "source_concept_id": "concept_backprop",
                "relationship_type": "depends_on",
                "target_id": "concept_chain",
                "target_title": "Chain Rule",
                "vault_status": "found",
                "learning_role": "mathematical_prerequisite",
                "confidence": "high",
                "status": "user_confirmed",
            },
        )
    prereqs = get_prerequisites(initialized_engine, "concept_backprop")
    assert len(prereqs) == 1
    assert prereqs[0].target_id == "concept_chain"

    neighborhood = get_one_hop_neighborhood(initialized_engine, "concept_chain")
    assert neighborhood.incoming_derived
    assert neighborhood.incoming_derived[0].derived_inverse is True
    assert neighborhood.incoming_derived[0].relationship_type == "prerequisite_for"
    assert neighborhood.incoming_derived[0].target_id == "concept_backprop"
    assert neighborhood.incoming_derived[0].target_title == "Backpropagation"


def test_one_hop_rejects_missing_concept(initialized_engine: Engine) -> None:
    with pytest.raises(ConceptNotFoundError, match="missing-concept"):
        get_one_hop_neighborhood(initialized_engine, "missing-concept")


def test_parent_child_buckets_follow_graph_direction(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "parent", "Parent")
    _upsert_concept(initialized_engine, "child", "Child")
    with begin_connection(initialized_engine) as connection:
        relationships.insert_relationship(
            connection,
            {
                "source_concept_id": "parent",
                "relationship_type": "parent_of",
                "target_id": "child",
                "target_title": "Child",
                "vault_status": "found",
                "learning_role": "supporting",
                "confidence": "high",
                "status": "user_confirmed",
            },
        )
    assert [
        r.target_id for r in get_parent_child_candidates(initialized_engine, "parent")["children"]
    ] == ["child"]
    assert [
        r.target_id for r in get_parent_child_candidates(initialized_engine, "child")["parents"]
    ] == ["parent"]


def test_encounter_outcomes(initialized_engine: Engine) -> None:
    _upsert_concept(initialized_engine, "concept_sgd", "SGD")
    base = normalize_source_identity(
        source_type="book",
        source_title="Hands-On Machine Learning",
    )
    enriched = normalize_source_identity(
        source_type="book",
        source_title="Hands-On Machine Learning",
        unit="Chapter 4",
    )
    other_unit = normalize_source_identity(
        source_type="book",
        source_title="Hands-On Machine Learning",
        unit="Chapter 6",
    )
    other_book = normalize_source_identity(
        source_type="book",
        source_title="Deep Learning Book",
    )

    with begin_connection(initialized_engine) as connection:
        learning_encounters.insert_learning_encounter(
            connection,
            {
                "concept_id": "concept_sgd",
                "source_type": "book",
                "source_title": "Hands-On Machine Learning",
                "unit_type": None,
                "unit": None,
                "section": None,
                "link": None,
                "external_id_type": None,
                "external_id_value": None,
                "role": "primary",
                "contribution_status": "pending",
                "content_attached": False,
                "content_id": None,
                "fingerprint": build_encounter_fingerprint(base),
            },
        )

    exact = compare_learning_encounter(initialized_engine, concept_id="concept_sgd", candidate=base)
    assert exact.outcome == EncounterOutcome.EXACT_SAME_ENCOUNTER

    enrich = compare_learning_encounter(
        initialized_engine, concept_id="concept_sgd", candidate=enriched
    )
    assert enrich.outcome == EncounterOutcome.SAME_SOURCE_ENRICH_EXISTING

    # Seed unit Chapter 4 then compare Chapter 6
    with begin_connection(initialized_engine) as connection:
        learning_encounters.delete_encounters_for_concept(connection, "concept_sgd")
        learning_encounters.insert_learning_encounter(
            connection,
            {
                "concept_id": "concept_sgd",
                "source_type": "book",
                "source_title": "Hands-On Machine Learning",
                "unit_type": None,
                "unit": "Chapter 4",
                "section": None,
                "link": None,
                "external_id_type": None,
                "external_id_value": None,
                "role": "primary",
                "contribution_status": "pending",
                "content_attached": False,
                "content_id": None,
                "fingerprint": build_encounter_fingerprint(enriched),
            },
        )
    new_unit = compare_learning_encounter(
        initialized_engine, concept_id="concept_sgd", candidate=other_unit
    )
    assert new_unit.outcome == EncounterOutcome.SAME_SOURCE_NEW_UNIT

    different = compare_learning_encounter(
        initialized_engine, concept_id="concept_sgd", candidate=other_book
    )
    assert different.outcome == EncounterOutcome.DIFFERENT_SOURCE


@pytest.mark.parametrize(
    "identity_fields",
    [
        {"link": "https://example.com/course"},
        {"external_id_type": "isbn", "external_id_value": "978-0-00-000000-0"},
    ],
)
def test_source_identifier_additions_are_enrichment(identity_fields: dict[str, str]) -> None:
    candidate = normalize_source_identity(
        source_type="book",
        source_title="Shared Source",
        **identity_fields,
    )
    result = compare_against_rows(
        [
            {
                "id": 1,
                "concept_id": "concept_source",
                "source_type": "book",
                "source_title": "Shared Source",
            }
        ],
        candidate=candidate,
    )

    assert result.outcome == EncounterOutcome.SAME_SOURCE_ENRICH_EXISTING


def test_source_urls_preserve_case_sensitive_components() -> None:
    upper = normalize_source_identity(
        source_type="web", source_title="Page", link="HTTPS://EXAMPLE.TEST/A?q=X"
    )
    lower = normalize_source_identity(
        source_type="web", source_title="Page", link="https://example.test/a?q=X"
    )
    assert upper.link == "https://example.test/A?q=X"
    assert build_encounter_fingerprint(upper) != build_encounter_fingerprint(lower)


def test_same_title_with_conflicting_links_is_a_different_source() -> None:
    existing = normalize_source_identity(
        source_type="web", source_title="Page", link="https://example.test/first"
    )
    candidate = normalize_source_identity(
        source_type="web", source_title="Page", link="https://example.test/second"
    )
    row = {
        "encounter_id": 1,
        "concept_id": "concept_web",
        "source_type": existing.source_type,
        "source_title": existing.source_title,
        "link": existing.link,
        "unit": None,
        "unit_type": None,
        "section": None,
        "external_id_type": None,
        "external_id_value": None,
    }

    comparison = compare_against_rows([row], candidate=candidate)

    assert comparison.outcome == EncounterOutcome.DIFFERENT_SOURCE


def test_same_source_and_unit_with_different_section_is_new_encounter() -> None:
    existing = normalize_source_identity(
        source_type="book",
        source_title="Machine Learning",
        unit="Chapter 4",
        section="Gradient Descent",
    )
    candidate = normalize_source_identity(
        source_type="book",
        source_title="Machine Learning",
        unit="Chapter 4",
        section="Normal Equation",
    )
    row = {
        "id": 1,
        "concept_id": "concept_linear_models",
        "source_type": existing.source_type,
        "source_title": existing.source_title,
        "unit": existing.unit,
        "unit_type": None,
        "section": existing.section,
        "link": None,
        "external_id_type": None,
        "external_id_value": None,
    }

    comparison = compare_against_rows([row], candidate=candidate)

    assert comparison.outcome == EncounterOutcome.SAME_SOURCE_NEW_UNIT


def test_new_unit_is_unambiguous_across_multiple_source_encounters() -> None:
    existing_rows = [
        {
            "id": index,
            "concept_id": "concept_linear_models",
            "source_type": "book",
            "source_title": "Machine Learning",
            "unit": f"Chapter {index}",
            "unit_type": "chapter",
            "section": None,
            "link": None,
            "external_id_type": None,
            "external_id_value": None,
        }
        for index in (1, 2)
    ]
    candidate = normalize_source_identity(
        source_type="book",
        source_title="Machine Learning",
        unit_type="chapter",
        unit="Chapter 3",
    )

    comparison = compare_against_rows(existing_rows, candidate=candidate)

    assert comparison.outcome == EncounterOutcome.SAME_SOURCE_NEW_UNIT
    assert comparison.matched_encounter_id is None
    assert comparison.evidence == {"new_unit": "chapter 3", "same_source_count": 2}


def test_external_identifier_values_preserve_case() -> None:
    upper = normalize_source_identity(
        source_type="video",
        source_title="Lesson",
        external_id_type="youtube",
        external_id_value="AbC",
    )
    lower = normalize_source_identity(
        source_type="video",
        source_title="Lesson",
        external_id_type="youtube",
        external_id_value="abc",
    )
    assert upper.external_id_value == "AbC"
    assert build_encounter_fingerprint(upper) != build_encounter_fingerprint(lower)
