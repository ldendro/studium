## Branch Summary

**Phase:** 1 - Vault Storage Core
**Branch:** 6 - Validation Layer
**Status:** `merged`

---

## 1. Goal

Implement critical error and warning validation behavior for parsing, serializing, creating, updating, and writing to a vault for concept notes. Validation from B3, B4, and B5 was deferred to this branch. This layer implementation exists now because after parsing and serialization we can validate whole note structures instead of simple schema validation from B3. 

---
## 2. Branch Context

This section should be written before Cursor creates the detailed implementation plan.

### Main System Area

This branch primarily affects:

-  Note structure validation

### Branch Dependencies

B3 for schema definitions, B4 for parsing functionality, and B5 for serialization functionality. All important invalidating the flow from creating a note, saving to vault, and then reading that note from the vault. 

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

- `[[Concept Name]]`
    
- `[[Concept Name]]`
    

Questions I should be able to answer:

---

## 4. Cursor Implementation Planning Prompt

Use this prompt to ask Cursor for a detailed implementation plan **before any code is generated**.

Cursor should not implement yet. The goal of this step is to produce a clear plan that I can review, question, and approve.

```text
We are planning the implementation for a single branch of Studium.

Do not implement code yet.

Project context:
Studium is an AI-assisted learning system built around Markdown/Obsidian-compatible notes, concept graphs, scaffold generation, source-aware RAG, local/source library processing, and agent-based note review.

Phase: 1 - Vault Storage Core

Branch: 6 - Validation Layer

Branch goal:
Validate parsing -> serialization and serialization -> parsing, handling different types of erros as warning or critical. 

Expected outcome:
A validation layer implemented that ensures concept notes follow the expected organization constraints through creating, updating, and writing to vault. 

Relevant context:
4 - Branch Plan, 3 - Technical Plan, and 2 - Final Phase Roadmap. 

Known constraints:
- Keep implementation scoped to this branch.
- Do not introduce broad architecture changes unless you explicitly explain why they are necessary.
- If you believe a schema, system model, or architecture decision needs to change, call that out before implementation.
- Prefer clear, maintainable code over clever abstractions.
- Favor code I can understand and explain.
- Include tests or verification steps where appropriate.
- Assume I will review and approve this plan before implementation.

Please produce a branch implementation plan with:

1. Summary of your proposed approach
2. Files likely to be created or modified
3. Step-by-step implementation sequence
4. Data model or schema changes, if any
5. Important functions/classes/modules likely needed
6. Tests or verification steps to add
7. Risks, edge cases, or assumptions
8. Questions or decisions needed before implementation
```

---

## 5. Cursor Implementation Plan

## 1. Summary of Proposed Approach

Implement a dedicated `studium.validation` layer that sits above B3 schemas, B4 parsing, and B5 serialization. It does not replace Pydantic or re-parse YAML everywhere; it orchestrates operation-mode rules and produces a single `ValidationResult` per call.

### Design principles

1. **Two layers, one responsibility each**
    - B4 (unchanged role): syntactic/structural parse — split frontmatter, load YAML, build `ConceptNoteMetadata` when possible, detect sections, emit initial `ValidationIssue` lists on `ParsedConceptNote`.
    - B6 (new): semantic/operation rules — classify issues as critical vs warning based on mode, add deferred checks (H1 mismatch, multiple-primary encounters, empty domains, scaffold/section consistency), and validate generated/proposed notes strictly.
2. **Mode-driven severity, not duplicate validators**
    - Use a small severity policy table keyed by `(operation, issue_code)` rather than four separate validator implementations.
    - Example: `missing_canonical_section` → `WARNING` on `PARSE`, `CRITICAL` on `CREATE`/`UPDATE`/`WRITE`; `unknown_field` → `WARNING` on `PARSE`, `CRITICAL` on write modes.
3. **Three validation entry shapes**
    - Parsed note path — `validate_parsed_concept_note(parsed, operation=PARSE)` wraps B4 output and adds B6 rules.
    - Structured note path — `validate_concept_metadata(metadata, operation=..., sections=..., unknown_fields=...)` for metadata + optional section context (used by create/update flows before serialization).
    - Generated note path — `validate_generated_concept_note(metadata, body, operation=CREATE)` runs metadata + section rules, then optionally a serialization round-trip check (`serialize` → `parse` → assert no new critical issues and canonical structure intact).
