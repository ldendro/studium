"""Small explicit migration runner for durable application state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Engine, inspect, select

from studium.app.config import AppConfig
from studium.app.database import APP_SCHEMA_VERSION, app_metadata, app_transaction, metadata


class AppSchemaTooNewError(RuntimeError):
    """Raised when app data was written by a newer Studium build."""


@dataclass(frozen=True, slots=True)
class MigrationResult:
    before: int
    after: int
    applied: tuple[int, ...]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def current_schema_version(engine: Engine) -> int:
    if "app_metadata" not in inspect(engine).get_table_names():
        return 0
    with engine.connect() as connection:
        row = connection.execute(
            select(app_metadata.c.schema_version).order_by(app_metadata.c.id).limit(1)
        ).first()
    return 0 if row is None else int(row.schema_version)


def migrate_app_database(engine: Engine, config: AppConfig) -> MigrationResult:
    """Apply ordered, forward-only migrations to the app database."""

    before = current_schema_version(engine)
    if before > APP_SCHEMA_VERSION:
        raise AppSchemaTooNewError(
            f"Application data schema {before} is newer than supported schema "
            f"{APP_SCHEMA_VERSION}."
        )

    applied: list[int] = []
    version = before
    if version < 1:
        _migration_1(engine, config)
        version = 1
        applied.append(1)

    return MigrationResult(before=before, after=version, applied=tuple(applied))


def _migration_1(engine: Engine, config: AppConfig) -> None:
    metadata.create_all(engine)
    now = utc_now()
    with app_transaction(engine) as connection:
        row = connection.execute(select(app_metadata.c.id).limit(1)).first()
        if row is None:
            connection.execute(
                app_metadata.insert().values(
                    schema_version=1,
                    vault_path=str(config.resolved_vault_root),
                    vault_identifier=config.vault_identifier,
                    created_at=now,
                    updated_at=now,
                )
            )
