"""Application-database migration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect, text

from studium.app.config import AppConfig
from studium.app.database import APP_SCHEMA_VERSION, create_app_engine
from studium.app.migrations import AppSchemaTooNewError, current_schema_version, migrate_app_database


def test_fresh_database_migrates_to_current_schema(tmp_path: Path) -> None:
    config = AppConfig(vault_root=tmp_path / "vault", app_data_dir=tmp_path / "app-data")
    config.ensure_directories()
    engine = create_app_engine(config.database_path)
    result = migrate_app_database(engine, config)
    assert result.before == 0
    assert result.after == APP_SCHEMA_VERSION
    assert current_schema_version(engine) == APP_SCHEMA_VERSION
    columns = {column["name"] for column in inspect(engine).get_columns("jobs")}
    assert {"attempt", "retry_of_id"} <= columns


def test_schema_newer_than_supported_is_rejected(tmp_path: Path) -> None:
    config = AppConfig(vault_root=tmp_path / "vault", app_data_dir=tmp_path / "app-data")
    config.ensure_directories()
    engine = create_app_engine(config.database_path)
    migrate_app_database(engine, config)
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE app_metadata SET schema_version = :version"),
            {"version": APP_SCHEMA_VERSION + 5},
        )
    with pytest.raises(AppSchemaTooNewError):
        migrate_app_database(engine, config)


def test_job_columns_are_added_to_existing_schema(tmp_path: Path) -> None:
    config = AppConfig(vault_root=tmp_path / "vault", app_data_dir=tmp_path / "app-data")
    config.ensure_directories()
    engine = create_app_engine(config.database_path)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE app_metadata (
                    id INTEGER PRIMARY KEY,
                    schema_version INTEGER NOT NULL,
                    vault_path TEXT NOT NULL,
                    vault_identifier VARCHAR(64) NOT NULL,
                    created_at VARCHAR(32) NOT NULL,
                    updated_at VARCHAR(32) NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE jobs (
                    id VARCHAR(64) PRIMARY KEY,
                    job_type VARCHAR(48) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    progress FLOAT NOT NULL,
                    message TEXT,
                    payload_json TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    created_at VARCHAR(32) NOT NULL,
                    started_at VARCHAR(32),
                    finished_at VARCHAR(32)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO app_metadata (
                    schema_version, vault_path, vault_identifier, created_at, updated_at
                ) VALUES (2, :vault, 'vault', :now, :now)
                """
            ),
            {
                "vault": str(config.resolved_vault_root),
                "now": "2026-08-26T00:00:00Z",
            },
        )
    result = migrate_app_database(engine, config)
    assert 3 in result.applied
    assert result.after == APP_SCHEMA_VERSION
    columns = {column["name"] for column in inspect(engine).get_columns("jobs")}
    assert "attempt" in columns
    assert "retry_of_id" in columns
