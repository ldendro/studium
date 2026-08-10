"""Vector search: exact NumPy cosine and optional sqlite-vec backend."""

from studium.index.vector.facade import (
    search_concept_identity_vectors,
    search_concept_semantic_vectors,
    search_module_semantic_vectors,
)
from studium.index.vector.factory import create_vector_backend
from studium.index.vector.models import ModelSpaceFilter, VectorConceptHit, VectorModuleHit
from studium.index.vector.numpy_backend import NumpyVectorSearchBackend
from studium.index.vector.protocol import VectorSearchBackend
from studium.index.vector.similarity import cosine_scores, l2_normalize_matrix, l2_normalize_vector

__all__ = [
    "ModelSpaceFilter",
    "NumpyVectorSearchBackend",
    "VectorConceptHit",
    "VectorModuleHit",
    "VectorSearchBackend",
    "cosine_scores",
    "create_vector_backend",
    "l2_normalize_matrix",
    "l2_normalize_vector",
    "search_concept_identity_vectors",
    "search_concept_semantic_vectors",
    "search_module_semantic_vectors",
]
