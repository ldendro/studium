"""CLI path helpers."""

from __future__ import annotations

from pathlib import Path

from studium.serialization import slugify_title
from studium.vault.errors import VaultPathError
from studium.vault.vault import Vault


def default_concept_path(canonical_title: str) -> str:
    """Return the default vault-relative path for a new concept note."""
    hyphen_slug = slugify_title(canonical_title).replace("_", "-")
    return f"concepts/{hyphen_slug}.md"


def resolve_note_path(vault: Vault, path_arg: str) -> str:
    """Resolve a CLI note path to a vault-relative POSIX path.

    Absolute paths are accepted only when they resolve under the vault root.
    """
    candidate = Path(path_arg)
    if candidate.is_absolute():
        resolved = candidate.resolve()
        root = vault.root
        if not (resolved == root or resolved.is_relative_to(root)):
            msg = f"Path escapes vault root: {path_arg}"
            raise VaultPathError(msg)
        return resolved.relative_to(root).as_posix()

    vault.resolve_path(path_arg)
    return Path(path_arg).as_posix()
