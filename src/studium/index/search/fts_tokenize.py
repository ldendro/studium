"""FTS5 query tokenization via the real SQLite unicode61 tokenizer."""

from __future__ import annotations

import sqlite3
import threading

from studium.index.repositories.fts import FTS_TOKENIZER

_lock = threading.Lock()
_tokenizer_connection: sqlite3.Connection | None = None


def _get_tokenizer_connection() -> sqlite3.Connection:
    """Lazy in-memory FTS table used only to extract unicode61 tokens."""
    global _tokenizer_connection
    if _tokenizer_connection is None:
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.execute(f"CREATE VIRTUAL TABLE doc USING fts5(body, tokenize='{FTS_TOKENIZER}')")
        connection.execute("CREATE VIRTUAL TABLE doc_vocab USING fts5vocab(doc, 'instance')")
        _tokenizer_connection = connection
    return _tokenizer_connection


def tokenize_fts_text(text: str) -> list[str]:
    """Return tokens exactly as our FTS5 ``unicode61`` tables would index them.

    Uses SQLite's own tokenizer (including ``remove_diacritics 1``) rather than a
    Python NFKD/casefold approximation, which mishandles cases such as German
    ``ß`` (``Straße`` → ``straße``, not ``strasse``) and Indic marks
    (``कर्म`` must keep the virama).

    Used for MATCH query construction and ``matched_fields`` diagnostics.
    """
    if not text:
        return []
    with _lock:
        connection = _get_tokenizer_connection()
        connection.execute("DELETE FROM doc")
        connection.execute("INSERT INTO doc(body) VALUES (?)", (text,))
        rows = connection.execute("SELECT term FROM doc_vocab ORDER BY offset").fetchall()
    return [str(row[0]) for row in rows]
