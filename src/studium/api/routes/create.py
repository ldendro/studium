"""Phase 4 recommendation-led Create routes."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict

from studium.api.dependencies import WorkspaceDep
from studium.create import (
    CreateIntent,
    CreateProposal,
    GeneratedDraft,
    build_draft,
    build_preview,
    commit_draft,
    list_drafts,
    propose_create,
    save_draft_snapshot,
)
from studium.create.service import delete_draft, get_draft
from studium.writes import (
    CollisionError,
    StaleFileError,
    WriteProposalBlockedError,
)

router = APIRouter(prefix="/api/create", tags=["create"])


class SaveDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft: GeneratedDraft
    title: str
    recommendation: dict[str, Any] | None = None
    snapshot_id: str | None = None


@router.post("/propose", response_model=CreateProposal)
def propose(payload: CreateIntent, workspace: WorkspaceDep) -> CreateProposal:
    return propose_create(workspace, payload)


@router.post("/draft", response_model=GeneratedDraft)
def generate_draft(payload: CreateProposal, workspace: WorkspaceDep) -> GeneratedDraft:
    try:
        return build_draft(workspace, payload)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/preview")
def preview(payload: GeneratedDraft, workspace: WorkspaceDep) -> dict[str, Any]:
    return build_preview(workspace, payload).model_dump(mode="json")


@router.post("/commit")
def commit(payload: GeneratedDraft, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        return commit_draft(workspace, payload).model_dump(mode="json")
    except StaleFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "stale_write",
                "message": str(exc),
                "recovery": "Reload the note, review the merged diff, and commit again.",
            },
        ) from exc
    except CollisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "collision", "message": str(exc)},
        ) from exc
    except WriteProposalBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "validation_blocked", "message": str(exc)},
        ) from exc


@router.get("/drafts")
def drafts(workspace: WorkspaceDep) -> dict[str, Any]:
    return {"drafts": list_drafts(workspace)}


@router.get("/drafts/{draft_id}")
def draft(draft_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        return get_draft(workspace, draft_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Draft not found.") from exc


@router.put("/drafts")
def save(payload: SaveDraftRequest, workspace: WorkspaceDep) -> dict[str, Any]:
    return save_draft_snapshot(
        workspace,
        payload.draft,
        title=payload.title,
        recommendation=payload.recommendation,
        snapshot_id=payload.snapshot_id,
    )


@router.delete("/drafts/{draft_id}", status_code=204)
def remove_draft(draft_id: str, workspace: WorkspaceDep) -> Response:
    try:
        delete_draft(workspace, draft_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Draft not found.") from exc
    return Response(status_code=204)
