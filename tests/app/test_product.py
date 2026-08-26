"""Productization: export, backup, restore, deletion, and demo seed."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from studium.app.demo import seed_demo_workspace
from studium.app.product import ProductService
from studium.app.providers import ProviderSettings
from studium.app.search import search_workspace
from studium.app.workspace import WorkspaceContext
from studium.review import ReviewService
from studium.serialization.concept_id import generate_concept_id


def test_demo_seed_search_review_export_and_backup(workspace: WorkspaceContext, tmp_path: Path) -> None:
    result = seed_demo_workspace(workspace)
    assert result["seeded"] is True
    assert workspace.vault.exists("concepts/gradient-descent.md")

    search = search_workspace(workspace, text="GD")
    titles = [item["canonical_title"] for item in search["ranked_concepts"]]
    assert "Gradient Descent" in titles

    alias_search = search_workspace(workspace, text="Steepest Descent")
    assert any(
        item["canonical_title"] == "Gradient Descent" for item in alias_search["ranked_concepts"]
    )

    momentum_id = generate_concept_id("Momentum Optimization")
    session = ReviewService(workspace).latest(momentum_id)
    assert session.concept_id == momentum_id

    service = ProductService(workspace)
    export = service.create_export("complete", lambda _value, _message: None)
    export_path = service.resolve_artifact("export", str(export["id"]))
    with zipfile.ZipFile(export_path) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert any(name.startswith("markdown/concepts/") for name in names)
        assert any(name.startswith("sources/") for name in names)

    backup = service.create_backup(lambda _value, _message: None)
    verification = service.verify_backup(str(backup["id"]))
    assert verification["valid"] is True

    recovered_vault = tmp_path / "recovered-vault"
    restored = service.restore_backup_copy(
        str(backup["id"]),
        target_vault=recovered_vault,
        app_data_dir=tmp_path / "recovered-app",
        confirmation="RESTORE COPY",
    )
    assert Path(restored["vault_path"]).is_dir()
    assert (recovered_vault / "concepts" / "gradient-descent.md").is_file()

    with pytest.raises(ValueError):
        service.restore_backup_copy(
            str(backup["id"]),
            target_vault=tmp_path / "other",
            app_data_dir=tmp_path / "other-app",
            confirmation="wrong",
        )


def test_remote_provider_update_is_blocked(workspace: WorkspaceContext) -> None:
    service = ProductService(workspace)
    with pytest.raises(ValueError, match="Remote model routing"):
        service.update_providers(
            ProviderSettings(
                llm_provider="openai_compatible",
                llm_base_url="https://api.example.test/v1",
                remote_data_allowed=False,
            )
        )


def test_clear_derived_index_keeps_markdown(workspace: WorkspaceContext) -> None:
    seed_demo_workspace(workspace)
    markdown = workspace.vault.read_markdown("concepts/gradient-descent.md")
    ProductService(workspace).clear_data(
        "derived_index",
        confirmation="DELETE DERIVED INDEX",
    )
    assert workspace.vault.read_markdown("concepts/gradient-descent.md") == markdown
    with pytest.raises(ValueError):
        ProductService(workspace).clear_data("exports", confirmation="nope")
