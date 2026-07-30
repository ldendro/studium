## 1. Goal

The purpose of this branch is to implement the sparse retrieval aspect of the overall retrieval system, including implementing deterministic and weighted lexical retrieval of note content based on user query. This branch includes the use of weighted SQLite full-text retrieval for concepts and scaffolds modules, which will be reviewed up for further understanding in this document. 

---

## 2. Branch Context

- Mainly involves the sparse retrieval side of the overall retrieval system, so exact ID lookup, normalized title lookup, approved-alias lookup, keyword search, concept overview search, concept-domain search, and scaffold module lexical search. 

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

Phase: 2

Branch: Weighted Full Text Search

Branch goal:
Implement determinstic concept identiy lookup and weighted SQLite full-text retrieval for concepts and scaffold modules to not only incorporate as part of the entire retrieval system but to also utilize as a baseline when implementing the embedding pipeline for retrieval in later branches.

Expected outcome:


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