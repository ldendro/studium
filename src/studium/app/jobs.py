"""Durable local background jobs with progress and crash recovery."""

from __future__ import annotations

import json
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import Any
from uuid import uuid4

from sqlalchemy import Engine, select

from studium.app.database import app_transaction, jobs, row_dict
from studium.app.migrations import utc_now

ProgressCallback = Callable[[float, str | None], None]
JobFunction = Callable[[ProgressCallback], dict[str, Any] | None]


class JobManager:
    """Run bounded local work while persisting user-visible state."""

    def __init__(self, engine: Engine, *, max_workers: int = 2) -> None:
        self._engine = engine
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="studium")
        self._futures: dict[str, Future[dict[str, Any] | None]] = {}
        self._lock = Lock()
        self._recover_interrupted_jobs()

    def submit(
        self,
        job_type: str,
        payload: dict[str, Any],
        function: JobFunction,
    ) -> dict[str, Any]:
        job_id = f"job_{uuid4().hex}"
        now = utc_now()
        with app_transaction(self._engine) as connection:
            connection.execute(
                jobs.insert().values(
                    id=job_id,
                    job_type=job_type,
                    status="queued",
                    progress=0.0,
                    payload_json=json.dumps(payload, sort_keys=True),
                    created_at=now,
                )
            )
        future = self._executor.submit(self._run, job_id, function)
        with self._lock:
            self._futures[job_id] = future
        return self.get(job_id)

    def _run(self, job_id: str, function: JobFunction) -> dict[str, Any] | None:
        self._update(job_id, status="running", started_at=utc_now(), progress=0.01)

        def progress(value: float, message: str | None = None) -> None:
            self._update(job_id, progress=max(0.0, min(1.0, value)), message=message)

        try:
            result = function(progress) or {}
        except Exception as exc:
            self._update(
                job_id,
                status="failed",
                error=f"{type(exc).__name__}: {exc}",
                finished_at=utc_now(),
            )
            raise
        else:
            self._update(
                job_id,
                status="completed",
                progress=1.0,
                result_json=json.dumps(result, sort_keys=True, default=str),
                finished_at=utc_now(),
            )
            return result

    def _update(self, job_id: str, **values: Any) -> None:
        with app_transaction(self._engine) as connection:
            connection.execute(jobs.update().where(jobs.c.id == job_id).values(**values))

    def get(self, job_id: str) -> dict[str, Any]:
        with self._engine.connect() as connection:
            row = connection.execute(select(jobs).where(jobs.c.id == job_id)).first()
        if row is None:
            raise KeyError(job_id)
        return _decode_job(row_dict(row))

    def list(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(jobs).order_by(jobs.c.created_at.desc()).limit(limit)
            ).all()
        return [_decode_job(row_dict(row)) for row in rows]

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=False)

    def _recover_interrupted_jobs(self) -> None:
        now = utc_now()
        with app_transaction(self._engine) as connection:
            connection.execute(
                jobs.update()
                .where(jobs.c.status.in_(["queued", "running"]))
                .values(
                    status="failed",
                    error="The application stopped before this job completed. Retry the operation.",
                    finished_at=now,
                )
            )


def _decode_job(row: dict[str, Any]) -> dict[str, Any]:
    decoded = dict(row)
    for key in ("payload_json", "result_json"):
        raw = decoded.pop(key, None)
        decoded[key.removesuffix("_json")] = None if raw is None else json.loads(str(raw))
    return decoded