4. **Reads permissive, writes cautious (Technical Plan §Validation Layer, Final Roadmap §5.10)**
    - Parsing existing vault files may yield warnings without blocking inspection.
    - Generated/proposed content must satisfy full canonical structure before B7 will commit.
5. **No vault I/O in B6**
    - Path traversal, collision detection, and stale-hash checks stay in B7. B6 validates note _content_ only.

---

## 2. Files Likely to Be Created or Modified

### New

|File|Purpose|
|---|---|
|`src/studium/validation/concept_note.py`|Top-level orchestrators: `validate_parsed_concept_note`, `validate_concept_metadata`, `validate_generated_concept_note`, optional `parse_and_validate`|
|`src/studium/validation/rules.py`|Individual rule functions returning `list[ValidationIssue]` (encounters, sections, metadata hygiene, scaffold consistency)|
|`src/studium/validation/severity.py`|`ValidationOperation` severity policy + `apply_operation_severity(issues, operation)`|
|`src/studium/validation/result.py`|`build_validation_result(issues, operation)` helper; optional `merge_issues`|
|`tests/validation/conftest.py`|Shared fixtures / builders|
|`tests/validation/helpers.py`|Builders for parsed notes, metadata overrides|
|`tests/validation/test_severity.py`|Mode reclassification tests|
|`tests/validation/test_metadata_rules.py`|Metadata-specific rules|
|`tests/validation/test_section_rules.py`|Canonical section + H1 checks|
|`tests/validation/test_encounter_rules.py`|Multiple-primary, encounter shape|
|`tests/validation/test_concept_note.py`|Integration: parse/create/write modes, round-trip|
|`tests/fixtures/validation/`|Invalid-note fixtures (multiple primary, bad enums in raw YAML, etc.)|

### Modified

|File|Change|
|---|---|
|`src/studium/validation/__init__.py`|Export public validation API|
|`src/studium/schemas/validation.py`|Optional: add `ValidationResult.ok(operation)` / `from_issues()` factory (small ergonomics only)|
|`tests/parsing/test_concept_note.py`|May add assertions that B4 issues are re-classified correctly when passed through B6 (light touch)|

### Not changed (consume only)

- `schemas/` models (unless enum-parse decision in §8 requires adjustment)
- `serialization/` (called for round-trip checks only)
- `vault/`, `writes/`, `cli/` (B7/B8 wire validation in)

---

## 3. Step-by-Step Implementation Sequence

### Step 1 — Severity policy and result builder

- Define stable `code` strings for all Phase 1 issues (`unknown_field`, `missing_canonical_section`, `h1_title_mismatch`, `multiple_primary_encounters`, `empty_concept_domains`, `missing_aliases`, `scaffold_modules_without_section`, etc.).
- Implement `DEFAULT_SEVERITY: dict[tuple[ValidationOperation, str], ValidationSeverity]` with parse-permissive / write-strict defaults.
- Implement `build_validation_result(issues, operation) -> ValidationResult` where `is_valid = not critical_errors`.

### Step 2 — Metadata rules (`rules.py`)

- `check_unknown_fields(unknown_fields)` — always emitted; severity applied in step 1.
- `check_empty_concept_domains(metadata)` — warning in all modes (per Technical Plan create flow).
- `check_missing_aliases(metadata)` — warning when empty.
- `check_duplicate_scaffold_module_ids(metadata)` — prefer surfacing Pydantic's error with code `duplicate_scaffold_module_id`; add explicit check only if clearer messages needed.
- `check_scaffold_module_section_consistency(metadata, sections)` — warn when modules exist but `Scaffold Modules` section missing (Phase 1 warn-only).

### Step 3 — Learning encounter rules

- `check_multiple_primary_encounters(encounters)` — critical on `CREATE`/`UPDATE`/`WRITE`; warning on `PARSE` (tolerate imperfect existing notes per B3 decision).
- Optionally warn when no encounter has `role: primary` on parse (non-blocking).

### Step 4 — Section rules

- `check_canonical_sections(sections)` — uses `ParsedMarkdownSections.canonical_missing`.
- `check_h1_title_match(metadata, sections)` — warn when `sections.h1_title` is set and ≠ `metadata.canonical_title` (deferred from B4).

### Step 5 — Parsed-note orchestrator

- `validate_parsed_concept_note(parsed, operation=PARSE)`:
    1. Start with `parsed.critical_errors` + `parsed.warnings` from B4.
    2. If `parsed.metadata` is not `None`, run metadata/encounter/section rules.
    3. Pass `parsed.unknown_metadata_fields` into unknown-field rule.
    4. Apply severity policy for `operation`.
    5. Return `ValidationResult`.

