## Branch Summary

**Phase:** 1 - Vault Storage Core   
**Branch:** 3 -  Concept Note Schemas
**Status:** `merged`

---

## 1. Goal

We need to define schema models early as future branches will rely on organized and aggregated metadata for corresponding source, concept notes, relationships, and other key aspects of the system. We will define Pydantic models for key schemas that parsing, serialization, validation, and write proposals will use.

---

## 2. Branch Context

### Main System Area

This branch primarily affects:

-  Markdown parsing
-  Data schemas
### Branch Dependencies

This branch depends on: None
### Risks / Things to Watch

Review and ensure model schemas are aligned and accurately convey functionality for future use cases. 

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

### Pydantic Models: 

- A Pydantic model, unlike standard Python classes, enforces strict data compliance at runtime. When you pass untrusted data (like API requests or JSON files) into a model, Pydantic parses, type-coerces, and guarantees that the resulting output strictly matches the defined schema.
	- **Data Validation:** Automatically throws clear errors if input data types do not match the fields.
	- **Type Coercion:** Cleverly converts compatible data types, such as turning the string `"42"` into the integer `42`.
	- **Serialization:** Easily exports data back into native Python dictionaries using `model_dump()` or JSON strings via `model_dump_json()`.
	- **JSON Schema Generation:** Instantly outputs a standard JSON Schema from your data rules for documentation.

---

## 4. Cursor Implementation Planning Prompt

Use this prompt to ask Cursor for a detailed implementation plan **before any code is generated**.

Cursor should not implement yet. The goal of this step is to produce a clear plan that I can review, question, and approve.

```text
We are planning the implementation for a single branch of Studium.

Do not implement code yet.

Project context:
Studium is an AI-assisted learning system built around Markdown/Obsidian-compatible notes, concept graphs, scaffold generation, source-aware RAG, local/source library processing, and agent-based note review.

Phase: 

Phase: `1 - Vault Storage Core`

Branch: `3 - Concept Note Schemas`

Expected outcome:
Pydantic models exist for all Phase 1 metadata structures and the schemas reflect the approved concept taxonomy in this phases technical plan. Models support required fields and defaults where appropriate and model tests cover valid and invalid schema cases

Relevant context:
See Data Models & Schemas section in this phases technical plan for metadata taxonomy. If there are any suggestions with specific fields in within the implemented pydantic models and the values they represent, note these recommendations before implementing. 

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
### 1. Summary of proposed approach

Define Phase 1 metadata as a small set of strict Pydantic v2 models under [`src/studium/schemas/`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/), aligned with the Technical Plan §5 (Data Models and Schemas).

Design principles:

1. Enums where the Technical Plan lists allowed values — `concept_type`, source types, module types, relationship types, relationship `vault_status`, encounter `role`, `contribution_status`, etc. Use `StrEnum` for readability and Pyright safety.
2. Plain `str` for note lifecycle fields without exhaustive enums — `status`, `review_status`, and note-level `vault_status` only have example values in the plan (`scaffolded`, `not_submitted`, `draft`), not a closed list. Model them as non-empty strings; B6 can tighten later if taxonomy is finalized.
3. `extra="forbid"` on metadata models — unknown YAML keys fail at model construction. Parse-time “warn on unknown field” behavior belongs in B6, which can validate raw dicts before strict model construction.
4. Structural validators in B3, operation-mode logic in B6 — e.g. `learning_encounters` min length 1, duplicate scaffold module IDs, `schema_version == 1`, `note_type == "concept"`. “Warn on parse / reject on write” for unknown enum values is B6.
5. One small factory helper — `default_studium_learning_encounter()` matching the Technical Plan default, for tests and later B5 serialization.
6. Include supporting models — `ValidationIssue`, `ValidationResult`, `WriteProposal` as pure data containers (no validation orchestration yet).
---

### 2. Files likely to be created or modified

New

|File|Contents|
|---|---|
|[`src/studium/schemas/enums.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/enums.py)|All `StrEnum` types|
|[`src/studium/schemas/source.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/source.py)|`SourceMetadata`|
|[`src/studium/schemas/learning_encounter.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/learning_encounter.py)|`LearningEncounter`, `default_studium_learning_encounter()`|
|[`src/studium/schemas/scaffold_module.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/scaffold_module.py)|`ScaffoldModuleMetadata`|
|[`src/studium/schemas/relationship.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/relationship.py)|`RelationshipMetadata`|
|[`src/studium/schemas/concept_note.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/concept_note.py)|`ConceptNoteMetadata` + cross-field validators|
|[`src/studium/schemas/validation.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/validation.py)|`ValidationIssue`, `ValidationResult`, `ValidationOperation`|
|[`src/studium/schemas/write_proposal.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/write_proposal.py)|`WriteProposal`, `WriteOperation`|
|[`tests/schemas/conftest.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/tests/schemas/conftest.py)|Shared valid metadata fixture from Technical Plan example|
|[`tests/schemas/test_concept_note.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/tests/schemas/test_concept_note.py)|Valid/invalid concept note cases|
|[`tests/schemas/test_learning_encounter.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/tests/schemas/test_learning_encounter.py)|Encounter + source cases|
|[`tests/schemas/test_scaffold_module.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/tests/schemas/test_scaffold_module.py)|Module metadata cases|
|[`tests/schemas/test_relationship.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/tests/schemas/test_relationship.py)|Relationship cases|
|[`tests/schemas/test_validation.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/tests/schemas/test_validation.py)|Validation result/issue cases|
|[`tests/schemas/test_write_proposal.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/tests/schemas/test_write_proposal.py)|Write proposal cases|

