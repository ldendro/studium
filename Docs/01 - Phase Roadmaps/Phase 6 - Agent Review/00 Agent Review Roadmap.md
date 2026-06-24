## Purpose

Build the quality-control layer of Studium.

Phase 6 introduces Agent Review: a structured review system that analyzes completed or partially completed concept notes, identifies weaknesses, proposes improvements, and gates whether a note is ready to become an accepted concept in the main learning vault.

This phase answers:

> Is this concept note good enough to become part of my trusted learning system?

Agent Review should not replace the user’s judgment. It should function like an expert reviewer that leaves precise comments, proposes improvements, and helps the user revise the note until it is strong enough to submit.

---

## Why This Phase Comes Here

Agent Review comes after Create and Source Content Intelligence because it depends on the previous learning workflow.

Phase 4 creates and edits scaffolded concept notes.

Phase 5 makes those notes source-aware.

Phase 6 reviews those notes before they become accepted knowledge.

After Phase 6, Studium has the core loop needed for real personal use:

```text
Search
↓
Create scaffold
↓
Use source intelligence
↓
Fill note
↓
Agent review
↓
Accept into main vault
```

This phase is the last core phase before initializing the real learning vault for ongoing use.

---

## Core Principle

The system investigates and critiques.  
The user decides and approves.

Agent Review should:

```text
review notes
identify issues
leave anchored comments
propose patches
suggest missing modules
check relationships
check source fidelity
aggregate readiness
block acceptance on critical issues
```

Agent Review should not:

```text
silently rewrite notes
silently accept notes
silently mutate the graph
silently overwrite accepted content
replace user judgment
```

---

## Draft vs Accepted Notes

During development, one vault directory may be used, but note state should be distinguished through metadata.

Draft notes may exist in the vault, but they should not appear in the accepted concept graph.

Accepted notes appear in Search and graph visualization.

Example draft metadata:

```yaml
status: in_progress
review_status: not_submitted
vault_status: draft
graph_visibility: hidden
retention_status: not_started
mastery_status: unassessed
```

Example accepted metadata:

```yaml
status: accepted
review_status: approved
vault_status: accepted
graph_visibility: visible
retention_status: not_started
mastery_status: unassessed
```

Important distinction:

```text
accepted means the note is trusted enough to enter the learning vault.
accepted does not mean the user has mastered the concept.
```

Retention and Mastery are handled by later phases.

---

## Search Graph Visibility Rule

Only accepted/submitted concept notes should populate the Search graph by default.

Draft notes should remain accessible through a Drafts view, but they should not appear as stable nodes in the graph.

Rules:

```text
draft / in_progress / needs_revision:
hidden from accepted graph

accepted / approved:
visible in accepted graph
```

For accepted notes with pending updates:

```text
current accepted version remains visible
pending update remains staged
graph does not change until update is reviewed and accepted
```

---

## Drafts View

Phase 6 should include or prepare a simple Drafts view.

This allows unfinished notes to remain accessible without polluting the accepted concept graph.

Drafts may include notes with statuses such as:

```text
scaffolded
in_progress
ready_for_review
needs_revision
approved_with_suggestions
```

Draft list example:

```text
Drafts:
- Stochastic Gradient Descent — in_progress
- Backpropagation — needs_revision
- Regularization — ready_for_review
```

The Drafts view should allow the user to reopen a note, continue editing, submit for review, or review previous comments.

---

## Review Requirement Before Acceptance

A note cannot be marked accepted until it has completed at least one Agent Review.

Acceptance requires:

```text
at least one review completed
zero unresolved critical findings
essential module coverage satisfied
user explicitly submits/accepts
```

The user can save drafts freely, but cannot accept a note into the main learning vault until these conditions are met.

---

## Review Statuses

Agent Review should use clear statuses instead of numeric scores.

Global review statuses:

```text
not_submitted
ready_for_review
in_review
needs_revision
approved_with_suggestions
approved
```

Severity levels for findings:

```text
critical
recommended
optional
```

Meaning:

```text
critical:
blocks acceptance

recommended:
does not block acceptance, but should probably be addressed

optional:
nice-to-have improvement
```

Avoid numeric scores in Phase 6.

---

## Note Lifecycle Statuses

Note lifecycle status should remain separate from review status.

