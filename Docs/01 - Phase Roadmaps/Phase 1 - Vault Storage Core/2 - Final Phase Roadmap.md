# Phase 1: Vault Storage Core

## 1. Purpose

Phase 1 establishes the durable storage foundation for Studium.

This phase gives Studium the ability to create, read, parse, validate, and safely write Obsidian-compatible Markdown concept notes inside a controlled test vault. It does not build the Create UI, Search graph, Agent Review, Backlog, Retention, or Mastery systems yet. Instead, it defines the stable note structure those later phases depend on.

This phase answers:

> How does Studium store concept knowledge in a durable, portable, human-readable, and machine-parseable way?

---

## 2. Phase Outcome

By the end of this phase, Studium should be able to:

- read Markdown concept notes from a test vault
    
- parse YAML frontmatter and Markdown body sections
    
- create new Studium-compatible concept notes
    
- assign stable concept IDs
    
- store learning encounter metadata without using a separate `primary_source` field
    
- store scaffold module metadata without generating meaningful scaffold content
    
- store relationship metadata in YAML and readable Markdown sections
    
- validate concept notes with critical errors and warnings
    
- generate safe write proposals before committing file changes
    
- write new or updated concept notes to a test vault without corrupting Markdown content
    

The outcome is a reliable storage layer, not an intelligent learning system yet.

---

## 3. Why This Phase Comes Now

This phase comes first because every later part of Studium depends on durable concept-note storage.

Create needs a note format to generate into.  
Search needs parseable notes to index.  
Source Content Intelligence needs a place to attach learning encounters.  
Agent Review needs stable module IDs and reviewable sections.  
Backlog needs concepts and relationships to reference.  
Retention and Mastery need accepted concept notes as their eventual learning targets.

Studium cannot reason over concepts until it can reliably store and parse them.

---

## 4. Core Principles for This Phase

- Concept notes are the primary durable knowledge object.
    
- Studium is concept-driven; no other first-class note type is needed in Phase 1.
    
- Preserve Obsidian-compatible Markdown.
    
- Keep Markdown human-readable and YAML machine-readable.
    
- Treat YAML as the source of truth for structured metadata.
    
- Do not introduce intelligence before the storage model is stable.
    
- Define containers for future scaffold modules without deciding which modules a concept needs.
    
- Use `learning_encounters` as the only source/encounter model.
    
- Do not use a separate `primary_source` field.
    
- Use `studium` as the default learning encounter when no external source is attached.
    
- Prefer safe write proposals over silent file mutation.
    
- Validate clearly, but do not reject notes aggressively unless the issue is structurally dangerous.
    
- Keep Phase 1 filesystem/Markdown-first; do not introduce SQLite yet.
    

---

## 5. Core Features / Capabilities Introduced

### 5.1 Test Vault Storage

Phase 1 should operate against a test vault, not the user’s real Obsidian vault.

The test vault provides a safe development environment where Studium can create, parse, validate, and update Markdown files without risking real learning notes.

This feature should support:

- a configurable test vault directory
    
- reading Markdown files from that directory
    
- writing generated concept notes into that directory
    
- using fixture notes for automated tests
    
- avoiding accidental writes outside the configured vault root
    

Important behavior:

- all file operations should be scoped to the configured test vault
    
- generated notes should be Obsidian-compatible Markdown files
    
- unsafe paths or path traversal attempts should be blocked
    
- the storage layer should not assume a real Obsidian vault is connected yet
    

Important constraints:

- no real user vault integration in Phase 1
    
- no Obsidian plugin integration
    
- no UI for selecting vault folders yet
    

---

### 5.2 Concept Note as the First-Class Note Type

Phase 1 should implement `note_type: concept` as the only durable first-class note type.

Studium is concept-driven. Other potential content forms, such as examples, reflections, comparisons, derivations, and code implementations, should eventually live as scaffold modules inside concept notes rather than as separate top-level note types.

This feature should support:

- `note_type: concept`
    
- required `note_subtype`
    
- required `canonical_title`
    
- optional aliases
    
- stable concept IDs
    
- concept-level lifecycle metadata
    

