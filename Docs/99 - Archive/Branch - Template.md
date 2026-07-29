## 1. Goal

Describe the purpose of this branch in 2–4 sentences.

This branch exists to:

At the end of this branch, the system should be able to:

---

## 2. Branch Context

This section should be written before Cursor creates the detailed implementation plan.

### Main System Area

This branch primarily affects:

-  Vault storage
    
-  Markdown parsing
    
-  Data schemas
    
-  Concept graph
    
-  Search
    
-  Create workflow
    
-  Source intelligence
    
-  Agent behavior
    
-  UI / UX
    
-  Testing infrastructure
    
-  Developer tooling
    
-  Other:
    

### Branch Dependencies

This branch depends on:

### Risks / Things to Watch

Potential issues, tradeoffs, or fragile areas:

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

Phase:

Branch:

Branch goal:
<branch goal>

Expected outcome:
<what the system should be able to do after this branch>

Relevant context:
<briefly paste or summarize relevant details from the Phase Roadmap, Technical Plan, Branch Plan, schemas, system models, or prior branches>

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

Paste or summarize Cursor’s implementation plan here before implementation begins.

### Proposed Approach

### Files Likely Touched

### Implementation Sequence

### Data Model / Schema Changes

### Important Functions / Classes / Modules

### Tests / Verification Proposed

### Risks, Edge Cases, or Assumptions

### Questions Before Implementation

### Plan Review Notes

My notes after reviewing Cursor’s plan:

### Approved to Implement?

-  Yes
    
-  No, revise plan first
    

---