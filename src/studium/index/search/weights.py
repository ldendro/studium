"""Initial FTS field weights for BM25 column weighting."""

from __future__ import annotations

# Relative weights for concept_fts indexed columns:
# title, aliases, domains, overview (UNINDEXED concept_id ignored by bm25()).
CONCEPT_FTS_WEIGHTS: tuple[float, float, float, float] = (
    10.0,  # title
    8.0,  # aliases
    2.0,  # domains
    4.0,  # overview
)

# Relative weights for module_fts indexed columns:
# title, type, focus, body (UNINDEXED module_id/concept_id ignored).
MODULE_FTS_WEIGHTS: tuple[float, float, float, float] = (
    8.0,  # title
    2.0,  # type
    3.0,  # focus
    1.0,  # body
)

# Tokenizer DDL constant lives in repositories.fts (FTS_TOKENIZER) to avoid
# circular imports between repositories and search.
