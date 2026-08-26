"""Shared fixtures for application-service tests."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from studium.app.workspace import WorkspaceContext


@pytest.fixture
def workspace(tmp_path: Path) -> Generator[WorkspaceContext, None, None]:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "concepts").mkdir()
    context = WorkspaceContext(
        vault,
        app_data_dir=tmp_path / "app-data",
        sync_on_open=False,
    )
    try:
        yield context
    finally:
        context.close()
