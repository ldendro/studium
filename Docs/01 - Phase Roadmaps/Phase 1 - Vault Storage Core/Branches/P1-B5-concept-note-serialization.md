## Branch Summary

**Phase:** 1 - Vault Storage Core  
**Branch:** 5 - Concept Note Serialization
**Status:** `in_progress`

---

## 1. Goal

From the components created from parsing markdown files (concept metadata and body content divided into sections), generate full markdown concept notes. Essentially the reverse of the previous branch, essential for viewing a markdown file within the test vault. Goals for this branch include concept ID generation, the serialization of new concept notes into markdown, and ensuring generated YAML and markdown follows canonical order. 

---

## 2. Branch Context

### Main System Area

This branch primarily affects:

-  Markdown serialization
-  Concept ID generation
### Branch Dependencies

P1-B4-markdown-frontmatter-parsing to ensure parsed markdown notes can be serialized to return to format before parsing. 

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

Branch: 5 - Concept Note Serialization

Branch goal:
To serialize concept metadata and body content (canonical sections) into full markdown notes with unique concept id's. 

Expected outcome:
Serialize parsed concept notes to return them to the state they were before parsing, with respective unique ID's. Also projecting relationships into readable Markdown sections as descibed in the techincal plan. 

Relevant context:
See `3 - Technical Plan`, `4 - Branch Plan`, and `2 - Final Phase Roadmap`

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

Implement the reverse of B4: turn `ConceptNoteMetadata` + Markdown body into a full Obsidian-compatible `.md` file, with stable concept ID generation and canonical ordering for new/generated notes.

Design principles:

1. Two serialization paths
    
    - Preserve body — `serialize_concept_note(metadata, body)` joins canonical YAML frontmatter with an existing body unchanged. Used for round-trip (`parse` → `serialize`) and simple updates.
    - Generate body — `build_canonical_concept_body(metadata)` emits `# <canonical_title>` plus empty canonical `##` sections and relationship projections into `## Prerequisites` and `## Related Concepts`. Used for new note creation.
2. YAML is authoritative for relationships — Markdown bullets are display-only projections; no bidirectional sync in B5.
    
3. Canonical ordering on generate — New/generated output uses fixed YAML key order (Technical Plan §5.1) and section order from `CANONICAL_SECTION_TITLES` (already in `parsing/sections.py`; serialization imports it to stay DRY).
    
4. Concept ID generation in B5 — Finalize `slugify_title()` + `generate_concept_id()` using `concept_<slug>_<short_hash>` (Final Phase Roadmap §5.3). Hash is derived from canonical title (deterministic for new notes); assigned `id` on existing metadata is never overwritten by serialize.
    
5. PyYAML for dump — Reuse existing `pyyaml` dependency. Build an `OrderedDict`/explicit key list for canonical field order; normalize `None` optional fields to YAML null/empty style matching the Technical Plan example (`unit_type:` with no value).
    
6. Round-trip verification — Golden tests: `parse_concept_note(fixture)` → `serialize_concept_note(metadata, body)` → metadata-equivalent re-parse. Full byte-identical round-trip is not required if YAML key order/null formatting differs from hand-authored fixtures.
    

Explicitly out of scope for B5: `WriteProposal` / vault writes (B7), CLI `create-concept` (B8), operation-mode validation orchestration (B6), scaffold module _content_ generation, graph resolution.

---

### 2. Files likely to be created or modified

New

|File|Contents|
|---|---|
|`src/studium/serialization/concept_id.py`|`slugify_title()`, `generate_concept_id()`|
|`src/studium/serialization/metadata_yaml.py`|`CANONICAL_YAML_KEYS`, `metadata_to_ordered_dict()`, `serialize_metadata_to_yaml()`|
|`src/studium/serialization/body.py`|`build_canonical_concept_body()`, optional scaffold module index lines|
|`src/studium/serialization/relationships.py`|`project_relationships()`, section grouping + wikilink bullets|
|`src/studium/serialization/concept_note.py`|`serialize_concept_note()`, `create_concept_note_markdown()`|
|`tests/serialization/conftest.py`|Shared metadata fixtures|
|`tests/serialization/helpers.py`|Builders for metadata/relationships|
|`tests/serialization/test_concept_id.py`|Slug + ID generation|
|`tests/serialization/test_metadata_yaml.py`|YAML order, nulls, datetime format|
|`tests/serialization/test_relationships.py`|Projection grouping + bullet format|
|`tests/serialization/test_body.py`|Canonical section structure|
|`tests/serialization/test_concept_note.py`|Full serialize + round-trip|
|`tests/fixtures/serialization/expected_*.md`|Golden expected output for generated notes|

Modified

|File|Change|
|---|---|
|`src/studium/serialization/__init__.py`|Public exports|
|`tests/fixtures/parsing/`|Add `concept_with_relationships.md` (optional, for projection tests)|

