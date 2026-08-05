"""Unit tests for sync hashing and embedding input builders."""

from __future__ import annotations

from studium.index.sync.embedding_inputs import (
    build_identity_embedding_input,
    build_module_embedding_input,
    build_semantic_embedding_input,
    truncate_module_body,
)
from studium.index.sync.hashes import hash_projection_payload, hash_text
from studium.index.sync.overview import extract_concept_overview, normalize_overview_text
from studium.parsing.markdown_sections import parse_markdown_sections


def test_hash_text_stable() -> None:
    assert hash_text("abc") == hash_text("abc")
    assert hash_text("abc") != hash_text("abd")


def test_projection_hash_key_order_independent() -> None:
    assert hash_projection_payload({"b": 1, "a": 2}) == hash_projection_payload({"a": 2, "b": 1})


def test_identity_and_semantic_inputs() -> None:
    identity = build_identity_embedding_input(canonical_title="SGD", aliases=["SGD"])
    assert identity == "Title: SGD\nAliases: SGD"
    semantic = build_semantic_embedding_input(
        canonical_title="SGD",
        aliases=["SGD"],
        concept_type="algorithm",
        domains=["ml"],
        overview_plaintext="An optimizer",
    )
    assert "Overview: An optimizer" in semantic
    module = build_module_embedding_input(
        title="Update",
        module_type="derivation",
        focus="math",
        body="",
    )
    assert module.startswith("Module Title: Update")


def test_truncate_module_body() -> None:
    assert truncate_module_body("abc", max_chars=10) == "abc"
    assert truncate_module_body("abcdefghij", max_chars=4) == "abcd"


def test_overview_extraction_and_normalization() -> None:
    body = "\n".join(
        [
            "# Title",
            "",
            "## Concept Overview",
            "",
            "Hello   **world** and [link](https://example.com).",
            "",
            "## Prerequisites",
            "",
        ]
    )
    sections = parse_markdown_sections(body)
    markdown, plaintext = extract_concept_overview(body, sections)
    assert "Hello" in markdown
    assert plaintext == normalize_overview_text(markdown)
    assert "world" in plaintext
    assert "link" in plaintext
    assert "**" not in plaintext
    assert "https://" not in plaintext
