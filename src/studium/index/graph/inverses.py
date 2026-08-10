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


def derive_inverse_relationship_type(relationship_type: str) -> str | None:
    """Return the inverse type for ``relationship_type``, or None if unknown."""
    return INVERSE_RELATIONSHIP_TYPES.get(relationship_type)