### Step 6 — Metadata-only orchestrator

- `validate_concept_metadata(metadata, *, operation, sections=None, unknown_fields=None)` for create/update paths before serialization.
- Used when you have a valid `ConceptNoteMetadata` but no raw Markdown yet.

### Step 7 — Generated-note orchestrator + round-trip

- `validate_generated_concept_note(metadata, body, operation=CREATE)`:
    1. Run `validate_concept_metadata(..., sections=parse_markdown_sections(body))`.
    2. Round-trip check (branch goal): `serialized = serialize_concept_note(metadata, body)` → `reparsed = parse_concept_note(serialized)` → ensure `reparsed.metadata == metadata`, no new critical errors, `canonical_missing == []` for strict modes.
    3. Emit critical if round-trip introduces structural drift (guards B5 regressions).

### Step 8 — Public exports and thin convenience API

- `parse_and_validate(raw_markdown, operation=PARSE) -> tuple[ParsedConceptNote, ValidationResult]` for B8 CLI.
- Wire `studium.validation.__init__.py`.

### Step 9 — Tests and verification

- Unit tests per rule module + integration tests per operation mode.
- Reuse existing parsing fixtures; add validation-specific fixtures.
- Run `uv run ruff check .`, `uv run pyright`, `uv run pytest`.

---

## 4. Data Model or Schema Changes

|Topic|Recommendation|
|---|---|
|`ValidationIssue` / `ValidationResult`|No structural change required. Optionally add a small factory on `ValidationResult`.|
|`ParsedConceptNote`|No change. Keep embedded issues from B4; B6 composes `ValidationResult`.|
|`ConceptNoteMetadata`|Likely no change. Duplicate module IDs and min encounters stay in Pydantic.|
|Enum strictness on parse|Decision needed (§8). Technical Plan says unknown `concept_type` / `source_type` should warn on parse but current StrEnums cause Pydantic critical failures in B4. Options: (a) add permissive pre-check on `raw_metadata` in B6 before trusting `metadata is None`, (b) loosen enum fields to `str` + B6 validation, or (c) add a parallel permissive parse path in `yaml_frontmatter`. Call out before implementation.|
|`WriteProposal`|No change in B6. B7 will call B6 and copy issues onto the proposal.|

---

## 5. Important Functions / Classes / Modules

|Symbol|Role|
|---|---|
|`validate_parsed_concept_note(parsed, operation=PARSE)`|Primary read path after B4|
|`validate_concept_metadata(metadata, *, operation, sections, unknown_fields)`|Validate structured metadata for create/update|
|`validate_generated_concept_note(metadata, body, operation=CREATE)`|Strict validation of proposed file content + round-trip|
|`parse_and_validate(raw_markdown, operation=PARSE)`|Convenience for CLI / vault reads|
|`apply_operation_severity(issues, operation)`|Central mode → severity mapping|
|`build_validation_result(issues, operation)`|Partition into critical/warnings, set `is_valid`|
|`check_multiple_primary_encounters(...)`|Write-mode critical rule|
|`check_h1_title_match(...)`|Deferred semantic check|
|`check_canonical_sections(...)`|Section presence with mode-dependent severity|
|`check_unknown_fields(...)`|Parse warn / write critical|

### Explicitly deferred to later branches

|Symbol|Branch|
|---|---|
|`build_create_note_proposal(...)`|B7|
|`commit_write_proposal(...)`|B7|
|Vault path / collision / hash validation|B7|
|`studium validate-note` / `validate-vault` CLI|B8|
|Relationship graph resolution / semantic correctness|Phase 2+|

---

## 6. Tests / Verification Steps

### `test_severity.py`

- `unknown_field`: WARNING on `PARSE`, CRITICAL on `WRITE`
- `missing_canonical_section`: WARNING on `PARSE`, CRITICAL on `CREATE`
- Warnings-only → `is_valid=True`; any critical → `is_valid=False`

### `test_metadata_rules.py`

- Empty `concept_domains` → warning
- Missing `aliases` → warning
- Duplicate scaffold module IDs → critical (via metadata validation path)

### `test_encounter_rules.py`

- Two `primary` encounters → warning on `PARSE`, critical on `WRITE`
- Single primary → no issue

### `test_section_rules.py`

