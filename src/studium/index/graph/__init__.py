"""Graph queries and learning-encounter comparison."""

from studium.index.graph.encounters import (
    build_encounter_fingerprint,
    build_source_fingerprint,
    compare_learning_encounter,
    normalize_source_identity,
)
from studium.index.graph.inverses import derive_inverse_relationship_type
from studium.index.graph.models import (
    EncounterComparison,
    EncounterOutcome,
    GraphRelationship,
    OneHopNeighborhood,
    SourceIdentity,
)
from studium.index.graph.queries import (
    derive_inverse_relationship,
    get_concepts_depending_on,
    get_direct_relationships,
    get_one_hop_neighborhood,
    get_parent_child_candidates,
    get_prerequisites,
    get_relationships_grouped_by_learning_role,
    get_relationships_grouped_by_type,
)

__all__ = [
    "EncounterComparison",
    "EncounterOutcome",
    "GraphRelationship",
    "OneHopNeighborhood",
    "SourceIdentity",
    "build_encounter_fingerprint",
    "build_source_fingerprint",
    "compare_learning_encounter",
    "derive_inverse_relationship",
    "derive_inverse_relationship_type",
    "get_concepts_depending_on",
    "get_direct_relationships",
    "get_one_hop_neighborhood",
    "get_parent_child_candidates",
    "get_prerequisites",
    "get_relationships_grouped_by_learning_role",
    "get_relationships_grouped_by_type",
    "normalize_source_identity",
]
