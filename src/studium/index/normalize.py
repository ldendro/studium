"""Normalization helpers for indexed string columns and exact lookup."""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_HYPHEN_UNDERSCORE = re.compile(r"[-_]+")
# Strip light surrounding punctuation from the whole string after other transforms.
_SURROUNDING_PUNCT = re.compile(r"^[\s\"'`.,:;!?()\[\]{}<>]+|[\s\"'`.,:;!?()\[\]{}<>]+$")


def _strip_latin_combining_marks(text: str) -> str:
    """Remove Latin combining diacritics (unicode61 ``remove_diacritics 1``-like).

    Keeps script-specific non-spacing marks such as Devanagari virama so identity
    folding does not rewrite Indic orthography.
    """
    parts: list[str] = []
    for char in unicodedata.normalize("NFKD", text):
        if unicodedata.category(char) == "Mn":
            name = unicodedata.name(char, "")
            if "COMBINING" in name:
                continue
            parts.append(char)
            continue
        parts.append(char)
    return "".join(parts)


def normalize_for_lookup(text: str) -> str:
    """Normalize text for deterministic title/alias equality matching.

    Matching-only transforms (Technical Plan §4.8), plus Latin diacritic folding
    so identity lookup agrees with FTS ``remove_diacritics 1`` (``cafe`` ≡
    ``Café``). Does not stem or mutate display/metadata source strings held
    elsewhere.
    """
    normalized = _strip_latin_combining_marks(text)
    normalized = unicodedata.normalize("NFKC", normalized)
    normalized = normalized.casefold()
    normalized = _HYPHEN_UNDERSCORE.sub(" ", normalized)
    normalized = _SURROUNDING_PUNCT.sub("", normalized)
    normalized = _WHITESPACE.sub(" ", normalized).strip()
    # Punctuation strip can leave edges dirty; collapse again.
    normalized = _SURROUNDING_PUNCT.sub("", normalized)
    return _WHITESPACE.sub(" ", normalized).strip()


def normalize_title(text: str) -> str:
    """Return a normalized title/alias for equality lookup columns.

    Delegates to ``normalize_for_lookup`` so indexed columns and query-time
    matching use the same rules.
    """
    return normalize_for_lookup(text)


def dedupe_aliases_by_normalized(aliases: list[str]) -> list[str]:
    """Keep the first display alias for each distinct normalized form.

    ``foo-bar`` and ``foo_bar`` share a normalized key under
    ``normalize_for_lookup``, but ``concept_aliases`` is unique on
    ``(concept_id, normalized_alias)``. Deduplicating before insert avoids
    integrity errors during projection.
    """
    seen: set[str] = set()
    deduped: list[str] = []
    for alias in aliases:
        key = normalize_for_lookup(alias)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(alias)
    return deduped