Not changed

- `schemas/` (consume B3 models; no schema changes expected)
- `parsing/` (consume `CANONICAL_SECTION_TITLES`, `parse_concept_note` for round-trip tests)
- `validation/`, `writes/`, `cli/`, `vault/`

---

### 3. Step-by-step implementation sequence

1. Concept ID module (`concept_id.py`)
    
    - `slugify_title(title: str) -> str` — lowercase, trim, replace whitespace/punctuation runs with `_`, collapse repeats, strip leading/trailing `_`, ASCII-fold or strip unsupported chars (decision in §8).
    - `generate_concept_id(canonical_title: str, *, salt: str | None = None) -> str` — `concept_{slug}_{hash6}` where hash6 is first 6 hex chars of SHA-256 over a stable input string.
2. YAML serialization (`metadata_yaml.py`)
    
    - Define `CANONICAL_YAML_KEYS` matching Technical Plan §5.1 field order.
    - `metadata_to_ordered_dict(metadata: ConceptNoteMetadata) -> dict` — `model_dump(mode="json")` then reorder; nested structures preserve logical field order (source fields, encounter fields).
    - `serialize_metadata_to_yaml(metadata) -> str` — `yaml.dump(..., default_flow_style=False, sort_keys=False, allow_unicode=True)` with custom representer for `None` → empty/null per approved style.
    - Serialize datetimes as `2026-06-25T00:00:00Z`.
3. Relationship projection (`relationships.py`)
    
    - Map `RelationshipType` → section:
        - Prerequisites: `depends_on` (recommended default)
        - Related Concepts: `prerequisite_for`, `related_to`, `variant_of`, `parent_of`, `child_of`, `contrasts_with`
    - Emit bullets: `- [[{target_title}]]` (Obsidian wikilink; vault_status does not alter display per Create roadmap guidance).
    - `project_relationships(relationships) -> tuple[list[str], list[str]]` returning prerequisite lines and related lines.
4. Canonical body builder (`body.py`)
    
    - `build_canonical_concept_body(metadata, *, project_relationships: bool = True) -> str`
    - Emit sections in `CANONICAL_SECTION_TITLES` order with `# {canonical_title}` H1.
    - Inject relationship bullets under Prerequisites / Related Concepts when projecting.
    - Optional: list scaffold module `title` (or `id`) as bullets under `## Module Index` when `scaffold_modules` non-empty (metadata container only; no content sections).
5. Top-level serializer (`concept_note.py`)
    
    - `serialize_concept_note(metadata, body: str) -> str` — `---\n{yaml}\n---\n{body}`; body passed through unchanged (no strip/normalize).
    - `create_concept_note_markdown(canonical_title: str, **overrides) -> str` — builds default metadata (ID, timestamps, `default_studium_learning_encounter()`, lifecycle defaults), canonical body, then serializes.
    - `build_concept_note_metadata(canonical_title, **overrides) -> ConceptNoteMetadata` — factory for new notes (reuses B3 defaults).
6. Wire exports in `serialization/__init__.py`.
    
7. Tests — unit tests per module + golden files + round-trip integration (see §6).
    
8. Verify — `uv run ruff check .`, `uv run pyright`, `uv run pytest`.
    

---

### 4. Data model or schema changes

|Topic|Decision|
|---|---|
|B3 schemas|No changes — serialize from existing `ConceptNoteMetadata`, `RelationshipMetadata`, etc.|
|New models|None required — pure functions; optional small `SerializedConceptNote` dataclass only if it simplifies tests (not recommended)|
|Shared constants|Import `CANONICAL_SECTION_TITLES` from `studium.parsing.sections` (or extract to `studium/canonical.py` if you prefer zero cross-module parsing→serialization dependency; not required for B5)|
|`ParsedConceptNote`|Unchanged — round-trip uses `parsed.metadata` + `parsed.body`|

Canonical YAML key order (proposed):

id, schema_version, note_type, concept_type, concept_domains,

canonical_title, aliases, status, review_status, vault_status,

learning_encounters, scaffold_modules, relationships,

created_at, updated_at

---

### 5. Important functions / classes / modules

|Symbol|Role|
|---|---|
|`slugify_title(title)`|Normalized slug segment for concept IDs|
|`generate_concept_id(canonical_title)`|Stable `concept_<slug>_<hash>` IDs for new notes|
|`serialize_metadata_to_yaml(metadata)`|Canonical-order YAML text (no delimiters)|
|`build_canonical_concept_body(metadata)`|Empty canonical sections + relationship projection|
|`project_relationships(relationships)`|YAML relationships → Markdown bullet lines|
|`serialize_concept_note(metadata, body)`|Full Markdown file string|
|`build_concept_note_metadata(...)`|Construct valid metadata for a new note|
|`create_concept_note_markdown(title, ...)`|End-to-end new note generation|

Explicitly deferred

