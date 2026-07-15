"""create-concept CLI command."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from pydantic import ValidationError

from studium.cli.formatting import format_create_committed, format_write_proposal
from studium.cli.paths import default_concept_path, resolve_note_path
from studium.vault import Vault
from studium.vault.errors import VaultError
from studium.writes import (
    CollisionError,
    WriteError,
    WriteProposalBlockedError,
    build_create_note_proposal_from_title,
    commit_write_proposal,
    proposal_can_be_committed,
)


def cmd_create_concept(args: Namespace) -> int:
    """Create a concept note via write proposal, optionally committing it."""
    try:
        vault = Vault(Path(args.vault))
        if args.path:
            target_path = resolve_note_path(vault, args.path)
        else:
            target_path = default_concept_path(args.title)
        proposal = build_create_note_proposal_from_title(vault, target_path, args.title)

        print(format_write_proposal(proposal, dry_run=bool(args.dry_run)))

        if not proposal_can_be_committed(proposal):
            return 1

        if args.dry_run:
            return 0

        commit_write_proposal(vault, proposal)
        print(format_create_committed(proposal.target_path))
        return 0
    except (
        VaultError,
        CollisionError,
        WriteProposalBlockedError,
        WriteError,
        ValidationError,
    ) as exc:
        print(f"error: {exc}")
        return 1