Possible note statuses:

```text
scaffolded
in_progress
accepted
```

Possible vault statuses:

```text
draft
accepted
```

Possible future learning statuses:

```text
retention_status: not_started
mastery_status: unassessed
```

These statuses should not be collapsed into one field.

---

## Essential Module Coverage

Agent Review should check whether the note contains enough scaffold coverage for the concept subtype.

The user should not be able to accept a concept note that defers essential scaffold modules.

Default required/recommended modules should be based on concept subtype.

Example:

```text
ml_concept:
essential:
- conceptual_explanation
- worked_example

recommended:
- code_implementation
- implementation_notes
- comparison
```

```text
mathematical_concept:
essential:
- conceptual_explanation
- worked_example

recommended:
- derivation
- application
```

```text
programming_concept:
essential:
- conceptual_explanation
- code_implementation

recommended:
- worked_example
- implementation_notes
- misconception_debugging
```

The subtype templates should provide rule-based defaults.

The review agent may recommend adjustments when a specific concept requires different coverage.

Missing essential modules should be treated as critical findings.

---

## Review Architecture

Phase 6 should use a hybrid review system:

```text
rule-based preflight checks
↓
specialized module review agents
↓
source fidelity review
↓
graph / relationship review
↓
rule-based aggregation
↓
anchored comments and proposed patches
↓
user approval / rejection
```

This balances accuracy, efficiency, and cost.

Rule-based checks should handle deterministic validation.

Agents should focus on conceptual and qualitative review.

---

## Rule-Based Preflight Checks

Before agent review, Studium should run deterministic checks.

Rule-based checks may include:

```text
metadata schema validity
required fields present
status consistency
review_status consistency
vault_status consistency
graph_visibility consistency
module IDs unique
module metadata valid
source references valid
citation references resolve to source records
relationship target IDs valid
relationship duplicates
broken internal links
Markdown structure valid
module index matches headings
essential module coverage by subtype
```

This reduces latency and lets review agents focus on conceptual quality.

---

## Specialized Review Agents

Phase 6 should use specialized review agents by module or review type.

Initial agent list:

```text
conceptual_explanation_review_agent
worked_example_review_agent
code_implementation_review_agent
implementation_notes_review_agent
comparison_review_agent
derivation_review_agent
application_review_agent
misconception_debugging_review_agent
source_fidelity_review_agent
graph_relationship_review_agent
```

These agents may be implemented using prompt engineering at first and later improved through specialized models or fine-tuning.

Specialization enables:

```text
smaller contexts
more accurate review
parallel execution
module-specific feedback
better latency when run concurrently
easier future optimization
```

---

## Parallel Module Review

Module reviews should be capable of running in parallel.

Example:

```text
Conceptual Explanation module → conceptual explanation review agent
Worked Example module → worked example review agent
Code Implementation module → code implementation review agent
Comparison module → comparison review agent
```

Benefits:

```text
faster wall-clock time
focused agent prompts
lower per-agent context load
easier retry if one review fails
more precise comments
```

If parallel execution is not available at first, the architecture should still be designed around independent module review results.

---

## Module-Aware Review

Agent Review should review notes at the scaffold-module level.

For each module, the review should inspect:

```text
completion
clarity
conceptual correctness
whether the user’s filled responses demonstrate understanding
whether prompts were answered meaningfully
whether examples/calculations are correct
whether module purpose is fulfilled
whether module should be revised, expanded, or split
```

Review output should be module-specific.

Example:

```text
Worked Example: Manual SGD Update
- critical: Step 3 uses the wrong gradient sign.
- recommended: Add one sentence explaining what the update changed.
```

Blank or mostly untouched modules should be reviewed structurally, but not deeply reviewed conceptually.

If an essential module is blank, acceptance should be blocked.

---

## Source Fidelity Review

For source-grounded notes, Agent Review should include a source fidelity pass.

This review should check only the cited or attached source references relevant to the note. It should not re-analyze the entire source.

Source fidelity review should verify:

```text
source-supported claims are actually supported
citations point to relevant source passages
source-grounded modules do not misrepresent the source
unsupported claims are labeled as agent/user additions
important source references are not broken
```

This acts as an agent checking another agent’s source support.

