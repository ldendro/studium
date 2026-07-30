"""Hash helpers for synchronization."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from studium.writes.hashing import hash_file_content

__all__ = [
    "hash_file_content",
    "hash_projection_payload",
    "hash_text",
]


def hash_text(text: str) -> str:
    """Return the SHA-256 hex digest of UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_projection_payload(payload: Any) -> str:
    """Hash a JSON-canonical serialization of projected index fields."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hash_text(encoded)
