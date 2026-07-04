"""Split YAML frontmatter from Markdown body content."""

from __future__ import annotations

import re
from dataclasses import dataclass

from studium.parsing.errors import FrontmatterError

_FRONTMATTER_PATTERN = re.compile(
    r"^(?:\ufeff)?---\r?\n(.*?)(?:\r?\n)?---\r?\n?",
    re.DOTALL,
)


@dataclass(frozen=True)
class FrontmatterSplit:
    """Raw frontmatter text and body separated from a Markdown file."""

    frontmatter_text: str
    body: str
    raw_markdown: str


def split_frontmatter(raw_markdown: str) -> FrontmatterSplit:
    """Separate YAML frontmatter from the Markdown body without altering either part.

    The opening ``---`` must appear at the start of the file (after an optional UTF-8 BOM).
    The body is returned as an exact substring of ``raw_markdown``.
    """
    match = _FRONTMATTER_PATTERN.match(raw_markdown)
    if match is None:
        msg = "Markdown file must start with YAML frontmatter delimited by '---' lines"
        raise FrontmatterError(msg)

    return FrontmatterSplit(
        frontmatter_text=match.group(1),
        body=raw_markdown[match.end() :],
        raw_markdown=raw_markdown,
    )
