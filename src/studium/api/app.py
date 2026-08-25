"""FastAPI application factory for the local Studium service."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from studium.api.dependencies import RegistryDep, WorkspaceDep, get_registry
from studium.api.models import OpenWorkspaceRequest, SyncRequest
from studium.app.workspace import WorkspaceContext, WorkspaceRegistry


def create_app(
    *,
    vault_root: Path | None = None,
    app_data_dir: Path | None = None,
    frontend_dir: Path | None = None,
) -> FastAPI:
    registry = WorkspaceRegistry()
    if vault_root is not None:
        registry.open(vault_root, app_data_dir=app_data_dir)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        registry.close()

    app = FastAPI(
        title="Studium",
        description="Local-first learning workspace API",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.workspace_registry = registry
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(_system_router())
    _include_feature_routers(app)
    _mount_frontend(app, frontend_dir)
    return app


def _system_router() -> APIRouter:
    router = APIRouter(prefix="/api", tags=["system"])

    @router.get("/health")
    def health(request: Request) -> dict[str, Any]:
        registry = get_registry(request)
        try:
            workspace = registry.active
        except RuntimeError:
            return {"status": "onboarding", "workspace_open": False}
        return {"workspace_open": True, **workspace.health(probe_llm=False)}

    @router.get("/workspace")
    def workspace_status(
        workspace: WorkspaceDep,
    ) -> dict[str, Any]:
        return workspace.health(probe_llm=False)

    @router.post("/workspace/open")
    def open_workspace(
        payload: OpenWorkspaceRequest,
        registry: RegistryDep,
    ) -> dict[str, Any]:
        path = payload.vault()
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Vault directory does not exist: {path}",
            )
        if not path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Vault path is not a directory: {path}",
            )
        opened = registry.open(path, app_data_dir=payload.app_data())
        return opened.health(probe_llm=False)

    @router.post("/index/sync")
    def synchronize(
        payload: SyncRequest,
        workspace: WorkspaceDep,
    ) -> dict[str, Any]:
        if not payload.background:
            report = workspace.sync(embed=payload.embeddings)
            return {"background": False, "report": report.model_dump(mode="json")}

        job = workspace.jobs.submit(
            "index_sync",
            {"embeddings": payload.embeddings},
            lambda progress: _sync_job(workspace, payload.embeddings, progress),
        )
        return {"background": True, "job": job}

    @router.get("/jobs")
    def list_jobs(
        workspace: WorkspaceDep,
    ) -> dict[str, Any]:
        return {"jobs": workspace.jobs.list()}

    @router.get("/jobs/{job_id}")
    def get_job(
        job_id: str,
        workspace: WorkspaceDep,
    ) -> dict[str, Any]:
        try:
            return workspace.jobs.get(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found.") from exc

    @router.get("/providers/health")
    def provider_health(
        workspace: WorkspaceDep,
    ) -> dict[str, Any]:
        return {
            "embedding": workspace.model_space(),
            "llm": workspace.health(probe_llm=True)["llm"],
        }

    return router


def _sync_job(
    workspace: WorkspaceContext,
    embeddings: bool,
    progress: Any,
) -> dict[str, Any]:
    progress(0.1, "Scanning vault")
    report = workspace.sync(embed=embeddings)
    progress(0.95, "Publishing index")
    return report.model_dump(mode="json")


def _include_feature_routers(app: FastAPI) -> None:
    """Import routers lazily so the service foundation stays independently usable."""

    module_names = (
        "studium.api.routes.search",
        "studium.api.routes.create",
        "studium.api.routes.sources",
        "studium.api.routes.review",
        "studium.api.routes.learning",
        "studium.api.routes.product",
    )
    for module_name in module_names:
        try:
            module = __import__(module_name, fromlist=["router"])
        except ModuleNotFoundError as exc:
            if exc.name is not None and module_name.startswith(exc.name):
                continue
            raise
        app.include_router(module.router)


def _mount_frontend(app: FastAPI, frontend_dir: Path | None) -> None:
    root = (
        frontend_dir.expanduser().resolve()
        if frontend_dir is not None
        else Path(__file__).resolve().parents[3] / "web" / "dist"
    )
    index = root / "index.html"
    assets = root / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found.")
        if not index.is_file():
            raise HTTPException(
                status_code=503,
                detail="Frontend build is unavailable. Run the web development server or build it.",
            )
        return FileResponse(index)
