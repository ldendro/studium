"""Markdown and YAML frontmatter parsing (branch P1-B4).

Splits Markdown files into frontmatter and body, parses YAML, and detects
canonical sections without mutating files.

H1 heading vs ``canonical_title`` mismatch validation is deferred to B6.
"""

from studium.parsing.concept_note import parse_concept_note
from studium.parsing.errors import FrontmatterError, ParseError, YamlParseError
from studium.parsing.frontmatter import FrontmatterSplit, split_frontmatter
from studium.parsing.markdown_sections import (
    MarkdownHeading,
    ParsedMarkdownSections,
    parse_markdown_sections,
)
from studium.parsing.models import ParsedConceptNote
from studium.parsing.yaml_frontmatter import YamlParseResult, parse_yaml_frontmatter
from studium.schemas.canonical import CANONICAL_SECTION_TITLES

__all__ = [
    "CANONICAL_SECTION_TITLES",
    "FrontmatterError",
    "FrontmatterSplit",
    "MarkdownHeading",
    "ParseError",
    "ParsedConceptNote",
    "ParsedMarkdownSections",
    "YamlParseError",
    "YamlParseResult",
    "parse_concept_note",
    "parse_markdown_sections",
    "parse_yaml_frontmatter",
    "split_frontmatter",
]
