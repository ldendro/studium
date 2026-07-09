"""Content hashing for stale-write detection."""

from __future__ import annotations

import hashlib


def hash_file_content(content: str) -> str:
    """Return the SHA-256 hex digest of UTF-8 file content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
