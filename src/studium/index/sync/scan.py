"""Vault scanning for synchronization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from studium.index.sync.hashes import hash_file_content
from studium.vault import Vault


@dataclass(frozen=True, slots=True)
class ScannedFile:
    path: str
    content: str
    file_hash: str
    mtime_ns: int


def scan_vault(vault: Vault) -> list[ScannedFile]:
    """List Markdown files with content hashes and mtime."""
    scanned: list[ScannedFile] = []
    for relative_path in vault.list_markdown_files():
        content = vault.read_markdown(relative_path)
        absolute = vault.resolve_path(relative_path)
        scanned.append(
            ScannedFile(
                path=relative_path,
                content=content,
                file_hash=hash_file_content(content),
                mtime_ns=_mtime_ns(absolute),
            )
        )
    return scanned


def _mtime_ns(path: Path) -> int:
    return path.stat().st_mtime_ns
