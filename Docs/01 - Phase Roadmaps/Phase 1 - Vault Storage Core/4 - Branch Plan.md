## 1. Branch Plan Purpose

This document breaks Phase 1 into implementation branches.

The goal is to move from the Technical Plan to branch-sized implementation steps without overplanning every file or function.

Each branch should:

- implement one coherent slice of the phase
    
- build on previous branches
    
- produce testable behavior
    
- move Phase 1 closer to its completion standard
    
- stay small enough to understand, review, and document
    

Phase 1 should remain a pure Python storage layer with testable functions and a minimal CLI. Frontend work begins later.

---

## 2. Phase Completion Target

By the end of the final branch, Phase 1 should satisfy the completion standard defined in:

```text
00 Phase Roadmap.md
01 Technical Plan.md
```

Phase-level completion summary:

- Studium can create, parse, validate, serialize, and safely write concept notes in a test vault.
    
- Concept notes use the Phase 1 metadata schema, including concept identity, concept taxonomy, learning encounters, scaffold module metadata, relationships, and lifecycle fields.
    
- YAML frontmatter is machine-readable, while Markdown body content remains Obsidian-compatible and human-readable.
    
- Safe write proposals protect file mutations before commits.
    
- Minimal CLI commands allow manual verification of create and validation flows.
    
- Automated tests cover the core storage behavior needed by later phases.
    

---

## 3. Branch Sequence Overview

| Branch | Name                                 | Main Goal                                                                                | Key Output                                                                                                                         |
| ------ | ------------------------------------ | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 01     | `P1-B1-core-package-foundation`      | Establish the Python package, tooling, and test foundation.                              | Working project foundation with pytest, Ruff, Pyright, and pre-commit.                                                             |
| 02     | `P1-B2-vault-access-layer`           | Implement safe file access inside a configured test vault.                               | Vault path resolution, Markdown file reading, and safe vault-root enforcement.                                                     |
| 03     | `P1-B3-concept-note-schemas`         | Define Pydantic schemas for Phase 1 concept note metadata.                               | Structured schema models for concept notes, learning encounters, scaffold modules, relationships, validation, and write proposals. |
| 04     | `P1-B4-markdown-frontmatter-parser`  | Parse Markdown files into frontmatter, body content, sections, and structured note data. | Markdown/frontmatter parser with raw and high-level parse flows.                                                                   |
| 05     | `P1-B5-concept-note-serialization`   | Generate full Markdown concept notes from metadata and canonical body sections.          | Serializer, concept ID generation, canonical YAML order, canonical Markdown sections, and relationship Markdown projection.        |
| 06     | `P1-B6-validation-layer`             | Implement critical error and warning validation behavior.                                | Validation system for parse/create/update/write modes.                                                                             |
| 07     | `P1-B7-write-proposals-vault-writes` | Implement safe write proposals and committed test-vault writes.                          | `WriteProposal` creation, stale-write protection, collision detection, and proposal commit behavior.                               |
| 08     | `P1-B8-cli-and-phase-verification`   | Add minimal CLI and end-to-end fixture coverage.                                         | CLI commands and final Phase 1 verification tests.                                                                                 |

---

## 4. Branch Details

### Branch 01: `P1-B1-core-package-foundation`

**Goal:**  
Create the initial Python project foundation for Phase 1 storage work. This branch should establish the package structure, test setup, linting, type checking, and pre-commit tooling needed for the rest of the phase.

**Why this branch comes here:**  
All later branches need a clean package foundation and reliable checks. This branch does not implement storage behavior yet; it prepares the codebase for implementation.

**Technical Plan sections addressed:**

- Technical Scope
    
- Testing Strategy
    
- Cursor / Implementation Constraints
    

**Roadmap capabilities addressed:**

- testable storage foundation
    
- pure Python implementation base
    

**Implementation focus:**

- initialize broad Python package structure
    
- configure pytest
    
- configure Ruff
    
- configure Pyright
    
- configure pre-commit
    
- add placeholder package/module structure as needed
    
- add a trivial smoke test to verify tooling
    

**Expected output:**

- Python project can run tests
    
- linting and type checking can run
    
