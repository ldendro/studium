"""validate-note CLI command."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from studium.cli.formatting import format_validation_result
from studium.cli.paths import resolve_note_path
from studium.schemas import ValidationOperation
from studium.validation import parse_and_validate
from studium.vault import Vault
from studium.vault.errors import VaultError


def cmd_validate_note(args: Namespace) -> int:
    """Validate a single concept note under a vault."""
    try:
        vault = Vault(Path(args.vault))
        relative_path = resolve_note_path(vault, args.path)
        raw = vault.read_markdown(relative_path)
        _, result = parse_and_validate(raw, operation=ValidationOperation.PARSE)
        print(format_validation_result(relative_path, result))
        return 0 if result.is_valid else 1
    except VaultError as exc:
        print(f"error: {exc}")
        return 1