Important behavior:

- every Studium note created in Phase 1 should be a concept note
    
- `note_subtype` should be required
    
- if no more specific subtype is known, `general_concept` may be used as the default
    
- future note types are not blocked, but they are not implemented now
    

Important constraints:

- no `reflection` note type
    
- no `example` note type
    
- no `unknown` note type
    
- no backlog note type
    
- no imported/legacy-note conversion flow
    

---

### 5.3 Stable Concept ID Generation

Phase 1 should define a stable ID format for concept notes.

The recommended direction is:

```text
concept_<slugified_canonical_title>_<short_hash>
```

Example:

```text
concept_stochastic_gradient_descent_a1b2c3
```

The exact mechanics can be finalized in the Technical Plan, but Phase 1 should establish that concept identity is durable and not dependent only on the note title or file path.

This feature should support:

- stable concept IDs
    
- readable IDs
    
- collision-resistant IDs
    
- title changes without necessarily changing concept identity
    

Important behavior:

- generated IDs should be deterministic enough to be understandable
    
- IDs should remain stable once assigned
    
- canonical title and concept ID should be separate fields
    

Important constraints:

- exact slug/hash rules should be finalized in `01 Technical Plan.md`
    
- Phase 1 does not need advanced duplicate detection; that belongs more naturally to Phase 2
    

---

### 5.4 Markdown File Reading and Parsing

Phase 1 should read Markdown files from the test vault and separate structured metadata from human-readable content.

This feature should support:

- reading `.md` files
    
- detecting YAML frontmatter
    
- parsing frontmatter
    
- preserving Markdown body content
    
- identifying headings and major sections
    
- returning a structured representation of the note
    

Important behavior:

- parsing should not rewrite the file
    
- frontmatter parsing and body parsing should be separate concerns
    
- Markdown formatting should not be destroyed or normalized unnecessarily
    
- files with invalid YAML should produce validation errors rather than silent failure
    

Important constraints:

- no full Markdown editor
    
- no rich-text editing
    
- no bidirectional sync between arbitrary Markdown edits and YAML metadata yet
    

---

### 5.5 YAML Frontmatter Metadata Model

Phase 1 should define the initial metadata model for concept notes.

Example direction:

```yaml
id: concept_stochastic_gradient_descent_a1b2c3
note_type: concept
note_subtype: ml_concept
canonical_title: Stochastic Gradient Descent
aliases:
  - SGD

status: scaffolded
review_status: not_submitted
vault_status: draft

learning_encounters:
  - source:
      type: studium
      title: Studium
      unit_type:
      unit:
      section:
      link:
    role: primary
    contribution_status: pending
    content_attached: false
    content_id:

scaffold_modules: []

relationships: []

created_at:
updated_at:
```

This feature should support:

- required universal metadata fields
    
- concept-specific metadata
    
- default lifecycle fields
    
- learning encounter metadata
    
- scaffold module metadata
    
- relationship metadata
    
- timestamps
    

Important behavior:

- `primary_source` should not exist
    
- `learning_encounters` should be required
    
- at least one learning encounter should exist
    
- the first/default encounter should have `role: primary`
    
- `status`, `review_status`, and `vault_status` should be stored
    
- `graph_visibility` should not be stored; it should later be derived from `vault_status`
    
- `retention_status` and `mastery_status` should be deferred to later phases
    

Important constraints:

- full schema details belong in the Technical Plan and Data Schemas
    
- Phase 1 should not overbuild lifecycle logic
    
- Phase 1 only stores review/vault metadata; it does not enforce Agent Review behavior
    

---

### 5.6 Learning Encounter Storage

Phase 1 should replace the old `primary_source` idea with `learning_encounters`.

A learning encounter records the context through which the user encountered or created the concept note.

When no external source is attached, the primary learning encounter should be:

```yaml
learning_encounters:
  - source:
      type: studium
      title: Studium
      unit_type:
      unit:
      section:
      link:
    role: primary
    contribution_status: pending
    content_attached: false
    content_id:
```

This means the note/scaffold originated inside Studium without a formally attached external source.

Supported source types should include:

- `studium`
    
