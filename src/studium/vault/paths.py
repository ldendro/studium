"""Safe vault-relative path resolution."""

from __future__ import annotations

from pathlib import Path

from studium.vault.errors import VaultNotFoundError, VaultPathError


def resolve_vault_path(vault_root: Path, relative_path: str | Path) -> Path:
    """Resolve a vault-relative path and ensure it stays inside the vault root.

    Absolute paths are rejected before joining because on POSIX,
    ``vault_root / Path("/etc/passwd")`` ignores the vault root entirely.

    Symlinks are resolved; targets outside the vault root raise ``VaultPathError``.
    """
    root = vault_root.resolve()
    if not root.exists():
        msg = f"Vault root does not exist: {vault_root}"
        raise VaultNotFoundError(msg)
    if not root.is_dir():
        msg = f"Vault root is not a directory: {vault_root}"
        raise VaultNotFoundError(msg)

    rel = Path(relative_path)
    if rel.is_absolute():
        msg = f"Absolute paths are not allowed: {relative_path}"
        raise VaultPathError(msg)

    resolved = (root / rel).resolve()
    if not is_path_under_root(resolved, root):
        msg = f"Path escapes vault root: {relative_path}"
        raise VaultPathError(msg)

    return resolved


def is_path_under_root(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)