- All canonical sections present → no section issues
- Missing `## Prerequisites` → mode-dependent severity
- H1 `"Foo"` vs `canonical_title: "Bar"` → warning

### `test_concept_note.py` (integration)

- `valid_concept_note.md` → `PARSE`: valid, may have zero warnings
- `unknown_metadata_field.md` → `PARSE`: valid with `unknown_field` warning; `WRITE`: invalid
- `missing_canonical_section.md` → `PARSE`: valid with section warning; `CREATE`: invalid
- `invalid_yaml_note.md` → critical regardless of mode
- `create_concept_note_markdown("X")` → `CREATE`: valid, no critical, all sections present
- Round-trip: `parse → serialize → parse` on valid fixture → `WRITE` validation passes
- Round-trip: generated note → `validate_generated_concept_note` → valid

### Verification commands

uv run ruff check .

uv run pyright

uv run pytest tests/validation -q

uv run pytest # full suite regression

---

## 7. Risks, Edge Cases, and Assumptions

|Risk|Mitigation|
|---|---|
|Duplicating Pydantic validation|B6 adds only cross-field and operation-mode rules; rely on B4/Pydantic for shape errors|
|B4 and B6 both emit section/unknown-field issues|B6 re-classifies B4 issues by operation rather than re-detecting in B4|
|Enum values fail at parse time as critical|Address in §8; may need `raw_metadata` inspection when `metadata is None`|
|UPDATE validates body that intentionally diverges from canonical|Strict modes apply to proposed `after_content` from Studium serialization, not arbitrary hand-edited preservation paths in B7|
|Round-trip false positives from YAML formatting|Round-trip asserts metadata equality + no critical parse errors, not byte identity (consistent with B5)|
|Over-abstraction across four modes|Single severity table + three orchestrators, not four parallel validator classes|

### Assumptions

- B3/B4/B5 APIs are stable.
- `ParsedConceptNote.critical_errors` from B4 are always `CRITICAL` severity before B6 re-classification (B6 may only upgrade warnings → critical, not downgrade critical → warning except where explicitly documented).
- Phase 1 does not validate relationship target existence against a vault index.
- Scaffold module content under `## Scaffold Modules` is not validated in Phase 1 (metadata-only warn if section missing).

---

## 8. Questions / Decisions Needed Before Implementation

1. Unknown enum values on parse — Technical Plan requires warn-on-parse for unknown `concept_type` / `source_type` / module types, but StrEnums + `extra="forbid"` currently produce critical Pydantic errors. Recommend: add a `validate_raw_metadata_enums(raw_metadata) -> list[ValidationIssue]` in B6 that runs on `parsed.raw_metadata` and, for `PARSE` mode, treats unknown enum strings as warnings even when `metadata is None`. Confirm or prefer schema loosening instead.
    
2. UPDATE vs WRITE severity — Should `UPDATE` and `WRITE` share identical strictness? Recommend: yes for Phase 1; `WRITE` is an alias-level equivalent unless you want `UPDATE` to allow preserving non-canonical bodies (which would weaken write safety).
    
3. Multiple primary on parse — Warn only (recommended per B3) or silent? Recommend: warning on `PARSE`, critical on write modes.
    
4. H1 mismatch severity — Always warning, or critical on create/write? Recommend: warning in all modes (cosmetic/Obsidian drift); block writes only if you want stricter behavior.
    
5. Round-trip as hard gate — Should `validate_generated_concept_note` always run serialize→parse round-trip, or only in tests? Recommend: always for `CREATE`/`WRITE` modes — directly supports your branch goal and catches serializer regressions before B7.
    
6. Empty `concept_domains` — Warning on create (Technical Plan) but empty list is schema-valid. Recommend: warning in all modes when list is empty.
    
7. Refactor B4 to remove embedded warnings? — Recommend: no; keep B4 issues on `ParsedConceptNote`, let B6 re-classify. Minimizes B4 churn.
    
8. `validate_concept_metadata` vs `validate_parsed_concept_note` naming — Approve proposed public API surface above, or prefer a single `validate_concept_note(...)` with a discriminated input type?

---

## 6. Implementation Notes

### Validation Layer Reference Table

Severity is applied last by `build_validation_result()` → `apply_operation_severity()` in `severity.py`. Detection happens earlier in B4 or B6 as shown below.

### Entry points by operation