- `book`
    
- `video`
    
- `paper`
    
- `article`
    
- `class`
    
- `work`
    
- `project`
    
- `documentation`
    
- `chatbot`
    
- `podcast`
    
- `imported_note`
    
- `other`
    

This feature should support:

- at least one learning encounter per concept note
    
- `role: primary` for the first/default encounter
    
- future additional encounters
    
- external source metadata
    
- future source attachment references
    
- future chatbot-session references
    

Important behavior:

- `studium` is the default source type when no external source is attached
    
- `chatbot` remains separate from `studium`
    
- a future Studium chatbot conversation may be pulled in as a `chatbot` source
    
- uploaded PDFs, books, videos, or other sources can later become richer learning encounters
    
- source rendering and side-by-side learning are not implemented in Phase 1
    

Important constraints:

- remove `self_study` as a distinct source type for now
    
- remove `none` as a source type
    
- do not implement source processing, source viewers, transcript extraction, or RAG yet
    

---

### 5.7 Scaffold Module Metadata and Containers

Phase 1 should define the storage shape for scaffold modules, but it should not decide which modules a concept needs.

The key distinction:

```text
Phase 1 defines the container.
Phase 4 decides what goes inside the container.
```

Phase 1 should support:

```yaml
scaffold_modules: []
```

Later phases may populate it with entries such as:

```yaml
scaffold_modules:
  - id: module_sgd_conceptual_explanation_001
    type: conceptual_explanation
    title: Conceptual Explanation
    status: scaffolded
```

This feature should support:

- a `scaffold_modules` metadata field
    
- an empty default list
    
- stable future module IDs
    
- future module type/status metadata
    
- a Markdown section where scaffold modules can eventually live
    

Important behavior:

- Phase 1 should not infer scaffold module needs
    
- Phase 1 should not generate meaningful scaffold content
    
- Phase 1 should not call an agent to decide module composition
    
- Phase 1 should only ensure that concept notes can safely hold scaffold metadata and module sections later
    

Important constraints:

- no Create-agent scaffold planning
    
- no module recommendation
    
- no module quality review
    
- no module-level search
    

---

### 5.8 Canonical Markdown Section Containers

Phase 1 should create a canonical Markdown structure for concept notes.

The provisional section containers are:

```markdown
# <Canonical Title>

## Concept Overview

## Prerequisites

## Module Index

## Scaffold Modules

## Related Concepts

## Open Questions / Gaps
```

These sections provide a stable note shape without determining the actual scaffold modules.

This feature should support:

- readable concept notes in Obsidian
    
- stable locations for future content
    
- future scaffold module insertion
    
- future relationship display
    
- future open-question tracking
    

Important behavior:

- new concept notes should include the canonical section containers
    
- missing canonical sections should produce validation warnings, not critical errors
    
- the exact canonical section list can be finalized in the Technical Plan
    
- `Recommended Videos` should not be included in Phase 1; it is deferred to Phase 4
    

Important constraints:

- Phase 1 does not decide which scaffold modules belong to a concept
    
- Phase 1 does not generate learning content
    
- Phase 1 does not research or recommend learning resources
    

---

### 5.9 Relationship Metadata and Markdown Projection

Phase 1 should define how relationships are stored.

Relationships should support both existing and missing concept targets.

Recommended direction:

```yaml
relationships:
  - relationship_type: depends_on
    target_id:
    target_title: Partial Derivatives
    role: prerequisite
    vault_status: missing
```

If the target exists:

```yaml
relationships:
  - relationship_type: depends_on
    target_id: concept_partial_derivatives_m3n4p5
    target_title: Partial Derivatives
    role: prerequisite
    vault_status: found
```

This feature should support:

- `relationship_type`
    
- `target_id`
    
- `target_title`
    
- `role`
    
- `vault_status`
    
- missing targets
    
- found targets
    
- unresolved targets
    

Important behavior:

- YAML relationships are the source of truth
    
- Markdown relationship sections are readable projections
    
- relationship targets may be missing in Phase 1
    
- Phase 1 stores relationships but does not resolve graph structure
    
