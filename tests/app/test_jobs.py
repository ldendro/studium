"""Background job persistence and crash recovery."""

from __future__ import annotations

from pathlib import Path

from studium.app.config import AppConfig
from studium.app.database import create_app_engine, jobs
from studium.app.jobs import JobManager
from studium.app.migrations import migrate_app_database, utc_now


def test_job_manager_records_success_and_failure(tmp_path: Path) -> None:
    config = AppConfig(vault_root=tmp_path / "vault", app_data_dir=tmp_path / "app-data")
    config.ensure_directories()
    engine = create_app_engine(config.database_path)
    migrate_app_database(engine, config)
    manager = JobManager(engine, max_workers=1)
    try:
        completed = manager.submit(
            "index_sync",
            {"embeddings": True},
            lambda progress: {"ok": True} if progress(1.0, "done") is None else None,
        )
        assert manager.wait(completed["id"])["status"] == "completed"

        failed = manager.submit(
            "workspace_export",
            {"kind": "markdown"},
            lambda _progress: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        stored = manager.wait(failed["id"])
        assert stored["status"] == "failed"
        assert stored["error"] is not None
        retried = manager.submit(
            "workspace_export",
            {"kind": "markdown"},
            lambda progress: {"files": 1} if progress(1.0, "ok") is None else None,
            retry_of_id=failed["id"],
        )
        finished = manager.wait(retried["id"])
        assert finished["attempt"] == 2
        assert finished["retry_of_id"] == failed["id"]
    finally:
        manager.close()


def test_interrupted_jobs_are_marked_failed(tmp_path: Path) -> None:
    config = AppConfig(vault_root=tmp_path / "vault", app_data_dir=tmp_path / "app-data")
    config.ensure_directories()
    engine = create_app_engine(config.database_path)
    migrate_app_database(engine, config)
    with engine.begin() as connection:
        connection.execute(
            jobs.insert().values(
                id="job_interrupted",
                job_type="source_processing",
                status="running",
                progress=0.4,
                payload_json="{}",
                attempt=1,
                created_at=utc_now(),
            )
        )
    manager = JobManager(engine, max_workers=1)
    try:
        recovered = manager.get("job_interrupted")
        assert recovered["status"] == "failed"
        assert "stopped" in str(recovered["error"]).casefold()
    finally:
        manager.close()
