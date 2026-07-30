"""Lexical search: deterministic identity lookup and weighted FTS5."""

from studium.index.repositories.fts import FTS_TOKENIZER
from studium.index.search.fts import (
    build_fts_match_query,
    search_concepts_fts,
    search_modules_fts,
)
from studium.index.search.lookup import resolve_concept_identity
from studium.index.search.models import (
    ExactMatchType,
    IdentityMatch,
    IdentityResolution,
    LexicalConceptHit,
    LexicalModuleHit,
    LexicalSearchResult,
    ResolutionState,
)
from studium.index.search.service import search_concepts_lexical
from studium.index.search.weights import CONCEPT_FTS_WEIGHTS, MODULE_FTS_WEIGHTS

__all__ = [
    "CONCEPT_FTS_WEIGHTS",
    "FTS_TOKENIZER",
    "MODULE_FTS_WEIGHTS",
    "ExactMatchType",
    "IdentityMatch",
    "IdentityResolution",
    "LexicalConceptHit",
    "LexicalModuleHit",
    "LexicalSearchResult",
    "ResolutionState",
    "build_fts_match_query",
    "resolve_concept_identity",
    "search_concepts_fts",
    "search_concepts_lexical",
    "search_modules_fts",
]
