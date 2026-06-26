# Branch: `<branch-name>`

## Branch Summary

**Phase:** `<Phase number and name>`  
**Branch:** `<branch number and name>`  
**Status:** `planned | in_progress | implemented | reviewed | merged`

---

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
<phase number and name>

Branch:
<branch number and name>

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

## 6. Implementation Notes

Complete this during or immediately after implementation.

### Files Changed

### New Files Added

### Important Functions / Classes / Modules Added or Changed

### Data Model or Schema Changes

### UI Changes

### Agent Behavior Changes

### Other Important Changes

---

## 7. Code Understanding

Complete this after the implementation satisfies the branch goal.

The purpose of this section is not to document every line of code.  
The purpose is to prove that I understand the implementation well enough to move on.

### Main Implementation Flow

Explain the main flow in my own words.

### Key Files and Responsibilities

- `<file>` —
    
- `<file>` —
    
- `<file>` —
    

### Important Logic I Need to Understand

Explain the parts of the implementation that are most important, non-obvious, or easy to misunderstand.

### Key Design Decisions

What implementation choices matter for future branches?

### How This Branch Fits the Phase

Explain how this branch moves the current phase closer to completion.

---

## 8. Tests and Verification

### Automated Checks

-  Ruff
    
-  Pyright
    
-  pytest
    
-  coverage
    
-  frontend tests, if applicable
    
-  other:
    

### Tests Added or Updated

### Manual Verification

Steps used to verify this branch manually:

### Verification Result

### Testing Gaps / Follow-Up

Anything not tested yet that should be remembered:

---

## 9. Branch Reflection

Write this after implementation.

### What I Learned

### What Was Confusing

### What I Would Improve Later

### Follow-Up Backlog Items

Add these to the appropriate Backlog file if they should not be handled in this branch.

### Documentation Updates Needed

-  Concepts
    
-  Data Schemas
    
-  System Models
    
-  Agent Behavior
    
-  UI UX
    
-  Technical Architecture
    
-  Backlog
    
-  Decisions / ADRs
    
-  None
    

Notes:

---

## 10. Final Branch Summary

Short final summary after the branch is complete:

```text
This branch added <summary>. It changed <main files/areas>. The main implementation flow is <brief explanation>. It was verified by <tests/manual checks>. Remaining follow-ups are <items or none>.
```