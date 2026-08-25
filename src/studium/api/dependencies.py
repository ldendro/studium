"""FastAPI dependency helpers."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from studium.app.workspace import WorkspaceContext, WorkspaceRegistry


def get_registry(request: Request) -> WorkspaceRegistry:
    registry = getattr(request.app.state, "workspace_registry", None)
    if not isinstance(registry, WorkspaceRegistry):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Workspace registry is unavailable.",
        )
    return registry


def get_workspace(request: Request) -> WorkspaceContext:
    registry = get_registry(request)
    try:
        return registry.active
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No vault is open. Complete onboarding or open a workspace first.",
        ) from exc
