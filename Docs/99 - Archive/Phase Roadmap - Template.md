## 1. Purpose

Explain the purpose of this phase in 2–5 sentences.

This section should answer:

- What is this phase introducing?
    
- Why does this phase exist?
    
- What new capability does Studium gain after this phase?
    

---

## 2. Phase Outcome

By the end of this phase, Studium should be able to:

This should describe the user/system capability gained, not the low-level implementation.

---

## 3. Why This Phase Comes Now

Explain why this phase belongs here in the roadmap.

This section should answer:

- What previous capabilities does this phase depend on?
    
- What future phases depend on this phase?
    
- Why can’t this phase be skipped or delayed?
    

---

## 4. Core Principles for This Phase

List the principles that should guide this phase.

Examples:

- Preserve Obsidian-compatible Markdown.
    
- Do not mutate user notes without approval.
    
- Keep intelligence separate from storage when appropriate.
    
- Prefer explicit schemas over hidden assumptions.
    
- Build only the foundation needed for later phases.
    

Principles:

---

## 5. Core Features / Capabilities Introduced

This is the main body of the roadmap.

Each major feature or capability introduced in this phase should get its own subsection.

The goal is to explain the core functionality clearly enough that the Technical Plan and Branch Plan can later be derived from it.

---

### 5.1 `<Feature / Capability Name>`

Explain what this feature does and why it matters.

This feature should support:

Important behavior:

Important constraints:

Example:

```text
Vault File Reading allows Studium to safely discover and read Markdown files from an Obsidian-compatible vault. This is necessary before the system can parse notes, validate schemas, build indexes, or propose updates.
```

---

### 5.2 `<Feature / Capability Name>`

Explain what this feature does and why it matters.

This feature should support:

Important behavior:

Important constraints:

---

### 5.3 `<Feature / Capability Name>`

Explain what this feature does and why it matters.

This feature should support:

Important behavior:

Important constraints:

---

## 6. Key System Behaviors

Summarize the important behaviors the system must support by the end of the phase.

These can overlap with the feature sections, but this section should make the expected behavior easy to scan.

Behaviors:

---

## 7. Data and State Introduced

Describe any durable data, metadata, statuses, schemas, IDs, or files introduced in this phase.

This may include:

- note metadata
    
- schema fields
    
- status fields
    
- IDs
    
- relationships
    
- source references
    
- generated files
    
- local database records
    
- review artifacts
    

Data/state introduced:

Full schema details can later live in `Data Schemas/` or `01 Technical Plan.md`.

---

## 8. User/System Workflow

Describe the main workflow enabled by this phase.

```text
Input
↓
System action
↓
Validation/check
↓
Output
```

Workflow:

```text
<step>
↓
<step>
↓
<step>
```

---

## 9. Scope of This Phase

This phase includes:

This should define the functional boundary of the phase.

---

## 10. Non-Goals

This phase does not include:

Non-goals prevent the phase from expanding too much during implementation.

---

## 11. Relationship to Other Phases

### Depends On

### Enables

### Later Phase Dependencies

- Phase `<number>` depends on this because...
    
- Phase `<number>` depends on this because...
    

---

## 12. Risks and Design Concerns

List the main risks, ambiguities, or design concerns for this phase.

Risks:

---

## 13. Phase Decisions / Amendments

Capture important decisions made while refining the phase.

This is especially important when later phases changed assumptions from the original roadmap.

Decisions/amendments:

If a decision is foundational and long-lived, create or update an ADR in `Decisions/`.

---

## 14. Expected Outputs

List the artifacts or system capabilities that should exist when the phase is done.

Expected outputs:

- ## working code:
    
- ## documentation:
    
- ## schemas/models:
    
- ## tests/fixtures:
    

---

## 15. Completion Standard

Phase `<number>` is complete when:

Example:

```text
Phase 1 is complete when Studium can read, parse, validate, and safely propose writes for Obsidian-compatible concept notes using the current metadata model, without corrupting Markdown content.
```

---

## 16. Use Cases / Criteria-Met Scenarios

These use cases should verify that the roadmap has been satisfied.

### UC-01: `<Use Case Name>`

**Scenario:**

**Expected behavior:**

**Criteria met:**

---

### UC-02: `<Use Case Name>`

**Scenario:**

**Expected behavior:**

**Criteria met:**

---

### UC-03: `<Use Case Name>`

**Scenario:**

**Expected behavior:**

**Criteria met:**

---

## 17. Future Enhancements

List ideas related to this phase that should not be implemented now.

Future enhancements:

---

## 18. Open Questions

List unresolved questions that must be answered before or during technical planning.

Open questions: