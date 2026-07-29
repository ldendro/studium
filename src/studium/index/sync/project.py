"""Deterministic projection of a valid concept note into index row payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from studium.index.sync.embedding_inputs import (
    identity_input_from_metadata,
    module_input_from_metadata,
    semantic_input_from_metadata,
)
from studium.index.sync.hashes import hash_projection_payload, hash_text
from studium.index.sync.overview import extract_concept_overview
from studium.parsing.models import ParsedConceptNote


def _iso(value: datetime) -> str:
    aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return aware.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class ConceptProjection:
    concept_id: str
    file_path: str
    file_hash: str
    projection_hash: str
    identity_input: str
    identity_input_hash: str
    semantic_input: str
    semantic_input_hash: str
    concept: dict[str, Any]
    alias_values: list[str]
    domain_values: list[str]
    encounter_rows: list[dict[str, Any]]
    relationship_rows: list[dict[str, Any]]
    module_rows: list[dict[str, Any]]
    module_inputs: list[tuple[str, str, str]]  # module_id, input_text, input_hash
    concept_search_document_text: str
    module_search_documents: list[dict[str, Any]]
    hash_payload: dict[str, Any]


def project_concept_note(
    parsed: ParsedConceptNote,
    *,
    file_path: str,
    file_hash: str,
    indexed_revision: int,
) -> ConceptProjection:
    """Build deterministic projection payloads from a valid parsed note."""
    if parsed.metadata is None:
        msg = "Cannot project a note without structured metadata"
        raise ValueError(msg)

    metadata = parsed.metadata
    overview_markdown, overview_plaintext = extract_concept_overview(parsed.body, parsed.sections)
    identity_input = identity_input_from_metadata(metadata)
    semantic_input = semantic_input_from_metadata(metadata, overview_plaintext=overview_plaintext)
    identity_input_hash = hash_text(identity_input)
    semantic_input_hash = hash_text(semantic_input)

    concept_id = metadata.id
    alias_values = list(metadata.aliases)
    domain_values = list(metadata.concept_domains)

    encounter_rows = [
        _encounter_row(concept_id, encounter) for encounter in metadata.learning_encounters
    ]
    relationship_rows = [
        _relationship_row(concept_id, relationship) for relationship in metadata.relationships
    ]

    module_rows: list[dict[str, Any]] = []
    module_inputs: list[tuple[str, str, str]] = []
    module_search_documents: list[dict[str, Any]] = []
    for module in metadata.scaffold_modules:
        input_text = module_input_from_metadata(module)
        input_hash = hash_text(input_text)
        module_inputs.append((module.id, input_text, input_hash))
        module_rows.append(
            {
                "module_id": module.id,
                "concept_id": concept_id,
                "type": str(module.type),
                "title": module.title,
                "status": str(module.status),
                "origin": None if module.origin is None else str(module.origin),
                "focus": module.focus,
                "heading": None,
                "anchor": None,
                "segment_count": 1,
                "module_input_hash": input_hash,
                "indexed_revision": indexed_revision,
            }
        )
        module_search_documents.append(
            {
                "module_id": module.id,
                "concept_id": concept_id,
                "document_text": _module_search_text(module.title, str(module.type), module.focus),
                "indexed_revision": indexed_revision,
            }
        )

    concept_search_text = _concept_search_text(
        metadata.canonical_title, alias_values, overview_plaintext
    )
    concept_row = {
        "concept_id": concept_id,
        "canonical_title": metadata.canonical_title,
        "concept_type": str(metadata.concept_type),
        "status": str(metadata.status),
        "review_status": str(metadata.review_status),
        "vault_status": str(metadata.vault_status),
        "file_path": file_path,
        "h1_title": parsed.sections.h1_title,
        "overview_markdown": overview_markdown or None,
        "overview_plaintext": overview_plaintext or None,
        "identity_input_hash": identity_input_hash,
        "semantic_input_hash": semantic_input_hash,
        "note_schema_version": int(metadata.schema_version),
        "validity_state": "valid",
        "indexed_revision": indexed_revision,
        "note_created_at": _iso(metadata.created_at),
        "note_updated_at": _iso(metadata.updated_at),
    }

    hash_payload = {
        "concept": {
            key: value
            for key, value in concept_row.items()
            if key not in {"indexed_revision", "identity_input_hash", "semantic_input_hash"}
        },
        "aliases": alias_values,
        "domains": domain_values,
        "encounters": encounter_rows,
        "relationships": relationship_rows,
        "modules": [
            {
                key: value
                for key, value in row.items()
                if key not in {"indexed_revision", "module_input_hash"}
            }
            for row in module_rows
        ],
        "concept_search_document": concept_search_text,
        "module_search_documents": [
            {"module_id": doc["module_id"], "document_text": doc["document_text"]}
            for doc in module_search_documents
        ],
        "identity_input": identity_input,
        "semantic_input": semantic_input,
        "module_inputs": [
            {"module_id": module_id, "input_text": input_text}
            for module_id, input_text, _ in module_inputs
        ],
    }
    projection_hash = hash_projection_payload(hash_payload)

    return ConceptProjection(
        concept_id=concept_id,
        file_path=file_path,
        file_hash=file_hash,
        projection_hash=projection_hash,
        identity_input=identity_input,
        identity_input_hash=identity_input_hash,
        semantic_input=semantic_input,
        semantic_input_hash=semantic_input_hash,
        concept=concept_row,
        alias_values=alias_values,
        domain_values=domain_values,
        encounter_rows=encounter_rows,
        relationship_rows=relationship_rows,
        module_rows=module_rows,
        module_inputs=module_inputs,
        concept_search_document_text=concept_search_text,
        module_search_documents=module_search_documents,
        hash_payload=hash_payload,
    )


def indexed_file_row_for_projection(
    projection: ConceptProjection,
    *,
    mtime_ns: int,
    indexed_at: str,
    revision: int,
) -> dict[str, Any]:
    return {
        "file_path": projection.file_path,
        "concept_id": projection.concept_id,
        "note_schema_version": projection.concept["note_schema_version"],
        "file_hash": projection.file_hash,
        "projection_hash": projection.projection_hash,
        "mtime_ns": mtime_ns,
        "index_state": "valid",
        "last_success_revision": revision,
        "invalid_since_revision": None,
        "validation_errors_json": None,
        "indexed_at": indexed_at,
    }


def _concept_search_text(title: str, aliases: list[str], overview: str) -> str:
    parts = [title, *aliases]
    if overview:
        parts.append(overview)
    return " ".join(parts)


def _module_search_text(title: str, module_type: str, focus: str | None) -> str:
    parts = [title, module_type]
    if focus:
        parts.append(focus)
    return " ".join(parts)


def _encounter_row(concept_id: str, encounter: Any) -> dict[str, Any]:
    external = encounter.source.external_id
    return {
        "concept_id": concept_id,
        "source_type": str(encounter.source.type),
        "source_title": encounter.source.title,
        "unit_type": encounter.source.unit_type,
        "unit": encounter.source.unit,
        "section": encounter.source.section,
        "link": encounter.source.link,
        "external_id_type": None if external is None else external.type,
        "external_id_value": None if external is None else external.value,
        "role": str(encounter.role),
        "contribution_status": str(encounter.contribution_status),
        "content_attached": bool(encounter.content_attached),
        "content_id": encounter.content_id,
        "fingerprint": None,
    }


def _relationship_row(concept_id: str, relationship: Any) -> dict[str, Any]:
    return {
        "source_concept_id": concept_id,
        "relationship_type": str(relationship.relationship_type),
        "target_id": relationship.target_id,
        "target_title": relationship.target_title,
        "vault_status": str(relationship.vault_status),
        "learning_role": str(relationship.learning_role),
        "confidence": str(relationship.confidence),
        "status": str(relationship.status),
    }
