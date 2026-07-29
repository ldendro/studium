"""Normalization helpers for indexed string columns."""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_title(text: str) -> str:
    """Return a case-folded, whitespace-collapsed title for equality lookup."""
    return _WHITESPACE.sub(" ", text.casefold()).strip()
