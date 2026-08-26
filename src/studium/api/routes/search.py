"""Phase 3 Search, concept detail, and graph routes."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from studium.api.dependencies import WorkspaceDep
from studium.app.search import (
    concept_detail,
    graph_projection,
    search_facets,
    search_workspace,
)
from studium.index.search import ConceptSearchFilters

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    filters: ConceptSearchFilters = Field(default_factory=ConceptSearchFilters)
    include_modules: bool = True
    include_drafts: bool = False
    diagnostics: bool = False


@router.post("/search")
def run_search(payload: SearchRequest, workspace: WorkspaceDep) -> dict[str, Any]:
    return search_workspace(
        workspace,
        text=payload.text,
        filters=payload.filters,
        include_modules=payload.include_modules,
        include_drafts=payload.include_drafts,
        diagnostics=payload.diagnostics,
    )


@router.get("/search/facets")
def facets(
    workspace: WorkspaceDep,
    include_drafts: bool = Query(default=False),
) -> dict[str, Any]:
    return search_facets(workspace, include_drafts=include_drafts)


@router.get("/concepts/{concept_id}")
def get_concept(concept_id: str, workspace: WorkspaceDep) -> dict[str, Any]:
    try:
        return concept_detail(workspace, concept_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Concept not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/graph")
def get_graph(
    workspace: WorkspaceDep,
    center: str | None = Query(default=None),
    domain: str | None = Query(default=None),
    include_drafts: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        return graph_projection(
            workspace,
            center=center,
            domain=domain,
            include_drafts=include_drafts,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Concept not found.") from exc
