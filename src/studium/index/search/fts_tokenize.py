"""FTS5 query construction helpers that mirror the unicode61 tokenizer."""

from __future__ import annotations

import unicodedata


def tokenize_fts_text(text: str) -> list[str]:
    """Tokenize text the way our FTS5 ``unicode61`` tables do.

    Mirrors SQLite FTS5 unicode61 with diacritic removal (observed on current
    SQLite and made explicit via ``remove_diacritics 1`` in DDL):

    - NFKD + strip non-spacing marks
    - casefold
    - split on non-alphanumeric boundaries (``_`` and ``-`` are separators)

    Used both for MATCH query construction and ``matched_fields`` diagnostics so
    retrieval metadata agrees with ranking.
    """
    normalized = unicodedata.normalize("NFKD", text)
    folded_chars: list[str] = []
    for char in normalized:
        if unicodedata.category(char) == "Mn":
            continue
        folded_chars.append(char.casefold())
    folded = "".join(folded_chars)

    tokens: list[str] = []
    current: list[str] = []
    for char in folded:
        if char.isalnum():
            current.append(char)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tokens