- pre-commit hooks are configured
    
- broad package structure exists for later storage modules
    

**Testing / verification:**

- run pytest successfully
    
- run Ruff successfully
    
- run Pyright successfully
    
- run pre-commit successfully
    

**Branch success criteria:**

-  Python package foundation exists.
    
-  pytest runs successfully.
    
-  Ruff and Pyright run successfully.
    
-  pre-commit is configured and runs successfully.
    
-  The project is ready for Phase 1 storage implementation.
    

**Notes / risks:**

- Avoid adding real storage logic in this branch.
    
- Cursor may choose exact file names, but should keep the structure understandable.
    

---

### Branch 02: `P1-B2-vault-access-layer`

**Goal:**  
Implement safe file access for a configured test vault. This branch should allow Studium to resolve vault-relative paths, read Markdown files, list Markdown files, and prevent unsafe access outside the vault root.

**Why this branch comes here:**  
Before parsing, schemas, serialization, or writes matter, Studium needs safe access to Markdown files inside a vault-like directory.

**Technical Plan sections addressed:**

- Vault Access Layer
    
- Write / Mutation Behavior
    
- Testing Strategy
    

**Roadmap capabilities addressed:**

- test vault storage
    
- Markdown file reading
    
- safe vault-root enforcement
    

**Implementation focus:**

- vault root configuration
    
- vault-relative path resolution
    
- path traversal protection
    
- Markdown file reading
    
- Markdown file listing
    
- basic file existence checks
    
- temp-directory-based tests
    

**Expected output:**

- code can safely read Markdown files from a test vault
    
- unsafe paths are rejected
    
- Markdown files can be listed from the vault root
    
- tests prove vault access behavior works
    

**Testing / verification:**

- unit tests for safe path resolution
    
- integration tests using temporary directories
    
- tests for blocked path traversal
    
- tests for reading and listing Markdown files
    

**Branch success criteria:**

-  Vault-relative paths resolve safely.
    
-  Access outside the vault root is blocked.
    
-  Markdown files can be read from a test vault.
    
-  Markdown files can be listed from a test vault.
    
-  Vault access behavior is tested with temporary directories.
    

**Notes / risks:**

- This branch should not implement parsing or schema validation yet.
    
- It should only handle safe file access.
    

---

### Branch 03: `P1-B3-concept-note-schemas`

**Goal:**  
Define the Pydantic schema models for Phase 1 concept note metadata and supporting structures. This branch creates the structured data model that later parsing, serialization, validation, and write proposals will use.

**Why this branch comes here:**  
Parsing needs a target structure. Defining schemas before parser behavior prevents the parser from becoming a loose, untyped dictionary pipeline.

**Technical Plan sections addressed:**

- Concept Note Schema Models
    
- Data Models and Schemas
    
- Validation Result
    
- Write Proposal
    

**Roadmap capabilities addressed:**

- YAML frontmatter metadata model
    
- learning encounter storage
    
- scaffold module metadata
    
- relationship metadata
    
- schema versioning
    
- concept taxonomy
    

**Implementation focus:**

- `ConceptNoteMetadata`
    
- `LearningEncounter`
    
- `SourceMetadata`
    
- `ScaffoldModuleMetadata`
    
- `RelationshipMetadata`
    
- `ValidationIssue`
    
- `ValidationResult`
    
- `WriteProposal`
    
- enum-like values for concept type, source type, module type, relationship type, and lifecycle statuses
    
- `schema_version: 1`
    

**Expected output:**

- Pydantic models exist for all Phase 1 metadata structures
    
- schemas reflect the approved concept taxonomy
    
- models support required fields and defaults where appropriate
    
- model tests cover valid and invalid schema cases
    

**Testing / verification:**

- unit tests for valid concept note metadata
    
- unit tests for missing required fields
    
- unit tests for learning encounter requirements
    
- unit tests for scaffold module metadata
    
- unit tests for relationship metadata
    
- unit tests for schema version behavior
    

**Branch success criteria:**

-  Phase 1 Pydantic schema models exist.
    
-  `note_type: concept` is enforced.
    
-  `concept_type` and `concept_domains` are modeled.
    
