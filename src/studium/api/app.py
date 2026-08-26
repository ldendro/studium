"""FastAPI application factory for the local Studium service."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, cast
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from starlette.middleware.base import RequestResponseEndpoint

from studium.api.dependencies import RegistryDep, WorkspaceDep, get_registry
from studium.api.models import CreateWorkspaceRequest, OpenWorkspaceRequest, SyncRequest
from studium.app.onboarding import create_workspace, inspect_vault
from studium.app.workspace import WorkspaceContext, WorkspaceRegistry

logger = logging.getLogger(__name__)
VaultPathQuery = Annotated[str, Query(min_length=1)]


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
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:8765",
            "http://localhost:8765",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def content_safe_request_log(
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid4().hex
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "api_request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "exception_type": type(exc).__name__,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            raise
        response.headers["x-request-id"] = request_id
        logger.info(
            "api_request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return response

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

    @router.get("/workspace/inspect")
    def inspect_workspace(path: VaultPathQuery) -> dict[str, Any]:
        return inspect_vault(Path(path))

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

    @router.post("/workspace/create", status_code=status.HTTP_201_CREATED)
    def create_new_workspace(
        payload: CreateWorkspaceRequest,
        registry: RegistryDep,
    ) -> dict[str, Any]:
        try:
            workspace, seeded = create_workspace(
                registry,
                vault_path=payload.vault(),
                app_data_dir=payload.app_data(),
                demo=payload.demo,
            )
        except (FileExistsError, OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "workspace": workspace.health(probe_llm=False),
            "demo": seeded,
        }

    @router.post("/workspace/close")
    def close_workspace(registry: RegistryDep) -> dict[str, Any]:
        registry.close()
        return {"status": "onboarding", "workspace_open": False}

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
        return {"jobs": [_job_response(job) for job in workspace.jobs.list()]}

    @router.get("/jobs/{job_id}")
    def get_job(
        job_id: str,
        workspace: WorkspaceDep,
    ) -> dict[str, Any]:
        try:
            return _job_response(workspace.jobs.get(job_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found.") from exc

    @router.post("/jobs/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
    def retry_job(job_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
        try:
            job = workspace.jobs.get(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found.") from exc
        if job["status"] in {"queued", "running"}:
            raise HTTPException(status_code=409, detail="Job is still active.")
        payload = job.get("payload")
        values: dict[str, Any] = cast(dict[str, Any], payload) if isinstance(payload, dict) else {}
        job_type = str(job["job_type"])
        try:
            if job_type == "index_sync":
                embeddings = bool(values.get("embeddings", True))
                retried = workspace.jobs.submit(
                    job_type,
                    {"embeddings": embeddings},
                    lambda progress: _sync_job(workspace, embeddings, progress),
                    retry_of_id=job_id,
                )
            elif job_type == "source_processing":
                from studium.sources import SourceService

                source_id = str(values.get("source_id") or "")
                if not source_id:
                    raise ValueError("Source job payload is invalid.")
                retried = SourceService(workspace).enqueue_processing(
                    source_id,
                    retry_of_id=job_id,
                )["job"]
            else:
                from studium.api.routes.product import retry_product_job

                retried = retry_product_job(job, workspace)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Referenced source was not found.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"job": _job_response(retried)}

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


def _job_response(job: dict[str, Any]) -> dict[str, Any]:
    value = dict(job)
    value["retryable"] = value.get("status") == "failed" and value.get("job_type") in {
        "index_sync",
        "source_processing",
        "workspace_export",
        "workspace_backup",
    }
    return value


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


def _resolve_frontend_dir(frontend_dir: Path | None) -> Path:
    if frontend_dir is not None:
        return frontend_dir.expanduser().resolve()
    here = Path(__file__).resolve()
    candidates = [Path.cwd() / "web" / "dist"]
    if len(here.parents) > 3:
        candidates.append(here.parents[3] / "web" / "dist")
    for candidate in candidates:
        if (candidate / "index.html").is_file():
            return candidate.resolve()
    return candidates[0].resolve()


_ASSET_MEDIA_TYPES = {
    ".css": "text/css",
    ".html": "text/html",
    ".ico": "image/x-icon",
    ".js": "text/javascript",
    ".json": "application/json",
    ".map": "application/json",
    ".mjs": "text/javascript",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


def _file_response(path: Path) -> FileResponse:
    return FileResponse(path, media_type=_ASSET_MEDIA_TYPES.get(path.suffix.lower()))


def _mount_frontend(app: FastAPI, frontend_dir: Path | None) -> None:
    root = _resolve_frontend_dir(frontend_dir)
    index = root / "index.html"

    @app.api_route(
        "/{path:path}",
        methods=["GET", "HEAD"],
        include_in_schema=False,
        response_model=None,
    )
    def spa(path: str) -> FileResponse | HTMLResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found.")
        if path:
            candidate = (root / path).resolve()
            if _is_inside(candidate, root) and candidate.is_file():
                return _file_response(candidate)
        if index.is_file():
            return _file_response(index)
        return HTMLResponse(_FRONTEND_MISSING_HTML, status_code=503)


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


_FRONTEND_MISSING_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Studium frontend is not built</title>
    <style>
      body { margin: 0; min-height: 100vh; display: grid; place-items: center;
        background: #0c1016; color: #edf0f4; font-family: system-ui, sans-serif; }
      main { max-width: 36rem; padding: 2rem; }
      code { color: #deb66a; }
    </style>
  </head>
  <body>
    <main>
      <p>Frontend build missing</p>
      <h1>Studium needs the React client before it can open.</h1>
      <p>From the repository root, install the UI, build it, then serve it:</p>
      <p>
        <code>cd web && npm install && npm run build && cd .. && make app</code>
      </p>
    </main>
  </body>
</html>
"""