- Phase 2 will handle indexing, search, and relationship resolution
    

Important constraints:

- no graph visualization
    
- no duplicate relationship intelligence
    
- no automatic prerequisite inference
    
- no syncing user-edited Markdown relationship bullets back into YAML yet
    

Future behavior:

- a later phase, likely around Agent Review, may detect user edits to Markdown relationship sections, route those edits through agent verification, and update YAML only after verification
    

---

### 5.10 Schema Validation Layer

Phase 1 should include validation for concept note structure.

Validation should have two levels:

```text
critical errors
warnings
```

Critical errors may include:

- invalid YAML
    
- missing required ID
    
- missing `note_type`
    
- unsupported `note_type`
    
- missing `canonical_title`
    
- missing required `note_subtype`
    
- malformed `learning_encounters`
    
- malformed `relationships`
    
- duplicate scaffold module IDs
    
- unsafe write target path
    

Warnings may include:

- missing aliases
    
- missing optional metadata
    
- missing canonical Markdown sections
    
- empty scaffold module list
    
- missing source attachment
    
- incomplete relationship target information
    
- empty relationship list
    

This feature should support:

- parsing invalid notes safely
    
- preventing dangerous writes
    
- warning without overblocking
    
- protecting against manual Obsidian edits
    
- protecting against future schema drift
    
- protecting against malformed agent-generated output
    

Important behavior:

- validation should be permissive for reading
    
- validation should be stricter for writing
    
- only dangerous or structurally invalid states should block writes
    
- missing canonical Markdown sections should be warnings only
    

Important constraints:

- no complex migration system
    
- no full schema version migration yet
    
- no strict rejection for every incomplete learning field
    

---

### 5.11 Safe Write Proposals

Phase 1 should introduce a storage-layer write proposal primitive.

This is not a user approval workflow. It is a low-level safety mechanism.

A write proposal describes what Studium intends to write before committing the change.

Example:

```text
operation: create_note
target_path: /test_vault/concepts/stochastic-gradient-descent.md
content_preview: <generated markdown>
warnings: []
would_overwrite_existing_file: false
```

For updates:

```text
operation: update_note
target_path: /test_vault/concepts/stochastic-gradient-descent.md
before: <existing content>
after: <proposed content>
warnings:
- This update changes YAML relationships.
```

This feature should support:

- proposal-first writes
    
- content previews
    
- collision detection
    
- unsafe path detection
    
- create-note operations
    
- simple update-note operations
    
- later approval workflows
    

Important behavior:

- Phase 1 can commit writes to the test vault after a proposal is generated
    
- Phase 1 does not need an Approve/Reject UI
    
- future Create and Agent Review workflows can build approval layers on top of this primitive
    

Important constraints:

- no full backup/version history
    
- no accepted-note versioning
    
- no Git-like diff system
    
- no Agent Review approval workflow
    

---

### 5.12 Test Vault Fixtures

Phase 1 should include test vault fixtures as part of the repo.

Example fixture direction:

```text
tests/fixtures/test_vault/
  valid_concept_note.md
  studium_origin_concept.md
  concept_with_learning_encounter.md
  concept_with_scaffold_modules.md
  concept_with_missing_relationship_target.md
  invalid_yaml_note.md
```

This feature should support:

- repeatable tests
    
- parsing validation
    
- write behavior verification
    
- relationship schema validation
    
- learning encounter validation
    
- scaffold module metadata validation
    

Important behavior:

- tests should not depend on the real Obsidian vault
    
- tests should use temporary or fixture vault directories
    
- write tests should avoid mutating committed fixtures unless intentionally designed to do so
    

Important constraints:

- no real user data
    
- no real source processing
    
- no UI test fixtures yet
    

---

## 6. Key System Behaviors

By the end of Phase 1, Studium should be able to:

- create a valid concept note in a test vault
    
- assign a stable concept ID
    
- require `note_type: concept`
    
- require `note_subtype`
    
- use `general_concept` when no better subtype is known
    
- create a default `studium` learning encounter when no external source is attached
    
- parse YAML frontmatter
    
- preserve Markdown body content
    
- identify canonical Markdown sections
    
