"""Phase 11 local productization, privacy, export, and recovery routes."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from studium.api.dependencies import RegistryDep, WorkspaceDep
from studium.app.onboarding import import_vault_archive
from studium.app.product import DataArea, ExportKind, ProductService
from studium.app.providers import ProviderSettings

router = APIRouter(prefix="/api/product", tags=["local product"])
MAX_VAULT_ARCHIVE_BYTES = 200 * 1024 * 1024


class ProviderUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    embedding_provider: Literal["local_hash", "sentence_transformers"] = "local_hash"
    embedding_model: str = Field(min_length=1)
    llm_provider: Literal["disabled", "openai_compatible"] = "disabled"
    llm_base_url: str = Field(min_length=1)
    llm_model: str = Field(min_length=1)
    llm_api_key_env: str = Field(min_length=1)
    remote_data_allowed: bool = False

    def settings(self) -> ProviderSettings:
        return ProviderSettings(**self.model_dump())


class ExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ExportKind
    background: bool = True


class BackupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    background: bool = True


class RestoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_vault_path: str = Field(min_length=1)
    app_data_path: str | None = None
    confirmation: str


class ClearDataRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation: str


@router.get("/overview")
def overview(workspace: WorkspaceDep) -> dict[str, Any]:
    return ProductService(workspace).overview()


@router.put("/providers")
def update_providers(
    payload: ProviderUpdateRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        result = ProductService(workspace).update_providers(payload.settings())
    except (ImportError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if result["embedding_space_changed"]:
        job = workspace.jobs.submit(
            "index_sync",
            {"embeddings": True, "reason": "provider_change"},
            lambda progress: _sync_after_provider_change(workspace, progress),
        )
        result["reindex_job"] = job
    else:
        result["reindex_job"] = None
    return result


@router.post("/providers/probe")
def probe_providers(workspace: WorkspaceDep) -> dict[str, Any]:
    return {
        "embedding": workspace.model_space(),
        "llm": workspace.health(probe_llm=True)["llm"],
    }


@router.post("/exports", status_code=status.HTTP_202_ACCEPTED)
def create_export(payload: ExportRequest, workspace: WorkspaceDep) -> dict[str, Any]:
    service = ProductService(workspace)
    if not payload.background:
        return {
            "background": False,
            "artifact": service.create_export(payload.kind, _ignore_progress),
        }
    job = workspace.jobs.submit(
        "workspace_export",
        {"kind": payload.kind},
        lambda progress: service.create_export(payload.kind, progress),
    )
    return {"background": True, "job": job}


@router.get("/exports/{export_id}/download")
def download_export(export_id: str, workspace: WorkspaceDep) -> FileResponse:
    try:
        path = ProductService(workspace).resolve_artifact("export", export_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Export not found.") from exc
    return FileResponse(
        path,
        filename=f"studium-{workspace.vault.root.name}-{export_id}.zip",
        media_type="application/zip",
    )


@router.delete("/exports/{export_id}", status_code=204)
def delete_export(export_id: str, workspace: WorkspaceDep) -> Response:
    try:
        ProductService(workspace).delete_artifact("export", export_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Export not found.") from exc
    return Response(status_code=204)


@router.post("/backups", status_code=status.HTTP_202_ACCEPTED)
def create_backup(payload: BackupRequest, workspace: WorkspaceDep) -> dict[str, Any]:
    service = ProductService(workspace)
    if not payload.background:
        return {
            "background": False,
            "artifact": service.create_backup(_ignore_progress),
        }
    job = workspace.jobs.submit(
        "workspace_backup",
        {},
        lambda progress: service.create_backup(progress),
    )
    return {"background": True, "job": job}


@router.post("/backups/{backup_id}/verify")
def verify_backup(backup_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        return ProductService(workspace).verify_backup(backup_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backup not found.") from exc


@router.post("/backups/{backup_id}/restore")
def restore_backup(
    backup_id: str,
    payload: RestoreRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        return ProductService(workspace).restore_backup_copy(
            backup_id,
            target_vault=Path(payload.target_vault_path),
            app_data_dir=(None if payload.app_data_path is None else Path(payload.app_data_path)),
            confirmation=payload.confirmation,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backup not found.") from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/backups/{backup_id}/download")
def download_backup(backup_id: str, workspace: WorkspaceDep) -> FileResponse:
    try:
        path = ProductService(workspace).resolve_artifact("backup", backup_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backup not found.") from exc
    return FileResponse(
        path,
        filename=f"studium-backup-{workspace.vault.root.name}-{backup_id}.zip",
        media_type="application/zip",
    )


@router.delete("/backups/{backup_id}", status_code=204)
def delete_backup(backup_id: str, workspace: WorkspaceDep) -> Response:
    try:
        ProductService(workspace).delete_artifact("backup", backup_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backup not found.") from exc
    return Response(status_code=204)


@router.delete("/data/{area}")
def clear_data(
    area: DataArea,
    payload: ClearDataRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        return ProductService(workspace).clear_data(
            area,
            confirmation=payload.confirmation,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/vault/import", status_code=status.HTTP_201_CREATED)
async def import_vault(
    file: Annotated[UploadFile, File()],
    registry: RegistryDep,
    target_vault_path: Annotated[str, Form()],
    app_data_path: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    archive = await file.read(MAX_VAULT_ARCHIVE_BYTES + 1)
    if len(archive) > MAX_VAULT_ARCHIVE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Vault archive exceeds the 200 MB compressed limit.",
        )
    try:
        workspace, report = import_vault_archive(
            registry,
            archive_bytes=archive,
            vault_path=Path(target_vault_path),
            app_data_dir=None if not app_data_path else Path(app_data_path),
        )
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "workspace": workspace.health(probe_llm=False),
        "import": report,
    }


def retry_product_job(
    job: dict[str, Any],
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    service = ProductService(workspace)
    job_type = str(job["job_type"])
    payload = job.get("payload")
    values: dict[str, Any] = cast(dict[str, Any], payload) if isinstance(payload, dict) else {}
    if job_type == "workspace_export":
        kind = str(values.get("kind"))
        if kind not in {"markdown", "sources", "complete"}:
            raise ValueError("Export job payload is invalid.")
        export_kind = cast(ExportKind, kind)
        return workspace.jobs.submit(
            job_type,
            {"kind": export_kind},
            lambda progress: service.create_export(export_kind, progress),
            retry_of_id=str(job["id"]),
        )
    if job_type == "workspace_backup":
        return workspace.jobs.submit(
            job_type,
            {},
            lambda progress: service.create_backup(progress),
            retry_of_id=str(job["id"]),
        )
    raise ValueError("This job type cannot be retried from the activity panel.")


def _sync_after_provider_change(workspace: WorkspaceDep, progress: Any) -> dict[str, Any]:
    progress(0.08, "Re-embedding vault with the selected model")
    report = workspace.rebuild_derived_index(synchronize=True)
    progress(0.98, "Publishing the new model space")
    return {} if report is None else report.model_dump(mode="json")


def _ignore_progress(_value: float, _message: str | None = None) -> None:
    return None
