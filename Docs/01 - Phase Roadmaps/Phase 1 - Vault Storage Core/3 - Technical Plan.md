## 1. Technical Purpose

Phase 1 establishes the technical foundation for reading, creating, validating, serializing, and safely writing Studium concept notes as Obsidian-compatible Markdown files.

The main technical layer being built is the **vault storage layer**. This layer should understand how Studium concept notes are represented on disk, how YAML frontmatter maps into structured Python/Pydantic models, how Markdown body sections are parsed and preserved, and how file writes are safely proposed before being committed.

This phase must make the following true before later phases begin:

- Studium can create a valid concept note without the Create UI.
    
- Studium can parse a Markdown concept note into structured metadata and body content.
    
- Studium can validate note metadata and section structure.
    
- Studium can safely write new notes and simple updates to a test vault.
    
- Later phases can depend on stable concept IDs, learning encounters, scaffold module metadata, relationships, and lifecycle metadata.
    

Phase 1 should remain a **pure Python storage layer** with testable functions and a minimal CLI. Frontend work begins later.

---

## 2. Roadmap Capabilities Being Implemented

This technical plan implements the following Phase 1 roadmap capabilities:

- test vault storage
    
- concept note as the only first-class note type
    
- stable concept ID generation
    
- Markdown file reading and parsing
    
- YAML frontmatter metadata model
    
- learning encounter storage
    
- scaffold module metadata and containers
    
- canonical Markdown section containers
    
- relationship metadata and Markdown projection
    
- schema validation layer
    
- safe write proposals
    
- test vault fixtures
    
- minimal CLI for manual verification
    

---

## 3. Technical Scope

This phase technically includes:

- pure Python storage-layer code
    
- broad internal modules for vault access, Markdown parsing, schemas, validation, serialization, writes, and CLI
    
- Pydantic models for structured metadata
    
- YAML frontmatter parsing
    
- Markdown body preservation
    
- canonical Markdown generation for new notes
    
- schema versioning through `schema_version: 1`
    
- strict-enough validation for writes and permissive-enough validation for reads
    
- safe write proposal objects
    
- commit behavior for approved/generated proposals
    
- minimal CLI commands for manual verification
    
- fixture-based and golden-file-style tests
    

The Technical Plan should define broad modules and interfaces. Cursor may decide exact file names during branch implementation, as long as it stays within this phase’s architecture.

---

## 4. System Components Introduced or Modified

### Vault Access Layer

**Purpose:**  
Provide safe access to Markdown files inside a configured test vault.

**Responsibilities:**

- resolve vault-relative paths safely
    
- prevent writes outside the vault root
    
- read Markdown files
    
- write Markdown files through committed write proposals
    
- detect file existence and collisions
    
- support temporary test vaults during testing
    

**Inputs:**

- vault root path
    
- relative note path
    
- Markdown content
    
- write proposal
    

**Outputs:**

- raw Markdown content
    
- resolved safe paths
    
- file existence/collision information
    
- committed writes
    

**Notes / Constraints:**

- Phase 1 should use a test vault only.
    
- Real Obsidian vault integration is not included.
    
- Path traversal should be treated as a critical error.
    

---

### Markdown Parser

**Purpose:**  
Parse Markdown files into YAML frontmatter and body content without corrupting formatting.

**Responsibilities:**

- detect YAML frontmatter block
    
- separate frontmatter from Markdown body
    
- preserve raw Markdown body
    
- detect top-level and second-level headings
    
- identify canonical sections when present
    

**Inputs:**

- raw Markdown file content
    

**Outputs:**

- raw YAML frontmatter text
    
- parsed Markdown body
    
- detected headings/sections
    
- parse errors if frontmatter is malformed
    

**Notes / Constraints:**

- Parsing must not rewrite files.
    
- Existing body content should be preserved exactly unless a later write operation intentionally changes it.
    
- Missing canonical sections should be surfaced through validation, not automatically fixed during parsing.
    

---

### YAML Frontmatter Parser

**Purpose:**  
Convert YAML frontmatter into structured metadata.

**Responsibilities:**

- parse YAML text
    
- return raw metadata dictionary
    
- detect malformed YAML
    
- pass parsed metadata into Pydantic models
    
- preserve unknown fields during parsing only long enough to warn
    

**Inputs:**

- YAML frontmatter text
    

**Outputs:**

- parsed metadata dictionary
    
- parse errors
    
- Pydantic model validation result
    

**Notes / Constraints:**

- Invalid YAML is a critical error.
    
- Unknown fields are allowed during parsing with warnings.
    
- Unknown fields are rejected during generated/proposed writes unless explicitly whitelisted.
    

---

### Concept Note Schema Models