- store scaffold module metadata as an empty or populated list
    
- store relationships with both `target_id` and `target_title`
    
- represent missing relationship targets
    
- validate notes with critical errors and warnings
    
- generate safe write proposals before committing changes
    
- write new concept notes safely to a test vault
    
- support simple update operations through write proposals
    

---

## 7. Data and State Introduced

Phase 1 introduces the following durable metadata/state concepts:

- concept note ID
    
- `note_type`
    
- `note_subtype`
    
- `canonical_title`
    
- `aliases`
    
- `status`
    
- `review_status`
    
- `vault_status`
    
- `learning_encounters`
    
- `source.type`
    
- `source.title`
    
- `source.unit_type`
    
- `source.unit`
    
- `source.section`
    
- `source.link`
    
- `role`
    
- `contribution_status`
    
- `content_attached`
    
- `content_id`
    
- `scaffold_modules`
    
- scaffold module IDs
    
- scaffold module types
    
- scaffold module statuses
    
- `relationships`
    
- `relationship_type`
    
- `target_id`
    
- `target_title`
    
- relationship `role`
    
- relationship `vault_status`
    
- `created_at`
    
- `updated_at`
    

Phase 1 does not introduce:

- `primary_source`
    
- `self_study`
    
- `none` source type
    
- `graph_visibility`
    
- `retention_status`
    
- `mastery_status`
    

Graph visibility should later be derived from `vault_status`.

Retention and mastery state should be deferred until their respective phases and may live outside YAML unless there is a clear reason to embed them.

---

## 8. User/System Workflow

Main create-note storage workflow:

```text
Concept note request
↓
Generate concept ID
↓
Build YAML metadata
↓
Build canonical Markdown section containers
↓
Validate note structure
↓
Generate safe write proposal
↓
Commit note to test vault
↓
Read note back and parse it
```

Main parse/validate workflow:

```text
Existing Markdown file
↓
Read file content
↓
Parse YAML frontmatter
↓
Parse Markdown body sections
↓
Validate metadata and section structure
↓
Return parsed concept note with errors/warnings
```

Main update workflow:

```text
Existing concept note
↓
Proposed metadata or section update
↓
Validate proposed result
↓
Generate safe write proposal
↓
Commit update to test vault when called
```

---

## 9. Scope of This Phase

This phase includes:

- test vault configuration
    
- Markdown file reading
    
- YAML frontmatter parsing
    
- Markdown section parsing
    
- concept note creation
    
- concept ID generation
    
- concept note metadata model
    
- `learning_encounters` source model
    
- default `studium` learning encounter
    
- scaffold module metadata shape
    
- canonical section containers
    
- relationship metadata shape
    
- relationship Markdown projection
    
- validation errors and warnings
    
- safe write proposal primitive
    
- safe writes to test vault
    
- simple update support
    
- test vault fixtures
    

---

## 10. Non-Goals

This phase does not include:

- real Obsidian vault integration
    
- Obsidian plugin development
    
- SQLite indexing
    
- Concept Graph Core
    
- Search UI
    
- Create UI
    
- agent-generated scaffold planning
    
- source-aware RAG
    
- PDF processing
    
- video processing
    
- source viewer UI
    
- Studium chatbot
    
- Agent Review
    
- approval/rejection UI
    
- Backlog lifecycle
    
- Retention
    
- Mastery Dashboard
    
- recommended videos
    
- full backup/version history
    
- accepted-note versioning
    
- legacy note import/conversion
    
- additional first-class note types
    

---

## 11. Relationship to Other Phases

### Depends On

None.

Phase 1 is the storage foundation.

### Enables

- Phase 2: Concept Graph Core
    
- Phase 3: Search
    
- Phase 4: Create
    
- Phase 5: Source Content Intelligence
    
- Phase 6: Agent Review
    
- Phase 7: Backlog
    
- Phase 8: Retention
    
- Phase 9: Mastery Dashboard
    

### Later Phase Dependencies

- Phase 2 depends on Phase 1 because the graph needs parseable concept notes, stable IDs, and relationship metadata.
    
