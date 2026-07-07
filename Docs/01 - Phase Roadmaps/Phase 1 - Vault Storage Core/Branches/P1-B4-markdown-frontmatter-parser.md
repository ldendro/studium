## Branch Summary

**Phase:** 1 - Vault Storage Core   
**Branch:** 4 -  Markdown Frontmatter Parser
**Status:** `merged`

---

## 1. Goal

Enable parsing markdown files into YAML Frontmatter and body content and then parsing derived YAML Frontmatter into structured note metadata based on the pydantic models implemented in the previous branch. Validate format isn't corrupted when parsing and detecting headings/sections when present. So the markdown parser will parse markdown files into YAML Frontmatter and sections and then the YAML Frontmatter parser will parse the YAML Frontmatter parser from the markdown parsers output into a parsed metadata dictionary with parse errors if thrown and pydantic model validation results implemented in the previous branch. 

---

## 2. Branch Context

This section should be written before Cursor creates the detailed implementation plan.
### Main System Area

This branch primarily affects:

- Markdown parsing
- YAML Frontmatter Parsing. 

### Branch Dependencies

This branch depends on P1-B3-concept-note-schemas for abstracting concept note metadata based on a notes YAML Frontmatter, which is structured via the pydantic models introduced in the previous branch. 

### Risks / Things to Watch

Ensure markdown files are properly parsed, where the functionality introduced doesn't miss key information from a markdown file when parsing into YAML Frontmatter and body content. 

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.
### YAML Frontmatter
- A block of metadata at the very top of a markdown files, enclosed by triple dashes (---)
- Uses key-value pairs (note fields and values) to store information. 

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

Branch: 4 - Markdown Frontmatter Parser

Branch goal:
To define both a markdown parser which seperates YAML frontmatter and markdown body content (by cannonical sections mentioned in the final phase roadmap for phase 1) and a YAML Frontmatter parse that parses YAML Frontmatter into the pydantic models defined in src/studium/schema. Validation is necessary for both of these parses as well to ensure they enable the expected functionality across a wide array of test cases. 

Expected outcome:
Parsers work as expected and set up eventual serialization in later branches. 

Relevant context:
Relevant context for implementation include the following files: `4 - Branch Plan`, '3 - Technical Plan`, and `2 - Final Phase Roadmap`.

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

Build a read-only, two-stage parser under `src/studium/parsing/` that bridges raw Markdown files and the B3 Pydantic schemas without mutating content.

Stage A — Markdown split + section detection

- `split_frontmatter(raw_markdown)` separates the opening `---` YAML block from the body using a line-based scanner (not a Markdown library), preserving the body byte-for-byte.
- `parse_markdown_sections(body)` scans for ATX `#` / `##` headings, ignoring headings inside fenced code blocks, and flags which canonical Phase 1 sections are present.

Stage B — YAML → structured metadata

- `parse_yaml_frontmatter(yaml_text)` uses PyYAML (`safe_load`) to produce a raw `dict[str, Any]`, surfacing malformed YAML as a critical parse error.
- Known keys are validated into `ConceptNoteMetadata` via Pydantic. Because B3 models use `extra="forbid"`, unknown top-level keys are stripped before validation and returned separately for B6 warning generation.
- Optional nullable fields (`source.unit_type`, `content_id`, etc.) normalize `""` → `None` before Pydantic construction (per B3 recommendation).

High-level composition

- `parse_concept_note(raw_markdown)` calls the lower-level functions in order and returns a single `ParsedConceptNote` wrapper (deferred from B3, lives in `parsing/` not `schemas/`).
- B4 performs syntactic + structural validation (invalid YAML, missing frontmatter, Pydantic failures, section detection). Full operation-mode validation (`parse` vs `write` strictness, unknown-field severity, multiple-primary checks) stays in B6.

Design principles:

- No file writes, no body normalization, no auto-repair of missing sections.
- Lower-level functions are independently testable; high-level parser is a thin composer.
- Parse errors use `ValidationIssue` from B3 for consistency with B6/CLI, but B4 does not implement `validate_concept_metadata(mode=...)`.

---

### 2. Files likely to be created or modified

New

