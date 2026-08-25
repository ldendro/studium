"""Derived inverse relationship types (not persisted)."""

from __future__ import annotations

# Persisted type → derived inverse type when reading the graph from the target side.
INVERSE_RELATIONSHIP_TYPES: dict[str, str] = {
    "depends_on": "prerequisite_for",
    "prerequisite_for": "depends_on",
    "parent_of": "child_of",
    "child_of": "parent_of",
    "related_to": "related_to",
    "contrasts_with": "contrasts_with",
    "variant_of": "variant_of",
}

PREREQUISITE_TYPES: frozenset[str] = frozenset({"depends_on"})
PARENT_TYPES: frozenset[str] = frozenset({"parent_of"})
CHILD_TYPES: frozenset[str] = frozenset({"child_of"})
VARIANT_TYPES: frozenset[str] = frozenset({"variant_of"})

INVERSE_LEARNING_ROLES: dict[str, str] = {
    "mathematical_prerequisite": "application_context",
    "conceptual_prerequisite": "application_context",
    "implementation_prerequisite": "application_context",
    "foundational_theory": "application_context",
    "broader_parent_concept": "specialized_child_concept",
    "specialized_child_concept": "broader_parent_concept",
    "alternative_variant": "alternative_variant",
    "comparison_target": "comparison_target",
    "supporting_concept": "application_context",
    "application_context": "supporting_concept",
}


def derive_inverse_relationship_type(relationship_type: str) -> str | None:
    """Return the inverse type for ``relationship_type``, or None if unknown."""
    return INVERSE_RELATIONSHIP_TYPES.get(relationship_type)


def derive_inverse_learning_role(learning_role: str) -> str:
    """Return the target's role when an assertion is viewed in reverse."""
    return INVERSE_LEARNING_ROLES.get(learning_role, "supporting_concept")