If a citation does not support the claim it is attached to, that should be a critical finding.

---

## Graph and Relationship Review

Agent Review should include graph/relationship review before acceptance.

This review should check:

```text
relationship type correctness
relationship direction correctness
prerequisite vs variant distinction
parent/child relationship correctness
related concepts are not mislabeled as prerequisites
approved relationships only
missing obvious prerequisites
draft relationship targets are not treated as accepted graph nodes
```

Example issue:

```text
Batch Gradient Descent is marked as a prerequisite for Gradient Descent.
```

Possible review finding:

```text
recommended:
Batch Gradient Descent appears to be a variant/related concept, not a prerequisite.
```

Incorrect relationship direction or misleading prerequisite links may be critical if they would corrupt the graph.

---

## Aggregated Readiness Assessment

The final review summary should be mostly rule-based aggregation.

It should aggregate:

```text
rule-based preflight results
module review results
source fidelity results
graph relationship results
unresolved critical findings
missing essential modules
```

The aggregator should assign one of:

```text
needs_revision
approved_with_suggestions
approved
```

The aggregator should not be a heavy agent by default.

Readiness logic:

```text
critical findings present → needs_revision
missing essential modules → needs_revision
no critical findings + recommended findings → approved_with_suggestions
no critical/recommended findings → approved
```

The user still explicitly decides when to accept the note, but acceptance is blocked while critical findings remain unresolved.

---

## Anchored Review Comments

Review comments should live outside the Markdown body.

They should be anchored to the part of the note they critique.

Accepted changes modify the Markdown.

Rejected comments are dismissed or archived.

Review comment anchors should support precise targeting.

Preferred anchor model:

```yaml
review_comment:
  id: comment_001
  target:
    module_id: module_sgd_conceptual_explanation_001
    block_id: block_014
    start_offset: 42
    end_offset: 96
    display_location:
      line_start: 83
      line_end: 85
  severity: critical
  message: "This statement incorrectly describes SGD as using the full dataset gradient."
  proposed_patch: "SGD estimates the gradient using one example or a mini-batch rather than the full dataset."
  status: open
```

Primary anchor:

```text
block ID + text range
```

Fallback/display anchor:

```text
line numbers, heading, or module location
```

This enables Google Docs-style review comments without cluttering the Markdown note.

---

## Review Comment UI

The review UI should feel like comments in a document editor.

Expected behavior:

```text
agent highlights text, paragraph, module, metadata field, or relationship
comment appears in margin
user can accept, reject, edit, or ask agent to revise
```

User actions:

```text
Accept suggested change
Reject comment
Edit proposed change before applying
Ask agent to revise suggestion
Resolve comment manually
Re-run review
```

Accepted comments with patches should update the Markdown or metadata.

Rejected comments should be dismissed or archived outside the note body.

---

## Structured Proposed Changes

Agent Review should produce structured proposed changes, not just freeform feedback.

Possible proposed changes:

```text
replace text
add missing explanation
remove misleading statement
add worked example step
revise calculation
add relationship
remove relationship
change relationship type
add source citation
remove unsupported citation
add scaffold module
revise module title
update metadata field
```

All proposed changes require user approval.

---

## Iterative Review Loop

Agent Review should support multiple review cycles.

Workflow:

```text
User submits note for review
↓
Agent Review returns comments and readiness status
↓
User accepts/rejects/edits suggestions
↓
User may re-run review
↓
Review repeats until note has no critical findings
↓
User accepts note into vault
```

A note must be reviewed at least once before acceptance.

The user may review multiple times before accepting.

---

## Review History

Review history should be stored for traceability and iteration.

The purpose of review history is to answer:

```text
What did the agent flag last time?
Did the user fix the issue?
Why did this note move from needs_revision to accepted?
Which modules have been reviewed?
When was this note last reviewed?
```

Review metadata can live in the concept note:

```yaml
review_status: approved
last_review_id: review_003
review_count: 3
```

Full review artifacts/comments should live outside the Markdown body.

Example location:

```text
/_studium_reviews/concept_stochastic_gradient_descent/review_003.json
```

or equivalent app metadata storage.

Older reviews should be accessible if needed but should not clutter the normal writing experience.

---

## Accepting a Note

A note can be accepted only when:

