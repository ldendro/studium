"""Markdown body section and heading detection."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from studium.parsing.sections import CANONICAL_SECTION_TITLES

_FENCE_PATTERN = re.compile(r"^(```+|~~~+)")


class MarkdownHeading(BaseModel):
    """A detected ATX heading in the Markdown body."""

    model_config = ConfigDict(extra="forbid")

    level: Literal[1, 2]
    title: str
    line_number: int = Field(ge=1)
    raw_line: str


class ParsedMarkdownSections(BaseModel):
    """Detected headings and canonical section presence in a note body."""

    model_config = ConfigDict(extra="forbid")

    headings: list[MarkdownHeading]
    h1_title: str | None
    canonical_present: list[str]
    canonical_missing: list[str]


def parse_markdown_sections(body: str) -> ParsedMarkdownSections:
    """Detect ATX h1/h2 headings and which canonical sections are present.

    Headings inside fenced code blocks are ignored. Only level-1 and level-2 ATX
    headings are recorded. Canonical section matching is exact on the stripped
    heading title.

    H1 title vs ``canonical_title`` mismatch validation is deferred to B6.
    """
    headings: list[MarkdownHeading] = []
    in_fence = False
    fence_marker: str | None = None

    for line_number, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        fence_match = _FENCE_PATTERN.match(stripped)

        if fence_match is not None:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[:3]
            elif fence_marker is not None and stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = None
            continue

        if in_fence:
            continue

        if stripped.startswith("## "):
            headings.append(
                MarkdownHeading(
                    level=2,
                    title=stripped[3:].strip(),
                    line_number=line_number,
                    raw_line=line,
                )
            )
        elif stripped.startswith("# "):
            headings.append(
                MarkdownHeading(
                    level=1,
                    title=stripped[2:].strip(),
                    line_number=line_number,
                    raw_line=line,
                )
            )

    h1_title = next((heading.title for heading in headings if heading.level == 1), None)
    h2_titles = {heading.title for heading in headings if heading.level == 2}
    canonical_present = [title for title in CANONICAL_SECTION_TITLES if title in h2_titles]
    canonical_missing = [title for title in CANONICAL_SECTION_TITLES if title not in h2_titles]

    return ParsedMarkdownSections(
        headings=headings,
        h1_title=h1_title,
        canonical_present=canonical_present,
        canonical_missing=canonical_missing,
    )
