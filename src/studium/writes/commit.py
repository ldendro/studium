"""Commit write proposals to the vault."""

from __future__ import annotations

from studium.schemas import WriteOperation, WriteProposal
from studium.vault.vault import Vault
from studium.writes.errors import CollisionError, StaleFileError, WriteProposalBlockedError
from studium.writes.hashing import hash_file_content
from studium.writes.proposal import proposal_can_be_committed


def commit_write_proposal(vault: Vault, proposal: WriteProposal) -> None:
    """Commit a write proposal when it is safe against current vault state."""
    if not proposal_can_be_committed(proposal):
        msg = "Write proposal has critical errors and cannot be committed"
        raise WriteProposalBlockedError(msg, proposal=proposal)

    if proposal.operation == WriteOperation.CREATE_NOTE:
        if vault.exists(proposal.target_path):
            msg = f"Target file already exists: {proposal.target_path}"
            raise CollisionError(msg, target_path=proposal.target_path)
    elif proposal.operation == WriteOperation.UPDATE_NOTE:
        if not vault.exists(proposal.target_path):
            msg = f"Target file not found: {proposal.target_path}"
            raise WriteProposalBlockedError(msg, proposal=proposal)

        resolved = vault.resolve_path(proposal.target_path)
        current_content = resolved.read_text(encoding="utf-8")
        current_hash = hash_file_content(current_content)
        if current_hash != proposal.expected_existing_hash:
            msg = f"File changed since proposal was built: {proposal.target_path}"
            raise StaleFileError(
                msg,
                target_path=proposal.target_path,
                expected_hash=proposal.expected_existing_hash,
                actual_hash=current_hash,
            )
    else:
        msg = f"Unsupported write operation: {proposal.operation}"
        raise WriteProposalBlockedError(msg, proposal=proposal)

    resolved = vault.resolve_path(proposal.target_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(proposal.after_content, encoding="utf-8")
