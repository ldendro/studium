"""Helpers for vault index synchronization tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.parsing.helpers import build_canonical_body, build_valid_frontmatter_yaml


def write_concept_note(
    vault_root: Path,
    relative_path: str,
    *,
    overview: str = "",
    modules_yaml: str | None = None,
    **metadata_overrides: Any,
) -> str:
    """Write a valid concept note into the vault and return the relative path."""
    title = metadata_overrides.get("canonical_title", "Test Concept")
    yaml_block = build_valid_frontmatter_yaml(**metadata_overrides)
    if modules_yaml is not None:
        yaml_block = yaml_block.replace("scaffold_modules: []", modules_yaml.rstrip())
    body = build_canonical_body(title)
    if overview:
        body = body.replace(
            "## Concept Overview\n\n",
            f"## Concept Overview\n\n{overview}\n\n",
        )
    target = vault_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"---\n{yaml_block}\n---\n{body}", encoding="utf-8")
    return relative_path


def write_invalid_note(vault_root: Path, relative_path: str, content: str) -> str:
    target = vault_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return relative_path
