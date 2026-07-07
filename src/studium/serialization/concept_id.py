"""Stable concept ID generation."""

from __future__ import annotations

import hashlib
import re
import unicodedata


def slugify_title(title: str) -> str:
    """Normalize a canonical title into an ASCII slug segment for concept IDs."""
    normalized = unicodedata.normalize("NFKD", title)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", lowered)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "concept"


def generate_concept_id(canonical_title: str) -> str:
    """Return a stable concept ID in ``concept_<slug>_<hash6>`` format."""
    slug = slugify_title(canonical_title)
    digest = hashlib.sha256(canonical_title.strip().encode("utf-8")).hexdigest()[:6]
    return f"concept_{slug}_{digest}"
