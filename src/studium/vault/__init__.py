"""Vault access layer (branch P1-B2).

Safe file access inside a configured test vault: path resolution, vault-root
enforcement, Markdown reading, and listing.
"""

from studium.vault.errors import (
    VaultError,
    VaultNotFoundError,
    VaultPathError,
    VaultTypeError,
)
from studium.vault.paths import resolve_vault_path
from studium.vault.vault import Vault

__all__ = [
    "Vault",
    "VaultError",
    "VaultNotFoundError",
    "VaultPathError",
    "VaultTypeError",
    "resolve_vault_path",
]
