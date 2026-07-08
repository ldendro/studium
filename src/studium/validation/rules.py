"""Validation rules for concept note metadata and structure."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from studium.parsing.markdown_sections import ParsedMarkdownSections
from studium.schemas import (
    ConceptNoteMetadata,
    ConceptType,
    EncounterRole,
    LearningEncounter,
    ScaffoldModuleType,
    SourceType,
    ValidationIssue,
    ValidationOperation,
    ValidationSeverity,
)

_ENUM_PYDANTIC_CODES = frozenset({"enum", "literal_error"})
_ALLOWED_CONCEPT_TYPES = frozenset(member.value for member in ConceptType)
_ALLOWED_SOURCE_TYPES = frozenset(member.value for member in SourceType)
_ALLOWED_SCAFFOLD_MODULE_TYPES = frozenset(member.value for member in ScaffoldModuleType)


def validate_raw_metadata_enums(raw_metadata: Mapping[str, Any]) -> list[ValidationIssue]:
    """Detect unknown enum-like string values in raw parsed metadata."""
    issues: list[ValidationIssue] = []

    concept_type = raw_metadata.get("concept_type")
    if isinstance(concept_type, str) and concept_type not in _ALLOWED_CONCEPT_TYPES:
        issues.append(
            ValidationIssue(
                message=f"Unknown concept_type: {concept_type}",
                severity=ValidationSeverity.WARNING,
                field="concept_type",
                code="unknown_concept_type",
            )
        )

    encounters = raw_metadata.get("learning_encounters")
    if isinstance(encounters, list):
        encounter_items = cast(list[Any], encounters)
        for index, encounter in enumerate(encounter_items):
            if not isinstance(encounter, Mapping):
                continue
            encounter_map = cast(Mapping[str, Any], encounter)
            source = encounter_map.get("source")
            if not isinstance(source, Mapping):
                continue
            source_map = cast(Mapping[str, Any], source)
            source_type = source_map.get("type")
            if isinstance(source_type, str) and source_type not in _ALLOWED_SOURCE_TYPES:
                issues.append(
                    ValidationIssue(
                        message=f"Unknown source type: {source_type}",
                        severity=ValidationSeverity.WARNING,
                        field=f"learning_encounters.{index}.source.type",
                        code="unknown_source_type",
                    )
                )

    modules = raw_metadata.get("scaffold_modules")
    if isinstance(modules, list):
        module_items = cast(list[Any], modules)
        for index, module in enumerate(module_items):
            if not isinstance(module, Mapping):
                continue
            module_map = cast(Mapping[str, Any], module)
            module_type = module_map.get("type")
            if isinstance(module_type, str) and module_type not in _ALLOWED_SCAFFOLD_MODULE_TYPES:
                issues.append(
                    ValidationIssue(
                        message=f"Unknown scaffold module type: {module_type}",
                        severity=ValidationSeverity.WARNING,
                        field=f"scaffold_modules.{index}.type",
                        code="unknown_module_type",
                    )
                )

    return issues


def filter_parse_enum_critical_errors(
    issues: list[ValidationIssue],
    raw_metadata: Mapping[str, Any],
    operation: ValidationOperation,
) -> list[ValidationIssue]:
    """Drop redundant Pydantic enum critical errors when parse-mode warnings apply."""
    if operation != ValidationOperation.PARSE:
        return issues

    enum_warning_fields = {issue.field for issue in validate_raw_metadata_enums(raw_metadata)}
    if not enum_warning_fields:
        return issues

    filtered: list[ValidationIssue] = []
    for issue in issues:
        if (
            issue.severity == ValidationSeverity.CRITICAL
            and issue.field in enum_warning_fields
            and issue.code in _ENUM_PYDANTIC_CODES
        ):
            continue
        filtered.append(issue)
    return filtered


def check_unknown_fields(unknown_fields: list[str]) -> list[ValidationIssue]:
    """Emit issues for top-level metadata fields not in the schema."""
    return [
        ValidationIssue(
            message=f"Unknown metadata field: {field}",
            severity=ValidationSeverity.WARNING,
            field=field,
            code="unknown_field",
        )
        for field in unknown_fields
    ]


def check_empty_concept_domains(metadata: ConceptNoteMetadata) -> list[ValidationIssue]:
    """Warn when concept_domains is present but empty."""
    if metadata.concept_domains:
        return []
    return [
        ValidationIssue(
            message="concept_domains is empty",
            severity=ValidationSeverity.WARNING,
            field="concept_domains",
            code="empty_concept_domains",
        )
    ]


def check_missing_aliases(metadata: ConceptNoteMetadata) -> list[ValidationIssue]:
    """Warn when aliases is present but empty."""
    if metadata.aliases:
        return []
    return [
        ValidationIssue(
            message="aliases is empty",
            severity=ValidationSeverity.WARNING,
            field="aliases",
            code="missing_aliases",
        )
    ]


def check_multiple_primary_encounters(
    encounters: list[LearningEncounter] | None,
) -> list[ValidationIssue]:
    """Detect more than one primary learning encounter."""
    if not encounters:
        return []

    primary_count = sum(1 for encounter in encounters if encounter.role == EncounterRole.PRIMARY)
    if primary_count <= 1:
        return []
    return [
        ValidationIssue(
            message="Multiple primary learning encounters are not allowed",
            severity=ValidationSeverity.WARNING,
            field="learning_encounters",
            code="multiple_primary_encounters",
        )
    ]


def check_multiple_primary_encounters_raw(
    raw_metadata: Mapping[str, Any],
) -> list[ValidationIssue]:
    """Detect multiple primary encounters in raw metadata when models are unavailable."""
    encounters = raw_metadata.get("learning_encounters")
    if not isinstance(encounters, list) or not encounters:
        return []

    primary_count = 0
    encounter_items = cast(list[Any], encounters)
    for encounter in encounter_items:
        if isinstance(encounter, Mapping):
            encounter_map = cast(Mapping[str, Any], encounter)
            if encounter_map.get("role") == EncounterRole.PRIMARY.value:
                primary_count += 1

    if primary_count <= 1:
        return []
    return [
        ValidationIssue(
            message="Multiple primary learning encounters are not allowed",
            severity=ValidationSeverity.WARNING,
            field="learning_encounters",
            code="multiple_primary_encounters",
        )
    ]


def check_canonical_sections(sections: ParsedMarkdownSections) -> list[ValidationIssue]:
    """Emit issues for missing canonical Markdown sections."""
    return [
        ValidationIssue(
            message=f"Missing canonical section: {section_title}",
            severity=ValidationSeverity.WARNING,
            field=f"sections.{section_title}",
            code="missing_canonical_section",
        )
        for section_title in sections.canonical_missing
    ]


def check_h1_title_match(
    metadata: ConceptNoteMetadata,
    sections: ParsedMarkdownSections,
) -> list[ValidationIssue]:
    """Warn when the Markdown H1 title differs from canonical_title."""
    if sections.h1_title is None or sections.h1_title == metadata.canonical_title:
        return []
    return [
        ValidationIssue(
            message=(
                f"H1 title {sections.h1_title!r} does not match "
                f"canonical_title {metadata.canonical_title!r}"
            ),
            severity=ValidationSeverity.WARNING,
            field="sections.h1_title",
            code="h1_title_mismatch",
        )
    ]


def check_scaffold_module_section_consistency(
    metadata: ConceptNoteMetadata,
    sections: ParsedMarkdownSections,
) -> list[ValidationIssue]:
    """Warn when scaffold module metadata exists but the body section is missing."""
    if not metadata.scaffold_modules:
        return []
    if "Scaffold Modules" not in sections.canonical_missing:
        return []
    return [
        ValidationIssue(
            message="scaffold_modules metadata present but Scaffold Modules section is missing",
            severity=ValidationSeverity.WARNING,
            field="sections.Scaffold Modules",
            code="scaffold_modules_without_section",
        )
    ]


def collect_metadata_validation_issues(
    metadata: ConceptNoteMetadata,
    *,
    sections: ParsedMarkdownSections | None,
    unknown_fields: list[str] | None,
) -> list[ValidationIssue]:
    """Run metadata and optional section validation rules."""
    issues: list[ValidationIssue] = []
    if unknown_fields:
        issues.extend(check_unknown_fields(unknown_fields))
    issues.extend(check_empty_concept_domains(metadata))
    issues.extend(check_missing_aliases(metadata))
    issues.extend(check_multiple_primary_encounters(metadata.learning_encounters))
    if sections is not None:
        issues.extend(check_canonical_sections(sections))
        issues.extend(check_h1_title_match(metadata, sections))
        issues.extend(check_scaffold_module_section_consistency(metadata, sections))
    return issues


def collect_raw_metadata_validation_issues(
    raw_metadata: Mapping[str, Any],
    *,
    sections: ParsedMarkdownSections | None,
    unknown_fields: list[str] | None,
) -> list[ValidationIssue]:
    """Run validation rules that do not require a parsed metadata model."""
    issues: list[ValidationIssue] = []
    if unknown_fields:
        issues.extend(check_unknown_fields(unknown_fields))
    issues.extend(validate_raw_metadata_enums(raw_metadata))
    issues.extend(check_multiple_primary_encounters_raw(raw_metadata))
    if sections is not None:
        issues.extend(check_canonical_sections(sections))
    return issues