-  `learning_encounters` are modeled and required.
    
-  scaffold module and relationship metadata are modeled.
    
-  schema model tests pass.
    

**Notes / risks:**

- Do not overbuild future schema behavior.
    
- Retention and mastery status should not be added in Phase 1.
    
- Relationship `role` should not be included in Phase 1.
    

---

### Branch 04: `P1-B4-markdown-frontmatter-parser`

**Goal:**  
Implement Markdown and YAML frontmatter parsing. This branch should split Markdown files into frontmatter and body content, parse YAML into raw metadata, detect Markdown sections, and support a high-level concept note parsing flow.

**Why this branch comes here:**  
Schemas now exist, so Markdown/YAML parsing can produce structured data instead of untyped output. This branch bridges raw Markdown files and the concept note schema layer.

**Technical Plan sections addressed:**

- Markdown Parser
    
- YAML Frontmatter Parser
    
- Data Flow / System Flow
    
- Parsing vs Serialization
    

**Roadmap capabilities addressed:**

- Markdown file reading and parsing
    
- YAML frontmatter parsing
    
- Markdown body preservation
    
- canonical section detection
    

**Implementation focus:**

- split YAML frontmatter from Markdown body
    
- parse YAML frontmatter into raw metadata
    
- preserve raw Markdown body content
    
- detect headings and canonical sections
    
- expose lower-level raw parse functions
    
- expose high-level concept note parse function without duplicating parsing logic
    
- return structured parse results and validation-ready objects
    

**Expected output:**

- raw Markdown can be split into frontmatter and body
    
- YAML frontmatter can be parsed
    
- Markdown body can be preserved
    
- section headings can be detected
    
- high-level parser can produce parsed concept note output
    

**Testing / verification:**

- unit tests for frontmatter splitting
    
- unit tests for invalid/missing frontmatter behavior
    
- unit tests for YAML parsing
    
- fixture tests for Markdown notes
    
- tests confirming body content is preserved
    
- tests for section detection
    

**Branch success criteria:**

-  Frontmatter and body content can be separated.
    
-  YAML frontmatter can be parsed.
    
-  Invalid YAML is detected.
    
-  Markdown body content is preserved.
    
-  Canonical sections can be detected.
    
-  High-level parsing reuses lower-level parsing functions without duplicate logic.
    

**Notes / risks:**

- Parsing should not mutate files.
    
- Avoid duplicating logic between raw parsing and high-level concept parsing.
    
- Validation strictness should be completed in Branch 06.
    

---

### Branch 05: `P1-B5-concept-note-serialization`

**Goal:**  
Implement concept note serialization and new note generation. This branch should convert structured concept metadata and canonical body sections into complete Obsidian-compatible Markdown files.

**Why this branch comes here:**  
After schemas and parsing exist, Studium needs the reverse direction: generating valid Markdown concept notes from structured data.

**Technical Plan sections addressed:**

- Concept Note Serializer
    
- Stable Concept ID Generation
    
- Canonical Markdown Section Containers
    
- Relationship Projection Layer
    

**Roadmap capabilities addressed:**

- stable concept ID generation
    
- concept note creation
    
- canonical YAML key order
    
- canonical Markdown section containers
    
- relationship Markdown projection
    
- scaffold module metadata containers
    

**Implementation focus:**

- slug generation
    
- concept ID generation
    
- default Studium learning encounter creation
    
- canonical YAML key ordering
    
- canonical Markdown section generation
    
- full Markdown file serialization
    
- relationship projection into `## Prerequisites` and `## Related Concepts`
    
- basic new concept note generation from title and optional metadata
    

**Expected output:**

- new concept note Markdown can be generated
    
- generated notes have stable concept IDs
    
- generated notes include canonical YAML ordering
    
- generated notes include canonical Markdown section order
    
- relationships can be projected into readable Markdown sections
    

**Testing / verification:**

- unit tests for slug generation
    
- unit tests for concept ID generation
    
- unit tests for default Studium encounter creation
    
- golden-file tests for generated Markdown output
    
- tests for relationship Markdown projection
    
- tests for canonical section generation
    

**Branch success criteria:**

