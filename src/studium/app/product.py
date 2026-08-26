"""Local productization services: privacy, exports, backups, and data controls."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import tempfile
import zipfile
from collections.abc import Callable, Iterator
from dataclasses import asdict
from pathlib import Path, PurePosixPath
from typing import Any, Literal, cast
from uuid import uuid4

from sqlalchemy import delete, select

from studium.app.config import AppConfig
from studium.app.database import (
    app_transaction,
    draft_snapshots,
    jobs,
    mastery_snapshots,
    note_versions,
    profile_observations,
    retention_cards,
    review_events,
    review_findings,
    review_sessions,
    source_contributions,
    sources,
)
from studium.app.migrations import utc_now
from studium.app.providers import (
    EMBEDDING_PROVIDERS,
    LLM_PROVIDERS,
    ProviderSettings,
    api_key_is_configured,
    provider_route,
)
from studium.app.workspace import WorkspaceContext

Progress = Callable[[float, str | None], None]
ExportKind = Literal["markdown", "sources", "complete"]
DataArea = Literal[
    "derived_index",
    "source_library",
    "learning_history",
    "review_history",
    "jobs",
    "exports",
    "backups",
    "logs",
]

_ARTIFACT_ID = re.compile(r"^(?:export|backup)_[0-9a-f]{32}$")
_BACKUP_FORMAT_VERSION = 1
logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, workspace: WorkspaceContext) -> None:
        self.workspace = workspace

    def overview(self) -> dict[str, Any]:
        settings = self.workspace.provider_settings
        return {
            "providers": {
                **asdict(settings),
                "route": (
                    "disabled"
                    if settings.llm_provider == "disabled"
                    else provider_route(settings.llm_base_url)
                ),
                "api_key_configured": api_key_is_configured(settings),
            },
            "provider_options": {
                "embedding": list(EMBEDDING_PROVIDERS),
                "llm": list(LLM_PROVIDERS),
            },
            "locations": self.data_locations(),
            "migration": {
                "before": self.workspace.migration.before,
                "after": self.workspace.migration.after,
                "applied": list(self.workspace.migration.applied),
            },
            "exports": self.list_exports(),
            "backups": self.list_backups(),
        }

    def update_providers(self, settings: ProviderSettings) -> dict[str, Any]:
        previous_model = self.workspace.model_space()
        self.workspace.update_provider_settings(settings)
        current_model = self.workspace.model_space()
        return {
            "providers": self.overview()["providers"],
            "embedding_space_changed": previous_model != current_model,
            "health": self.workspace.health(probe_llm=False),
        }

    def create_export(self, kind: ExportKind, progress: Progress) -> dict[str, Any]:
        identifier = f"export_{uuid4().hex}"
        target = self.workspace.config.exports_dir / f"{identifier}.zip"
        progress(0.05, "Preparing portable export")
        checksums: dict[str, str] = {}
        with zipfile.ZipFile(
            target,
            mode="x",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as archive:
            if kind in {"markdown", "complete"}:
                markdown_paths = self.workspace.vault.list_markdown_files()
                for index, relative in enumerate(markdown_paths):
                    data = self.workspace.vault.resolve_path(relative).read_bytes()
                    archive_name = f"markdown/{relative}"
                    _write_archive_bytes(archive, archive_name, data, checksums)
                    progress(
                        0.1 + (index + 1) / max(1, len(markdown_paths)) * 0.42,
                        f"Exporting Markdown ({index + 1}/{len(markdown_paths)})",
                    )
            if kind in {"sources", "complete"}:
                source_files = list(_source_asset_files(self.workspace))
                for index, (archive_name, path) in enumerate(source_files):
                    _write_archive_bytes(
                        archive,
                        archive_name,
                        path.read_bytes(),
                        checksums,
                    )
                    progress(
                        0.55 + (index + 1) / max(1, len(source_files)) * 0.35,
                        f"Exporting sources ({index + 1}/{len(source_files)})",
                    )
            manifest = {
                "format": "studium-export",
                "format_version": 1,
                "id": identifier,
                "kind": kind,
                "created_at": utc_now(),
                "vault_id": self.workspace.vault_id,
                "vault_name": self.workspace.vault.root.name,
                "file_count": len(checksums),
                "checksums": checksums,
            }
            archive.writestr("manifest.json", _json_bytes(manifest))
        progress(1.0, "Export ready")
        logger.info(
            "workspace_export_created",
            extra={"artifact_id": identifier, "export_kind": kind},
        )
        return self._artifact_descriptor(target, "export")

    def list_exports(self) -> list[dict[str, Any]]:
        return self._list_artifacts(self.workspace.config.exports_dir, "export")

    def create_backup(self, progress: Progress) -> dict[str, Any]:
        identifier = f"backup_{uuid4().hex}"
        target = self.workspace.config.backups_dir / f"{identifier}.zip"
        checksums: dict[str, str] = {}
        progress(0.03, "Taking a consistent application snapshot")
        with (
            self.workspace.maintenance_lock(),
            tempfile.TemporaryDirectory(
                prefix=".studium-backup-",
                dir=self.workspace.config.backups_dir,
            ) as temporary,
        ):
            database_snapshot = Path(temporary) / "studium.sqlite"
            _snapshot_sqlite(self.workspace.config.database_path, database_snapshot)
            vault_files = list(_tree_files(self.workspace.vault.root))
            source_files = list(_source_asset_files(self.workspace))
            with zipfile.ZipFile(
                target,
                mode="x",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=6,
            ) as archive:
                total = max(1, len(vault_files) + len(source_files) + 1)
                completed = 0
                for relative, path in vault_files:
                    _write_archive_bytes(
                        archive,
                        f"vault/{relative}",
                        path.read_bytes(),
                        checksums,
                    )
                    completed += 1
                    progress(
                        0.08 + completed / total * 0.76,
                        f"Snapshotting vault ({completed}/{total})",
                    )
                _write_archive_bytes(
                    archive,
                    "app/studium.sqlite",
                    database_snapshot.read_bytes(),
                    checksums,
                )
                completed += 1
                for archive_name, path in source_files:
                    _write_archive_bytes(
                        archive,
                        f"app/{archive_name}",
                        path.read_bytes(),
                        checksums,
                    )
                    completed += 1
                    progress(
                        0.08 + completed / total * 0.76,
                        f"Snapshotting local state ({completed}/{total})",
                    )
                soul = self.workspace.config.workspace_dir / "soul.md"
                if soul.is_file():
                    _write_archive_bytes(
                        archive,
                        "app/soul.md",
                        soul.read_bytes(),
                        checksums,
                    )
                manifest = {
                    "format": "studium-backup",
                    "format_version": _BACKUP_FORMAT_VERSION,
                    "id": identifier,
                    "created_at": utc_now(),
                    "vault_id": self.workspace.vault_id,
                    "vault_name": self.workspace.vault.root.name,
                    "app_schema_version": self.workspace.migration.after,
                    "file_count": len(checksums),
                    "checksums": checksums,
                }
                archive.writestr("manifest.json", _json_bytes(manifest))
        progress(1.0, "Backup verified and ready")
        verification = self.verify_backup(identifier)
        if not verification["valid"]:
            target.unlink(missing_ok=True)
            raise RuntimeError("The backup failed integrity verification.")
        logger.info("workspace_backup_created", extra={"artifact_id": identifier})
        return self._artifact_descriptor(target, "backup")

    def list_backups(self) -> list[dict[str, Any]]:
        return self._list_artifacts(self.workspace.config.backups_dir, "backup")

    def verify_backup(self, identifier: str) -> dict[str, Any]:
        path = self.resolve_artifact("backup", identifier)
        errors: list[str] = []
        checked = 0
        try:
            with zipfile.ZipFile(path) as archive:
                corrupt = archive.testzip()
                if corrupt is not None:
                    errors.append(f"Archive CRC failed for {corrupt}.")
                manifest = _read_manifest(archive, expected_format="studium-backup")
                checksums = _string_mapping(manifest.get("checksums"))
                for name, expected in checksums.items():
                    try:
                        actual = hashlib.sha256(archive.read(name)).hexdigest()
                    except KeyError:
                        errors.append(f"Missing archived file: {name}")
                        continue
                    checked += 1
                    if actual != expected:
                        errors.append(f"Checksum mismatch: {name}")
        except (KeyError, OSError, ValueError, zipfile.BadZipFile) as exc:
            errors.append(f"{type(exc).__name__}: backup could not be read")
        return {
            "id": identifier,
            "valid": not errors,
            "checked_files": checked,
            "errors": errors,
        }

    def restore_backup_copy(
        self,
        identifier: str,
        *,
        target_vault: Path,
        app_data_dir: Path | None,
        confirmation: str,
    ) -> dict[str, Any]:
        if confirmation != "RESTORE COPY":
            raise ValueError("Type RESTORE COPY to confirm non-destructive recovery.")
        verification = self.verify_backup(identifier)
        if not verification["valid"]:
            raise ValueError("Backup integrity verification failed.")
        target = target_vault.expanduser().resolve()
        current = self.workspace.vault.root
        if target == current or target.is_relative_to(current) or current.is_relative_to(target):
            raise ValueError("Recovery target must be separate from the active vault.")
        if target.exists():
            raise FileExistsError("Recovery target already exists.")
        target.parent.mkdir(parents=True, exist_ok=True)
        config = AppConfig(vault_root=target, app_data_dir=app_data_dir)
        if config.workspace_dir.exists():
            raise FileExistsError("Recovery application-data target already exists.")

        archive_path = self.resolve_artifact("backup", identifier)
        staging = Path(tempfile.mkdtemp(prefix=".studium-restore-", dir=target.parent))
        vault_stage = staging / "vault"
        app_stage = staging / "app"
        created_workspace = False
        try:
            with zipfile.ZipFile(archive_path) as archive:
                for member in archive.infolist():
                    if member.filename == "manifest.json" or member.is_dir():
                        continue
                    relative = _safe_archive_member(member)
                    if relative.parts[0] not in {"vault", "app"}:
                        continue
                    destination = staging.joinpath(*relative.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source, destination.open("wb") as output:
                        shutil.copyfileobj(source, output)
            if not vault_stage.is_dir() or not (app_stage / "studium.sqlite").is_file():
                raise ValueError(
                    "Backup does not contain a restorable vault and application state."
                )
            os.replace(vault_stage, target)
            config.ensure_directories()
            created_workspace = True
            shutil.copy2(app_stage / "studium.sqlite", config.database_path)
            restored_sources = app_stage / "sources"
            if restored_sources.is_dir():
                shutil.copytree(
                    restored_sources,
                    config.source_assets_dir,
                    dirs_exist_ok=True,
                )
            if (app_stage / "soul.md").is_file():
                shutil.copy2(app_stage / "soul.md", config.workspace_dir / "soul.md")
            _retarget_restored_database(config)
        except Exception:
            shutil.rmtree(target, ignore_errors=True)
            if created_workspace:
                shutil.rmtree(config.workspace_dir, ignore_errors=True)
            raise
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        logger.info("workspace_backup_restored", extra={"artifact_id": identifier})
        return {
            "backup_id": identifier,
            "vault_path": str(target),
            "app_data_path": str(config.resolved_app_data_dir),
            "message": "Recovered into a separate copy. Open it when you are ready.",
        }

    def resolve_artifact(self, kind: Literal["export", "backup"], identifier: str) -> Path:
        if not _ARTIFACT_ID.fullmatch(identifier) or not identifier.startswith(f"{kind}_"):
            raise KeyError(identifier)
        root = (
            self.workspace.config.exports_dir
            if kind == "export"
            else self.workspace.config.backups_dir
        )
        path = root / f"{identifier}.zip"
        if not path.is_file():
            raise KeyError(identifier)
        return path

    def delete_artifact(
        self,
        kind: Literal["export", "backup"],
        identifier: str,
    ) -> None:
        self.resolve_artifact(kind, identifier).unlink()

    def data_locations(self) -> list[dict[str, Any]]:
        config = self.workspace.config
        return [
            _location("vault", "Markdown vault", config.resolved_vault_root, False),
            _location("app_database", "Application database", config.database_path, False),
            _location(
                "derived_index",
                "Rebuildable concept index",
                self.workspace.index_config.database_path,
                True,
            ),
            _location("source_library", "Original source assets", config.source_assets_dir, True),
            _location("exports", "Generated exports", config.exports_dir, True),
            _location("backups", "Local backups", config.backups_dir, True),
            _location("logs", "Content-safe diagnostic logs", config.logs_dir, True),
        ]

    def clear_data(self, area: DataArea, *, confirmation: str) -> dict[str, Any]:
        expected = f"DELETE {area.replace('_', ' ').upper()}"
        if confirmation != expected:
            raise ValueError(f"Type {expected} to confirm.")
        if area == "derived_index":
            self.workspace.rebuild_derived_index(synchronize=False)
        elif area == "source_library":
            with app_transaction(self.workspace.app_engine) as connection:
                connection.execute(delete(source_contributions))
                connection.execute(delete(sources))
            shutil.rmtree(self.workspace.config.source_assets_dir, ignore_errors=True)
            self.workspace.config.source_assets_dir.mkdir(parents=True, exist_ok=True)
        elif area == "learning_history":
            with app_transaction(self.workspace.app_engine) as connection:
                connection.execute(delete(mastery_snapshots))
                connection.execute(delete(review_events))
                connection.execute(delete(retention_cards))
                connection.execute(delete(profile_observations))
            (self.workspace.config.workspace_dir / "soul.md").unlink(missing_ok=True)
        elif area == "review_history":
            with app_transaction(self.workspace.app_engine) as connection:
                connection.execute(delete(review_findings))
                connection.execute(delete(review_sessions))
                connection.execute(delete(note_versions))
                connection.execute(delete(draft_snapshots))
        elif area == "jobs":
            with app_transaction(self.workspace.app_engine) as connection:
                connection.execute(delete(jobs).where(jobs.c.status.not_in(["queued", "running"])))
        elif area == "exports":
            _clear_directory(self.workspace.config.exports_dir)
        elif area == "backups":
            _clear_directory(self.workspace.config.backups_dir)
        elif area == "logs":
            for path in self.workspace.config.logs_dir.glob("studium.jsonl*"):
                if path.name == "studium.jsonl":
                    path.write_text("", encoding="utf-8")
                elif path.is_file():
                    path.unlink()
        logger.warning("workspace_data_cleared", extra={"data_area": area})
        return {"area": area, "cleared": True, "locations": self.data_locations()}

    def _list_artifacts(
        self,
        directory: Path,
        kind: Literal["export", "backup"],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in directory.glob(f"{kind}_*.zip"):
            try:
                items.append(self._artifact_descriptor(path, kind))
            except (KeyError, OSError, ValueError, zipfile.BadZipFile):
                continue
        return sorted(
            items,
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )

    def _artifact_descriptor(
        self,
        path: Path,
        kind: Literal["export", "backup"],
    ) -> dict[str, Any]:
        expected = f"studium-{kind}"
        with zipfile.ZipFile(path) as archive:
            manifest = _read_manifest(archive, expected_format=expected)
        identifier = str(manifest["id"])
        if path.stem != identifier:
            raise ValueError("Artifact filename does not match its manifest.")
        return {
            "id": identifier,
            "artifact_type": kind,
            "kind": manifest.get("kind"),
            "created_at": str(manifest["created_at"]),
            "size_bytes": path.stat().st_size,
            "file_count": int(manifest.get("file_count") or 0),
            "download_url": f"/api/product/{kind}s/{identifier}/download",
        }


def _snapshot_sqlite(source: Path, target: Path) -> None:
    with (
        sqlite3.connect(source) as source_connection,
        sqlite3.connect(target) as target_connection,
    ):
        source_connection.backup(target_connection)


def _source_asset_files(workspace: WorkspaceContext) -> Iterator[tuple[str, Path]]:
    root = workspace.config.source_assets_dir.resolve()
    with workspace.app_engine.connect() as connection:
        rows = connection.execute(
            select(sources.c.id, sources.c.asset_path, sources.c.original_filename)
        ).all()
    for row in rows:
        if row.asset_path is None:
            continue
        path = Path(str(row.asset_path)).resolve()
        if not path.is_file() or not path.is_relative_to(root):
            continue
        filename = Path(str(row.original_filename or path.name)).name
        yield f"sources/{row.id}/{filename}", path


def _tree_files(root: Path) -> Iterator[tuple[str, Path]]:
    excluded = {".git", ".studium-data", "__pycache__"}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        yield relative.as_posix(), path


def _write_archive_bytes(
    archive: zipfile.ZipFile,
    name: str,
    data: bytes,
    checksums: dict[str, str],
) -> None:
    archive.writestr(name, data)
    checksums[name] = hashlib.sha256(data).hexdigest()


def _json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True).encode("utf-8")


def _read_manifest(
    archive: zipfile.ZipFile,
    *,
    expected_format: str,
) -> dict[str, Any]:
    loaded: Any = json.loads(archive.read("manifest.json"))
    if not isinstance(loaded, dict):
        raise ValueError("Artifact manifest is missing or invalid.")
    payload = cast(dict[str, Any], loaded)
    if payload.get("format") != expected_format:
        raise ValueError("Artifact manifest is missing or invalid.")
    return payload


def _string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    mapping = cast(dict[Any, Any], value)
    return {
        str(key): str(item)
        for key, item in mapping.items()
        if isinstance(key, str) and isinstance(item, str)
    }


def _safe_archive_member(member: zipfile.ZipInfo) -> PurePosixPath:
    path = PurePosixPath(member.filename)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
        or member.external_attr >> 16 & 0o170000 == 0o120000
    ):
        raise ValueError(f"Unsafe backup member: {member.filename}")
    return path


def _retarget_restored_database(config: AppConfig) -> None:
    now = utc_now()
    with sqlite3.connect(config.database_path) as connection:
        connection.execute(
            "UPDATE app_metadata SET vault_path = ?, vault_identifier = ?, updated_at = ?",
            (str(config.resolved_vault_root), config.vault_identifier, now),
        )
        rows = connection.execute(
            "SELECT id, original_filename, asset_path FROM sources"
        ).fetchall()
        for source_id, original_filename, old_asset_path in rows:
            filename = Path(str(original_filename or old_asset_path or "source")).name
            new_path = config.source_assets_dir / str(source_id) / filename
            connection.execute(
                "UPDATE sources SET asset_path = ?, updated_at = ? WHERE id = ?",
                (str(new_path), now, source_id),
            )
        connection.commit()


def _location(
    identifier: str,
    label: str,
    path: Path,
    clearable: bool,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "label": label,
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": _path_size(path),
        "clearable": clearable,
        "confirmation": (f"DELETE {identifier.replace('_', ' ').upper()}" if clearable else None),
    }


def _path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if not path.is_dir():
        return 0
    return sum(
        item.stat().st_size for item in path.rglob("*") if item.is_file() and not item.is_symlink()
    )


def _clear_directory(directory: Path) -> None:
    for item in directory.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