- Phase 3 depends on Phase 1 because Search needs readable notes and metadata.
    
- Phase 4 depends on Phase 1 because Create needs a durable concept note format and scaffold containers.
    
- Phase 5 depends on Phase 1 because source encounters must be stored in concept notes.
    
- Phase 6 depends on Phase 1 because Agent Review needs stable modules, sections, statuses, and safe update primitives.
    
- Phase 7 depends on Phase 1 because backlog candidates point to concepts and relationships.
    
- Phase 8 depends on Phase 1 because retention eventually operates on accepted concept notes.
    
- Phase 9 depends on Phase 1 because mastery depends on stable concept identity and subtype.
    

---

## 12. Risks and Design Concerns

- The metadata schema may become too rigid too early.
    
- The metadata schema may become too loose and hard to validate later.
    
- Canonical section containers may need revision after deeper learning-design research.
    
- Markdown rewriting could accidentally corrupt user-authored formatting.
    
- Relationship YAML and Markdown projections could drift if users manually edit Markdown sections.
    
- `note_subtype` may require refinement as the Mastery phase becomes clearer.
    
- `studium` as a default learning encounter must be defined carefully so it means “no external source attached,” not “the user only learned from Studium.”
    
- Safe write proposals must remain simple and not become a premature approval workflow.
    
- Deferring SQLite keeps Phase 1 simpler, but Phase 2 must introduce indexing cleanly.
    
- Deferring retention/mastery status avoids schema clutter, but later phases must decide where that state lives.
    

---

## 13. Phase Decisions / Amendments

The original Phase 1 roadmap has been amended based on later roadmap decisions.

Decisions/amendments:

- `note_type: concept` is the only first-class durable note type in Phase 1.
    
- `reflection`, `example`, and similar content forms are not top-level note types.
    
- Examples, reflections, code implementations, comparisons, derivations, and applications should eventually live as scaffold modules inside concept notes.
    
- `note_type: unknown` is not needed.
    
- Backlog is not a note type.
    
- `primary_source` is removed entirely.
    
- Source/context information lives in `learning_encounters`.
    
- Every concept note should have at least one learning encounter.
    
- If no external source is attached, the default primary encounter is `source.type: studium`.
    
- `self_study` and `none` are removed as source types.
    
- `chatbot` remains distinct from `studium`.
    
- A future Studium chatbot conversation may become a `chatbot` learning encounter source.
    
- Scaffold module metadata should be supported in Phase 1, but scaffold module selection/generation belongs to Phase 4.
    
- Canonical section containers should exist, but their exact final set can be refined in the Technical Plan.
    
- `Recommended Videos` is deferred to Phase 4.
    
- Relationship schema should support both `target_id` and `target_title`.
    
- Relationship schema should support missing, found, and unresolved targets.
    
- YAML is the source of truth for relationships.
    
- Markdown relationship sections are readable projections.
    
- Bidirectional Markdown-to-YAML relationship sync is deferred to a later phase.
    
- `status`, `review_status`, and `vault_status` are included in Phase 1 metadata.
    
- `graph_visibility` is not stored; it is later derived from `vault_status`.
    
- `retention_status` and `mastery_status` are deferred.
    
- Phase 1 remains filesystem/Markdown-first.
    
- SQLite begins later, likely Phase 2.
    
- Legacy/imported note conversion is not supported in Phase 1.
    
- Phase 1 includes safe write proposals but not approval UI.
    
- Phase 1 avoids real backup/version history.
    

Foundational ADR candidates:

- Use Markdown-compatible vault storage.
    
- Use YAML frontmatter for machine-readable metadata.
    
- Use concept notes as durable graph nodes.
    
- Use `learning_encounters` instead of `primary_source`.
    
- Use `studium` as the default source when no external source is attached.
    
- Treat scaffold modules as sections/modules inside concept notes, not top-level notes.
    
- Derive graph visibility from vault lifecycle state.
    
- Use safe write proposals before mutation.
    

---

## 14. Expected Outputs

Expected outputs:

### Working code

- vault configuration / vault root handling
    
- Markdown file reader
    
- YAML frontmatter parser
    
