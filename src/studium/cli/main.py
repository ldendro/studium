"""Studium CLI entrypoint."""

from __future__ import annotations

import argparse
import sys

from studium.cli.create_concept import cmd_create_concept
from studium.cli.validate_note import cmd_validate_note
from studium.cli.validate_vault import cmd_validate_vault


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser with Phase 1 subcommands."""
    parser = argparse.ArgumentParser(
        prog="studium",
        description="Studium Phase 1 vault storage CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser(
        "create-concept",
        help="Create a concept note in a test vault via a write proposal",
    )
    create.add_argument("title", help="Canonical title for the new concept note")
    create.add_argument(
        "--vault",
        required=True,
        help="Path to the vault root directory",
    )
    create.add_argument(
        "--path",
        default=None,
        help="Optional vault-relative target path (default: concepts/<slug>.md)",
    )
    create.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the write proposal without committing",
    )
    create.set_defaults(func=cmd_create_concept)

    validate_note = subparsers.add_parser(
        "validate-note",
        help="Validate a single Markdown concept note",
    )
    validate_note.add_argument("path", help="Vault-relative or absolute note path")
    validate_note.add_argument(
        "--vault",
        required=True,
        help="Path to the vault root directory",
    )
    validate_note.set_defaults(func=cmd_validate_note)

    validate_vault = subparsers.add_parser(
        "validate-vault",
        help="Validate all Markdown notes in a vault directory",
    )
    validate_vault.add_argument(
        "vault_dir",
        help="Path to the vault root directory",
    )
    validate_vault.set_defaults(func=cmd_validate_vault)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to a CLI command handler."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
