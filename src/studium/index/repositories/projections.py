"""Atomic concept projection upsert and removal."""

from __future__ import annotations

import json
from typing import Any, cast

from sqlalchemy.engine import Connection

from studium.index.normalize import dedupe_aliases_by_normalized
from studium.index.repositories import aliases as aliases_repo
from studium.index.repositories import concepts as concepts_repo
from studium.index.repositories import domains as domains_repo
from studium.index.repositories import fts as fts_repo
from studium.index.repositories import indexed_files as indexed_files_repo
from studium.index.repositories import invalid_records as invalid_records_repo
from studium.index.repositories import learning_encounters as learning_encounters_repo
from studium.index.repositories import relationships as relationships_repo
from studium.index.repositories import scaffold_modules as scaffold_modules_repo
from studium.index.repositories import search_documents as search_documents_repo


def remove_concept_projection(connection: Connection, concept_id: str) -> None:
    """Delete a concept, cascaded children, and FTS rows."""
    fts_repo.delete_all_fts_for_concept(connection, concept_id)
    concepts_repo.delete_concept(connection, concept_id)


def upsert_concept_projection(
    connection: Connection,
    *,
    concept: dict[str, Any],
    alias_values: list[str],
    domain_values: list[str],
    encounter_rows: list[dict[str, Any]],
    relationship_rows: list[dict[str, Any]],
    module_rows: list[dict[str, Any]],
    concept_search_document: dict[str, Any],
    module_search_documents: list[dict[str, Any]],
    indexed_file: dict[str, Any],
) -> None:
    """Replace one concept projection and its indexed-file row atomically.

    Caller must run this inside a transaction. Existing child rows for the
    concept are deleted and re-inserted so projection stays deterministic.
    """
    concept_id = str(concept["concept_id"])
    fts_repo.delete_all_fts_for_concept(connection, concept_id)
    aliases_repo.delete_aliases_for_concept(connection, concept_id)
    domains_repo.delete_domains_for_concept(connection, concept_id)
    learning_encounters_repo.delete_encounters_for_concept(connection, concept_id)
    relationships_repo.delete_relationships_for_source(connection, concept_id)
    scaffold_modules_repo.delete_modules_for_concept(connection, concept_id)
    search_documents_repo.delete_concept_search_document(connection, concept_id)

    concepts_repo.upsert_concept(connection, concept)
    # Hyphen/underscore variants normalize to the same key; keep one row each.
    unique_aliases = dedupe_aliases_by_normalized(alias_values)
    for alias in unique_aliases:
        aliases_repo.insert_alias(connection, concept_id=concept_id, alias=alias)
    for domain in domain_values:
        domains_repo.insert_domain(connection, concept_id=concept_id, domain=domain)
    for encounter in encounter_rows:
        learning_encounters_repo.insert_learning_encounter(connection, encounter)
    for relationship in relationship_rows:
        relationships_repo.insert_relationship(connection, relationship)
    for module in module_rows:
        scaffold_modules_repo.upsert_scaffold_module(connection, module)
    search_documents_repo.upsert_concept_search_document(connection, concept_search_document)
    for module_doc in module_search_documents:
        search_documents_repo.upsert_module_search_document(connection, module_doc)

    overview = ""
    fields_raw = concept_search_document.get("field_weights_json")
    if isinstance(fields_raw, str) and fields_raw:
        try:
            parsed_fields: object = json.loads(fields_raw)
        except json.JSONDecodeError:
            parsed_fields = None
        if isinstance(parsed_fields, dict):
            typed_fields = cast(dict[str, object], parsed_fields)
            overview_value = typed_fields.get("overview")
            overview = "" if overview_value is None else str(overview_value)

    fts_repo.sync_concept_projection_fts(
        connection,
        concept_id=concept_id,
        title=str(concept["canonical_title"]),
        aliases=alias_values,
        domains=domain_values,
        overview=overview,
        module_rows=module_rows,
    )

    indexed_files_repo.upsert_indexed_file(connection, indexed_file)
    invalid_records_repo.delete_invalid_records_for_path(connection, str(indexed_file["file_path"]))


def mark_path_invalid(
    connection: Connection,
    *,
    indexed_file: dict[str, Any],
    invalid_record: dict[str, Any],
    remove_concept_id: str | None,
) -> None:
    """Record an invalid/conflicted path and remove searchable projection if owned."""
    file_path = str(indexed_file["file_path"])
    if remove_concept_id is not None:
        existing = concepts_repo.get_concept(connection, remove_concept_id)
        if existing is not None and existing.get("file_path") == file_path:
            remove_concept_projection(connection, remove_concept_id)

    invalid_records_repo.delete_invalid_records_for_path(connection, file_path)
    indexed_files_repo.upsert_indexed_file(connection, indexed_file)
    invalid_records_repo.insert_invalid_record(connection, invalid_record)