```text
at least one Agent Review has completed
there are zero unresolved critical findings
essential module coverage is satisfied
the user explicitly accepts/submits the note
```

When accepted:

```yaml
status: accepted
review_status: approved
vault_status: accepted
graph_visibility: visible
retention_status: not_started
mastery_status: unassessed
```

Accepted notes become visible in Search and the accepted concept graph.

Acceptance does not mean mastery.

---

## Updating Accepted Notes

If a user modifies an already accepted note, the accepted version should remain stable until the update is reviewed and accepted.

Workflow:

```text
Accepted note exists
↓
User adds new module or proposes changes
↓
Pending update is staged
↓
Only pending update is reviewed
↓
If accepted, update is applied to accepted note
↓
Previous accepted version is archived
```

Graph updates should not appear until the staged update is accepted.

This prevents unreviewed relationships or modules from polluting the accepted graph.

---

## Lightweight Version History

Phase 6 should include lightweight version history for accepted notes.

Version history should preserve:

```text
previous accepted version
accepted update timestamp
review ID that approved update
summary of changes
```

Example:

```yaml
accepted_versions:
  - version: 1
    accepted_at:
    review_id: review_001
  - version: 2
    accepted_at:
    review_id: review_004
    change_summary: "Added Learning Rate Schedule module."
```

Full Git-like version control is not required in Phase 6.

---

## Integration With Create

Agent Review should integrate with Create.

Review may suggest:

```text
add missing scaffold module
generate better worked example
add misconception debugging module
revise comparison module
add source-supported relationship
```

The user should be able to route those suggestions back to Create.

Example:

```text
Review finding:
This concept lacks a worked example module.

User action:
Generate recommended module

Result:
Create opens with concept and suggested module context.
```

Create handles generation and editing.

Agent Review handles evaluation.

---

## Code Review Boundary

Phase 6 should not execute code or run test cases yet.

For `code_implementation` modules, review should be static/conceptual.

It may check:

```text
clear logic
obvious syntax issues
conceptual correctness
whether code matches explanation
missing edge cases
missing tests/prompts
```

Future enhancements may include:

```text
running code
validating outputs
visual algorithm execution
interactive algorithm tracing
NeetCode-style step-by-step visualizations
ML training loop visualizations
tensor shape tracing
gradient flow visualization
```

These are valuable but outside Phase 6 v1.

---

## Main Vault Readiness Milestone

After Phase 6, Studium should be ready to initialize the real main learning vault.

This does not mean every later feature is complete.

It means the core loop is safe enough for personal use:

```text
create scaffold
fill note
review note
accept note
search accepted concepts
```

Later phases add:

```text
Backlog
Retention
Mastery Dashboard
Personal Learning Model
Productization
```

Phase 6 is the last core roadmap phase before real vault usage begins.

---

## Build Work

Implement Agent Review.

This should include:

- review submission flow
    
- draft visibility rules
    
- accepted graph visibility rules
    
- Drafts view
    
- review status metadata
    
- vault status metadata
    
- retention/mastery placeholder statuses
    
- rule-based preflight checks
    
- essential module coverage checks
    
- specialized module review agents
    
- parallel module review support
    
- source fidelity review agent
    
- graph relationship review agent
    
- rule-based readiness aggregator
    
- severity levels
    
- anchored review comments
    
- precise text-range comment anchors
    
- proposed patch structure
    
- comment margin UI
    
- accept/reject/edit comment actions
    
- iterative re-review
    
- review history storage
    
- acceptance gating
    
- accepted note metadata update
    
- staged update workflow for accepted notes
    
- lightweight accepted-version history
    
- Create handoff for suggested modules
    
- static review for code implementation modules
    

---

## Phase 6 Use Cases

These use cases should be used as implementation checkpoints.

### UC-01: Submit Completed Concept Note for Review

Input:

```text
Concept note: Stochastic Gradient Descent
Status: in_progress
```

Expected behavior:

- user submits note for Agent Review
    
- rule-based preflight runs
    
- module-specific agents review modules
    
- source/graph reviews run if applicable
    
- aggregated readiness status is returned
    

---

### UC-02: Rule-Based Preflight Catches Metadata Error

Input:

```text
Concept note has duplicate module IDs.
```

Expected behavior:

