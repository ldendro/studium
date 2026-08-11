"""One-hop graph queries over indexed relationships."""

from __future__ import annotations

from typing import Any

from sqlalchemy.engine import Engine

from studium.index.graph.inverses import (
    CHILD_TYPES,
    PARENT_TYPES,
    PREREQUISITE_TYPES,
    VARIANT_TYPES,
    derive_inverse_relationship_type,
)
from studium.index.graph.models import GraphRelationship, OneHopNeighborhood
from studium.index.repositories import concepts as concepts_repo
from studium.index.repositories import relationships as relationships_repo


def _row_to_relationship(row: dict[str, Any], *, derived: bool = False) -> GraphRelationship:
    rel_type = str(row["relationship_type"])
    return GraphRelationship(
        id=None if row.get("id") is None else int(row["id"]),
        source_concept_id=str(row["source_concept_id"]),
        relationship_type=rel_type,
        target_id=None if row.get("target_id") is None else str(row["target_id"]),
        target_title=str(row["target_title"]),
        vault_status=str(row["vault_status"]),
        learning_role=str(row["learning_role"]),
        confidence=str(row["confidence"]),
        status=str(row["status"]),
        derived_inverse=derived,
        original_relationship_type=rel_type if derived else None,
    )


def get_direct_relationships(
    engine: Engine,
    concept_id: str,
) -> list[GraphRelationship]:
    """Outgoing relationships persisted for ``concept_id``."""
    with engine.connect() as connection:
        rows = relationships_repo.list_relationships_for_source(connection, concept_id)
    return [_row_to_relationship(row) for row in rows]


def get_relationships_grouped_by_type(
    engine: Engine,
    concept_id: str,
) -> dict[str, list[GraphRelationship]]:
    grouped: dict[str, list[GraphRelationship]] = {}
    for rel in get_one_hop_neighborhood(engine, concept_id).outgoing:
        grouped.setdefault(rel.relationship_type, []).append(rel)
    return grouped


def get_relationships_grouped_by_learning_role(
    engine: Engine,
    concept_id: str,
) -> dict[str, list[GraphRelationship]]:
    grouped: dict[str, list[GraphRelationship]] = {}
    for rel in get_one_hop_neighborhood(engine, concept_id).outgoing:
        grouped.setdefault(rel.learning_role, []).append(rel)
    return grouped


def get_prerequisites(engine: Engine, concept_id: str) -> list[GraphRelationship]:
    """Concepts this concept ``depends_on`` (outgoing prerequisites)."""
    return [
        rel
        for rel in get_direct_relationships(engine, concept_id)
        if rel.relationship_type in PREREQUISITE_TYPES
    ]


def get_concepts_depending_on(engine: Engine, concept_id: str) -> list[GraphRelationship]:
    """Derived ``prerequisite_for`` views: who depends on ``concept_id``."""
    return [
        rel
        for rel in _incoming_derived(engine, concept_id)
        if rel.relationship_type == "prerequisite_for"
        or rel.original_relationship_type == "depends_on"
    ]


def get_parent_child_candidates(
    engine: Engine,
    concept_id: str,
) -> dict[str, list[GraphRelationship]]:
    neighborhood = get_one_hop_neighborhood(engine, concept_id)
    children = [
        rel
        for rel in [*neighborhood.outgoing, *neighborhood.incoming_derived]
        if rel.relationship_type in PARENT_TYPES
        or (rel.derived_inverse and rel.original_relationship_type in CHILD_TYPES)
    ]
    parents = [
        rel
        for rel in [*neighborhood.outgoing, *neighborhood.incoming_derived]
        if rel.relationship_type in CHILD_TYPES
        or (rel.derived_inverse and rel.original_relationship_type in PARENT_TYPES)
    ]
    variants = [
        rel
        for rel in [*neighborhood.outgoing, *neighborhood.incoming_derived]
        if rel.relationship_type in VARIANT_TYPES
    ]
    return {"parents": parents, "children": children, "variants": variants}


def get_one_hop_neighborhood(engine: Engine, concept_id: str) -> OneHopNeighborhood:
    outgoing = get_direct_relationships(engine, concept_id)
    incoming = _incoming_derived(engine, concept_id)
    by_type: dict[str, list[GraphRelationship]] = {}
    by_role: dict[str, list[GraphRelationship]] = {}
    for rel in [*outgoing, *incoming]:
        by_type.setdefault(rel.relationship_type, []).append(rel)
        by_role.setdefault(rel.learning_role, []).append(rel)
    return OneHopNeighborhood(
        concept_id=concept_id,
        outgoing=outgoing,
        incoming_derived=incoming,
        by_type=by_type,
        by_learning_role=by_role,
    )


def derive_inverse_relationship(
    row: dict[str, Any],
    *,
    viewer_concept_id: str,
) -> GraphRelationship:
    """Build a derived inverse edge as seen from ``viewer_concept_id`` (the target)."""
    original_type = str(row["relationship_type"])
    inverse = derive_inverse_relationship_type(original_type)
    if inverse is None:
        inverse = original_type
    return GraphRelationship(
        id=None if row.get("id") is None else int(row["id"]),
        source_concept_id=viewer_concept_id,
        relationship_type=inverse,
        target_id=str(row["source_concept_id"]),
        target_title=str(row.get("source_title") or row["source_concept_id"]),
        vault_status=str(row["vault_status"]),
        learning_role=str(row["learning_role"]),
        confidence=str(row["confidence"]),
        status=str(row["status"]),
        derived_inverse=True,
        original_relationship_type=original_type,
    )


def _incoming_derived(engine: Engine, concept_id: str) -> list[GraphRelationship]:
    with engine.connect() as connection:
        rows = relationships_repo.list_relationships_for_target(connection, concept_id)
        enriched: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            source = concepts_repo.get_concept(connection, str(row["source_concept_id"]))
            item["source_title"] = source["canonical_title"] if source else row["source_concept_id"]
            enriched.append(item)
    return [derive_inverse_relationship(row, viewer_concept_id=concept_id) for row in enriched]
