"""validate-vault CLI command."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from studium.cli.formatting import format_validation_result
from studium.schemas import ValidationOperation
from studium.validation import parse_and_validate
from studium.vault import Vault
from studium.vault.errors import VaultError


def cmd_validate_vault(args: Namespace) -> int:
    """Validate all Markdown notes under a vault directory."""
    try:
        vault = Vault(Path(args.vault_dir))
        paths = vault.list_markdown_files()
        critical_count = 0
        warning_count = 0

        for relative_path in paths:
            raw = vault.read_markdown(relative_path)
            _, result = parse_and_validate(raw, operation=ValidationOperation.PARSE)
            critical_count += len(result.critical_errors)
            warning_count += len(result.warnings)
            print(format_validation_result(relative_path, result))
            print()

        file_count = len(paths)
        print(f"Summary: {file_count} files, {critical_count} critical, {warning_count} warnings")
        return 1 if critical_count else 0
    except VaultError as exc:
        print(f"error: {exc}")
        return 1
