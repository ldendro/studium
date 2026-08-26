"""FastAPI local-service tests."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from studium.api import create_app


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    app = create_app(app_data_dir=tmp_path / "app-data")
    with TestClient(app) as test_client:
        yield test_client


def test_health_starts_in_onboarding(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace_open"] is False
    assert payload["status"] == "onboarding"


def test_workspace_create_demo_search_and_product_controls(
    client: TestClient,
    tmp_path: Path,
) -> None:
    vault = tmp_path / "demo-vault"
    created = client.post(
        "/api/workspace/create",
        json={"vault_path": str(vault), "app_data_path": str(tmp_path / "app-data"), "demo": True},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["workspace"]["workspace_open"] is True
    assert body["demo"]["seeded"] is True

    health = client.get("/api/health")
    assert health.json()["vault_name"] == "demo-vault"

    inspect = client.get("/api/workspace/inspect", params={"path": str(vault)})
    assert inspect.json()["valid_concepts"] >= 4

    search = client.post("/api/search", json={"text": "learning rate"})
    assert search.status_code == 200, search.text
    assert search.json()["ranked_concepts"]

    overview = client.get("/api/product/overview")
    assert overview.status_code == 200
    assert overview.json()["providers"]["llm_provider"] == "disabled"

    blocked = client.put(
        "/api/product/providers",
        json={
            "embedding_provider": "local_hash",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_provider": "openai_compatible",
            "llm_base_url": "https://api.example.test/v1",
            "llm_model": "gpt-test",
            "llm_api_key_env": "STUDIUM_LLM_API_KEY",
            "remote_data_allowed": False,
        },
    )
    assert blocked.status_code == 422

    export = client.post("/api/product/exports", json={"kind": "markdown", "background": False})
    assert export.status_code == 202
    export_id = export.json()["artifact"]["id"]
    download = client.get(f"/api/product/exports/{export_id}/download")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/zip")

    jobs = client.get("/api/jobs")
    assert jobs.status_code == 200
    assert "jobs" in jobs.json()

    closed = client.post("/api/workspace/close")
    assert closed.status_code == 200
    assert closed.json()["workspace_open"] is False


def test_missing_frontend_explains_build_steps(tmp_path: Path) -> None:
    app = create_app(app_data_dir=tmp_path / "app-data", frontend_dir=tmp_path / "missing-dist")
    with TestClient(app) as test_client:
        response = test_client.get("/")
        assert response.status_code == 503
        assert "text/html" in response.headers["content-type"]
        assert "npm run build" in response.text


def test_spa_serves_javascript_assets_instead_of_index(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(
        "<!doctype html><div id='root'>shell</div><script src='/assets/app.js'></script>",
        encoding="utf-8",
    )
    (assets / "app.js").write_text("window.__studium = true;", encoding="utf-8")
    app = create_app(app_data_dir=tmp_path / "app-data", frontend_dir=dist)
    with TestClient(app) as test_client:
        html = test_client.get("/")
        assert html.status_code == 200
        assert "shell" in html.text
        javascript = test_client.get("/assets/app.js")
        assert javascript.status_code == 200
        assert "window.__studium" in javascript.text
        content_type = javascript.headers["content-type"]
        assert "javascript" in content_type
        assert "text/html" not in content_type
        nested = test_client.get("/search")
        assert nested.status_code == 200
        assert "shell" in nested.text
        assert "text/html" in nested.headers["content-type"]
