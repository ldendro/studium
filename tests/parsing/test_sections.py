"""Tests for Markdown section detection."""

from __future__ import annotations

from studium.parsing import CANONICAL_SECTION_TITLES, parse_markdown_sections


def test_detects_h1_and_canonical_h2_sections() -> None:
    body = """# Test Concept

## Concept Overview

Some text.

## Prerequisites

## Module Index

## Scaffold Modules

## Related Concepts

## Open Questions / Gaps
"""
    sections = parse_markdown_sections(body)

    assert sections.h1_title == "Test Concept"
    assert sections.canonical_present == list(CANONICAL_SECTION_TITLES)
    assert sections.canonical_missing == []


def test_missing_canonical_sections_reported() -> None:
    body = """# Test Concept

## Concept Overview

## Prerequisites
"""
    sections = parse_markdown_sections(body)

    assert "Module Index" in sections.canonical_missing
    assert "Related Concepts" in sections.canonical_missing


def test_headings_inside_code_fence_ignored() -> None:
    body = """# Test Concept

```markdown
## Concept Overview
# Not a real heading
```

## Concept Overview
"""
    sections = parse_markdown_sections(body)

    h2_titles = [heading.title for heading in sections.headings if heading.level == 2]
    assert h2_titles == ["Concept Overview"]


def test_h3_headings_not_counted_as_canonical() -> None:
    body = """# Test Concept

### Concept Overview
"""
    sections = parse_markdown_sections(body)

    assert sections.canonical_present == []
    assert "Concept Overview" in sections.canonical_missing


def test_extra_non_canonical_h2_allowed() -> None:
    body = """# Test Concept

## Concept Overview

## User Notes
"""
    sections = parse_markdown_sections(body)

    titles = [heading.title for heading in sections.headings if heading.level == 2]
    assert "User Notes" in titles
