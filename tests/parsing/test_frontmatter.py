"""Tests for frontmatter splitting."""

from __future__ import annotations

import pytest

from studium.parsing import FrontmatterError, split_frontmatter
from tests.parsing.helpers import build_valid_concept_note_markdown


def test_split_valid_frontmatter_and_body() -> None:
    markdown = build_valid_concept_note_markdown()
    split = split_frontmatter(markdown)

    assert "id: concept_test_abc123" in split.frontmatter_text
    assert split.body.startswith("# Test Concept")
    assert split.raw_markdown == markdown


def test_body_preserved_exactly_with_trailing_whitespace() -> None:
    markdown = build_valid_concept_note_markdown() + "  \n"
    split = split_frontmatter(markdown)

    assert split.body.endswith("  \n")
    assert markdown.endswith(split.body)


def test_split_supports_utf8_bom() -> None:
    markdown = "\ufeff" + build_valid_concept_note_markdown()
    split = split_frontmatter(markdown)

    assert split.frontmatter_text.startswith("id:")


def test_missing_frontmatter_raises() -> None:
    with pytest.raises(FrontmatterError, match="must start with YAML frontmatter"):
        split_frontmatter("# No frontmatter\n")


def test_missing_closing_delimiter_raises() -> None:
    with pytest.raises(FrontmatterError):
        split_frontmatter("---\nid: test\n# body\n")


def test_empty_frontmatter_block_splits() -> None:
    markdown = "---\n---\n# Body only metadata-empty\n"
    split = split_frontmatter(markdown)

    assert split.frontmatter_text == ""
    assert split.body == "# Body only metadata-empty\n"


def test_metadata_value_with_three_dashes_does_not_close_early() -> None:
    markdown = """---
id: concept_test_abc123
link: https://example/a---b
description: intro --- outro
---
# Body
"""
    split = split_frontmatter(markdown)

    assert "link: https://example/a---b" in split.frontmatter_text
    assert "description: intro --- outro" in split.frontmatter_text
    assert split.body == "# Body\n"
