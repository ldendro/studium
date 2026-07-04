"""YAML frontmatter parsing and metadata normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import yaml
from pydantic import ValidationError

from studium.parsing.errors import YamlParseError
from studium.schemas import ConceptNoteMetadata, ValidationIssue, ValidationSeverity

_OPTIONAL_SOURCE_FIELDS = ("unit_type", "unit", "section", "link")


@dataclass(frozen=True)
class YamlParseResult:
    """Raw and schema-known metadata extracted from YAML frontmatter text."""

    raw_metadata: dict[str, Any]
    known_metadata: dict[str, Any]
    unknown_fields: list[str]
    metadata: ConceptNoteMetadata | None
    metadata_issues: list[ValidationIssue]


def parse_yaml_frontmatter(yaml_text: str) -> YamlParseResult:
    """Parse YAML text into a metadata dictionary and validate known fields.

    Unknown top-level keys are stripped before Pydantic validation and returned
    separately so B6 can emit parse-time warnings. Empty strings on optional
    nullable fields are normalized to ``None`` before validation.
    """
    try:
        loaded = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        msg = f"Invalid YAML frontmatter: {exc}"
        raise YamlParseError(msg) from exc

    if loaded is None:
        raw_metadata: dict[str, Any] = {}
    elif not isinstance(loaded, dict):
        msg = "YAML frontmatter must parse to a mapping"
        raise YamlParseError(msg)
    else:
        raw_metadata = cast(dict[str, Any], loaded)

    unknown_fields = sorted(
        key for key in raw_metadata if key not in ConceptNoteMetadata.model_fields
    )
    known_metadata = {
        key: value for key, value in raw_metadata.items() if key in ConceptNoteMetadata.model_fields
    }
    normalized_metadata = _normalize_empty_strings(known_metadata)

    metadata: ConceptNoteMetadata | None = None
    metadata_issues: list[ValidationIssue] = []
    try:
        metadata = ConceptNoteMetadata.model_validate(normalized_metadata)
    except ValidationError as exc:
        metadata_issues = _pydantic_errors_to_issues(exc)

    return YamlParseResult(
        raw_metadata=raw_metadata,
        known_metadata=normalized_metadata,
        unknown_fields=unknown_fields,
        metadata=metadata,
        metadata_issues=metadata_issues,
    )


def _normalize_empty_strings(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize empty strings to None on optional nullable metadata fields."""
    normalized = dict(data)

    encounters = normalized.get("learning_encounters")
    if isinstance(encounters, list):
        normalized_encounters: list[Any] = []
        for encounter in cast(list[Any], encounters):
            if isinstance(encounter, dict):
                normalized_encounters.append(
                    _normalize_learning_encounter(cast(dict[str, Any], encounter))
                )
            else:
                normalized_encounters.append(encounter)
        normalized["learning_encounters"] = normalized_encounters

    relationships = normalized.get("relationships")
    if isinstance(relationships, list):
        normalized_relationships: list[Any] = []
        for relationship in cast(list[Any], relationships):
            if isinstance(relationship, dict):
                normalized_relationships.append(
                    _normalize_relationship(cast(dict[str, Any], relationship))
                )
            else:
                normalized_relationships.append(relationship)
        normalized["relationships"] = normalized_relationships

    scaffold_modules = normalized.get("scaffold_modules")
    if isinstance(scaffold_modules, list):
        normalized_modules: list[Any] = []
        for module in cast(list[Any], scaffold_modules):
            if isinstance(module, dict):
                normalized_modules.append(_normalize_scaffold_module(cast(dict[str, Any], module)))
            else:
                normalized_modules.append(module)
        normalized["scaffold_modules"] = normalized_modules

    return normalized


def _normalize_learning_encounter(encounter: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(encounter)
    if normalized.get("content_id") == "":
        normalized["content_id"] = None

    source = normalized.get("source")
    if isinstance(source, dict):
        normalized["source"] = _normalize_source(cast(dict[str, Any], source))

    return normalized


def _normalize_source(source: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(source)
    for field in _OPTIONAL_SOURCE_FIELDS:
        if normalized.get(field) == "":
            normalized[field] = None
    return normalized


def _normalize_relationship(relationship: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(relationship)
    if normalized.get("target_id") == "":
        normalized["target_id"] = None
    return normalized


def _normalize_scaffold_module(module: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(module)
    for field in ("origin", "focus"):
        if normalized.get(field) == "":
            normalized[field] = None
    return normalized


def _pydantic_errors_to_issues(error: ValidationError) -> list[ValidationIssue]:
    return [
        ValidationIssue(
            message=issue["msg"],
            severity=ValidationSeverity.CRITICAL,
            field=".".join(str(part) for part in issue["loc"]) or None,
            code=str(issue["type"]),
        )
        for issue in error.errors()
    ]