|File|Contents|
|---|---|
|`src/studium/parsing/errors.py`|`ParseError` exception hierarchy (`FrontmatterError`, `YamlParseError`, etc.)|
|`src/studium/parsing/frontmatter.py`|`split_frontmatter()`, `FrontmatterSplit` result dataclass|
|`src/studium/parsing/yaml_frontmatter.py`|`parse_yaml_frontmatter()`, empty-string normalization, unknown-field extraction|
|`src/studium/parsing/sections.py`|`CANONICAL_SECTION_TITLES`, `MarkdownHeading`, `ParsedMarkdownSections`, `parse_markdown_sections()`|
|`src/studium/parsing/models.py`|`ParsedConceptNote`, intermediate result types|
|`src/studium/parsing/concept_note.py`|`parse_concept_note()`, pydantic error → `ValidationIssue` conversion helper|
|`tests/parsing/conftest.py`|Shared fixtures (valid note string, minimal note builder)|
|`tests/parsing/helpers.py`|Fixture builders (mirrors `tests/schemas/helpers.py` pattern)|
|`tests/parsing/test_frontmatter.py`|Frontmatter split cases|
|`tests/parsing/test_yaml_frontmatter.py`|YAML parse + normalization cases|
|`tests/parsing/test_sections.py`|Heading/section detection cases|
|`tests/parsing/test_concept_note.py`|End-to-end parse flow|
|`tests/fixtures/parsing/*.md`|Committed fixture notes (valid, invalid YAML, missing section, etc.)|

Modified

|File|Change|
|---|---|
|`src/studium/parsing/__init__.py`|Public exports|
|`pyproject.toml`|Add `pyyaml` runtime dependency|

Not changed

- `schemas/` (B3 models are consumed, not modified)
- `validation/` (B6)
- `serialization/` (B5)
- `vault/` (B2 — parser accepts raw strings; vault integration optional later)
- `cli/` (B8)

---

### 3. Step-by-step implementation sequence

1. Add `pyyaml` dependency to `pyproject.toml`.
    
2. Define canonical section constants in `sections.py`:
    
    Concept Overview
    
    Prerequisites
    
    Module Index
    
    Scaffold Modules
    
    Related Concepts
    
    Open Questions / Gaps
    
    Plus helper to compute `present` / `missing` sets from detected `##` headings.
    
3. Implement `split_frontmatter()` in `frontmatter.py`:
    
    - Require file to start with `---` (allow UTF-8 BOM).
    - Find closing `---` on its own line.
    - Return `FrontmatterSplit(frontmatter_text, body, raw_markdown)` with body as exact substring.
    - Raise `FrontmatterError` for missing/malformed delimiters.
4. Implement `parse_yaml_frontmatter()` in `yaml_frontmatter.py`:
    
    - `yaml.safe_load` → `dict` (reject non-dict root).
    - Detect unknown top-level keys vs `ConceptNoteMetadata.model_fields`.
    - Recursively normalize `""` → `None` on known optional nullable paths (`source.*`, `content_id`, `target_id`, relationship optional fields).
    - Return `YamlParseResult(raw_dict, known_dict, unknown_fields, yaml_error)`.
