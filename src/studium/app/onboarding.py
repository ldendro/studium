"""Vault inspection, creation, and safe local archive import."""

from __future__ import annotations

import io
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from studium.app.demo import seed_demo_workspace
from studium.app.workspace import WorkspaceContext, WorkspaceRegistry
from studium.validation import parse_and_validate
from studium.vault import Vault

MAX_IMPORT_FILES = 10_000
MAX_IMPORT_UNCOMPRESSED_BYTES = 500 * 1024 * 1024


def inspect_vault(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        return {
            "path": str(resolved),
            "exists": False,
            "is_directory": False,
            "markdown_files": 0,
            "valid_concepts": 0,
            "invalid_markdown": 0,
            "ready": False,
            "message": "Directory does not exist.",
        }
    if not resolved.is_dir():
        return {
            "path": str(resolved),
            "exists": True,
            "is_directory": False,
            "markdown_files": 0,
            "valid_concepts": 0,
            "invalid_markdown": 0,
            "ready": False,
            "message": "Path is not a directory.",
        }
    vault = Vault(resolved)
    markdown = vault.list_markdown_files()
    valid = 0
    invalid = 0
    for relative in markdown:
        _parsed, validation = parse_and_validate(vault.read_markdown(relative))
        if validation.critical_errors:
            invalid += 1
        else:
            valid += 1
    return {
        "path": str(resolved),
        "exists": True,
        "is_directory": True,
        "markdown_files": len(markdown),
        "valid_concepts": valid,
        "invalid_markdown": invalid,
        "ready": True,
        "message": (
            "Vault can be opened."
            if not invalid
            else f"Vault can be opened; {invalid} Markdown file(s) will be excluded from the index."
        ),
    }


def create_workspace(
    registry: WorkspaceRegistry,
    *,
    vault_path: Path,
    app_data_dir: Path | None,
    demo: bool,
) -> tuple[WorkspaceContext, dict[str, Any] | None]:
    target = vault_path.expanduser().resolve()
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise FileExistsError("New vault target must not exist or must be an empty directory.")
    target.mkdir(parents=True, exist_ok=True)
    (target / "concepts").mkdir(exist_ok=True)
    workspace = registry.open(target, app_data_dir=app_data_dir)
    seeded = seed_demo_workspace(workspace) if demo else None
    return workspace, seeded


def import_vault_archive(
    registry: WorkspaceRegistry,
    *,
    archive_bytes: bytes,
    vault_path: Path,
    app_data_dir: Path | None,
) -> tuple[WorkspaceContext, dict[str, Any]]:
    target = vault_path.expanduser().resolve()
    if target.exists():
        raise FileExistsError("Import target already exists.")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".studium-import-", dir=target.parent))
    imported_files = 0
    imported_bytes = 0
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            members = [member for member in archive.infolist() if not member.is_dir()]
            if len(members) > MAX_IMPORT_FILES:
                raise ValueError(f"Archive contains more than {MAX_IMPORT_FILES} files.")
            prefix = _common_directory_prefix(members)
            for member in members:
                member_path = _safe_member(member)
                parts = member_path.parts[1:] if prefix else member_path.parts
                if not parts:
                    continue
                imported_bytes += member.file_size
                if imported_bytes > MAX_IMPORT_UNCOMPRESSED_BYTES:
                    raise ValueError("Archive expands beyond the 500 MB import limit.")
                destination = staging.joinpath(*parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output)
                imported_files += 1
        if imported_files == 0:
            raise ValueError("Archive contains no importable files.")
        os.replace(staging, target)
    except zipfile.BadZipFile as exc:
        shutil.rmtree(staging, ignore_errors=True)
        raise ValueError("The selected file is not a readable ZIP archive.") from exc
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    workspace = registry.open(target, app_data_dir=app_data_dir)
    report = inspect_vault(target)
    report.update({"imported_files": imported_files, "imported_bytes": imported_bytes})
    return workspace, report


def _safe_member(member: zipfile.ZipInfo) -> PurePosixPath:
    path = PurePosixPath(member.filename)
    is_symlink = member.external_attr >> 16 & 0o170000 == 0o120000
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
        or is_symlink
    ):
        raise ValueError(f"Unsafe archive member: {member.filename}")
    return path


def _common_directory_prefix(members: list[zipfile.ZipInfo]) -> bool:
    paths = [_safe_member(member) for member in members]
    if not paths or any(len(path.parts) < 2 for path in paths):
        return False
    first = paths[0].parts[0]
    return all(path.parts[0] == first for path in paths)
