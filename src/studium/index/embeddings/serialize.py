"""Float32 little-endian vector BLOB codec."""

from __future__ import annotations

import struct


def pack_vector(values: list[float]) -> bytes:
    """Serialize a vector as little-endian float32 values."""
    return struct.pack(f"<{len(values)}f", *values)


def unpack_vector(blob: bytes, *, dimension: int | None = None) -> list[float]:
    """Deserialize a little-endian float32 vector BLOB."""
    if len(blob) % 4 != 0:
        msg = f"Vector blob length {len(blob)} is not a multiple of 4"
        raise ValueError(msg)
    count = len(blob) // 4
    if dimension is not None and count != dimension:
        msg = f"Vector blob has {count} floats, expected dimension {dimension}"
        raise ValueError(msg)
    return list(struct.unpack(f"<{count}f", blob))
