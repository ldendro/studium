"""Split YAML frontmatter from Markdown body content."""

from __future__ import annotations

from dataclasses import dataclass

from studium.parsing.errors import FrontmatterError


@dataclass(frozen=True)
class FrontmatterSplit:
    """Raw frontmatter text and body separated from a Markdown file."""

    frontmatter_text: str
    body: str
    raw_markdown: str


def split_frontmatter(raw_markdown: str) -> FrontmatterSplit:
    """Separate YAML frontmatter from the Markdown body without altering either part.

    The opening ``---`` must appear at the start of the file (after an optional UTF-8 BOM).
    The closing ``---`` must appear alone on its own line so metadata values may contain
    three dashes (for example URLs or descriptions). The body is returned as an exact
    substring of ``raw_markdown``.
    """
    start_offset = 0
    if raw_markdown.startswith("\ufeff"):
        start_offset = 1

    if not raw_markdown.startswith("---", start_offset):
        msg = "Markdown file must start with YAML frontmatter delimited by '---' lines"
        raise FrontmatterError(msg)

    opening_line_end = raw_markdown.find("\n", start_offset)
    if opening_line_end == -1:
        msg = "Markdown file must start with YAML frontmatter delimited by '---' lines"
        raise FrontmatterError(msg)

    opening_line = raw_markdown[start_offset:opening_line_end]
    if not _is_delimiter_line(opening_line):
        msg = "Markdown file must start with YAML frontmatter delimited by '---' lines"
        raise FrontmatterError(msg)

    content_start = opening_line_end + 1
    closing_line_start = _find_closing_delimiter_line(raw_markdown, content_start)
    if closing_line_start is None:
        msg = "Markdown file must start with YAML frontmatter delimited by '---' lines"
        raise FrontmatterError(msg)

    body_start = _line_end_after(raw_markdown, closing_line_start)
    return FrontmatterSplit(
        frontmatter_text=raw_markdown[content_start:closing_line_start],
        body=raw_markdown[body_start:],
        raw_markdown=raw_markdown,
    )


def _is_delimiter_line(line: str) -> bool:
    return line.rstrip("\r") == "---"


def _find_closing_delimiter_line(text: str, start: int) -> int | None:
    pos = start
    while pos <= len(text):
        line_end = text.find("\n", pos)
        if line_end == -1:
            if _is_delimiter_line(text[pos:]):
                return pos
            return None

        line = text[pos:line_end]
        if _is_delimiter_line(line):
            return pos
        pos = line_end + 1

    return None


def _line_end_after(text: str, line_start: int) -> int:
    line_end = text.find("\n", line_start)
    if line_end == -1:
        return len(text)
    return line_end + 1