- rule-based preflight catches duplicate IDs
    
- finding is marked critical
    
- model review does not need to spend tokens identifying it
    
- acceptance is blocked
    

---

### UC-03: Missing Essential Module Blocks Acceptance

Input:

```text
Concept: SGD
Subtype: ml_concept
Modules:
- Conceptual Explanation only
```

Expected behavior:

- essential module coverage check detects missing worked example
    
- critical finding is created
    
- note cannot be accepted until resolved or coverage rule is changed with justification
    

---

### UC-04: Parallel Module Review

Input:

```text
Concept note contains:
- Conceptual Explanation
- Worked Example
- Code Implementation
```

Expected behavior:

- each module can be reviewed independently
    
- specialized agents run in parallel if available
    
- results are aggregated into one review summary
    

---

### UC-05: Module-Level Conceptual Error

Input:

```text
Worked example uses wrong gradient sign.
```

Expected behavior:

- worked example review agent flags issue
    
- finding is critical
    
- comment anchors to the exact text/range
    
- proposed correction is generated
    

---

### UC-06: Google-Docs-Style Comment

Agent flags:

```text
“SGD computes the full gradient over the dataset.”
```

Expected behavior:

- exact phrase is highlighted
    
- margin comment explains issue
    
- proposed patch is available
    
- user can accept, reject, edit, or ask agent to revise
    

---

### UC-07: User Accepts Proposed Patch

Input:

```text
User accepts proposed replacement text.
```

Expected behavior:

- Markdown content is updated
    
- comment is resolved
    
- review artifact records accepted change
    

---

### UC-08: User Rejects Proposed Patch

Input:

```text
User rejects proposed change.
```

Expected behavior:

- Markdown is unchanged
    
- comment is dismissed or archived
    
- if finding was critical, acceptance may remain blocked unless resolved another way
    

---

### UC-09: User Edits Proposed Patch Before Applying

Input:

```text
User edits replacement text then applies it.
```

Expected behavior:

- edited patch updates Markdown
    
- comment resolves
    
- review history records user-modified application
    

---

### UC-10: Re-Run Review After Revisions

Input:

```text
User applies fixes and re-runs Agent Review.
```

Expected behavior:

- new review is created
    
- previous review remains in history
    
- unresolved issues are rechecked
    
- readiness status updates
    

---

### UC-11: Source Fidelity Review

Input:

```text
Source-grounded module cites Hands-On ML, Chapter 4.
```

Expected behavior:

- source fidelity agent checks cited chunks only
    
- unsupported citation is flagged if claim is not supported
    
- unsupported source claim can block acceptance
    

---

### UC-12: Graph Relationship Review

Input:

```text
Gradient Descent note proposes Batch Gradient Descent as prerequisite.
```

Expected behavior:

- graph review agent flags likely incorrect relationship type
    
- suggests variant/related relationship instead
    
- user approves or rejects relationship change
    

---

### UC-13: Review Suggests New Scaffold Module

Input:

```text
Concept note lacks useful worked example.
```

Expected behavior:

- review recommends new worked example module
    
- user can route suggestion back to Create
    
- Create generates module proposal
    
- new module requires review before note can be accepted
    

---

### UC-14: Partial Note Reviewed But Not Accepted

Input:

```text
Note has several blank essential modules.
```

Expected behavior:

- review can still run
    
- blank modules are structurally reviewed
    
- conceptual review is skipped for blank content
    
- acceptance is blocked
    

---

### UC-15: Approved With Suggestions

Input:

```text
No critical findings, but several recommended improvements.
```

Expected behavior:

- readiness status becomes approved_with_suggestions
    
- user may accept note or address suggestions first
    
- accepted status is allowed because no critical findings remain
    

---

### UC-16: Accepted Note Becomes Searchable

Input:

```text
User accepts reviewed note.
```

Expected behavior:

- metadata updates to accepted
    
- graph_visibility becomes visible
    
- note appears in Search graph
    
- retention_status remains not_started
    
- mastery_status remains unassessed
    

---

### UC-17: Draft Note Hidden From Search Graph

Input:

```text
Note status: in_progress
Vault status: draft
```

Expected behavior:

- note remains accessible in Drafts
    
- note does not appear in accepted concept graph
    

---