**Purpose:**  
Define the structured metadata model for Studium concept notes.

**Responsibilities:**

- represent concept note metadata
    
- validate required fields
    
- define allowed enum-like values
    
- serialize metadata into canonical YAML order
    
- support schema versioning
    

**Inputs:**

- parsed YAML metadata
    
- generated metadata from note creation
    

**Outputs:**

- validated Pydantic models
    
- validation errors/warnings
    
- serialized YAML-ready dictionaries
    

**Notes / Constraints:**

- Pydantic should be used for schema modeling and validation.
    
- `note_type` is always `concept` in Phase 1.
    
- `concept_type` replaces the earlier `note_subtype` model.
    
- `concept_domains` are labels only in Phase 1.
    

---

### Concept Note Serializer

**Purpose:**  
Convert structured metadata and Markdown body content into a full Markdown file.

**Responsibilities:**

- serialize Pydantic metadata to YAML
    
- emit YAML fields in canonical order
    
- generate canonical Markdown section containers for new notes
    
- preserve existing Markdown body during parsing and simple updates where possible
    
- produce full Markdown file content
    

**Inputs:**

- concept note metadata model
    
- Markdown body sections
    
- canonical section configuration
    

**Outputs:**

- full Markdown content
    

**Notes / Constraints:**

- New notes should use canonical YAML key order and canonical Markdown section order.
    
- Existing notes should not be automatically reordered during parsing.
    
- Phase 1 can generate full replacement content for proposed updates, but should not implement complex patching.
    

---

### Validation Layer

**Purpose:**  
Validate concept note metadata, Markdown sections, relationships, scaffold modules, and write operations.

**Responsibilities:**

- distinguish critical errors from warnings
    
- validate parsed notes permissively
    
- validate generated/proposed notes strictly
    
- block writes with critical errors
    
- surface warnings without always blocking
    
- produce structured validation results
    

**Inputs:**

- parsed concept note
    
- generated concept note
    
- write proposal
    
- operation type: parse, create, update, write
    

**Outputs:**

- validation result
    
- critical errors
    
- warnings
    

**Notes / Constraints:**

- Reads should be permissive.
    
- Writes should be cautious.
    
- Generated notes missing canonical sections should be treated as an internal critical error.
    

---

### Relationship Projection Layer

**Purpose:**  
Represent YAML relationships in human-readable Markdown sections.

**Responsibilities:**

- store relationships in YAML as source of truth
    
- project prerequisite-style relationships into `## Prerequisites`
    
- project non-prerequisite relationships into `## Related Concepts`
    
- support found, missing, and unresolved targets
    
- avoid semantic validation of relationship correctness in Phase 1
    

**Inputs:**

- relationship metadata list
    

**Outputs:**

- Markdown relationship bullets
    
- validation warnings/errors
    

**Notes / Constraints:**

- No graph resolution in Phase 1.
    
- No bidirectional Markdown-to-YAML relationship sync in Phase 1.
    
- Phase 2 or Phase 6 may later add smarter relationship verification.
    

---

### Safe Write Proposal Layer

**Purpose:**  
Represent intended file writes before they are committed.

**Responsibilities:**

- build write proposal objects
    
- show target path
    
- include before/after content
    
- detect collisions and overwrite risk
    
- include validation warnings/errors
    
- include expected file hash for update safety
    
- commit write proposals only if safe
    

**Inputs:**

- create or update operation
    
- target path
    
- before content, if any
    
- after content
    
- validation result
    

**Outputs:**

- `WriteProposal`
    
- committed file write, if explicitly committed
    

**Notes / Constraints:**

- This is not a UI approval layer.
    
- Phase 1 returns proposal objects.
    
- Later Create/Agent Review UI can display and approve/reject proposals.
    

---

### Minimal CLI Layer

**Purpose:**  
Provide manual verification commands for Phase 1 and a foundation for later phases.

**Responsibilities:**

- create a concept note from a title
    
- validate a single note
    
- validate a vault directory
    
- print validation results in readable form
    

**Commands:**

```text
studium create-concept "<title>"
studium validate-note <path>
studium validate-vault <path>
```

**Notes / Constraints:**

- CLI should remain thin.
    
- CLI should call storage-layer functions rather than containing business logic.
    
- No update CLI is required in Phase 1.
    

---

## 5. Data Models and Schemas

### 5.1 Concept Note Metadata

**Purpose:**  
Represent the YAML frontmatter for a Studium concept note.

**Used by:**

- parser
    
- validator
    
- serializer
    
- write proposal builder
    
- CLI
    
- future Create/Search/Review systems
    

**Fields:**

```yaml
id:
schema_version:
note_type:
concept_type:
concept_domains:
canonical_title:
aliases:

status:
review_status:
vault_status:

learning_encounters:

scaffold_modules:

relationships:

created_at:
updated_at:
```