- Markdown section parser
    
- concept note creation utility
    
- concept ID generation utility
    
- concept note serializer
    
- concept note validator
    
- relationship metadata support
    
- scaffold module metadata support
    
- learning encounter metadata support
    
- safe write proposal primitive
    
- safe file write behavior for test vault
    
- simple update behavior through write proposals
    

### Documentation

- amended Phase 1 roadmap
    
- Phase 1 Technical Plan
    
- Phase 1 Branch Plan
    
- branch implementation docs
    
- relevant ADRs if needed
    

### Schemas/models

- concept note metadata schema v1
    
- learning encounter schema v1
    
- source metadata schema v1
    
- scaffold module metadata schema v1
    
- relationship metadata schema v1
    
- validation error/warning model
    
- safe write proposal model
    

### Tests/fixtures

- valid concept note fixture
    
- Studium-origin concept note fixture
    
- external-source learning encounter fixture
    
- scaffold module metadata fixture
    
- missing relationship target fixture
    
- invalid YAML fixture
    
- parser tests
    
- validation tests
    
- write proposal tests
    
- safe write tests
    

---

## 15. Completion Standard

Phase 1 is complete when Studium can read, parse, validate, create, and safely write Obsidian-compatible concept notes in a test vault using the current metadata model without corrupting Markdown content.

More specifically, Phase 1 is complete when:

- concept notes can be created with valid YAML frontmatter
    
- concept notes can be read back and parsed correctly
    
- `note_type: concept` is enforced
    
- `note_subtype` is required
    
- concept IDs are generated in the chosen stable format
    
- every concept note has at least one learning encounter
    
- `studium` is used as the default source when no external source is attached
    
- scaffold module metadata is supported
    
- canonical Markdown section containers are created
    
- relationships can represent found, missing, and unresolved targets
    
- validation produces critical errors and warnings
    
- safe write proposals are generated before file mutation
    
- new notes and simple updates can be written to the test vault
    
- representative fixtures and tests exist
    

---

## 16. Use Cases / Criteria-Met Scenarios

### UC-01: Create Studium-Origin Concept Note

**Scenario:**  
Create a new concept note for “Stochastic Gradient Descent” without attaching an external source.

**Expected behavior:**

- Studium creates a Markdown concept note in the test vault
    
- note has a stable concept ID
    
- `note_type` is `concept`
    
- `note_subtype` is present
    
- `learning_encounters` contains one primary encounter
    
- primary encounter has `source.type: studium`
    
- `scaffold_modules` is present as an empty list
    
- canonical Markdown section containers are created
    
- validation passes
    

**Criteria met:**

- concept note creation works
    
- default Studium-origin encounter works
    
- required metadata exists
    
- canonical Markdown structure exists
    

---

### UC-02: Create Concept Note With External Source

**Scenario:**  
Create a new concept note for “Gradient Descent” with a book source.

**Expected behavior:**

- note is created with `note_type: concept`
    
- `learning_encounters` includes a primary book encounter
    
- source metadata stores title/unit fields
    
- no separate `primary_source` field exists
    
- validation passes
    

**Criteria met:**

- external learning encounter storage works
    
- `primary_source` has been removed
    
- source metadata is stored through `learning_encounters`
    

---

### UC-03: Parse Existing Valid Concept Note

**Scenario:**  
Read an existing valid concept note from the test vault.

**Expected behavior:**

- Markdown file is read
    
- YAML frontmatter is parsed
    
- Markdown body is preserved
    
- canonical sections are identified
    
- metadata is returned in structured form
    
- validation returns no critical errors
    

**Criteria met:**

- file reading works
    
- frontmatter parsing works
    
- section parsing works
    
- validation works
    

---

### UC-04: Detect Invalid YAML

**Scenario:**  
Read a concept note with malformed YAML frontmatter.

**Expected behavior:**

- parser does not silently fail
    
- validation returns a critical error
    
- file content is not modified
    
- no write occurs
    

**Criteria met:**

- invalid YAML is caught
    
- dangerous note state blocks writes
    
- parser is safe for malformed files
    

---

### UC-05: Validate Missing Canonical Section

