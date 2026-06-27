"""Configured test vault with safe read and list operations."""

from __future__ import annotations

from pathlib import Path

from studium.vault.errors import VaultNotFoundError, VaultTypeError
from studium.vault.paths import is_path_under_root, resolve_vault_path


class Vault:
    """Safe access to Markdown files inside a configured vault root."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        if not self._root.exists():
            msg = f"Vault root does not exist: {root}"
            raise VaultNotFoundError(msg)
        if not self._root.is_dir():
            msg = f"Vault root is not a directory: {root}"
            raise VaultNotFoundError(msg)

    @property
    def root(self) -> Path:
        return self._root

    def resolve_path(self, relative_path: str | Path) -> Path:
        """Resolve a vault-relative path after safety checks."""
        return resolve_vault_path(self._root, relative_path)

    def exists(self, relative_path: str | Path) -> bool:
        """Return whether a vault-relative path refers to an existing file."""
        resolved = self.resolve_path(relative_path)
        return resolved.is_file()

    def read_markdown(self, relative_path: str | Path) -> str:
        """Read a vault-relative Markdown file as UTF-8 text."""
        rel = Path(relative_path)
        if rel.suffix.lower() != ".md":
            msg = f"Expected a Markdown file (.md): {relative_path}"
            raise VaultTypeError(msg)

        resolved = self.resolve_path(relative_path)
        if not resolved.is_file():
            msg = f"Markdown file not found: {relative_path}"
            raise VaultNotFoundError(msg)

        return resolved.read_text(encoding="utf-8")

    def list_markdown_files(self) -> list[str]:
        """List all Markdown files under the vault root as vault-relative paths."""
        markdown_paths: list[str] = []
        for path in self._root.rglob("*.md"):
            resolved = path.resolve()
            if not is_path_under_root(resolved, self._root):
                continue
            if not resolved.is_file():
                continue
            markdown_paths.append(resolved.relative_to(self._root).as_posix())

        return sorted(markdown_paths)