**Required fields:**

- `id`
    
- `schema_version`
    
- `note_type`
    
- `concept_type`
    
- `concept_domains`
    
- `canonical_title`
    
- `aliases`
    
- `status`
    
- `review_status`
    
- `vault_status`
    
- `learning_encounters`
    
- `scaffold_modules`
    
- `relationships`
    
- `created_at`
    
- `updated_at`
    

**Validation rules:**

- `schema_version` must be `1`.
    
- `note_type` must be `concept`.
    
- `concept_type` must be present.
    
- `concept_domains` must be present, but may be an empty list.
    
- `canonical_title` must be non-empty.
    
- `aliases` must be a list; empty list is valid.
    
- `learning_encounters` must contain at least one encounter.
    
- `scaffold_modules` must be a list; empty list is valid.
    
- `relationships` must be a list; empty list is valid.
    
- `created_at` and `updated_at` should use ISO 8601 UTC.
    
- Unknown fields are warnings during parsing and rejected during writing.
    

**Example:**

```yaml
id: concept_stochastic_gradient_descent_a1b2c3
schema_version: 1
note_type: concept
concept_type: algorithm
concept_domains:
  - machine_learning
  - optimization
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

created_at: 2026-06-25T00:00:00Z
updated_at: 2026-06-25T00:00:00Z
```

---

### 5.2 Concept Type

**Purpose:**  
Classify the structural kind of concept.

This is different from `concept_domains`.

`concept_type` answers:

> What kind of concept is this?

`concept_domains` answers:

> What knowledge spaces does this concept belong to?

**Allowed initial values:**

```text
general_concept
mathematical_concept
algorithm
programming_concept
system_design_concept
theory_concept
process_concept
tooling_concept
```

**Validation rules:**

- `concept_type` is required.
    
- Generated notes should use one of the allowed values.
    
- Unknown values in parsed notes should warn.
    
- Unknown values in generated/proposed notes should be rejected unless explicitly allowed.
    

**Default:**

```yaml
concept_type: general_concept
```

---

### 5.3 Concept Domains

**Purpose:**  
Provide flexible domain/context labels that describe where a concept lives in the broader knowledge space.

Examples:

```yaml
concept_domains:
  - machine_learning
  - optimization
```

Important distinction:

```text
concept_domains are labels.
concept notes are learnable knowledge objects.
```

A domain label does not automatically create a concept node.

For example, `machine_learning` can exist as a domain label, while `Machine Learning` can also later exist as its own concept note if the user chooses to learn it.

**Validation rules:**

- field is required
    
- value must be a list
    
- empty list is allowed
    
- values should use lowercase snake_case
    
- domains are not enum-restricted in Phase 1
    
- Phase 1 does not infer relationships from domains
    
- Phase 1 does not create domain nodes
    

---

### 5.4 Learning Encounter

**Purpose:**  
Represent the context through which the user encountered or created the concept.

Every concept note must have at least one learning encounter.

**Fields:**

```yaml
source:
  type:
  title:
  unit_type:
  unit:
  section:
  link:
role:
contribution_status:
content_attached:
content_id:
```

**Required fields:**

- `source`
    
- `source.type`
    
- `source.title`
    
- `role`
    
- `contribution_status`
    
- `content_attached`
    
- `content_id`
    

**Allowed source types:**

```text
studium
book
video
paper
article
class
work
project
documentation
chatbot
podcast
imported_note
other
```

**Allowed roles:**

```text
primary
additional
```

**Allowed contribution statuses:**

```text
pending
user_described
source_attached
source_analyzed
integrated
no_new_contribution_detected
```

**Validation rules:**

- `learning_encounters` must contain at least one item.
    
- The first/default encounter should have `role: primary`.
    
- Multiple primary encounters are not allowed for generated/proposed writes.
    
- Unknown source types warn on parse and reject on write.
    
- `source.title` is required.
    
- `content_attached: false` is valid even for external source types.
    
- `content_id` may be empty/null until Phase 5 source processing exists.
    

**Default Studium-origin encounter:**

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

---

### 5.5 Scaffold Module Metadata

**Purpose:**  
Define the metadata shape for future scaffold modules without generating meaningful scaffold content in Phase 1.

**Fields:**

```yaml
id:
type:
title:
status:
origin:
focus:
```

**Allowed module types:**

```text
conceptual_explanation
worked_example
code_implementation
implementation_notes
comparison
derivation
application
misconception_debugging
custom
```

**Allowed statuses:**

```text
scaffolded
in_progress
completed
deferred
```

**Allowed future origins:**

```text
agent_recommended
user_requested
source_suggested
review_suggested
manual
```