-  Concept IDs can be generated in the approved format.
    
-  New concept notes can be serialized into Markdown.
    
-  Generated YAML follows canonical key order.
    
-  Generated Markdown follows canonical section order.
    
-  Relationships project into readable Markdown sections.
    
-  Golden-file tests verify generated output.
    

**Notes / risks:**

- ID algorithm details should be finalized during this branch.
    
- Serialization should not imply automatic rewriting of existing notes.
    
- Relationship projection is display output only; YAML remains source of truth.
    

---

### Branch 06: `P1-B6-validation-layer`

**Goal:**  
Implement Phase 1 validation rules for parsed, generated, updated, and written concept notes. This branch should distinguish critical errors from warnings and apply different strictness depending on operation mode.

**Why this branch comes here:**  
Parsing and serialization exist, so validation can now operate across actual note structures instead of isolated schema models.

**Technical Plan sections addressed:**

- Validation Layer
    
- Validation and Error Handling
    
- Validation Result
    
- Data Flow / System Flow
    

**Roadmap capabilities addressed:**

- schema validation layer
    
- critical errors and warnings
    
- parse/create/update/write validation modes
    
- protection against malformed notes
    

**Implementation focus:**

- validation modes: parse, create, update, write
    
- structured validation issues
    
- critical error vs warning behavior
    
- unknown-field behavior
    
- required metadata validation
    
- learning encounter validation
    
- scaffold module validation
    
- relationship validation
    
- canonical section validation
    
- generated-note strictness
    

**Expected output:**

- validation returns structured critical errors and warnings
    
- parsed notes tolerate warnings where appropriate
    
- generated/proposed writes are stricter
    
- generated notes missing canonical sections fail validation
    
- malformed writes are blocked by validation result
    

**Testing / verification:**

- unit tests for validation modes
    
- fixture tests for invalid YAML, missing fields, duplicate module IDs, missing sections
    
- tests for parse-vs-write unknown field behavior
    
- tests for multiple primary encounters
    
- tests for warning vs critical classification
    

**Branch success criteria:**

-  Validation supports parse/create/update/write modes.
    
-  Critical errors and warnings are returned in structured form.
    
-  Generated notes are held to stricter validation than parsed notes.
    
-  Unknown fields warn on parse and fail on write.
    
-  Validation tests cover key Phase 1 failure modes.
    

**Notes / risks:**

- Avoid duplicating Pydantic validation unnecessarily.
    
- Pydantic should validate schema shape; the validation layer should handle operation-specific rules.
    
- Treat more issues as critical for writes than for reads.
    

---

### Branch 07: `P1-B7-write-proposals-vault-writes`

**Goal:**  
Implement safe write proposals and committed file writes. This branch should make file mutation inspectable, validated, and protected against collisions or stale updates.

**Why this branch comes here:**  
At this point, Studium can access the vault, model metadata, parse notes, serialize notes, and validate structures. Now it can safely write to the test vault.

**Technical Plan sections addressed:**

- Safe Write Proposal Layer
    
- Write / Mutation Behavior
    
- Vault Access Layer
    
- Validation and Error Handling
    

**Roadmap capabilities addressed:**

- safe write proposals
    
- safe file writes to test vault
    
- simple update support
    
- collision detection
    
- stale-write protection
    

**Implementation focus:**

- build create-note write proposals
    
- build update-note write proposals
    
- include before/after content
    
- include warnings and critical errors
    
- detect create collisions
    
- hash existing files for update safety
    
- commit write proposals
    
- block commits with critical errors
    
- block stale update commits
    

**Expected output:**

- write proposals can be created
    
- proposals can be committed when safe
    
- create operations do not overwrite existing files
    
- update operations detect stale file changes
    
- writes remain scoped to the test vault
    

**Testing / verification:**

- unit tests for write proposal objects
    
- integration tests using temporary vault directories
    
- tests for create collision blocking
    
- tests for stale hash blocking
    
- tests for successful create commit
    
- tests for successful update commit
    
- tests for critical-error commit blocking
    

**Branch success criteria:**

-  Create-note write proposals can be built.
    
-  Update-note write proposals can be built.
    
-  Proposals with critical errors cannot be committed.
    
-  Create operations cannot overwrite existing files.
    
-  Update operations verify expected file hash.
    
-  Safe commits write to the test vault successfully.
    

**Notes / risks:**

- This branch should not add UI approval.
    
- Write proposals are returned as objects, not persisted as files.
    
- Full backup/version history remains out of scope.
    

---

### Branch 08: `P1-B8-cli-and-phase-verification`

**Goal:**  
Add the minimal Phase 1 CLI and complete end-to-end fixture verification. This branch proves that the full Phase 1 storage layer works from manual commands and automated tests.

**Why this branch comes here:**  
All core storage behavior exists by this point. The CLI can remain thin and call the storage-layer functions already implemented.

**Technical Plan sections addressed:**

- Minimal CLI Layer
    
- Testing Strategy
    
- Phase-Level Technical Completion Standard
    

**Roadmap capabilities addressed:**

- minimal CLI
    
- test vault fixtures
    
- end-to-end phase verification
    
- create and validation workflows
    

**Implementation focus:**

- `studium create-concept "<title>"`
    
- `studium validate-note <path>`
    
- `studium validate-vault <path>`
    
- readable CLI output for warnings/errors
    
- final fixture set
    
- final end-to-end tests
    
- phase criteria verification coverage
    

**Expected output:**

- CLI can create a concept note
    
- CLI can validate one note
    
- CLI can validate a vault directory
    
- fixture tests cover representative valid and invalid notes
    
- end-to-end tests prove Phase 1 completion criteria
    

**Testing / verification:**

- CLI integration tests
    
- end-to-end create → commit → parse → validate test
    
- full fixture vault validation
    
- golden-file checks where appropriate
    
- manual CLI verification
    

**Branch success criteria:**

-  `studium create-concept "<title>"` works.
    
-  `studium validate-note <path>` works.
    
-  `studium validate-vault <path>` works.
    
-  Final fixtures cover valid and invalid Phase 1 note cases.
    
-  End-to-end tests satisfy the Phase 1 technical completion standard.
    

**Notes / risks:**

- CLI should remain thin.
    
- Do not add advanced CLI workflows.
    
- The purpose is phase verification, not a complete user interface.
    

---

## 5. Phase Criteria Coverage

| Phase Criterion                                           | Covered By Branch(es) | Notes                                                                                                        |
| --------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| Python package and tooling foundation exists              | P1-B1                 | Includes pytest, Ruff, Pyright, and pre-commit.                                                              |
| Test vault files can be accessed safely                   | P1-B2                 | Includes path resolution, Markdown reading, listing, and vault-root safety.                                  |
| Pydantic metadata schemas exist                           | P1-B3                 | Covers concept notes, learning encounters, scaffold modules, relationships, validation, and write proposals. |
| YAML frontmatter can be parsed                            | P1-B4                 | Includes raw parsing and high-level concept note parsing.                                                    |
| Markdown body content can be preserved                    | P1-B4                 | Parsing should not rewrite or normalize body content.                                                        |
| Canonical sections can be detected                        | P1-B4, P1-B6          | Parser detects sections; validator classifies missing sections.                                              |
| New concept notes can be generated                        | P1-B5                 | Includes concept ID generation, default metadata, canonical sections, and serialization.                     |
| Relationships can be projected into Markdown              | P1-B5                 | Projects YAML relationships into `Prerequisites` and `Related Concepts`.                                     |
| Validation supports errors and warnings                   | P1-B6                 | Includes operation-specific validation behavior.                                                             |
| Generated notes are stricter than parsed notes            | P1-B6                 | Missing generated canonical sections become critical errors.                                                 |
| Safe write proposals can be created                       | P1-B7                 | Includes create and update proposals.                                                                        |
| Writes are protected against collisions and stale updates | P1-B7                 | Includes overwrite blocking and hash checks.                                                                 |
| Minimal CLI exists                                        | P1-B8                 | Includes create, validate-note, and validate-vault commands.                                                 |
| Phase can be verified end-to-end                          | P1-B8                 | Final fixtures and E2E tests prove completion criteria.                                                      |