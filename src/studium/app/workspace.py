"""Open-vault lifecycle and orchestration across Studium subsystems."""

from __future__ import annotations

import json
import logging
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any, cast

from studium.app.config import AppConfig, remember_last_workspace
from studium.app.database import (
    app_transaction,
    create_app_engine,
    get_setting,
    set_setting,
    sources,
)
from studium.app.jobs import JobManager
from studium.app.migrations import MigrationResult, migrate_app_database, utc_now
from studium.app.providers import (
    ProviderSettings,
    build_embedding_provider,
    build_llm_provider,
    provider_settings_from_mapping,
    validate_provider_settings,
)
from studium.index.config import IndexConfig
from studium.index.embeddings.protocol import EmbeddingProvider
from studium.index.embeddings.sync_embed import SyncAndEmbedReport, sync_and_embed
from studium.index.errors import IndexSchemaMismatchError
from studium.index.schema_manager import (
    create_engine_for_config,
    get_index_revision,
    initialize_index,
    rebuild_index,
)
from studium.index.sync.models import SyncReport
from studium.index.sync.synchronizer import sync_vault
from studium.llm.protocol import LLMProvider
from studium.schemas import WriteProposal
from studium.vault import Vault
from studium.writes import commit_write_proposal

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CommitResult:
    target_path: str
    index_revision: int
    sync: SyncReport


