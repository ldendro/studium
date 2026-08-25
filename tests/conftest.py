"""Root pytest fixtures shared across packages."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.engine import Engine

from studium.index import IndexConfig, create_engine_for_config, initialize_index


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    root.mkdir()
    return root


@pytest.fixture
def app_data(tmp_path: Path) -> Path:
    root = tmp_path / "app-data"
    root.mkdir()
    return root


@pytest.fixture
def index_config(vault_root: Path, app_data: Path) -> IndexConfig:
    return IndexConfig(vault_root=vault_root, app_data_dir=app_data)


@pytest.fixture
def initialized_engine(index_config: IndexConfig) -> Engine:
    engine = create_engine_for_config(index_config)
    initialize_index(engine, index_config)
    return engine
