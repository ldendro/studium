"""Create, source, and review API smoke tests against a demo workspace."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from studium.api import create_app
from studium.app.demo import seed_demo_workspace
from studium.app.workspace import WorkspaceRegistry
from studium.serialization.concept_id import generate_concept_id


@pytest.fixture
def demo_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "concepts").mkdir()
    app = create_app(vault_root=vault, app_data_dir=tmp_path / "app-data")
    registry = app.state.workspace_registry
    assert isinstance(registry, WorkspaceRegistry)
    seed_demo_workspace(registry.active)
    with TestClient(app) as test_client:
        yield test_client


def test_create_propose_and_source_library(demo_client: TestClient) -> None:
    proposal = demo_client.post(
        "/api/create/propose",
        json={"intent": "Adaptive Learning Rates", "learning_goal": "Compare schedules"},
    )
    assert proposal.status_code == 200, proposal.text
    payload = proposal.json()
    assert payload["canonical_title"]
    assert payload["modules"]

    sources = demo_client.get("/api/sources")
    assert sources.status_code == 200
    records = sources.json()["sources"]
    assert records
    source_id = records[0]["id"]
    retrieved = demo_client.post(
        "/api/sources/retrieve",
        json={"query": "momentum velocity", "source_id": source_id, "limit": 5},
    )
    assert retrieved.status_code == 200
    assert retrieved.json()["hits"]

    queue = demo_client.get("/api/review/queue")
    assert queue.status_code == 200
    assert any(
        item["concept_id"] == generate_concept_id("Momentum Optimization")
        for item in queue.json()["items"]
    )

    backlog = demo_client.get("/api/backlog")
    assert backlog.status_code == 200
    assert backlog.json()["items"]

    retention = demo_client.get("/api/retention/stats")
    assert retention.status_code == 200

    mastery = demo_client.get("/api/mastery/summary")
    assert mastery.status_code == 200
    assert mastery.json()["concepts"]

    profile = demo_client.get("/api/profile/observations")
    assert profile.status_code == 200
    assert profile.json()["observations"]
