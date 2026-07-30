"""Concept Overview extraction and light normalization for sync."""

from __future__ import annotations

import re

from studium.parsing.markdown_sections import MarkdownHeading, ParsedMarkdownSections

_WHITESPACE = re.compile(r"\s+")
_SIMPLE_MD_MARKERS = re.compile(r"[*_`#]+")
_MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def extract_section_markdown(
    body: str,
    section_title: str,
    headings: list[MarkdownHeading],
) -> str:
    """Return Markdown body text under an h2 section title (excluding the heading)."""
    lines = body.splitlines()
    start_line: int | None = None
    end_line = len(lines) + 1

    for index, heading in enumerate(headings):
        if heading.level != 2 or heading.title != section_title:
            continue
        start_line = heading.line_number + 1
        for following in headings[index + 1 :]:
            end_line = following.line_number
            break
        break

    if start_line is None:
        return ""

    # Headings use 1-based line numbers.
    return "\n".join(lines[start_line - 1 : end_line - 1]).strip()


def normalize_overview_text(markdown: str) -> str:
    """Lightly normalize overview Markdown for hashing and semantic inputs."""
    text = _MARKDOWN_LINK.sub(r"\1", markdown)
    text = _SIMPLE_MD_MARKERS.sub("", text)
    text = _WHITESPACE.sub(" ", text)
    return text.strip()


def extract_concept_overview(
    body: str,
    sections: ParsedMarkdownSections,
) -> tuple[str, str]:
    """Return ``(overview_markdown, overview_plaintext)`` for Concept Overview."""
    markdown = extract_section_markdown(body, "Concept Overview", sections.headings)
    plaintext = normalize_overview_text(markdown)
    return markdown, plaintext
