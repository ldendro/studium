"""Lexical and hybrid search: deterministic lookup, FTS5, and weighted RRF."""

from studium.index.repositories.fts import FTS_TOKENIZER
from studium.index.search.fts import (
    build_fts_match_query,
    search_concepts_fts,
    search_modules_fts,
)
from studium.index.search.hybrid import HybridSearchOptions, search_concepts
from studium.index.search.lookup import resolve_concept_identity
from studium.index.search.models import (
    ChannelContribution,
    ConceptSearchFilters,
    ConceptSearchLimits,
    ConceptSearchQuery,
    ConceptSearchResult,
    ExactMatchType,
    HybridModuleHit,
    IdentityMatch,
    IdentityResolution,
    LexicalConceptHit,
    LexicalModuleHit,
    LexicalSearchResult,
    RankedConceptCandidate,
    RankedModuleMatch,
    ResolutionState,
    SearchChannel,
    SearchEvidenceItem,
    SearchStatus,
)
from studium.index.search.rrf import fuse_ranked_lists, reciprocal_rank_score
from studium.index.search.service import search_concepts_lexical
from studium.index.search.weights import CONCEPT_FTS_WEIGHTS, MODULE_FTS_WEIGHTS

__all__ = [
    "CONCEPT_FTS_WEIGHTS",
    "FTS_TOKENIZER",
    "MODULE_FTS_WEIGHTS",
    "ChannelContribution",
    "ConceptSearchFilters",
    "ConceptSearchLimits",
    "ConceptSearchQuery",
    "ConceptSearchResult",
    "ExactMatchType",
    "HybridModuleHit",
    "HybridSearchOptions",
    "IdentityMatch",
    "IdentityResolution",
    "LexicalConceptHit",
    "LexicalModuleHit",
    "LexicalSearchResult",
    "RankedConceptCandidate",
    "RankedModuleMatch",
    "ResolutionState",
    "SearchChannel",
    "SearchEvidenceItem",
    "SearchStatus",
    "build_fts_match_query",
    "fuse_ranked_lists",
    "reciprocal_rank_score",
    "resolve_concept_identity",
    "search_concepts",
    "search_concepts_fts",
    "search_concepts_lexical",
    "search_modules_fts",
]