**Validation rules:**

- `scaffold_modules` may be an empty list.
    
- Empty list is valid with no warning in Phase 1.
    
- If a module exists, `id`, `type`, `title`, and `status` are required.
    
- `origin` is optional in Phase 1.
    
- `focus` is optional flexible text/slug.
    
- module IDs must be unique within a note.
    
- unknown module types warn on parse and reject on write.
    
- if metadata lists a module but the Markdown section is missing, Phase 1 should warn only.
    

**Example:**

```yaml
scaffold_modules:
  - id: module_sgd_gradient_update_derivation_001
    type: derivation
    title: Gradient Update Formula Derivation
    status: scaffolded
    origin: user_requested
    focus: gradient_update_formula
```

**Derivation module meaning:**  
A `derivation` module is a math/formula-heavy scaffold that explains how a formula, algorithm update, theoretical claim, or mathematical result is derived step by step.

---

### 5.6 Relationship Metadata

**Purpose:**  
Represent structured concept relationships in YAML.

**Fields:**

```yaml
relationship_type:
target_id:
target_title:
vault_status:
```

**Allowed relationship types:**

```text
depends_on
prerequisite_for
related_to
variant_of
parent_of
child_of
contrasts_with
```

**Allowed vault statuses:**

```text
found
missing
unresolved
```

**Meaning of vault statuses:**

```text
found = target concept exists in vault and target_id is known
missing = target concept does not exist yet
unresolved = system has not checked or cannot determine yet
```

**Validation rules:**

- `relationship_type` is required.
    
- `target_title` is required.
    
- `target_id` is optional when target is missing or unresolved.
    
- `vault_status` is required.
    
- Phase 1 validates shape only.
    
- Phase 1 does not validate semantic correctness of the relationship.
    
- Phase 1 does not resolve relationship targets against an index.
    

**Example missing/unresolved target:**

```yaml
relationships:
  - relationship_type: depends_on
    target_id:
    target_title: Chain Rule
    vault_status: unresolved
```

**Example found target:**

```yaml
relationships:
  - relationship_type: depends_on
    target_id: concept_chain_rule_x9y8z7
    target_title: Chain Rule
    vault_status: found
```

---

### 5.7 Validation Result

**Purpose:**  
Return structured validation output.

**Fields:**

```yaml
is_valid:
critical_errors:
warnings:
operation:
```

**Validation result behavior:**

- `critical_errors` block writes.
    
- `warnings` are surfaced but do not always block operations.
    
- `operation` matters because parsing and writing use different strictness.
    

Operations:

```text
parse
create
update
write
```

---

### 5.8 Write Proposal

**Purpose:**  
Represent a file write before it happens.

A `WriteProposal` is a low-level storage primitive, not a user approval UI.

**Fields:**

```yaml
operation:
target_path:
before_content:
after_content:
warnings:
critical_errors:
would_create:
would_update:
would_overwrite:
expected_existing_hash:
```

**Validation rules:**

- write proposals with critical errors cannot be committed
    
- new note creation is blocked if target already exists
    
- update writes should verify that the existing file hash still matches `expected_existing_hash`
    
- proposals are returned as objects in Phase 1, not saved as files
    

---

## 6. Data Flow / System Flow

### Flow 1: Create New Concept Note

```text
Concept title + optional metadata
↓
Generate concept ID
↓
Build ConceptNoteMetadata Pydantic model
↓
Create default learning encounter if no source provided
↓
Create empty scaffold_modules list
↓
Create empty relationships list unless relationships are provided
↓
Generate canonical Markdown section containers
↓
Serialize metadata + Markdown body into full Markdown
↓
Validate generated note
↓
Build WriteProposal
↓
Commit WriteProposal to test vault when called
```

Explanation:

- This flow creates a new Markdown concept note.
    
- It should use canonical YAML key order and canonical Markdown section order.
    
- It should not generate meaningful scaffold content.
    
- It should not require any UI.
    

Possible errors/warnings:

- critical: title missing
    
- critical: generated note missing required metadata
    
- critical: generated note missing canonical sections
    
- critical: target file already exists
    
- warning: concept domains empty
    

---

### Flow 2: Parse Existing Concept Note

```text
Markdown file path
↓
Read raw file content
↓
Separate YAML frontmatter from Markdown body
↓
Parse YAML into raw metadata
↓
Validate metadata with parse-level strictness
↓
Parse Markdown headings/sections
↓
Validate canonical section presence
↓
Return ParsedConceptNote + ValidationResult
```

Explanation:

- Parsing is read-only.
    
- The raw Markdown body should be preserved.
    
- Existing files may contain warnings without being modified.
    

Possible errors/warnings:

