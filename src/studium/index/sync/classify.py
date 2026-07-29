"""Classify vault files relative to indexed_files records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from studium.index.sync.models import FileSyncClass
from studium.index.sync.scan import ScannedFile
from studium.parsing.models import ParsedConceptNote
from studium.schemas import ValidationResult
from studium.schemas.enums import ValidationOperation
from studium.validation import parse_and_validate


def _empty_reasons() -> list[str]:
    return []


@dataclass(slots=True)
class FileAnalysis:
    path: str
    scanned: ScannedFile | None
    previous: dict[str, Any] | None
    sync_class: FileSyncClass
    concept_id: str | None = None
    parsed: ParsedConceptNote | None = None
    validation: ValidationResult | None = None
    moved_from: str | None = None
    reasons: list[str] = field(default_factory=_empty_reasons)


def analyze_vault_files(
    scanned: list[ScannedFile],
    indexed_rows: list[dict[str, Any]],
) -> list[FileAnalysis]:
    """Parse, classify, and detect moves/duplicates for all vault Markdown files."""
    indexed_by_path = {str(row["file_path"]): row for row in indexed_rows}
    vault_paths = {item.path for item in scanned}
    analyses: dict[str, FileAnalysis] = {}

    for item in scanned:
        previous = indexed_by_path.get(item.path)
        if (
            previous is not None
            and previous.get("file_hash") == item.file_hash
            and previous.get("index_state") == "valid"
        ):
            analyses[item.path] = FileAnalysis(
                path=item.path,
                scanned=item,
                previous=previous,
                sync_class=FileSyncClass.UNCHANGED,
                concept_id=_as_optional_str(previous.get("concept_id")),
            )
            continue

        parsed, validation = parse_and_validate(item.content, ValidationOperation.PARSE)
        concept_id = _concept_id_from_parse(parsed)
        sync_class = FileSyncClass.NEW if previous is None else FileSyncClass.CHANGED
        analyses[item.path] = FileAnalysis(
            path=item.path,
            scanned=item,
            previous=previous,
            sync_class=sync_class,
            concept_id=concept_id,
            parsed=parsed,
            validation=validation,
        )

    removed_paths = [path for path in indexed_by_path if path not in vault_paths]
    indexed_by_concept: dict[str, list[dict[str, Any]]] = {}
    for row in indexed_rows:
        concept_id = _as_optional_str(row.get("concept_id"))
        if concept_id is None:
            continue
        indexed_by_concept.setdefault(concept_id, []).append(row)

    # Detect moves: new path with concept_id whose previous path disappeared.
    for analysis in list(analyses.values()):
        if analysis.sync_class != FileSyncClass.NEW or analysis.concept_id is None:
            continue
        candidates = [
            row
            for row in indexed_by_concept.get(analysis.concept_id, [])
            if str(row["file_path"]) not in vault_paths
        ]
        if len(candidates) == 1:
            old_path = str(candidates[0]["file_path"])
            analysis.sync_class = FileSyncClass.MOVED
            analysis.moved_from = old_path
            analysis.previous = candidates[0]
            if old_path in removed_paths:
                removed_paths.remove(old_path)

    for path in removed_paths:
        row = indexed_by_path[path]
        analyses[path] = FileAnalysis(
            path=path,
            scanned=None,
            previous=row,
            sync_class=FileSyncClass.REMOVED,
            concept_id=_as_optional_str(row.get("concept_id")),
        )

    _apply_validation_and_duplicates(analyses)
    return sorted(analyses.values(), key=lambda item: item.path)


def _apply_validation_and_duplicates(analyses: dict[str, FileAnalysis]) -> None:
    concept_to_paths: dict[str, list[str]] = {}
    for analysis in analyses.values():
        if analysis.sync_class == FileSyncClass.REMOVED:
            continue
        if analysis.sync_class == FileSyncClass.UNCHANGED:
            previous = analysis.previous
            previous_state = None if previous is None else previous.get("index_state")
            if analysis.concept_id and previous_state == "valid":
                concept_to_paths.setdefault(analysis.concept_id, []).append(analysis.path)
            continue

        validation = analysis.validation
        parsed = analysis.parsed
        if validation is None or parsed is None:
            continue
        if not validation.is_valid or parsed.metadata is None:
            analysis.sync_class = FileSyncClass.INVALID
            analysis.reasons = [issue.message for issue in validation.critical_errors]
            continue
        analysis.concept_id = parsed.metadata.id
        concept_to_paths.setdefault(analysis.concept_id, []).append(analysis.path)

    for concept_id, paths in concept_to_paths.items():
        if len(paths) < 2:
            continue
        for path in paths:
            analysis = analyses[path]
            if analysis.sync_class == FileSyncClass.REMOVED:
                continue
            analysis.sync_class = FileSyncClass.DUPLICATE_ID_CONFLICT
            analysis.reasons = [f"Duplicate concept_id across files: {concept_id}"]


def _concept_id_from_parse(parsed: ParsedConceptNote) -> str | None:
    if parsed.metadata is not None:
        return parsed.metadata.id
    raw_id = parsed.raw_metadata.get("id")
    return raw_id if isinstance(raw_id, str) and raw_id else None


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text or None
