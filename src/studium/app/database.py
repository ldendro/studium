"""Durable per-vault application database.

The concept index remains a rebuildable Phase 2 projection. This database stores
state that is not appropriate in concept-note Markdown: jobs, review decisions,
source chunks, study events, mastery history, and user-controlled preferences.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    select,
)
from sqlalchemy.engine import Connection, Engine

APP_SCHEMA_VERSION = 3

metadata = MetaData()

app_metadata = Table(
    "app_metadata",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("schema_version", Integer, nullable=False),
    Column("vault_path", Text, nullable=False),
    Column("vault_identifier", String(64), nullable=False, unique=True),
    Column("created_at", String(32), nullable=False),
    Column("updated_at", String(32), nullable=False),
)

sources = Table(
    "sources",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("title", Text, nullable=False),
    Column("source_type", String(40), nullable=False),
    Column("status", String(40), nullable=False),
    Column("original_filename", Text),
    Column("asset_path", Text),
    Column("mime_type", String(128)),
    Column("content_hash", String(64), nullable=False),
    Column("size_bytes", Integer, nullable=False, default=0),
    Column("page_count", Integer),
    Column("metadata_json", Text, nullable=False, default="{}"),
    Column("processing_error", Text),
    Column("created_at", String(32), nullable=False),
    Column("updated_at", String(32), nullable=False),
    UniqueConstraint("content_hash", name="uq_sources_content_hash"),
)

source_chunks = Table(
    "source_chunks",
    metadata,
    Column("id", String(96), primary_key=True),
    Column(
        "source_id",
        String(64),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("ordinal", Integer, nullable=False),
    Column("text", Text, nullable=False),
    Column("section", Text),
    Column("page", Integer),
    Column("timestamp_start", Float()),
    Column("timestamp_end", Float()),
    Column("char_start", Integer),
    Column("char_end", Integer),
    Column("token_count", Integer, nullable=False, default=0),
    Column("embedding_json", Text),
    Column("embedding_model", Text),
    Column("created_at", String(32), nullable=False),
    UniqueConstraint("source_id", "ordinal", name="uq_source_chunks_ordinal"),
)
Index("ix_source_chunks_source", source_chunks.c.source_id, source_chunks.c.ordinal)

source_contributions = Table(
    "source_contributions",
    metadata,
    Column("id", String(64), primary_key=True),
    Column(
        "source_id",
        String(64),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("concept_id", String(128), nullable=False),
    Column("classification", String(64), nullable=False),
    Column("summary", Text, nullable=False),
    Column("evidence_json", Text, nullable=False, default="[]"),
    Column("proposed_module_json", Text),
    Column("status", String(40), nullable=False, default="proposed"),
    Column("created_at", String(32), nullable=False),
    Column("updated_at", String(32), nullable=False),
)
Index(
    "ix_source_contributions_concept",
    source_contributions.c.concept_id,
    source_contributions.c.status,
)

draft_snapshots = Table(
    "draft_snapshots",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("concept_id", String(128)),
    Column("title", Text, nullable=False),
    Column("target_path", Text),
    Column("operation", String(24), nullable=False, default="create"),
    Column("markdown", Text, nullable=False),
    Column("recommendation_json", Text),
    Column("created_at", String(32), nullable=False),
    Column("updated_at", String(32), nullable=False),
)
Index("ix_draft_snapshots_updated", draft_snapshots.c.updated_at)

review_sessions = Table(
    "review_sessions",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("concept_id", String(128), nullable=False),
    Column("file_path", Text, nullable=False),
    Column("status", String(40), nullable=False),
    Column("readiness", String(40), nullable=False),
    Column("summary_json", Text, nullable=False, default="{}"),
    Column("created_at", String(32), nullable=False),
    Column("completed_at", String(32)),
)
Index(
    "ix_review_sessions_concept",
    review_sessions.c.concept_id,
    review_sessions.c.created_at,
)

review_findings = Table(
    "review_findings",
    metadata,
    Column("id", String(64), primary_key=True),
    Column(
        "review_id",
        String(64),
        ForeignKey("review_sessions.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("concept_id", String(128), nullable=False),
    Column("module_id", String(128)),
    Column("category", String(40), nullable=False),
    Column("severity", String(24), nullable=False),
    Column("message", Text, nullable=False),
    Column("anchor_json", Text),
    Column("quoted_text", Text),
    Column("proposed_patch", Text),
    Column("status", String(24), nullable=False, default="open"),
    Column("decision_note", Text),
    Column("created_at", String(32), nullable=False),
    Column("resolved_at", String(32)),
)
Index(
    "ix_review_findings_review",
    review_findings.c.review_id,
    review_findings.c.status,
)

note_versions = Table(
    "note_versions",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("concept_id", String(128), nullable=False),
    Column("file_path", Text, nullable=False),
    Column("version", Integer, nullable=False),
    Column("content_hash", String(64), nullable=False),
    Column("markdown", Text, nullable=False),
    Column("reason", String(64), nullable=False),
    Column("created_at", String(32), nullable=False),
    UniqueConstraint("concept_id", "version", name="uq_note_versions_number"),
)

backlog_items = Table(
    "backlog_items",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("title", Text, nullable=False),
    Column("item_type", String(48), nullable=False),
    Column("status", String(32), nullable=False),
    Column("priority", Integer, nullable=False, default=50),
    Column("reason", Text, nullable=False),
    Column("origin", String(48), nullable=False),
    Column("related_concept_id", String(128)),
    Column("required_by_json", Text, nullable=False, default="[]"),
    Column("source_query", Text),
    Column("metadata_json", Text, nullable=False, default="{}"),
    Column("created_at", String(32), nullable=False),
    Column("updated_at", String(32), nullable=False),
    Column("completed_at", String(32)),
)
Index("ix_backlog_status_priority", backlog_items.c.status, backlog_items.c.priority)

retention_cards = Table(
    "retention_cards",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("concept_id", String(128), nullable=False),
    Column("module_id", String(128)),
    Column("module_type", String(48)),
    Column("prompt", Text, nullable=False),
    Column("expected_components_json", Text, nullable=False, default="[]"),
    Column("prompt_hash", String(64), nullable=False),
    Column("state", String(32), nullable=False, default="new"),
    Column("interval_days", Integer, nullable=False, default=0),
    Column("ease_factor", Float(), nullable=False, default=2.5),
    Column("repetitions", Integer, nullable=False, default=0),
    Column("lapses", Integer, nullable=False, default=0),
    Column("difficulty", Float(), nullable=False, default=0.3),
    Column("stability", Float(), nullable=False, default=0.0),
    Column("last_reviewed_at", String(32)),
    Column("next_review_at", String(32), nullable=False),
    Column("pinned", Boolean, nullable=False, default=False),
    Column("created_at", String(32), nullable=False),
    Column("updated_at", String(32), nullable=False),
    UniqueConstraint("concept_id", "prompt_hash", name="uq_retention_prompt"),
)
Index("ix_retention_due", retention_cards.c.state, retention_cards.c.next_review_at)

review_events = Table(
    "review_events",
    metadata,
    Column("id", String(64), primary_key=True),
    Column(
        "card_id",
        String(64),
        ForeignKey("retention_cards.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("concept_id", String(128), nullable=False),
    Column("module_id", String(128)),
    Column("response", Text),
    Column("evaluation", String(24), nullable=False),
    Column("score", Float(), nullable=False),
    Column("confidence", Integer),
    Column("latency_ms", Integer),
    Column("hints_used", Integer, nullable=False, default=0),
    Column("evaluator", String(32), nullable=False),
    Column("scheduled_interval_days", Integer, nullable=False),
    Column("created_at", String(32), nullable=False),
)
Index("ix_review_events_concept", review_events.c.concept_id, review_events.c.created_at)

mastery_snapshots = Table(
    "mastery_snapshots",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("concept_id", String(128), nullable=False),
    Column("module_id", String(128)),
    Column("score", Float(), nullable=False),
    Column("state", String(32), nullable=False),
    Column("signals_json", Text, nullable=False),
    Column("created_at", String(32), nullable=False),
)
Index(
    "ix_mastery_snapshots_concept",
    mastery_snapshots.c.concept_id,
    mastery_snapshots.c.created_at,
)

profile_observations = Table(
    "profile_observations",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("category", String(48), nullable=False),
    Column("statement", Text, nullable=False),
    Column("evidence_json", Text, nullable=False, default="[]"),
    Column("confidence", Float(), nullable=False),
    Column("status", String(24), nullable=False, default="proposed"),
    Column("pinned", Boolean, nullable=False, default=False),
    Column("source", String(32), nullable=False, default="inferred"),
    Column("created_at", String(32), nullable=False),
    Column("updated_at", String(32), nullable=False),
)
Index("ix_profile_observations_status", profile_observations.c.status)

settings = Table(
    "settings",
    metadata,
    Column("key", String(128), primary_key=True),
    Column("value_json", Text, nullable=False),
    Column("updated_at", String(32), nullable=False),
)

jobs = Table(
    "jobs",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("job_type", String(48), nullable=False),
    Column("status", String(32), nullable=False),
    Column("progress", Float(), nullable=False, default=0.0),
    Column("message", Text),
    Column("payload_json", Text, nullable=False, default="{}"),
    Column("result_json", Text),
    Column("error", Text),
    Column("attempt", Integer, nullable=False, default=1),
    Column("retry_of_id", String(64)),
    Column("created_at", String(32), nullable=False),
    Column("started_at", String(32)),
    Column("finished_at", String(32)),
)
Index("ix_jobs_status_created", jobs.c.status, jobs.c.created_at)


def create_app_engine(db_path: Path, *, busy_timeout_ms: int = 5000) -> Engine:
    """Open the per-vault app database with safe SQLite defaults."""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )

    def _configure(connection: Any, _record: Any) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
        cursor.close()

    event.listen(engine, "connect", _configure)
    return engine


@contextmanager
def app_transaction(engine: Engine) -> Generator[Connection, None, None]:
    with engine.begin() as connection:
        yield connection


def row_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


def get_setting(connection: Connection, key: str) -> str | None:
    row = connection.execute(select(settings.c.value_json).where(settings.c.key == key)).first()
    return None if row is None else str(row.value_json)


def set_setting(connection: Connection, key: str, value_json: str, *, updated_at: str) -> None:
    result = connection.execute(
        settings.update()
        .where(settings.c.key == key)
        .values(value_json=value_json, updated_at=updated_at)
    )
    if result.rowcount == 0:
        connection.execute(
            settings.insert().values(
                key=key,
                value_json=value_json,
                updated_at=updated_at,
            )
        )