- critical: invalid YAML
    
- critical: missing required structural metadata
    
- warning: unknown fields
    
- warning: missing canonical section
    
- warning: unknown concept type
    
- warning: unknown source type
    

---

### Flow 3: Serialize Concept Note

```text
ConceptNoteMetadata model + Markdown body/sections
↓
Convert Pydantic model to YAML-ready dictionary
↓
Apply canonical YAML key order
↓
Render YAML frontmatter
↓
Render Markdown body
↓
Return full Markdown content
```

Explanation:

- Serialization is the reverse of parsing.
    
- Generated notes should use canonical key order.
    
- Existing notes should not be reordered unless explicitly serialized as a proposed update.
    

Possible errors/warnings:

- critical: metadata model invalid
    
- critical: unknown fields during generated/proposed write
    
- warning: optional fields empty
    

---

### Flow 4: Validate Note

```text
Parsed or generated concept note
↓
Select validation mode: parse/create/update/write
↓
Validate required metadata
↓
Validate enum-like values
↓
Validate learning encounters
↓
Validate scaffold modules
↓
Validate relationships
↓
Validate canonical sections
↓
Return critical errors + warnings
```

Explanation:

- Validation strictness depends on operation.
    
- Writes are stricter than reads.
    
- Generated notes should satisfy all required canonical structure.
    

Possible errors/warnings:

- critical: malformed required schema
    
- critical: duplicate scaffold module IDs
    
- critical: multiple primary encounters during write
    
- warning: missing aliases
    
- warning: missing canonical section during parse
    
- warning: concept domains empty
    

---

### Flow 5: Build and Commit Write Proposal

```text
Target path + before content + after content
↓
Validate proposed output
↓
Detect whether operation creates or updates
↓
Detect collision/overwrite risk
↓
Hash existing file if updating
↓
Return WriteProposal
↓
Commit proposal if no critical errors and file hash still matches
```

Explanation:

- Write proposals make file mutation inspectable and safe.
    
- Phase 1 can commit proposals programmatically.
    
- Later UI phases can display proposals for human approval.
    

Possible errors/warnings:

- critical: target path outside vault
    
- critical: target file exists during create
    
- critical: proposal has critical validation errors
    
- critical: existing file changed since proposal generation
    
- warning: proposed note has non-blocking validation warnings
    

---

### Flow 6: CLI Manual Verification

```text
CLI command
↓
Call storage-layer function
↓
Return readable result
```

Commands:

```text
studium create-concept "<title>"
studium validate-note <path>
studium validate-vault <path>
```

Explanation:

- CLI should be thin.
    
- CLI should help manually test Phase 1 without a UI.
    
- CLI should not contain business logic.
    

Possible errors/warnings:

- critical: invalid path
    
- critical: invalid note
    
- warning: missing optional/canonical structure
    

---

## 7. Validation and Error Handling

### Validation Philosophy

Phase 1 should parse permissively but write cautiously.

Read operations should surface errors and warnings without modifying files. Write operations should block on critical errors and allow warnings only when the proposed write remains structurally safe.

Generated notes should be held to a stricter standard than existing parsed notes. If Studium generates a malformed concept note, that is an internal error and should be treated as critical.

### Critical Errors

Critical errors should block writes.

|Issue|Parse Existing Note|Generated/Proposed Write|
|---|---|---|
|Invalid YAML|Critical|Critical|
|Missing `id`|Critical|Critical|
|Missing `schema_version`|Critical|Critical|
|Unsupported `schema_version`|Critical or warning depending on parser tolerance|Critical|
|Missing `note_type`|Critical|Critical|
|`note_type` not `concept`|Critical|Critical|
|Missing `concept_type`|Critical|Critical|
|Missing `canonical_title`|Critical|Critical|
|Missing `learning_encounters`|Critical|Critical|
|Empty `learning_encounters`|Critical|Critical|
|Missing primary encounter|Critical|Critical|
|Multiple primary encounters|Warning or critical|Critical|
|Malformed scaffold module|Warning or critical depending on severity|Critical|
|Duplicate scaffold module IDs|Critical|Critical|
|Malformed relationship entry|Warning or critical depending on severity|Critical|
|Missing generated canonical section|Warning for parsed note|Critical|
|Target path outside vault|Critical|Critical|
|Create operation would overwrite file|Critical|Critical|
|Update proposal has stale file hash|Critical|Critical|

### Warnings

Warnings should be surfaced but should not always block operations.

