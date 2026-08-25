"""Phases 7-10 ongoing learning system routes."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field

from studium.api.dependencies import WorkspaceDep
from studium.app.learning import (
    BacklogService,
    MasteryService,
    ProfileService,
    RetentionService,
)
from studium.app.learning_models import (
    BacklogItemType,
    BacklogOrigin,
    BacklogStatus,
    ProfileCategory,
    ProfileObservationStatus,
)

router = APIRouter(tags=["learning"])

BacklogStatusQuery = Annotated[
    BacklogStatus | None,
    Query(alias="status"),
]
ProfileStatusQuery = Annotated[
    ProfileObservationStatus | None,
    Query(alias="status"),
]


def _empty_evidence() -> list[dict[str, Any]]:
    return []


class BacklogCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    item_type: BacklogItemType = BacklogItemType.NEW_CONCEPT
    reason: str
    origin: BacklogOrigin = BacklogOrigin.MANUAL
    priority: int = Field(default=50, ge=0, le=100)
    related_concept_id: str | None = None
    required_by: list[str] = Field(default_factory=list)
    source_query: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BacklogCandidatesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: list[dict[str, Any]]


class BacklogUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: BacklogStatus | None = None
    priority: int | None = Field(default=None, ge=0, le=100)
    reason: str | None = None
    title: str | None = None


class ResolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str | None = None


class GenerateCardsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str | None = None


class RetentionCardUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pinned: bool | None = None
    suspended: bool | None = None
    prompt: str | None = None


class RetentionReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    card_id: str
    response: str
    self_rating: int = Field(ge=0, le=5)
    confidence: int | None = Field(default=None, ge=1, le=5)
    latency_ms: int | None = Field(default=None, ge=0)
    hints_used: int = Field(default=0, ge=0)


class MasteryRecomputeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str | None = None


class ObservationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: ProfileCategory
    statement: str
    evidence: list[dict[str, Any]] = Field(default_factory=_empty_evidence)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: ProfileObservationStatus = ProfileObservationStatus.ACCEPTED
    pinned: bool = False
    source: str = "manual"


class ObservationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str | None = None
    category: ProfileCategory | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    status: ProfileObservationStatus | None = None
    pinned: bool | None = None


@router.get("/api/backlog")
def list_backlog(
    workspace: WorkspaceDep,
    status_filter: BacklogStatusQuery = None,
    origin: BacklogOrigin | None = None,
    item_type: BacklogItemType | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    items = BacklogService(workspace).list(
        status=status_filter,
        origin=origin,
        item_type=item_type,
        query=query,
    )
    return {"items": [item.model_dump(mode="json") for item in items]}


@router.post("/api/backlog", status_code=status.HTTP_201_CREATED)
def create_backlog(
    payload: BacklogCreateRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        item = BacklogService(workspace).create(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return item.model_dump(mode="json")


@router.post("/api/backlog/from-candidates", status_code=status.HTTP_201_CREATED)
def create_backlog_candidates(
    payload: BacklogCandidatesRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    items = BacklogService(workspace).create_many(payload.candidates)
    return {"items": [item.model_dump(mode="json") for item in items]}


@router.post("/api/backlog/derive")
def derive_backlog(workspace: WorkspaceDep) -> dict[str, Any]:
    items = BacklogService(workspace).derive_missing_relationships()
    return {"items": [item.model_dump(mode="json") for item in items]}


@router.patch("/api/backlog/{item_id}")
def update_backlog(
    item_id: str,
    payload: BacklogUpdateRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        return BacklogService(workspace).update(
            item_id,
            **payload.model_dump(),
        ).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backlog item not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/api/backlog/{item_id}/promote")
def promote_backlog(item_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        return BacklogService(workspace).promote(item_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backlog item not found.") from exc


@router.post("/api/backlog/{item_id}/confirm-resolution")
def confirm_backlog_resolution(
    item_id: str,
    payload: ResolutionRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        return BacklogService(workspace).confirm_resolution(
            item_id,
            payload.concept_id,
        ).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backlog item not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/api/backlog/{item_id}", status_code=204)
def dismiss_backlog(item_id: str, workspace: WorkspaceDep) -> Response:
    try:
        BacklogService(workspace).update(item_id, status=BacklogStatus.DISMISSED)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backlog item not found.") from exc
    return Response(status_code=204)


@router.get("/api/retention/cards")
def retention_cards_list(
    workspace: WorkspaceDep,
    queue: str | None = Query(default=None),
    concept_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    cards = RetentionService(workspace).list_cards(
        queue=queue,
        concept_id=concept_id,
        limit=limit,
    )
    return {"cards": [card.model_dump(mode="json") for card in cards]}


@router.get("/api/retention/due")
def retention_due(
    workspace: WorkspaceDep,
    limit: int = Query(default=30, ge=1, le=100),
) -> dict[str, Any]:
    cards = RetentionService(workspace).due(limit=limit)
    return {"cards": [card.model_dump(mode="json") for card in cards]}


@router.post("/api/retention/cards/generate")
def generate_retention_cards(
    payload: GenerateCardsRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    cards = RetentionService(workspace).generate(payload.concept_id)
    return {"cards": [card.model_dump(mode="json") for card in cards]}


@router.patch("/api/retention/cards/{card_id}")
def update_retention_card(
    card_id: str,
    payload: RetentionCardUpdateRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        card = RetentionService(workspace).update_card(
            card_id,
            **payload.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Retention card not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return card.model_dump(mode="json")


@router.post("/api/retention/review")
def review_retention(
    payload: RetentionReviewRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        result = RetentionService(workspace).review(**payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Retention card not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@router.get("/api/retention/stats")
def retention_stats(workspace: WorkspaceDep) -> dict[str, Any]:
    return RetentionService(workspace).stats()


@router.get("/api/mastery/summary")
def mastery_summary(workspace: WorkspaceDep) -> dict[str, Any]:
    return MasteryService(workspace).summary()


@router.get("/api/mastery/concepts/{concept_id}")
def concept_mastery(concept_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        return MasteryService(workspace).concept(concept_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Concept mastery not found.") from exc


@router.post("/api/mastery/recompute")
def recompute_mastery(
    payload: MasteryRecomputeRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    records = MasteryService(workspace).recompute(payload.concept_id)
    return {"concepts": [item.model_dump(mode="json") for item in records]}


@router.get("/api/mastery/graph")
def mastery_graph(workspace: WorkspaceDep) -> dict[str, Any]:
    return MasteryService(workspace).graph()


@router.get("/api/profile/observations")
def observations(
    workspace: WorkspaceDep,
    status_filter: ProfileStatusQuery = None,
) -> dict[str, Any]:
    values = ProfileService(workspace).list(status=status_filter)
    return {"observations": [item.model_dump(mode="json") for item in values]}


@router.post("/api/profile/observations", status_code=status.HTTP_201_CREATED)
def create_observation(
    payload: ObservationCreateRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        item = ProfileService(workspace).create(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return item.model_dump(mode="json")


@router.patch("/api/profile/observations/{observation_id}")
def update_observation(
    observation_id: str,
    payload: ObservationUpdateRequest,
    workspace: WorkspaceDep,
) -> dict[str, Any]:
    try:
        item = ProfileService(workspace).update(
            observation_id,
            **payload.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Profile observation not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return item.model_dump(mode="json")


@router.post("/api/profile/infer")
def infer_profile(workspace: WorkspaceDep) -> dict[str, Any]:
    values = ProfileService(workspace).infer()
    return {"observations": [item.model_dump(mode="json") for item in values]}


@router.get("/api/profile/soul")
def soul(workspace: WorkspaceDep) -> dict[str, Any]:
    return ProfileService(workspace).write_soul()

