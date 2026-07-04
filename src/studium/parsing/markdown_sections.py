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

    Fence detection follows CommonMark: a closing fence uses the same character as
    the opener, is at least as long as the opening fence, and contains only that
    character (plus optional trailing spaces).

    H1 title vs ``canonical_title`` mismatch validation is deferred to B6.
    """
    headings: list[MarkdownHeading] = []
    in_fence = False
    opening_fence: str | None = None

    for line_number, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        fence_marker = _opening_fence_marker(stripped)

        if fence_marker is not None:
            if not in_fence:
                in_fence = True
                opening_fence = fence_marker
            elif opening_fence is not None and _is_closing_fence(stripped, opening_fence):
                in_fence = False
                opening_fence = None
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


def _opening_fence_marker(stripped: str) -> str | None:
    match = _FENCE_PATTERN.match(stripped)
    if match is None:
        return None
    return match.group(1)


def _is_closing_fence(stripped: str, opening_fence: str) -> bool:
    fence_char = opening_fence[0]
    opening_length = len(opening_fence)

    run_length = 0
    for char in stripped:
        if char == fence_char:
            run_length += 1
        else:
            break

    if run_length < opening_length:
        return False

    return stripped[run_length:].strip() == ""