|Issue|Parse Existing Note|Generated/Proposed Write|
|---|---|---|
|Unknown field|Warning|Critical unless whitelisted|
|Unknown `concept_type`|Warning|Critical unless explicitly allowed|
|Empty `concept_domains`|Warning|Warning|
|Missing aliases|Warning|Warning|
|Empty relationships|Allowed|Allowed|
|Empty scaffold modules|Allowed|Allowed|
|Missing canonical section in existing note|Warning|Critical if generated|
|Unknown source type|Warning|Critical unless explicitly allowed|
|`content_attached: false` for external source|Allowed|Allowed|
|Missing optional source unit fields|Allowed|Allowed|
|Missing Markdown section for listed scaffold module|Warning|Warning|
|Missing `target_id` when `vault_status: missing`|Allowed|Allowed|
|Missing `target_id` when `vault_status: unresolved`|Allowed|Allowed|

### Error Handling Rules

- Parsing should never mutate the file.
    
- Invalid YAML should return a critical error and preserve raw content.
    
- Validation should return structured errors and warnings, not only strings.
    
- Write proposals should include validation results.
    
- Commit should fail if critical errors exist.
    
- Commit should fail if target path is unsafe.
    
- Commit should fail if update hash no longer matches the file on disk.
    
- Warnings should be visible in CLI output.
    

### Recovery / Follow-Up Behavior

- If parsing fails, return raw file content plus critical error where possible.
    
- If validation warns, return parsed note plus warnings.
    
- If write proposal fails, do not write anything.
    
- If commit fails due to stale hash, caller must rebuild the proposal.
    
- If generated note fails validation, treat it as an implementation bug to fix.
    

---

## 8. Write / Mutation Behavior

Phase 1 can create:

- new Markdown concept notes
    
- safe write proposal objects
    
- generated canonical Markdown content
    
- validation results
    
- CLI output
    

Phase 1 can update:

- existing concept note files through write proposals
    
- YAML metadata in proposed replacement content
    
- canonical sections in proposed replacement content when explicitly requested by the storage function
    

Phase 1 should never mutate directly without going through a write proposal.

Write behavior:

- new note creation generates a `WriteProposal`
    
- update operations generate a `WriteProposal`
    
- proposals can be committed only if no critical errors exist
    
- create proposals are blocked if the target file exists
    
- update proposals include an expected existing file hash
    
- commit verifies file hash before writing update content
    

Mutation constraints:

- no real vault writes
    
- no UI approval layer
    
- no version history
    
- no automatic Markdown section reordering for existing notes
    
- no automatic relationship semantic correction
    
- no source ingestion
    
- no scaffold generation
    

---

## 9. Interfaces / APIs / Functions Needed

Exact file names can be decided during branch implementation, but Phase 1 should expose a clear technical surface area.

### Vault Access

**Purpose:**  
Safely read and write Markdown files inside a vault root.

**Likely functions/interfaces:**

```text
read_markdown_file(vault_root, relative_path)
resolve_vault_path(vault_root, relative_path)
write_markdown_file_from_proposal(proposal)
list_markdown_files(vault_root)
```

---

### Markdown Parsing

**Purpose:**  
Separate YAML frontmatter from Markdown body and detect sections.

**Likely functions/interfaces:**

```text
split_frontmatter(raw_markdown)
parse_markdown_sections(markdown_body)
parse_concept_note(raw_markdown)
```

---

### Schema Modeling

**Purpose:**  
Represent structured concept note metadata.

**Likely models:**

```text
ConceptNoteMetadata
LearningEncounter
SourceMetadata
ScaffoldModuleMetadata
RelationshipMetadata
ValidationResult
ValidationIssue
WriteProposal
ParsedConceptNote
```

---

### Serialization

**Purpose:**  
Generate Markdown file content from structured metadata and body sections.

**Likely functions/interfaces:**

```text
serialize_metadata_to_yaml(metadata)
build_canonical_concept_body(title, relationships, scaffold_modules)
serialize_concept_note(metadata, body_markdown)
```

---

### Validation

**Purpose:**  
Validate metadata, sections, relationships, modules, and writes.

**Likely functions/interfaces:**

```text
validate_concept_metadata(metadata, mode)
validate_canonical_sections(parsed_sections, mode)
validate_learning_encounters(encounters, mode)
validate_scaffold_modules(modules, mode)
validate_relationships(relationships, mode)
validate_write_proposal(proposal)
```

---

### Concept Note Creation

**Purpose:**  
Create a valid concept note object and proposed write.

**Likely functions/interfaces:**

```text
generate_concept_id(canonical_title)
slugify_title(title)
create_default_studium_encounter()
build_concept_note_metadata(...)
create_concept_note(...)
```

---

### Write Proposals

**Purpose:**  
Preview and commit file writes safely.

**Likely functions/interfaces:**

```text
build_create_note_proposal(...)
build_update_note_proposal(...)
commit_write_proposal(...)
hash_file_content(content)
```