class WorkspaceContext:
    """All runtime resources for one vault, with serialized mutation boundaries."""

    def __init__(
        self,
        vault_root: Path,
        *,
        app_data_dir: Path | None = None,
        sync_on_open: bool = True,
    ) -> None:
        self.config = AppConfig(vault_root=vault_root, app_data_dir=app_data_dir)
        self.config.ensure_directories()
        self.vault = Vault(self.config.resolved_vault_root)
        self.index_config = IndexConfig(
            vault_root=self.config.resolved_vault_root,
            app_data_dir=self.config.resolved_app_data_dir,
        )
        self.index_engine = create_engine_for_config(self.index_config)
        try:
            initialize_index(self.index_engine, self.index_config)
        except IndexSchemaMismatchError:
            self.index_engine = rebuild_index(
                self.index_config,
                existing_engine=self.index_engine,
            )

        self.app_engine = create_app_engine(self.config.database_path)
        self.migration: MigrationResult = migrate_app_database(self.app_engine, self.config)
        self._lock = RLock()
        self.provider_settings = self._load_provider_settings()
        self.embedding_provider: EmbeddingProvider = build_embedding_provider(
            self.provider_settings
        )
        self.llm_provider: LLMProvider | None = build_llm_provider(self.provider_settings)
        self.jobs = JobManager(self.app_engine)
        self._recover_interrupted_sources()
        self.last_sync: SyncReport | None = None
        if sync_on_open:
            self.sync(embed=True)

    @property
    def vault_id(self) -> str:
        return self.config.vault_identifier

    def sync(self, *, embed: bool = True) -> SyncReport:
        with self._lock:
            if embed:
                report: SyncAndEmbedReport = sync_and_embed(
                    self.vault,
                    self.index_engine,
                    self.index_config,
                    self.embedding_provider,
                )
                self.last_sync = report.sync
            else:
                self.last_sync = sync_vault(
                    self.vault,
                    self.index_engine,
                    self.index_config,
                )
            return self.last_sync

    def commit(self, proposal: WriteProposal) -> CommitResult:
        """Commit a safe Phase 1 proposal and publish its new index projection."""

        with self._lock:
            commit_write_proposal(self.vault, proposal)
            report = self.sync(embed=True)
            return CommitResult(
                target_path=proposal.target_path,
                index_revision=report.revision_after,
                sync=report,
            )

    def model_space(self) -> dict[str, Any]:
        metadata = self.embedding_provider.model_metadata()
        return {
            "model_id": metadata.model_id,
            "model_revision": metadata.model_revision,
            "dimension": metadata.dimension,
            "normalizes_embeddings": metadata.normalizes_embeddings,
        }

    def health(self, *, probe_llm: bool = False) -> dict[str, Any]:
        llm_health: dict[str, Any]
        if self.llm_provider is None:
            llm_health = {
                "healthy": True,
                "ready": False,
                "model_id": None,
                "message": "LLM assistance is disabled; deterministic workflows remain available.",
            }
        elif probe_llm:
            llm_health = self.llm_provider.check_health().model_dump(mode="json")
        else:
            llm_health = {
                "healthy": None,
                "ready": None,
                "model_id": self.llm_provider.model_id(),
                "message": "Not probed",
            }
        return {
            "status": "ok",
            "workspace_open": True,
            "vault_id": self.vault_id,
            "vault_name": self.vault.root.name,
            "vault_path": str(self.vault.root),
            "index_revision": get_index_revision(self.index_engine),
            "index_database": str(self.index_config.database_path),
            "app_database": str(self.config.database_path),
            "last_sync": (
                None if self.last_sync is None else self.last_sync.model_dump(mode="json")
            ),
            "embedding": self.model_space(),
            "llm": llm_health,
            "app_schema_version": self.migration.after,
        }

    def reload_providers(self) -> None:
        self.provider_settings = self._load_provider_settings()
        self.embedding_provider = build_embedding_provider(self.provider_settings)
        self.llm_provider = build_llm_provider(self.provider_settings)

    def update_provider_settings(self, settings: ProviderSettings) -> None:
        """Validate and atomically activate user-controlled provider routing."""

        settings = validate_provider_settings(settings)
        embedding_provider = build_embedding_provider(settings)
        llm_provider = build_llm_provider(settings)
        payload = json.dumps(asdict(settings), sort_keys=True)
        with self._lock:
            with app_transaction(self.app_engine) as connection:
                set_setting(connection, "providers", payload, updated_at=utc_now())
            self.provider_settings = settings
            self.embedding_provider = embedding_provider
            self.llm_provider = llm_provider

    @contextmanager
    def maintenance_lock(self) -> Generator[None, None, None]:
        """Serialize snapshots and maintenance with all Studium note writes."""

        with self._lock:
            yield

    def rebuild_derived_index(self, *, synchronize: bool = True) -> SyncReport | None:
        with self._lock:
            self.index_engine = rebuild_index(
                self.index_config,
                existing_engine=self.index_engine,
            )
            self.last_sync = None
            return self.sync(embed=True) if synchronize else None

    def close(self) -> None:
        self.jobs.close()
        self.index_engine.dispose()
        self.app_engine.dispose()

    def _load_provider_settings(self) -> ProviderSettings:
        with self.app_engine.connect() as connection:
            raw = get_setting(connection, "providers")
        if raw is None:
            return ProviderSettings()
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                return ProviderSettings()
            return provider_settings_from_mapping(cast(dict[str, Any], payload))
        except (AttributeError, TypeError, ValueError):
            logger.warning("invalid_provider_settings_ignored")
            return ProviderSettings()

    def _recover_interrupted_sources(self) -> None:
        with app_transaction(self.app_engine) as connection:
            result = connection.execute(
                sources.update()
                .where(sources.c.status.in_(["queued", "extracting", "chunking", "embedding"]))
                .values(
                    status="failed",
                    processing_error=(
                        "Processing was interrupted when Studium stopped. "
                        "Retry this source from the library."
                    ),
                    updated_at=utc_now(),
                )
            )
        if result.rowcount:
            logger.warning(
                "source_jobs_recovered",
                extra={"recovered_source_count": result.rowcount},
            )


class WorkspaceRegistry:
    """Single-user registry with an explicit active workspace."""

    def __init__(self) -> None:
        self._active: WorkspaceContext | None = None
        self._lock = RLock()

    @property
    def active(self) -> WorkspaceContext:
        if self._active is None:
            raise RuntimeError("No Studium vault is open.")
        return self._active

    def open(
        self,
        vault_root: Path,
        *,
        app_data_dir: Path | None = None,
        sync_on_open: bool = True,
    ) -> WorkspaceContext:
        with self._lock:
            previous = self._active
            workspace = WorkspaceContext(
                vault_root,
                app_data_dir=app_data_dir,
                sync_on_open=sync_on_open,
            )
            self._active = workspace
            remember_last_workspace(
                workspace.config.resolved_vault_root,
                workspace.config.resolved_app_data_dir,
            )
            if previous is not None:
                previous.close()
            return workspace

    def close(self) -> None:
        with self._lock:
            if self._active is not None:
                self._active.close()
            self._active = None