### UC-18: Existing Accepted Note Gets Staged Update

Input:

```text
Accepted SGD note
User adds Learning Rate Schedules module
```

Expected behavior:

- accepted version remains visible
    
- new module is staged
    
- graph does not update yet
    
- staged update requires review
    

---

### UC-19: Accepted Update Applies New Version

Input:

```text
Staged module update is reviewed and accepted.
```

Expected behavior:

- accepted note is updated
    
- previous accepted version is archived
    
- version history records update
    
- graph updates if relationships changed
    

---

### UC-20: Code Implementation Static Review

Input:

```text
Code implementation module contains Python/PyTorch scaffold.
```

Expected behavior:

- code review agent performs static/conceptual review
    
- no code execution occurs
    
- future visual execution is not part of Phase 6
    

---

### UC-21: Review History Stored

Input:

```text
Note reviewed three times.
```

Expected behavior:

- latest review is shown by default
    
- previous review artifacts are stored
    
- review_count and last_review_id update
    

---

### UC-22: Critical Finding Blocks Acceptance

Input:

```text
Unresolved critical finding remains open.
```

Expected behavior:

- Accept note action is disabled or blocked
    
- user must resolve, reject with justification if allowed, or re-review
    

---

## Outputs

By the end of this phase, Studium should be able to:

- submit notes for Agent Review
    
- run rule-based preflight checks
    
- review notes by scaffold module
    
- run specialized review agents
    
- run module reviews in parallel when possible
    
- check source fidelity for cited content
    
- review graph relationships and prerequisites
    
- aggregate review results without a heavy summary agent
    
- create anchored review comments
    
- show Google Docs-style comment UI
    
- propose structured patches
    
- allow users to accept, reject, or edit proposed changes
    
- re-run reviews iteratively
    
- require at least one review before acceptance
    
- block acceptance on critical findings
    
- block acceptance on missing essential module coverage
    
- keep drafts out of accepted graph
    
- make accepted notes visible in Search
    
- stage updates to accepted notes
    
- maintain lightweight version history
    
- prepare main learning vault usage
    

---

## Success Criteria

Phase 6 is successful when Studium can act as a quality gate between draft notes and accepted learning knowledge.

The user should be able to:

- submit a concept note for review
    
- receive module-specific review comments
    
- see exact text ranges highlighted
    
- accept, reject, or edit proposed improvements
    
- re-run review after revision
    
- pass source-grounded content through citation fidelity checks
    
- pass relationships through graph review
    
- prevent incomplete or critically flawed notes from becoming accepted
    
- accept strong notes into the searchable graph
    
- keep drafts accessible but hidden from accepted graph
    
- stage updates to accepted notes without destabilizing the current accepted version
    

Phase 6 is complete when a user can submit a filled or partially filled concept note for module-aware Agent Review, receive structured findings and proposed changes, iterate through revisions, and mark the note as accepted only after at least one review has completed, no critical findings remain, and essential module coverage is satisfied.

---

## Dependencies

- Phase 1: Vault Storage Core
    
- Phase 2: Concept Graph Core
    
- Phase 3: Search
    
- Phase 4: Create
    
- Phase 5: Source Content Intelligence
    

---

## Non-Goals

Phase 6 should not include:

- retention scheduling
    
- mastery scoring
    
- daily review sessions
    
- full backlog lifecycle
    
- automatic note acceptance
    
- silent graph mutation
    
- code execution
    
- visual code execution
    
- test running
    
- full contradiction detection across the entire vault
    
- real-time collaborative commenting
    
- fine-tuned reviewer models
    
- full Git-like version control
    
- production multi-user permissions
    
- product billing/account features
    

---

## Future Enhancements

- code execution for code implementation modules
    
- test case execution
    
- visual algorithm execution
    
- NeetCode-style step-by-step algorithm traces
    
- ML training loop visualization
    
- tensor shape tracing
    
- gradient flow visualization
    
- richer contradiction detection
    
- full cross-vault consistency review
    
- fine-tuned specialized review agents
    
- reviewer model routing by module type
    
- confidence calibration for review agents
    
- reviewer benchmarking
    
- comment threads / user-agent discussion
    
- configurable review strictness
    
- persistent review analytics
    
- advanced version diffing
    
- Git-backed note versioning