---

### CLI

**Purpose:**  
Manual verification and future CLI foundation.

**Commands:**

```text
studium create-concept "<title>"
studium validate-note <path>
studium validate-vault <path>
```

---

## 10. Testing Strategy

Phase 1 should be heavily tested because later phases depend on this storage foundation.

### Unit Tests

- concept ID generation
    
- slug generation
    
- YAML frontmatter splitting
    
- invalid YAML detection
    
- metadata model validation
    
- learning encounter validation
    
- scaffold module validation
    
- relationship validation
    
- canonical section detection
    
- serialization to Markdown
    
- write proposal generation
    
- hash/stale-write detection
    

### Integration Tests

- create concept note → write proposal → commit → read back → parse → validate
    
- parse valid fixture note
    
- parse note with external source encounter
    
- parse note with scaffold module metadata
    
- parse note with missing relationship target
    
- update existing note through write proposal
    
- validate full test vault
    

### Fixture / Golden File Tests

Use committed fixture notes and expected outputs.

Potential fixtures:

```text
valid_concept_note.md
studium_origin_concept.md
external_source_concept.md
concept_with_scaffold_modules.md
concept_with_missing_relationship_target.md
concept_with_found_relationship_target.md
invalid_yaml_note.md
missing_required_fields.md
missing_canonical_section.md
duplicate_module_ids.md
```

Golden file tests should cover:

- metadata → expected Markdown output
    
- Markdown fixture → expected parsed metadata/sections
    
- invalid fixture → expected validation result
    

### Manual Verification

Use CLI commands:

```text
studium create-concept "Stochastic Gradient Descent"
studium validate-note <path>
studium validate-vault <path>
```

Manual verification should confirm:

- note file is created in the test vault
    
- YAML frontmatter is readable
    
- Markdown body is Obsidian-compatible
    
- validation results are understandable
    
- warnings and errors are visible
    

### Testing Gaps

- no frontend testing yet
    
- no real vault testing yet
    
- no source ingestion testing yet
    
- no graph/index testing yet
    
- no Agent Review testing yet
    

---

## 11. Technical Concepts to Understand

These concepts may become notes in `Concepts/` as needed.

### YAML Frontmatter

Why it matters:

- stores structured metadata inside Markdown files
    
- keeps notes portable and Obsidian-compatible
    
- gives Studium machine-readable state
    

Likely branches:

- Markdown/frontmatter parsing
    
- schema validation
    
- serialization
    

Essential before implementation: yes.

---

### Pydantic Schema Validation

Why it matters:

- turns raw YAML dictionaries into validated Python objects
    
- enforces required fields and enum-like values
    
- supports structured error handling
    

Likely branches:

- schema models
    
- validation layer
    

Essential before implementation: yes.

---

### Parsing vs Serialization

Why it matters:

- parsing reads Markdown into structured objects
    
- serialization writes structured objects back to Markdown
    
- understanding both prevents destructive file writes
    

Likely branches:

- Markdown parser
    
- serializer
    
- write proposals
    

Essential before implementation: yes.

---

### Safe Write Proposal

Why it matters:

- prevents silent mutation
    
- enables future UI approval workflows
    
- protects against stale updates and overwrites
    

Likely branches:

- write proposal builder
    
- vault write commit behavior
    

Essential before implementation: yes.

---

### Stable IDs

Why it matters:

- concept identity should not depend only on file name or title
    
- future graph/search/review systems need durable IDs
    

Likely branches:

- concept note creation
    
- relationship metadata
    

Essential before implementation: yes.

---

### Golden File Tests

Why it matters:

- storage systems need predictable input/output behavior
    
- Markdown generation/parsing should be regression-tested
    

Likely branches:

- parser tests
    
- serializer tests
    
- fixture testing
    

Essential before implementation: helpful, can be learned during testing branch.

---

## 12. Documentation Updates Expected

Potential updates during or after Phase 1:

-  `Concepts/YAML Frontmatter.md`
    
-  `Concepts/Pydantic Schema Validation.md`
    
-  `Concepts/Parsing vs Serialization.md`
    
-  `Concepts/Safe Write Proposal.md`
    
-  `Concepts/Stable IDs.md`
    
-  `Data Schemas/Concept Note Schema.md`
    
-  `Data Schemas/Learning Encounter Schema.md`
    
-  `Data Schemas/Scaffold Module Schema.md`
    
-  `Data Schemas/Relationship Schema.md`
    
-  `System Models/Concept Note Storage Model.md`
    
-  `Technical Architecture/Storage Architecture.md`
    
-  `Decisions/` ADRs after phase completion
    
-  `Backlog/` for deferred storage improvements
    

Notes:

- ADRs should be finalized after the phase is complete, not before implementation.
    
