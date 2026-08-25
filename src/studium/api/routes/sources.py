"""Phase 5 source library and intelligence routes."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

from typing import Annotated, Any

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict, Field

from studium.api.dependencies import WorkspaceDep
from studium.sources import SourceService

router = APIRouter(prefix="/api/sources", tags=["sources"])
MAX_UPLOAD_BYTES = 100 * 1024 * 1024


class RetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    source_id: str | None = None
    concept_id: str | None = None
    limit: int = Field(default=12, ge=1, le=50)


class AnalyzeContributionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    concept_id: str
    focus: str = ""


class ContributionDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_source(
    file: Annotated[UploadFile, File()],
    workspace: WorkspaceDep,
    title: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Source exceeds the 100 MB local processing limit.",
        )
    service = SourceService(workspace)
    try:
        source, duplicate = service.stage_upload(
            filename=file.filename or "source.txt",
            content=content,
            mime_type=file.content_type,
            title=title,
        )
        if duplicate:
            return {"source": source, "duplicate": True, "job": None}
        queued = service.enqueue_processing(str(source["id"]))
        return {**queued, "duplicate": False}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("")
def list_sources(
    workspace: WorkspaceDep,
    status_filter: str | None = Query(default=None, alias="status"),
    query: str | None = Query(default=None),
) -> dict[str, Any]:
    return {
        "sources": SourceService(workspace).list(
            status=status_filter,
            query=query,
        )
    }


@router.get("/contributions")
def contributions(
    workspace: WorkspaceDep,
    source_id: str | None = Query(default=None),
    concept_id: str | None = Query(default=None),
) -> dict[str, Any]:
    return {
        "contributions": SourceService(workspace).list_contributions(
            source_id=source_id,
            concept_id=concept_id,
        )
    }


@router.post("/retrieve")
def retrieve(payload: RetrievalRequest, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        hits = SourceService(workspace).retrieve(
            payload.query,
            source_id=payload.source_id,
            concept_id=payload.concept_id,
            limit=payload.limit,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Concept or source not found.") from exc
    return {"hits": [hit.model_dump(mode="json") for hit in hits]}


@router.post("/contributions/analyze")
def analyze(
    payload: AnalyzeContributionRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        result = SourceService(workspace).analyze_contribution(
            source_id=payload.source_id,
            concept_id=payload.concept_id,
            focus=payload.focus,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Concept or source not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@router.patch("/contributions/{contribution_id}")
def decide_contribution(
    contribution_id: str,
    payload: ContributionDecisionRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        return SourceService(workspace).decide_contribution(
            contribution_id,
            payload.status,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Contribution not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{source_id}")
def source_detail(
    source_id: str,
    workspace: WorkspaceDep,
    include_chunks: bool = Query(default=True),
) -> dict[str, Any]:
    try:
        return SourceService(workspace).get(source_id, include_chunks=include_chunks)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Source not found.") from exc


@router.post("/{source_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_source(source_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    service = SourceService(workspace)
    try:
        return service.enqueue_processing(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Source not found.") from exc


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: str, workspace: WorkspaceDep) -> Response:
    try:
        SourceService(workspace).delete(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Source not found.") from exc
    return Response(status_code=204)