| Operation | Typical caller                    | Orchestrator                                                                            |
| --------- | --------------------------------- | --------------------------------------------------------------------------------------- |
| PARSE     | Vault read, inspect existing file | `parse_and_validate()` → `validate_parsed_concept_note(op=PARSE)`                       |
| CREATE    | New note generation               | `validate_generated_concept_note(op=CREATE)`                                            |
| UPDATE    | Proposed edit content             | `validate_generated_concept_note(op=UPDATE)`                                            |
| WRITE     | Pre-commit content gate (B7)      | `validate_parsed_concept_note(op=WRITE)` or `validate_generated_concept_note(op=WRITE)` |

`CREATE`, `UPDATE`, and `WRITE` share the same strictness via `is_strict_operation()` in `severity.py`.

---

### Issues, detection, and severity

|Issue|Where detected|Function chain|PARSE|CREATE / UPDATE / WRITE|
|---|---|---|---|---|
|Invalid YAML|B4 parsing|`parse_concept_note()` → `parse_yaml_frontmatter()`|Critical|Critical|
|Missing frontmatter|B4 parsing|`parse_concept_note()` → `split_frontmatter()`|Critical|Critical|
|Schema shape errors (missing required fields, bad types, duplicate scaffold IDs, etc.)|B3 + B4|`parse_yaml_frontmatter()` → `ConceptNoteMetadata.model_validate()` → `_pydantic_errors_to_issues()`|Critical|Critical|
|Unknown metadata field|B4 (parse path)|`parse_concept_note()` — uses `yaml_result.unknown_fields`|Warning|Critical|
||B6 (metadata path)|`validate_concept_metadata()` → `collect_metadata_validation_issues()` → `check_unknown_fields()`|—|Critical|
|Missing canonical section|B4 (parse path)|`parse_concept_note()` — uses `sections.canonical_missing` from `parse_markdown_sections()`|Warning|Critical|
||B6 (generated path)|`validate_generated_concept_note()` → `parse_markdown_sections()` → `validate_concept_metadata()` → `check_canonical_sections()`|—|Critical|
|Unknown `concept_type`|B6|`validate_raw_metadata_enums()`|Warning¹|Critical|
|Unknown `source.type`|B6|`validate_raw_metadata_enums()`|Warning¹|Critical|
|Unknown scaffold module `type`|B6|`validate_raw_metadata_enums()`|Warning¹|Critical|
|Multiple primary encounters|B6|`validate_parsed_concept_note()` → `check_multiple_primary_encounters()` (if metadata exists) or `check_multiple_primary_encounters_raw()` (if not)|Warning|Critical|
||B6 (generated path)|`validate_concept_metadata()` → `collect_metadata_validation_issues()` → `check_multiple_primary_encounters()`|—|Critical|
|Empty `concept_domains`|B6|`validate_parsed_concept_note()` or `validate_concept_metadata()` → `check_empty_concept_domains()`|Warning|Warning|
|Empty `aliases`|B6|`validate_parsed_concept_note()` or `validate_concept_metadata()` → `check_missing_aliases()`|Warning|Warning|
|H1 ≠ `canonical_title`|B6|`validate_parsed_concept_note()` or `validate_concept_metadata()` → `check_h1_title_match()`|Warning|Warning|
|Scaffold metadata but no `## Scaffold Modules` section|B6|`validate_parsed_concept_note()` or `validate_concept_metadata()` → `check_scaffold_module_section_consistency()`|Warning|Warning|
|Round-trip metadata mismatch|B6|`validate_generated_concept_note()` → `_round_trip_issues()` → `serialize_concept_note()` → `parse_concept_note()`|—|Critical|
|Round-trip introduced parse errors|B6|Same as above|—|Critical|

¹ On PARSE, `filter_parse_enum_critical_errors()` removes the redundant Pydantic enum critical from B4 so only the B6 warning remains.

### Severity policy (`severity.py`)

|Code group|Codes|PARSE|CREATE / UPDATE / WRITE|
|---|---|---|---|
|Mode-sensitive|`unknown_field`, `missing_canonical_section`, `multiple_primary_encounters`, `unknown_concept_type`, `unknown_source_type`, `unknown_module_type`|Warning|Critical|
|Always warning|`h1_title_mismatch`, `empty_concept_domains`, `missing_aliases`, `scaffold_modules_without_section`|Warning|Warning|
|Always critical|`invalid_yaml`, `missing_frontmatter`, Pydantic codes (`enum`, `missing`, etc.), `round_trip_*`|Critical|Critical|
