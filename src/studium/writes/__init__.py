"""Safe write proposal layer (branch P1-B7).

Builds and commits write proposals with collision detection and
stale-write protection for the test vault.
"""

from studium.writes.commit import commit_write_proposal
from studium.writes.errors import (
    CollisionError,
    StaleFileError,
    WriteError,
    WriteProposalBlockedError,
)
from studium.writes.hashing import hash_file_content
from studium.writes.proposal import (
    build_create_note_proposal,
    build_create_note_proposal_from_title,
    build_metadata_update_proposal,
    build_update_note_proposal,
    proposal_can_be_committed,
)

__all__ = [
    "CollisionError",
    "StaleFileError",
    "WriteError",
    "WriteProposalBlockedError",
    "build_create_note_proposal",
    "build_create_note_proposal_from_title",
    "build_metadata_update_proposal",
    "build_update_note_proposal",
    "commit_write_proposal",
    "hash_file_content",
    "proposal_can_be_committed",
]
