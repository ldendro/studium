"""Initial FTS field weights for BM25 column weighting."""

from __future__ import annotations

# bm25() assigns weights by physical column position, including UNINDEXED
# columns. Pass 0.0 for identifier columns so searchable fields keep the
# advertised priorities (SQLite defaults omitted trailing columns to 1.0).
#
# concept_fts: concept_id UNINDEXED, title, aliases, domains, overview
CONCEPT_FTS_WEIGHTS: tuple[float, float, float, float, float] = (
    0.0,  # concept_id (UNINDEXED)
    10.0,  # title
    8.0,  # aliases
    2.0,  # domains
    4.0,  # overview
)

# module_fts: module_id UNINDEXED, concept_id UNINDEXED, title, type, focus, body
MODULE_FTS_WEIGHTS: tuple[float, float, float, float, float, float] = (
    0.0,  # module_id (UNINDEXED)
    0.0,  # concept_id (UNINDEXED)
    8.0,  # title
    2.0,  # type
    3.0,  # focus
    1.0,  # body
)

# Tokenizer DDL constant lives in repositories.fts (FTS_TOKENIZER) to avoid
# circular imports between repositories and search.