|Symbol|Branch|
|---|---|
|`validate_concept_metadata(mode=...)`|B6|
|`build_create_note_proposal(...)`|B7|
|`studium create-concept` CLI|B8|
|Body patching for partial updates|B7+|

---

### 6. Tests / verification steps

`test_concept_id.py`

- Slugify: `"Stochastic Gradient Descent"` → `stochastic_gradient_descent`
- ID format matches `concept_<slug>_<6 hex>`
- Same title → same ID (deterministic)
- Punctuation/unicode edge cases

`test_metadata_yaml.py`

- Keys appear in canonical order
- Datetimes use `Z` suffix
- Optional null source fields render like Technical Plan example
- `learning_encounters`, `scaffold_modules`, `relationships` lists serialize correctly

`test_relationships.py`

- `depends_on` → Prerequisites bullets
- `related_to`, `contrasts_with`, etc. → Related Concepts
- `vault_status: missing` still renders `[[Target Title]]` (no "missing" label)
- Multiple relationships preserve stable order (YAML list order)

`test_body.py`

- All six canonical `##` sections present in order
- H1 matches `canonical_title`
- Relationship bullets appear only in correct sections when projecting

`test_concept_note.py`

- `create_concept_note_markdown("Test Concept")` produces parseable output
- `serialize_concept_note` + `parse_concept_note` round-trip on `valid_concept_note.md` — metadata equal after re-parse
- Body bytes preserved in preserve-mode serialize
- Golden file: generated studium-origin note matches `tests/fixtures/serialization/expected_studium_origin.md`

Round-trip strategy

original → parse_concept_note → serialize_concept_note(metadata, body) → parse_concept_note

Assert: `metadata` equal, `body` equal, no new critical errors. YAML text may differ in key order from hand-authored fixture when using generate-mode; preserve-mode round-trip should be closest to original.

---

### 7. Risks, edge cases, and assumptions

|Risk|Mitigation|
|---|---|
|YAML dump reorders or reformats nulls|Explicit key list + custom null representer; golden tests|
|Round-trip not byte-identical|Document semantic round-trip as success criteria; preserve body verbatim|
|Relationship projection vs preserved body conflict|Only project when generating body; preserve-mode leaves body unchanged|
|Concept ID collisions|6-char hash + slug; document collision handling deferred to Phase 2|
|`prerequisite_for` section placement ambiguous|Fixed mapping table in `relationships.py`; test explicitly|
|Parsing import from serialization|One-way dep: serialization may import `parsing.sections` constants only|
|Scaffold module body content|Phase 1 emits containers/metadata index only — no generated learning content|

Assumptions

- B3 schemas and B4 parser are stable
- PyYAML is acceptable for dump (same as parse)
- New notes use UTC `created_at` / `updated_at` at generation time
- `default_studium_learning_encounter()` from B3 is the default for created notes
- Wikilink format `[[Target Title]]` is the Phase 1 projection standard

---

### 8. Questions / decisions needed before implementation

1. Concept ID hash algorithm — recommend SHA-256 of `canonical_title` (normalized), take first 6 hex chars → matches example `a1b2c3`. Alternative: UUID4 (non-deterministic). Recommend: deterministic SHA-256/6.
    
2. Slug rules — recommend: lowercase ASCII, non-alphanumeric → `_`, collapse `_`, max length cap (e.g. 80 chars). How to handle unicode titles (NFKD fold vs strip)? Recommend: ASCII fold + strip non-`[a-z0-9_]`.
    
3. Relationship → section mapping — recommend:
    
    - Prerequisites: `depends_on`
    - Related Concepts: all other types  
        Should `prerequisite_for` appear in Prerequisites (inverse) or Related Concepts? Recommend: Related Concepts (it's not a dependency _of_ this concept).
4. Bullet format — recommend `- [[{target_title}]]` only (Create roadmap style), not `- depends_on: [[...]]` (Initial roadmap style). Recommend: wikilink-only bullets.
    
5. Round-trip strictness — byte-identical file vs metadata+body semantic equality? Recommend: semantic equality for metadata+body; canonical YAML order acceptable on generate path.
    
6. YAML null style — `field:` (empty) vs `field: null` vs `field: ~`? Recommend: match `valid_concept_note.md` fixture — key with no value for optional nulls.
    
7. Scaffold module Module Index — list module titles as bullets when metadata present? Recommend: yes, title bullets only in B5; empty section if no modules.
    
8. `create_concept_note_markdown` in B5 vs B8 only — Branch plan includes basic generation in B5. Recommend: implement factory + serialize in B5; CLI wires it in B8.
    
9. Shared constants location — keep `CANONICAL_SECTION_TITLES` in `parsing/sections.py` and import from serialization? Recommend: yes for minimal diff; extract shared module later if needed.

---
See implementation plan for details, code implementation for this branch is fairly straight forward. 