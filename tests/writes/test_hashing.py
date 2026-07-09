"""Tests for content hashing."""

from __future__ import annotations

from studium.writes import hash_file_content


def test_same_content_produces_same_hash() -> None:
    content = "# Title\n\nBody with unicode: café"

    assert hash_file_content(content) == hash_file_content(content)


def test_different_content_produces_different_hash() -> None:
    assert hash_file_content("alpha") != hash_file_content("beta")


def test_hash_is_sha256_hex() -> None:
    digest = hash_file_content("test")

    assert len(digest) == 64
    assert all(char in "0123456789abcdef" for char in digest)
