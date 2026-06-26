# Phase `<number>` Technical Plan: `<Phase Name>`

## 1. Technical Purpose

Explain what this phase needs to establish technically.

This section should answer:

- What technical layer or subsystem is this phase building?
    
- What parts of the roadmap does this technical plan make implementable?
    
- What must be true technically before the next phase can begin?
    

---

## 2. Roadmap Capabilities Being Implemented

List the major capabilities from `00 Phase Roadmap.md` that this technical plan translates into implementation.

Capabilities:

This section should stay high-level. The detailed implementation split belongs in `02 Branch Plan.md`.

---

## 3. Technical Scope

Define the technical boundaries of this phase.

### Included

This phase technically includes:

### Excluded

This phase technically excludes:

Excluded items should usually become future phase work, backlog items, or future enhancements.

---

## 4. System Components Introduced or Modified

List the major technical components this phase introduces or changes.

Examples:

- vault file reader
    
- Markdown parser
    
- YAML frontmatter parser
    
- concept note serializer
    
- schema validator
    
- write proposal builder
    
- graph indexer
    
- search service
    
- source ingestion pipeline
    
- review comment engine
    

Components:

### `<Component Name>`

**Purpose:**

**Responsibilities:**

**Inputs:**

**Outputs:**

**Notes / Constraints:**

---

## 5. Data Models and Schemas

Define the data structures this phase introduces or modifies.

This section should include enough detail that the implementation can be planned safely.

### 5.1 `<Schema / Model Name>`

**Purpose:**

**Used by:**

**Fields:**

```yaml
field_name:
field_name:
field_name:
```

**Required fields:**

**Optional fields:**

**Validation rules:**

**Example:**

---

## 6. File and Folder Structure

Describe any expected project, vault, fixture, or generated-file structure.

### Application / Repo Structure

```text
<path>/
  <file>
  <folder>/
```

### Vault Structure

```text
<test_vault>/
  <folder>/
  <file>.md
```

### Test Fixture Structure

```text
tests/
  fixtures/
    <fixture>
```

Notes:

---

## 7. Data Flow / System Flow

Describe the main technical flow enabled by this phase.

Use simple diagrams.

### Flow 1: `<Flow Name>`

```text
Input
↓
Component/action
↓
Validation/check
↓
Output
```

Explanation:

### Flow 2: `<Flow Name>`

```text
Input
↓
Component/action
↓
Output
```

Explanation:

---

## 8. Validation and Error Handling

Define how this phase handles invalid input, malformed data, failed operations, and warnings.

### Critical Errors

Critical errors should block the operation.

Examples:

### Warnings

Warnings should be surfaced but should not always block the operation.

Examples:

### Error Handling Rules

---

## 9. Write / Mutation Behavior

Describe how this phase changes files, data, metadata, indexes, or app state.

This section should answer:

- What can this phase create?
    
- What can this phase update?
    
- What should never be mutated directly?
    
- Are writes direct, proposal-first, staged, or approval-based?
    
- What protects against accidental corruption?
    

Write behavior:

Mutation constraints:

---

## 10. Interfaces / APIs / Functions Needed

List the important functions, services, interfaces, or APIs the phase likely needs.

This is not the final implementation plan, but it should define the expected technical surface area.

### `<Function / Service / Interface Name>`

**Purpose:**

**Input:**

**Output:**

**Used by:**

**Notes:**

---

## 11. Testing Strategy

Define how this phase should be tested.

### Unit Tests

### Integration Tests

### Fixture / Golden File Tests

### Manual Verification

### Testing Gaps

---

## 12. Technical Concepts to Understand

List broader technical concepts needed to implement this phase confidently.

These may become notes in `Concepts/`.

Concepts:

- `[[Concept Name]]`
    
- `[[Concept Name]]`
    
- `[[Concept Name]]`
    

For each concept, answer:

- Why does this concept matter for this phase?
    
- Which branch will likely require it?
    
- Is it essential before implementation, or can it be learned during the branch?
    

---

## 13. Documentation Updates Expected

List documentation that may need to be created or updated during this phase.

Potential updates:

-  `Concepts/`
    
-  `Data Schemas/`
    
-  `System Models/`
    
-  `Agent Behavior/`
    
-  `UI UX/`
    
-  `Technical Architecture/`
    
-  `Decisions/`
    
-  `Backlog/`
    

Notes:

---

## 14. Architecture Decisions / ADR Candidates

List technical decisions that may deserve an ADR.

ADR candidates:

Decision notes:

---

## 15. Risks, Tradeoffs, and Open Technical Questions

### Risks

### Tradeoffs

### Open Technical Questions

These questions should be resolved before or during branch planning.

---

## 16. Phase-Level Technical Completion Standard

This phase is technically complete when:

This should be more technical than the roadmap completion standard.

Example:

```text
Phase 1 is technically complete when the codebase can create, parse, validate, serialize, and safely write concept notes in a test vault using the Phase 1 metadata schema, with automated tests covering valid notes, invalid YAML, missing sections, relationships, and write proposals.
```

---

## 17. Cursor / Implementation Constraints

These constraints should be passed into Cursor during branch implementation.

Implementation constraints:

- Keep changes scoped to the current branch.
    
- Do not change schemas without calling it out first.
    
- Do not introduce new architecture patterns without explanation.
    
- Prefer explicit, understandable code over clever abstractions.
    
- Add or update tests for implemented behavior.
    
- Preserve Markdown content unless the branch explicitly modifies it.
    
- Surface risks or edge cases before implementing them.
    

Additional phase-specific constraints: