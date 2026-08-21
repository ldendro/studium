"""Errors for the derived SQLite concept index."""

from __future__ import annotations


class ConceptIndexError(Exception):
    """Base error for index operations."""


class ConceptNotFoundError(ConceptIndexError):
    """Raised when a requested concept does not exist in the derived index."""

    def __init__(self, concept_id: str) -> None:
        self.concept_id = concept_id
        super().__init__(f"Concept not found in index: {concept_id}")


class IndexNotInitializedError(ConceptIndexError):
    """Raised when the index database has not been initialized."""


class IndexSchemaMismatchError(ConceptIndexError):
    """Raised when the on-disk index schema version is incompatible."""

    def __init__(self, found: int | None, expected: int) -> None:
        self.found = found
        self.expected = expected
        found_display = "missing" if found is None else str(found)
        super().__init__(
            f"Index schema version mismatch: found {found_display}, expected {expected}. "
            "Rebuild the derived index."
        )


class IndexIntegrityError(ConceptIndexError):
    """Raised when a repository operation violates index integrity constraints."""