5. Implement `parse_markdown_sections()` in `sections.py`:
    
    - Line-scan body; track fenced code blocks (``` and ~~~).
    - Extract ATX `#` (level 1) and `##` (level 2) headings with line number + raw line text.
    - Map level-2 titles to canonical section presence.
    - Do not extract section _content_ yet — headings only (content slicing is B5/B6 concern if needed).
6. Define `ParsedConceptNote` in `models.py`:
    
    class ParsedConceptNote(BaseModel):
    
    raw_markdown: str
    
    frontmatter_text: str
    
    body: str
    
    raw_metadata: dict[str, Any]
    
    metadata: ConceptNoteMetadata | None
    
    unknown_metadata_fields: list[str]
    
    sections: ParsedMarkdownSections
    
    critical_errors: list[ValidationIssue]
    
    warnings: list[ValidationIssue]
    
7. Implement `parse_concept_note()` in `concept_note.py`:
    
    - Call `split_frontmatter` → on failure, return `ParsedConceptNote` with critical error, empty body sections.
    - Call `parse_yaml_frontmatter` → invalid YAML = critical error.
    - Attempt `ConceptNoteMetadata.model_validate(known_dict)` → Pydantic `ValidationError` converted to `ValidationIssue` list (critical).
    - Unknown fields → `warnings` (not critical on parse).
    - Call `parse_markdown_sections(body)`.
    - Missing canonical sections → `warnings` only (per Technical Plan §7).
    - Return composed `ParsedConceptNote`.
8. Wire exports in `parsing/__init__.py`.
    
9. Add fixture `.md` files under `tests/fixtures/parsing/` aligned with Technical Plan §10 fixture list (start with 4–6 core fixtures; expand as needed).
    
10. Add tests (see §6).
    
11. Verify: `uv run ruff check .`, `uv run pyright`, `uv run pytest`.
    

---

### 4. Data model or schema changes

|Topic|Decision|
|---|---|
|`ParsedConceptNote`|New in `parsing/models.py` (deferred from B3; parser output wrapper, not pure metadata)|
|B3 schema models|No changes — consume `ConceptNoteMetadata`, `ValidationIssue`, enums as-is|
|`ValidationResult`|Not produced by B4 — B4 populates `critical_errors` / `warnings` on `ParsedConceptNote`; B6 wraps into `ValidationResult(operation=PARSE)`|
|Canonical sections|Parser constant, not a schema enum — list may evolve; B5 serializer will share the same constant (extract to shared module in B5 if duplication becomes an issue)|

Proposed `ParsedMarkdownSections` shape:

class MarkdownHeading(BaseModel):

level: Literal[1, 2]

title: str # stripped heading text

line_number: int # 1-based

raw_line: str # original line preserved

class ParsedMarkdownSections(BaseModel):

headings: list[MarkdownHeading]

h1_title: str | None

canonical_present: list[str]

canonical_missing: list[str]

---

### 5. Important functions / classes / modules

|Symbol|Role|
|---|---|
|`split_frontmatter(raw_markdown)`|Low-level: delimiter split, body preservation|
|`parse_yaml_frontmatter(yaml_text)`|Low-level: YAML → dict, unknown-field detection, normalization|
|`parse_markdown_sections(body)`|Low-level: heading + canonical section detection|
|`parse_concept_note(raw_markdown)`|High-level: composes all stages → `ParsedConceptNote`|
|`ParsedConceptNote`|Primary output for B6, B8 CLI, eventual vault read flow|
|`CANONICAL_SECTION_TITLES`|Shared vocabulary with B5 serializer|
|`_pydantic_errors_to_issues(err)`|Internal: `ValidationError` → `list[ValidationIssue]`|
|`_normalize_empty_strings(data)`|Internal: `""` → `None` on optional nullable fields|

Explicitly out of scope for B4

- `validate_concept_metadata(mode=...)` — B6
- `serialize_concept_note(...)` — B5
- Relationship Markdown projection — B5
- Vault `read_markdown` → parse convenience wrapper — optional thin helper, not required
- Scaffold module body section matching — B6 warning only if metadata lists module but `## Scaffold Modules` missing content

---

### 6. Tests / verification steps

`test_frontmatter.py`

- Valid `---` / `---` split with multiline YAML and body
- Body preserved exactly (trailing whitespace, blank lines, CRLF)
- Missing opening/closing delimiter → `FrontmatterError` / critical issue
- No frontmatter at file start → error
- YAML delimiter inside code fence in body does not interfere (body-only content)

`test_yaml_frontmatter.py`

- Valid YAML → dict
- Invalid YAML → error with message
- Non-dict root (scalar, list) → error
- Unknown top-level keys detected and stripped
- `""` normalized to `None` for optional source/relationship fields
- Valid dict validates into `ConceptNoteMetadata`

`test_sections.py`

- Detects `# Title` and all six canonical `##` sections
- Headings inside ` ``` ` fences ignored
- Missing sections appear in `canonical_missing`
- Extra non-canonical `##` headings allowed (e.g. user-added sections)
- `###` headings ignored for canonical detection (level 2 only)

`test_concept_note.py`

- Full valid note (Technical Plan §5.1 example) → `metadata` populated, no critical errors
- Invalid YAML fixture → critical error, `metadata is None`
- Missing required metadata field → critical error
- Unknown metadata field → warning, metadata still validates if known fields are valid
- Missing `## Module Index` → warning, not critical
- Body round-trip: `body` equals original body substring exactly
- High-level parser calls lower-level functions (no duplicated split/YAML logic)

Fixture files (committed under `tests/fixtures/parsing/`):

- `valid_concept_note.md`
- `invalid_yaml_note.md`
- `missing_canonical_section.md`
- `unknown_metadata_field.md`
- `external_source_concept.md` (optional for B4, useful for B6 handoff)

Toolchain: Ruff, Pyright (strict), pytest with coverage.

---

### 7. Risks, edge cases, and assumptions

|Risk|Mitigation|
|---|---|
|Markdown library normalizes/alters body|Use custom line scanner; never pass full file through a MD processor|
|`extra="forbid"` rejects unknown fields on parse|Strip unknown keys before Pydantic; track separately as warnings|
|Frontmatter `---` inside body confuses split|Only parse frontmatter block at file start (Obsidian convention)|
|Code fences contain `# headings`|Fence-aware section scanner|
|CRLF vs LF|Operate on string as read; preserve original body substring|
|YAML `null` vs empty string inconsistency|Normalize `""` → `None` on optional fields before Pydantic|
|B4 duplicates B6 validation|B4 = syntactic/structural only; B6 = operation-mode orchestration|
|Canonical section list may change|Centralize constant; B5 will need same list|

Assumptions

- B3 schemas are stable and complete for Phase 1 metadata
- Concept notes always have YAML frontmatter (no frontmatter = critical error)
- ATX headings only (`#` / `##`); setext headings not supported in Phase 1
- Files are UTF-8 (consistent with B2 vault reader)
- `pyyaml` is acceptable as the YAML library (Technical Plan open question)

---

### 8. Questions / decisions needed before implementation

1. YAML library — recommend PyYAML (`safe_load`). Alternative: `ruamel.yaml` (better round-trip, heavier). Recommendation: PyYAML for B4; B5 can revisit if comment preservation matters.
    
2. Missing frontmatter — treat as critical error (concept notes require frontmatter), or allow body-only parse with empty metadata? Recommendation: critical error.
    
3. Unknown metadata fields on parse — strip + warn (recommended, aligns with parse-permissive philosophy), or fail strict Pydantic and surface as critical? Recommendation: strip + warn.
    
4. `parse_concept_note` return shape — return `ParsedConceptNote` only (recommended), or also a fully formed `ValidationResult`? Recommendation: `ParsedConceptNote` with embedded issues; B6 builds `ValidationResult`.
    
5. H1 title vs `canonical_title` — ignore mismatch in B4, or emit warning when `# heading` ≠ `metadata.canonical_title`? Recommendation: defer to B6 (semantic validation).
    
6. Fixture strategy — commit `.md` files under `tests/fixtures/parsing/` (recommended for golden-style tests) vs inline strings only? Recommendation: both — fixtures for realistic notes, inline strings for edge cases.
    
7. Empty frontmatter block (`---\n---`) — critical error or valid empty dict (which will fail Pydantic)? Recommendation: valid empty dict → Pydantic critical errors for missing required fields (distinguishes from invalid YAML).
    
8. Vault convenience API — add `parse_concept_note_from_vault(vault, path)` in B4, or keep parser string-only until B8 CLI? Recommendation: string-only in B4; one-liner composition with `vault.read_markdown()` is trivial for callers.
---

## 6. Implementation Notes

### Canonical Section Titles 
- Settled on the following canonical section titles that would populate for every concept note, defined in `src/studium/parsing/sections.py`:
	- **Concept Overview**
	- **Prerequisites**
	- **Module Index**
	- **Scaffold Modules**
	- **Related Concepts**
	- **Open Questions/Gaps**

**High Level Description of parsing a concept note**
1. Call parse concept note function with raw markdown text.
2. Calls split Frontmatter function to split the raw markdown into Frontmatter YAML and markdown sections.
	1. Returns failed parse function return (ParsedNoteConcept class) with corresponding null and error values if error thrown. 
3. Call parse Yaml Frontmatter function on the Frontmatter text to get the concept note metadata, validated by the pydantic models defined for said metadata in `src/studium/schemas`.
	1. Returns failed parse function is YAML parsing throws unexpected error. 
4. Append validation issue defined in `src/studium/schemas/validation.py` to warnings list for all unknown fields found. 
5. Append validation issues from parsed metadata issues to critical errors list. 
6. Parse markdown body content into sections with parse markdown sections function
7. For every missing section in parsed sections, append validation issue of the missing section to warnings. 
8. Return ParsedConceptNote class with 
	1. raw markdown 
	2. frontmatter text
	3. body
	4. raw metadata
	5. metadata
	6. unknown metadata fields
	7. sections (parsed body content)
	8. critical errors list
	9. warnings list 
---

## 7. Code Understanding

See cursor implementation plan for code understanding. Code is fairly straight forward (everything implemented within parsing). Start at `concept_note.py` and branch out to each function call for understanding the flow of parsing a concept note. 

---

## 8. Tests and Verification

### Fixtures
- Defined 5 fixtures (markdown files) for golden path tests including:
	- Empty Frontmatter - Critical error thrown 
	- Invalid Yaml Note - Syntax error within YAMl Frontmatter
	- Missing canonical section - Warning thrown 
	- Unknown metadata field - Warning thrown and unknown field in appended to unknown field list
	- Valid concept note - Matches all expected metadata fields and canonical sections are present

### Tests
#### `test_frontmatter.py`

Tests `split_frontmatter()` — separating YAML frontmatter from the Markdown body.

|Test|Purpose|
|---|---|
|`test_split_valid_frontmatter_and_body`|Verifies a valid note splits into YAML text and body, and `raw_markdown` is unchanged|
|`test_body_preserved_exactly_with_trailing_whitespace`|Ensures body substring preservation includes trailing whitespace|
|`test_split_supports_utf8_bom`|Confirms files with a UTF-8 BOM still split correctly|
|`test_missing_frontmatter_raises`|Files without leading `---` raise `FrontmatterError`|
|`test_missing_closing_delimiter_raises`|Unclosed frontmatter block raises `FrontmatterError`|
|`test_empty_frontmatter_block_splits`|`---\n---\n` yields empty frontmatter text and a non-empty body|

Module under test: `studium.parsing.frontmatter.split_frontmatter`

---

#### `test_yaml_frontmatter.py`

Tests `parse_yaml_frontmatter()` — YAML → dict → `ConceptNoteMetadata`.

|Test|Purpose|
|---|---|
|`test_parse_valid_yaml_metadata`|Valid YAML produces a populated `ConceptNoteMetadata` with no issues|
|`test_invalid_yaml_raises`|Malformed YAML raises `YamlParseError`|
|`test_non_mapping_yaml_raises`|YAML that isn't a mapping (e.g. a scalar) raises `YamlParseError`|
|`test_empty_frontmatter_parses_to_empty_dict`|Empty YAML text → `{}`, no metadata, critical `metadata_issues`|
|`test_unknown_fields_stripped_and_reported`|Unknown keys are stripped from known metadata and listed in `unknown_fields`|
|`test_empty_strings_normalized_to_none`|`""` on optional nullable fields (`content_id`, source fields) becomes `None`|
|`test_metadata_issues_are_critical`|Incomplete metadata yields critical `metadata_issues`, not warnings|

Module under test: `studium.parsing.yaml_frontmatter.parse_yaml_frontmatter`

---

#### `test_sections.py`

Tests `parse_markdown_sections()` — ATX heading detection and canonical section presence.

|Test|Purpose|
|---|---|
|`test_detects_h1_and_canonical_h2_sections`|Detects `#` title and all six canonical `##` sections when present|
|`test_missing_canonical_sections_reported`|Missing sections appear in `canonical_missing`|
|`test_headings_inside_code_fence_ignored`|Headings inside fenced code blocks are not counted|
|`test_h3_headings_not_counted_as_canonical`|`###` headings do not satisfy canonical section requirements|
|`test_extra_non_canonical_h2_allowed`|Non-canonical `##` headings (e.g. `User Notes`) are detected but don't cause errors|

Module under test: `studium.parsing.markdown_sections.parse_markdown_sections`

---

#### `test_concept_note.py`

Tests `parse_concept_note()` — end-to-end composition of split, YAML parse, metadata validation, and section detection.

|Test|Purpose|
|---|---|
|`test_parse_valid_fixture_note`|Full valid fixture parses to metadata with no critical errors|
|`test_body_preserved_exactly`|High-level parser body matches low-level `split_frontmatter` body|
|`test_invalid_yaml_fixture_has_critical_error`|Invalid YAML fixture → `invalid_yaml` critical error, no metadata|
|`test_missing_frontmatter_is_critical_error`|Body-only input → `missing_frontmatter` critical error|
|`test_empty_frontmatter_yields_metadata_critical_errors`|Empty frontmatter → Pydantic critical errors for missing required fields|
|`test_unknown_metadata_field_warning`|Unknown YAML keys → `unknown_field` warning; metadata still validates|
|`test_missing_canonical_section_warning`|Missing `## Module Index` → `missing_canonical_section` warning|
|`test_inline_markdown_round_trip_metadata`|Programmatically built note parses cleanly with all canonical sections|

---


## 9. Final Branch Summary

Short final summary after the branch is complete:

```text
This branch added parsing functionality for turning raw markdown text into concept note metadata and canonical sections. This branch created the whole src/studium/parsing folder where parsing begins in `concept_note.py` with the `parse_concept_note()` function call passing in raw markdown text. The output of this function isa parsed note object following the ParsedConceptNote class defined in models.py. 
```