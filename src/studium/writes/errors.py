"""Write proposal and commit exceptions."""

from __future__ import annotations

from studium.schemas.write_proposal import WriteProposal


class WriteError(Exception):
    """Base exception for write layer failures."""


class WriteProposalBlockedError(WriteError):
    """Raised when a write proposal cannot be committed."""

    def __init__(self, message: str, *, proposal: WriteProposal | None = None) -> None:
        super().__init__(message)
        self.proposal = proposal


class CollisionError(WriteError):
    """Raised when a create commit would overwrite an existing file."""

    def __init__(self, message: str, *, target_path: str) -> None:
        super().__init__(message)
        self.target_path = target_path


class StaleFileError(WriteError):
    """Raised when an update commit targets content that changed since the proposal."""

    def __init__(
        self,
        message: str,
        *,
        target_path: str,
        expected_hash: str | None,
        actual_hash: str | None,
    ) -> None:
        super().__init__(message)
        self.target_path = target_path
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