- Documentation should be updated as needed, not as busywork.
    
- Branch docs remain the main place for branch-level implementation understanding.
    

---

## 13. Architecture Decisions / ADR Candidates

Potential ADRs after Phase 1 completion:

- Use Markdown-compatible vault storage.
    
- Use YAML frontmatter as the metadata source.
    
- Use `note_type: concept` as the only first-class Phase 1 note type.
    
- Use `concept_type` and `concept_domains` instead of `note_subtype`.
    
- Use `learning_encounters` instead of `primary_source`.
    
- Use `studium` as the default source when no external source is attached.
    
- Keep graph visibility derived from vault/review lifecycle rather than stored.
    
- Use Pydantic for schema validation.
    
- Use safe write proposals before file mutation.
    
- Defer SQLite/indexing until Phase 2.
    

Decision notes:

- These should remain candidates until implementation confirms they hold up.
    
- If implementation forces a change, the Technical Plan and ADR candidates should be amended.
    

---

## 14. Risks, Tradeoffs, and Open Technical Questions

### Risks

- Schema may become too rigid too early.
    
- Schema may become too loose and create future migration issues.
    
- `concept_domains` may blur with actual concept notes if not clearly defined.
    
- Markdown parsing may accidentally normalize or alter user content if implemented carelessly.
    
- YAML serialization may reorder or rewrite metadata in ways that are noisy.
    
- Safe write proposals may become too complex if overbuilt.
    
- Relationship types may need refinement in Phase 2.
    
- Canonical sections may need revision after Create/learning-design work.
    

### Tradeoffs

- Pydantic adds structure but requires careful handling of parse-vs-write strictness.
    
- Deferring SQLite keeps Phase 1 focused but means Phase 2 must build indexing cleanly.
    
- Storing domains as flexible strings avoids premature taxonomy design but may require cleanup later.
    
- Removing relationship `role` simplifies Phase 1 but may require richer metadata later.
    
- Keeping CLI minimal avoids overbuilding but limits manual workflows.
    

### Open Technical Questions

- Exact concept ID hash algorithm.
    
- Exact slug normalization rules.
    
- Exact Pydantic configuration for parse vs write modes.
    
- Exact YAML library to use.
    
- Exact Markdown parsing library or lightweight custom parsing approach.
    
- Exact formatting of relationship projections in Markdown.
    
- Whether concept domains should be normalized automatically.
    
- Whether CLI should accept optional metadata flags in Phase 1 or only title.
    
- How much detail validation issues should include: field path, message, severity, suggested fix.
    

---

## 15. Phase-Level Technical Completion Standard

Phase 1 is technically complete when the codebase can create, parse, validate, serialize, and safely write concept notes in a test vault using the Phase 1 metadata schema.

More specifically, it is complete when:

- Pydantic schemas exist for Phase 1 metadata models.
    
- YAML frontmatter can be parsed into structured models.
    
- Markdown bodies can be preserved and section headings detected.
    
- new concept notes can be generated with canonical YAML key order.
    
- new concept notes can be generated with canonical Markdown section order.
    
- concept IDs can be generated in the chosen stable format.
    
- default Studium learning encounters are created when no source is provided.
    
- external source encounters can be stored without attached content.
    
- scaffold module metadata can be validated.
    
- relationship metadata can represent found, missing, and unresolved targets.
    
- validation returns structured critical errors and warnings.
    
- generated notes missing required metadata or canonical sections fail validation.
    
- safe write proposals can be built and committed.
    
- stale update writes are blocked by hash checking.
    
- minimal CLI commands work for create and validation.
    
- automated tests cover valid notes, invalid YAML, missing required fields, missing sections, relationships, scaffold modules, and write proposals.
    

---

## 16. Cursor / Implementation Constraints

These constraints should be passed into Cursor during branch implementation.

Implementation constraints:

- Keep changes scoped to the current branch.
    
- Keep Phase 1 as a pure Python storage layer.
    
- Do not introduce frontend code.
    
- Do not introduce SQLite.
    
- Do not introduce FastAPI unless explicitly approved later.
    
- Do not change schemas without calling it out first.
    
- Do not introduce new architecture patterns without explanation.
    
- Prefer explicit, understandable code over clever abstractions.
    
- Use Pydantic for schema models and validation.
    
- Add or update tests for implemented behavior.
    
- Preserve Markdown body content unless the branch explicitly modifies it.
    
- Generated notes should follow canonical YAML key order.
    
- Generated notes should follow canonical Markdown section order.
    
- Existing notes should not be automatically reordered.
    
- Surface risks or edge cases before implementing them.
    
- If Cursor believes a roadmap or schema assumption is wrong, it should explain before implementing.