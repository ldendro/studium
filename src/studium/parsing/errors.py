"""Parse errors for Markdown and YAML frontmatter handling."""

from __future__ import annotations


class ParseError(Exception):
    """Base error for parsing failures."""


class FrontmatterError(ParseError):
    """Raised when YAML frontmatter delimiters are missing or malformed."""


class YamlParseError(ParseError):
    """Raised when YAML frontmatter text is syntactically invalid."""
