"""Vault access layer exceptions."""


class VaultError(Exception):
    """Base exception for vault access failures."""


class VaultPathError(VaultError):
    """Raised when a path escapes the vault root or is otherwise unsafe."""


class VaultNotFoundError(VaultError):
    """Raised when the vault root or a target file does not exist."""


class VaultTypeError(VaultError):
    """Raised when an operation targets a non-Markdown file."""