**Scenario:**  
Read a concept note missing `## Module Index`.

**Expected behavior:**

- note still parses
    
- validation returns a warning
    
- issue is not treated as a critical error
    
- no automatic destructive rewrite occurs
    

**Criteria met:**

- validation supports warnings
    
- incomplete but readable notes are tolerated
    
- canonical sections are encouraged but not over-enforced
    

---

### UC-06: Store Missing Relationship Target

**Scenario:**  
Create a concept note for “Backpropagation” with a relationship to missing concept “Chain Rule.”

**Expected behavior:**

- relationship stores `target_title: Chain Rule`
    
- `target_id` may be blank
    
- `vault_status` is `missing`
    
- Markdown relationship projection is readable
    
- validation passes
    

**Criteria met:**

- relationship schema supports missing concepts
    
- machine-readable and human-readable relationship forms exist
    
- Phase 1 does not need graph resolution
    

---

### UC-07: Store Found Relationship Target

**Scenario:**  
Create a concept note with a relationship to an existing concept ID.

**Expected behavior:**

- relationship stores `target_id`
    
- relationship stores `target_title`
    
- `vault_status` is `found`
    
- Markdown relationship projection is generated
    

**Criteria met:**

- relationship schema supports existing targets
    
- YAML remains source of truth
    
- Markdown projection works
    

---

### UC-08: Generate Safe Write Proposal

**Scenario:**  
Studium prepares to write a new concept note.

**Expected behavior:**

- write proposal is created before file mutation
    
- target path is shown
    
- content preview is available
    
- overwrite/collision risk is checked
    
- write can then be committed to the test vault
    

**Criteria met:**

- write proposal primitive exists
    
- direct silent mutation is avoided
    
- future approval workflows are enabled
    

---

### UC-09: Update Existing Note Through Proposal

**Scenario:**  
Studium prepares a simple metadata update for an existing concept note.

**Expected behavior:**

- existing file is read
    
- proposed updated content is generated
    
- validation runs on proposed result
    
- write proposal shows before/after content
    
- commit writes the update to the test vault
    

**Criteria met:**

- simple update support exists
    
- update path uses write proposal
    
- validation protects writes
    

---

### UC-10: Test Vault Fixture Coverage

**Scenario:**  
Run Phase 1 tests against fixture notes.

**Expected behavior:**

- valid fixtures parse successfully
    
- invalid YAML fixture returns critical error
    
- missing section fixture returns warning
    
- relationship fixtures validate correctly
    
- write proposal tests pass
    

**Criteria met:**

- fixtures exist
    
- parser/validator/write behavior is testable
    
- Phase 1 can be verified without a real vault
    

---

## 17. Future Enhancements

Future enhancements:

- real Obsidian vault connection
    
- Obsidian plugin integration
    
- SQLite-backed concept index
    
- richer schema validation
    
- schema migration reports
    
- relationship Markdown-to-YAML sync after agent verification
    
- full backup/version history
    
- accepted-note versioning
    
- patch/diff UI
    
- Create-agent scaffold module selection
    
- source-aware PDF/book/video workspace
    
- Studium chatbot
    
- chatbot conversation as source encounter
    
- recommended videos section
    
- retention status tracking
    
- mastery status tracking
    
- legacy note conversion, if ever needed
    

---

## 18. Open Questions

Open questions for the Technical Plan:

- What exact canonical Markdown section containers should Phase 1 create?
    
- Should additional learning-focused sections be added beyond Concept Overview, Prerequisites, Module Index, Scaffold Modules, Related Concepts, and Open Questions / Gaps?
    
- What exact ID generation algorithm should be used?
    
- What exact `note_subtype` values should be allowed in Phase 1?
    
- Should `note_subtype` validation be strict or allow arbitrary future strings?
    
- What exact schema validation library or internal validation approach should be used?
    
- What should the safe write proposal object look like?
    
- How much before/after diffing should Phase 1 include?
    
- How should relationship Markdown projections be formatted?
    
- How should timestamps be generated and updated?
    
- What folder structure should the test vault use?
    
- How should write tests avoid mutating committed fixture files?