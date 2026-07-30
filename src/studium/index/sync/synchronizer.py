"""Vault → derived index synchronization orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine

from studium.index.config import IndexConfig
from studium.index.engine import begin_connection
from studium.index.repositories import (
    concepts,
    indexed_files,
    invalid_records,
    projections,
    scaffold_modules,
)
from studium.index.schema_manager import (
    ensure_compatible_index,
    get_index_revision,
    increment_index_revision,
    rebuild_index,
)
from studium.index.sync.classify import FileAnalysis, analyze_vault_files
from studium.index.sync.models import (
    EmbeddingWorkRequest,
    FileSyncClass,
    SyncCounts,
    SyncReport,
    SyncStatus,
)
from studium.index.sync.project import (
    ConceptProjection,
    indexed_file_row_for_projection,
    project_concept_note,
)
from studium.index.sync.scan import scan_vault
from studium.vault import Vault


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def sync_vault(vault: Vault, engine: Engine, config: IndexConfig) -> SyncReport:
    """Incrementally synchronize vault Markdown into the derived concept index."""
    started_at = _utc_now()
    ensure_compatible_index(engine)
    if vault.root != config.resolved_vault_root:
        finished_at = _utc_now()
        return SyncReport(
            started_at=started_at,
            finished_at=finished_at,
            status=SyncStatus.FAILED,
            revision_before=get_index_revision(engine),
            revision_after=get_index_revision(engine),
            errors=[
                "Vault root does not match IndexConfig.resolved_vault_root: "
                f"{vault.root} != {config.resolved_vault_root}"
            ],
        )

    revision_before = get_index_revision(engine)
    pending_revision = revision_before + 1
    scanned = scan_vault(vault)

    with engine.connect() as connection:
        indexed_rows = indexed_files.list_indexed_files(connection)

    analyses = analyze_vault_files(scanned, indexed_rows)
    counts = SyncCounts(scanned=len(scanned))
    embedding_work: list[EmbeddingWorkRequest] = []
    warnings: list[str] = []
    errors: list[str] = []
    usable_state_changed = False

    for analysis in analyses:
        try:
            changed, work = _apply_analysis(
                engine,
                analysis,
                pending_revision=pending_revision,
                counts=counts,
            )
            usable_state_changed = usable_state_changed or changed
            embedding_work.extend(work)
            if changed and analysis.sync_class in {
                FileSyncClass.INVALID,
                FileSyncClass.DUPLICATE_ID_CONFLICT,
            }:
                warnings.extend(analysis.reasons)
        except Exception as exc:
            errors.append(f"{analysis.path}: {exc}")
            counts.invalid += 1

    revision_after = revision_before
    if usable_state_changed:
        revision_after = increment_index_revision(engine)

    status = _resolve_status(counts, errors, usable_state_changed)
    return SyncReport(
        started_at=started_at,
        finished_at=_utc_now(),
        status=status,
        revision_before=revision_before,
        revision_after=revision_after,
        counts=counts,
        embedding_work=embedding_work,
        warnings=warnings,
        errors=errors,
    )


def rebuild_vault_index(
    vault: Vault,
    config: IndexConfig,
    *,
    existing_engine: Engine | None = None,
) -> tuple[Engine, SyncReport]:
    """Dispose any existing engine, recreate an empty schema, and fully sync."""
    engine = rebuild_index(config, existing_engine=existing_engine)
    report = sync_vault(vault, engine, config)
    return engine, report


def _resolve_status(
    counts: SyncCounts,
    errors: list[str],
    usable_state_changed: bool,
) -> SyncStatus:
    if errors and not usable_state_changed:
        return SyncStatus.FAILED
    if errors:
        return SyncStatus.PARTIAL_SUCCESS
    if counts.invalid or counts.duplicate_conflicts:
        return SyncStatus.PARTIAL_SUCCESS
    if not usable_state_changed:
        return SyncStatus.NO_CHANGES
    return SyncStatus.SUCCESS


def _apply_analysis(
    engine: Engine,
    analysis: FileAnalysis,
    *,
    pending_revision: int,
    counts: SyncCounts,
) -> tuple[bool, list[EmbeddingWorkRequest]]:
    if analysis.sync_class == FileSyncClass.UNCHANGED:
        counts.unchanged += 1
        return False, []

    if analysis.sync_class == FileSyncClass.REMOVED:
        return _remove_file(engine, analysis, pending_revision=pending_revision, counts=counts), []

    if analysis.sync_class == FileSyncClass.INVALID:
        return (
            _mark_invalid(
                engine,
                analysis,
                pending_revision=pending_revision,
                counts=counts,
                reason_code="validation_failed",
            ),
            [],
        )

    if analysis.sync_class == FileSyncClass.DUPLICATE_ID_CONFLICT:
        return (
            _mark_invalid(
                engine,
                analysis,
                pending_revision=pending_revision,
                counts=counts,
                reason_code="duplicate_concept_id",
                count_as_duplicate=True,
            ),
            [],
        )

    if analysis.parsed is None or analysis.scanned is None:
        msg = f"Missing parse result for {analysis.path}"
        raise RuntimeError(msg)

    projection = project_concept_note(
        analysis.parsed,
        file_path=analysis.path,
        file_hash=analysis.scanned.file_hash,
        indexed_revision=pending_revision,
    )
    previous_concept = _load_previous_concept(engine, projection.concept_id)
    previous_modules = _load_previous_modules(engine, projection.concept_id)

    with begin_connection(engine) as connection:
        # Path-owned concept ID changed (A → B): drop the old projection first.
        if analysis.previous is not None and analysis.moved_from is None:
            previous_id = analysis.previous.get("concept_id")
            if previous_id is not None and str(previous_id) != projection.concept_id:
                existing = concepts.get_concept(connection, str(previous_id))
                if existing is not None and existing.get("file_path") == analysis.path:
                    projections.remove_concept_projection(connection, str(previous_id))

        if analysis.sync_class == FileSyncClass.MOVED and analysis.moved_from is not None:
            indexed_files.delete_indexed_file(connection, analysis.moved_from)
            invalid_records.delete_invalid_records_for_path(connection, analysis.moved_from)

        projections.upsert_concept_projection(
            connection,
            concept=projection.concept,
            alias_values=projection.alias_values,
            domain_values=projection.domain_values,
            encounter_rows=projection.encounter_rows,
            relationship_rows=projection.relationship_rows,
            module_rows=projection.module_rows,
            concept_search_document={
                "concept_id": projection.concept_id,
                "document_text": projection.concept_search_document_text,
                "field_weights_json": None,
                "indexed_revision": pending_revision,
            },
            module_search_documents=projection.module_search_documents,
            indexed_file=indexed_file_row_for_projection(
                projection,
                mtime_ns=analysis.scanned.mtime_ns,
                indexed_at=_utc_now_iso(),
                revision=pending_revision,
            ),
        )

    # Counters only after a successful commit (upsert rolled back ⇒ no count bump).
    if analysis.sync_class == FileSyncClass.MOVED:
        counts.moved += 1
    elif analysis.sync_class == FileSyncClass.NEW:
        counts.created += 1
    else:
        counts.updated += 1

    work = _embedding_work_for_projection(
        projection,
        previous_concept=previous_concept,
        previous_modules=previous_modules,
    )
    return True, work


def _remove_file(
    engine: Engine,
    analysis: FileAnalysis,
    *,
    pending_revision: int,
    counts: SyncCounts,
) -> bool:
    del pending_revision  # reserved for future tombstone revisions
    with begin_connection(engine) as connection:
        if analysis.concept_id is not None:
            existing = concepts.get_concept(connection, analysis.concept_id)
            if existing is not None and existing.get("file_path") == analysis.path:
                projections.remove_concept_projection(connection, analysis.concept_id)
        indexed_files.delete_indexed_file(connection, analysis.path)
        invalid_records.delete_invalid_records_for_path(connection, analysis.path)
    counts.removed += 1
    return True


def _mark_invalid(
    engine: Engine,
    analysis: FileAnalysis,
    *,
    pending_revision: int,
    counts: SyncCounts,
    reason_code: str,
    count_as_duplicate: bool = False,
) -> bool:
    scanned = analysis.scanned
    file_hash = None if scanned is None else scanned.file_hash
    mtime_ns = None if scanned is None else scanned.mtime_ns

    # Unchanged invalid/conflict content: do not rewrite diagnostics or bump revision.
    if (
        analysis.previous is not None
        and analysis.previous.get("file_hash") == file_hash
        and analysis.previous.get("index_state") == analysis.sync_class.value
    ):
        counts.unchanged += 1
        return False

    message = "; ".join(analysis.reasons) if analysis.reasons else reason_code
    details = {
        "reasons": analysis.reasons,
        "sync_class": analysis.sync_class.value,
    }
    remove_concept_id = analysis.concept_id
    # Prefer previous ownership when concept_id is known from index.
    if remove_concept_id is None and analysis.previous is not None:
        remove_concept_id = analysis.previous.get("concept_id")
        if remove_concept_id is not None:
            remove_concept_id = str(remove_concept_id)

    with begin_connection(engine) as connection:
        if analysis.moved_from is not None:
            old = indexed_files.get_indexed_file(connection, analysis.moved_from)
            if old is not None:
                old_concept_id = old.get("concept_id")
                if old_concept_id is not None:
                    existing = concepts.get_concept(connection, str(old_concept_id))
                    if existing is not None and existing.get("file_path") == analysis.moved_from:
                        projections.remove_concept_projection(connection, str(old_concept_id))
                indexed_files.delete_indexed_file(connection, analysis.moved_from)
                invalid_records.delete_invalid_records_for_path(connection, analysis.moved_from)

        # If this path previously owned a different concept id, remove that too.
        if analysis.previous is not None and analysis.moved_from is None:
            previous_id = analysis.previous.get("concept_id")
            if previous_id is not None and str(previous_id) != remove_concept_id:
                existing = concepts.get_concept(connection, str(previous_id))
                if existing is not None and existing.get("file_path") == analysis.path:
                    projections.remove_concept_projection(connection, str(previous_id))

        projections.mark_path_invalid(
            connection,
            indexed_file={
                "file_path": analysis.path,
                "concept_id": analysis.concept_id,
                "note_schema_version": None,
                "file_hash": file_hash,
                "projection_hash": None,
                "mtime_ns": mtime_ns,
                "index_state": analysis.sync_class.value,
                "last_success_revision": None
                if analysis.previous is None
                else analysis.previous.get("last_success_revision"),
                "invalid_since_revision": pending_revision,
                "validation_errors_json": json.dumps(details, sort_keys=True),
                "indexed_at": _utc_now_iso(),
            },
            invalid_record={
                "file_path": analysis.path,
                "concept_id": analysis.concept_id,
                "reason_code": reason_code,
                "message": message,
                "details_json": json.dumps(details, sort_keys=True),
                "since_revision": pending_revision,
                "recorded_at": _utc_now_iso(),
            },
            remove_concept_id=None if remove_concept_id is None else str(remove_concept_id),
        )

    if count_as_duplicate:
        counts.duplicate_conflicts += 1
    else:
        counts.invalid += 1
    return True


def _load_previous_concept(engine: Engine, concept_id: str) -> dict[str, Any] | None:
    with engine.connect() as connection:
        return concepts.get_concept(connection, concept_id)


def _load_previous_modules(engine: Engine, concept_id: str) -> dict[str, dict[str, Any]]:
    with engine.connect() as connection:
        rows = scaffold_modules.list_modules_for_concept(connection, concept_id)
    return {str(row["module_id"]): row for row in rows}


def _embedding_work_for_projection(
    projection: ConceptProjection,
    *,
    previous_concept: dict[str, Any] | None,
    previous_modules: dict[str, dict[str, Any]],
) -> list[EmbeddingWorkRequest]:
    work: list[EmbeddingWorkRequest] = []
    previous_identity = (
        None if previous_concept is None else previous_concept.get("identity_input_hash")
    )
    previous_semantic = (
        None if previous_concept is None else previous_concept.get("semantic_input_hash")
    )
    if previous_identity != projection.identity_input_hash:
        work.append(
            EmbeddingWorkRequest(
                owner_type="concept",
                owner_id=projection.concept_id,
                embedding_type="concept_identity",
                input_hash=projection.identity_input_hash,
                input_text=projection.identity_input,
                parent_concept_id=projection.concept_id,
            )
        )
    if previous_semantic != projection.semantic_input_hash:
        work.append(
            EmbeddingWorkRequest(
                owner_type="concept",
                owner_id=projection.concept_id,
                embedding_type="concept_semantic",
                input_hash=projection.semantic_input_hash,
                input_text=projection.semantic_input,
                parent_concept_id=projection.concept_id,
            )
        )

    for module_id, input_text, input_hash in projection.module_inputs:
        previous = previous_modules.get(module_id)
        previous_hash = None if previous is None else previous.get("module_input_hash")
        if previous_hash == input_hash:
            continue
        work.append(
            EmbeddingWorkRequest(
                owner_type="scaffold_module",
                owner_id=module_id,
                embedding_type="module_semantic",
                input_hash=input_hash,
                input_text=input_text,
                parent_concept_id=projection.concept_id,
                segment_id=f"{module_id}:0",
            )
        )
    return work