Modified

- [`src/studium/schemas/__init__.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/schemas/__init__.py) — public exports

Not changed

- `vault/`, `parsing/`, `serialization/`, `validation/`, `writes/`, `cli/`, `pyproject.toml` (Pydantic already a dependency)

---

### 3. Step-by-step implementation sequence

1. Add enums (`enums.py`) for all fields with explicit allowed values in Technical Plan §5.2–5.6:
    
    - `ConceptType`, `SourceType`, `EncounterRole`, `ContributionStatus`
    - `ScaffoldModuleType`, `ScaffoldModuleStatus`, `ScaffoldModuleOrigin`
    - `RelationshipType`, `RelationshipVaultStatus`
    - `ValidationOperation` (`parse`, `create`, `update`, `write`)
    - `WriteOperation` (`create_note`, `update_note`)
    - `ValidationSeverity` (`critical`, `warning`)
    
2. Add leaf models — `SourceMetadata`, `ScaffoldModuleMetadata`, `RelationshipMetadata`, `LearningEncounter` with required/optional fields per §5.4–5.6.
    
3. Add `ConceptNoteMetadata` with:
    
    - `schema_version: Literal[1] = 1`
    - `note_type: Literal["concept"] = "concept"`
    - Required lists defaulting to `[]` only where Technical Plan allows empty (`aliases`, `concept_domains`, `scaffold_modules`, `relationships`)
    - `learning_encounters` required, no default (must be provided)
    - `created_at` / `updated_at` as `datetime` (Pydantic parses ISO 8601)
    - `@model_validator` for duplicate scaffold module IDs
    
4. Add supporting models — `ValidationIssue`, `ValidationResult`, `WriteProposal`.
    
5. Add `default_studium_learning_encounter()` factory returning a valid `LearningEncounter`.
    
6. Wire exports in `schemas/__init__.py`.
    
7. Add tests using fixture dicts derived from the Technical Plan example (§5.1).
    
8. Verify — `uv run ruff check .`, `uv run pyright`, `uv run pytest`.
    

---

### 4. Data model or schema changes

This branch implements the Phase 1 schema (Technical Plan is source of truth). One intentional alignment note:

| Topic                                                         | Decision                                                                                                          |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `note_subtype` (older Final Phase Roadmap)                    | Not implemented — superseded by `concept_type` + `concept_domains` per Technical Plan §Concept Note Schema Models |
| Relationship `role` (e.g. `prerequisite` in roadmap examples) | Not included — Branch Plan B3 explicitly excludes it; relationship model uses `relationship_type` only            |
| `schema_version`                                              | Fixed at `1`                                                                                                      |
| Retention / mastery fields                                    | Not included (deferred)                                                                                           |
| `ParsedConceptNote`                                           | Deferred to B4 (parser output wrapper, not pure metadata)                                                         |

### Proposed model shapes (high level)

`SourceMetadata`

- Required: `type: SourceType`, `title: str` (non-empty)
- Optional nullable: `unit_type`, `unit`, `section`, `link` → `str | None = None`

`LearningEncounter`

- Required: `source`, `role`, `contribution_status`, `content_attached: bool`, `content_id: str | None` (key required, value may be null)

`ScaffoldModuleMetadata`

- Required when present: `id`, `type`, `title`, `status`
- Optional: `origin`, `focus`

`RelationshipMetadata`

- Required: `relationship_type`, `target_title`, `vault_status`
- Optional: `target_id: str | None = None`

`ConceptNoteMetadata`

- All §5.1 required fields
- Validators: non-empty `canonical_title`, `len(learning_encounters) >= 1`, unique scaffold `id`s

`ValidationIssue`

- `message: str`
- `severity: ValidationSeverity`
- `field: str | None = None` (dotted path, e.g. `learning_encounters.0.source.type`)
- `code: str | None = None` (stable machine-readable code for B6/CLI)

`ValidationResult`

- `is_valid: bool`
- `critical_errors: list[ValidationIssue]`
- `warnings: list[ValidationIssue]`
- `operation: ValidationOperation`

`WriteProposal`

- `operation: WriteOperation`
- `target_path: str`
- `before_content: str | None`
- `after_content: str`
- `warnings: list[ValidationIssue]`
- `critical_errors: list[ValidationIssue]`
- `would_create: bool`
- `would_update: bool`
- `would_overwrite: bool`
- `expected_existing_hash: str | None`

### Field recommendations (before implementation)

1. `content_id` and optional source fields — use `str | None`, not `""`, so YAML `null`/empty maps cleanly and B4 parsing can normalize empty strings to `None`.
2. `concept_domains` — require list presence (may be empty); add a lightweight `pattern=r"^[a-z][a-z0-9_]*$"` validator per domain string (Technical Plan §5.3). Invalid domains fail model construction; B6 can downgrade to warnings in parse mode if needed.
3. `concept_type` default — `ConceptType.GENERAL_CONCEPT` on `ConceptNoteMetadata` for generated notes (Technical Plan §5.2 default).
4. `note_type` / `schema_version` — use `Literal` defaults so generated models are self-validating.
5. Do not add `relationship.role` — use `relationship_type` (`depends_on`, etc.) only; avoids duplicating roadmap’s older shape.

---

### 5. Important functions / classes / modules

|Symbol|Role|
|---|---|
|`ConceptNoteMetadata`|Top-level YAML frontmatter model|
|`SourceMetadata`, `LearningEncounter`|Learning context model|
|`ScaffoldModuleMetadata`|Future scaffold container metadata|
|`RelationshipMetadata`|Graph edge metadata (shape only, no resolution)|
|`ValidationIssue`, `ValidationResult`|Structured validation output for B6/CLI|
|`WriteProposal`|Write safety primitive for B7|
|`default_studium_learning_encounter()`|Canonical Studium-origin encounter factory|
|`*Type` StrEnums|Shared vocabulary across parser, serializer, validator|

Explicitly out of scope for B3

- `validate_concept_metadata(mode=...)` — B6
- `ParsedConceptNote` — B4
- YAML serialization / key ordering — B5

---

### 6. Tests / verification steps

`tests/schemas/conftest.py`

- `valid_concept_note_data` — dict matching Technical Plan §5.1 example
- Helper to build minimal valid note with overrides

`test_concept_note.py`

- Valid full metadata constructs successfully
- Missing required fields → `ValidationError`
- `schema_version != 1` → error
- `note_type != "concept"` → error
- Empty `canonical_title` → error
- Empty `learning_encounters` → error
- Duplicate scaffold module IDs → error
- Unknown top-level field → error (`extra="forbid"`)
- `model_dump()` round-trip preserves values

`test_learning_encounter.py`

- Default Studium encounter factory is valid
- Missing `source.title` → error
- Invalid `source.type` → error
- `content_id: None` allowed

`test_scaffold_module.py`

- Valid module with optional `origin`/`focus`
- Missing required `id`/`type`/`title`/`status` → error

`test_relationship.py`

- Found / missing / unresolved targets (`target_id` optional)
- Missing `target_title` or `vault_status` → error

`test_validation.py`

- Build `ValidationResult` with critical errors → `is_valid=False`
- Warnings-only result constructible

`test_write_proposal.py`

- Construct create and update proposals with expected flags

Toolchain

- Ruff, Pyright (strict), pytest with coverage

---

### 7. Risks, edge cases, and assumptions

|Risk|Mitigation|
|---|---|
|Final Phase Roadmap still says `note_subtype`|Follow Technical Plan amendment (`concept_type` + `concept_domains`); flag doc drift, don’t implement `note_subtype`|
|Strict enums reject parsed notes with future/unknown values|Expected in B3; B6 will handle parse-time warnings before/alongside strict construction|
|Note lifecycle statuses (`status`, `review_status`, `vault_status`) lack closed enums|Use `str` now; document example values; enums can be added later without breaking YAML shape|
|Empty YAML keys vs `null`|B4 will normalize; models accept `None` for optional fields|
|`ValidationIssue` shape not fully specified in Technical Plan|Proposed minimal shape above; stable enough for B6/CLI|
|Over-validation in B3 duplicates B6|Keep B3 to schema shape + obvious cross-field rules; defer operation-mode strictness to B6|
|`extra="forbid"` may complicate gradual schema evolution|Correct for write path; B6 owns parse tolerance|

Assumptions

- Pydantic v2 already installed (B1)
- B2 vault layer is independent; no import needed in schemas
- ISO 8601 UTC datetimes in tests (e.g. `2026-06-25T00:00:00Z`)

---

### 8. Questions / decisions needed before implementation

1. Note lifecycle fields (`status`, `review_status`, `vault_status`) — keep as plain `str` (recommended), or define starter `StrEnum`s with the three example values only?
2. `concept_domains` snake_case — enforce via Pydantic pattern validator in B3 (recommended), or defer entirely to B6?
3. `ValidationIssue` fields — approve proposed shape (`message`, `severity`, optional `field`, optional `code`), or prefer a different structure?
4. Multiple `primary` learning encounters — reject in B3 `ConceptNoteMetadata` validator always (stricter), or leave to B6 write-mode only (recommended: B6 only, since parse should tolerate imperfect existing notes)?

Recommended defaults: (1) plain `str`, (2) enforce snake_case in B3, (3) approve proposed `ValidationIssue`, (4) defer multiple-primary check to B6.

---

## 6. Implementation Notes

### Enums defined

- **Concept Type:** What kind of concept being focused on, important for deriving specific scaffolds.
	- General concept, mathematical concept, algorithm, programming concept, system design concept, theory concept, process concept, tooling concept. 
- **Source Type:** What source is attached to the concept to foster the learning experience.
	- studium (Chat as a source in the future), book, video, paper, article, class, work, project, documentation, chatbot (not studium), podcast, imported note (might change as source, want to enable functionality for a user to upload handwritten notes that studium parses, writes, and reviews instead of RAGing context)
- **Encounter Role:** If the source attached is the first one, then primary. Else, additional.
	- primary, additional (might change to secondary in the future)
- **Contribution Status:** The status of the sources contribution to the development of the concept note.
	- pending, user_described, source_attached, source_analyzed, integrated, no_new_contribution_detected
- **Note Status:** Status of the note that the user is creating.
	- scaffolded, in_progress, in_review, completed, deferred, cancelled, on_hold
- **Review Status:** Status of the note during review.
	- not_submitted, in_review, approved
- **Note Vault Status:** Relation of concept note to the vault.
	- draft, accepted
- **Scaffold Module Type:** What kind of scaffold is being input into the concept note for fostering full coverage of learning, loose type with user queried agent defines modules. 
	- conceptual_explanation, worked_example, code_implementation, implementation_notes, comparison, derivation, application, misconception_debugging, custom
- **Scaffold Module Status** The status of implementation of a scaffold module within a concept note during creation.
	- scaffolded, in_progress, completed, deferred
- **Scaffold Module Origin:** How the scaffold module was proposed, most scaffolds will be initially agent recommended for retaining a concept but custom modules will have different origins (user query, source specific, agent recommended during retention is gaps, etc)
	- agent_recommended, user_requested. source_suggested, review_suggested, manual
- **Relationship Type:** Relationship one concept has with another, typically within the same concept domain.
	- depends_on, prerequisite_for, related_to, variant_of, parent_of, child_of, contrasts_with
- **Relationship Vault Status:** Primarily meant for identifying is a concept is in the vault or not, which would be used for backlog of concepts when an initial concept is searched. 
	- found, missing, unresolved
- **Validation Operation**: Used for validating actions with related metadata rules.
	- parse, create, update, write
- **Validation Severity:** Severity of errors when it comes to validating schemas.
	- critical, warning
- **Write Operation:** Type of operation when it comes to a note during CREATION
	- create_note, update_note

---

## 7. Code Understanding

See implementation plan for specific files changed (2. Files likely to be created or modified). Just basic definitions for core pydantic models, it helps to look at the code to understand the purpose of each model class:
- ConceptNoteMetadata
- Learning Encounter
- RelationshipMetadata
- ScaffoldModuleMetadata
- SourceMetadata
- ValidationIssue & ValidationResult (list of issues)
- WriteProposal

---

## 8. Tests and Verification

See implementation plan for more details about tests added (6. Tests/Verification Steps). Since pydantic models naturally include validation for invalid or empty fields, there isn't a lot of manual validation (only in concept_note.py for ensuring there is more than one learning encounter and that scaffolds aren't repeated) to ensure works as expected. Tests are pretty self explanatory, with helpers.py creating the fixture for the concept note metadata and other tests created using that fixture but changing certain values for raising errors or ensuring assertions. 

---

## 10. Final Branch Summary

Short final summary after the branch is complete:

```text
This branch added core schemas involed with keeping concept notes organized and easily accessible. This branch created the whole src/studium/schema folder as well as the tests/schemas folder. There will be future changhes to existing schemas based on needs so the schema version should increase with each new iteration. 
```