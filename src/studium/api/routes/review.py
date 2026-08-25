"""Phase 6 Agent Review routes embedded in Create."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict

from studium.api.dependencies import WorkspaceDep
from studium.review import ReviewService
from studium.writes import StaleFileError, WriteProposalBlockedError

router = APIRouter(prefix="/api/review", tags=["review"])


class SubmitReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str


class FindingDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    replacement: str | None = None
    decision_note: str | None = None


class PatchPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replacement: str | None = None


class AcceptanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acknowledge_recommended: bool = False


@router.get("/queue")
def queue(workspace: WorkspaceDep) -> dict[str, Any]:
    return {"items": ReviewService(workspace).list_queue()}


@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit(
    payload: SubmitReviewRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        review = ReviewService(workspace).submit(payload.concept_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Draft concept not found.") from exc
    except (ValueError, WriteProposalBlockedError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"review": review.model_dump(mode="json")}


@router.get("/sessions")
def sessions(
    workspace: WorkspaceDep,
    concept_id: str | None = Query(default=None),
) -> dict[str, Any]:
    values = ReviewService(workspace).list_sessions(concept_id)
    return {"sessions": [item.model_dump(mode="json") for item in values]}


@router.get("/sessions/{review_id}")
def session(review_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        value = ReviewService(workspace).get_session(review_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Review session not found.") from exc
    return value.model_dump(mode="json")


@router.post("/sessions/{review_id}/rerun", status_code=status.HTTP_201_CREATED)
def rerun(review_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    service = ReviewService(workspace)
    try:
        previous = service.get_session(review_id)
        review = service.submit(previous.concept_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Review session not found.") from exc
    except (ValueError, WriteProposalBlockedError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"review": review.model_dump(mode="json")}


@router.get("/concepts/{concept_id}/latest")
def latest(concept_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        return ReviewService(workspace).latest(concept_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="No review exists for this concept.") from exc


@router.get("/concepts/{concept_id}/gate")
def acceptance_gate(concept_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        return ReviewService(workspace).acceptance_gate(concept_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Draft concept not found.") from exc


@router.post("/concepts/{concept_id}/accept")
def accept(
    concept_id: str,
    payload: AcceptanceRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        return ReviewService(workspace).accept(
            concept_id,
            acknowledge_recommended=payload.acknowledge_recommended,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Draft concept not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except WriteProposalBlockedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/concepts/{concept_id}/versions")
def versions(concept_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    return {"versions": ReviewService(workspace).versions(concept_id)}


@router.post("/findings/{finding_id}/preview")
def preview_patch(
    finding_id: str,
    payload: PatchPreviewRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        return ReviewService(workspace).preview_patch(
            finding_id,
            payload.replacement,
        ).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Review finding not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/findings/{finding_id}/decision")
def decide_finding(
    finding_id: str,
    payload: FindingDecisionRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        return ReviewService(workspace).decide_finding(
            finding_id,
            action=payload.action,
            replacement=payload.replacement,
            decision_note=payload.decision_note,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Review finding not found.") from exc
    except StaleFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "stale_write",
                "message": str(exc),
                "recovery": "Run review again to refresh comment anchors.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except WriteProposalBlockedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

