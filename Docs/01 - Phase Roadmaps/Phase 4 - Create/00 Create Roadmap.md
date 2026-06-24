## Purpose

Build the first full learning-session workflow in Studium.

Phase 4 allows the user to enter a concept, learning request, source context, or Search handoff, then have Studium infer the correct workflow, propose scaffold modules, generate a guided learning scaffold, let the user fill/edit it inside the app, and save the resulting Markdown-compatible concept note to the vault.

This phase answers:

> How does a new or existing concept become a structured, learnable Studium note?

Create should not simply generate a finished AI-written note. It should generate a guided scaffold that helps the user actively learn, reconstruct, and organize the concept.

---

## Why This Phase Comes Here

Create comes after Search because the user should be able to inspect what already exists before creating or modifying anything.

Phase 2 provides concept graph intelligence.  
Phase 3 exposes that intelligence visually through Search.  
Phase 4 uses both to safely create or update structured concept notes without creating duplicates.

Create depends on:

- vault read/write behavior from Phase 1
    
- concept identity and graph reasoning from Phase 2
    
- Search-to-Create handoff context from Phase 3
    

---

## Core Principle

Create should be scaffold-first, not summary-first.

The agent should help the user learn by generating prompts, blanks, reconstruction tasks, worked-example frames, code frames, comparison structures, and reflection prompts.

The scaffold may include hints and partial structure, but it should not replace the user’s learning effort with a fully polished explanation.

---

## Updated Note Model

Starting in Phase 4, concept notes should be treated as the primary durable knowledge units.

The graph should remain concept-focused.

Durable graph nodes:

```text
concept notes
```

Not durable graph nodes:

```text
worked examples
code implementations
comparisons
derivations
applications
reflections
sources
```

These should usually live as scaffold modules inside concept notes.

This keeps the graph easier to reason about and prevents the vault from becoming cluttered with too many small nodes.

---

## Scaffold Modules

A concept note may contain one or many scaffold modules.

Initial Phase 4 scaffold module types:

```text
conceptual_explanation
worked_example
code_implementation
implementation_notes
comparison
derivation
application
misconception_debugging
```

Removed or folded-in module ideas:

```text
mathematical_reconstruction
visual_intuition
reflection
source_note_restructure
```

These are not separate Phase 4 module types.

Instead:

- mathematical reconstruction can live inside `conceptual_explanation` or `derivation`
    
- visual intuition can live inside `conceptual_explanation`
    
- reflection can appear as a mini-section inside each module
    
- source-note restructuring becomes part of Source Content Intelligence later
    

---

## Scaffold Module IDs

Every scaffold module should have a stable internal ID.

This allows Search, Agent Review, Retention, and future editing workflows to target specific sections inside a concept note without turning those sections into graph nodes.

Example:

```yaml
scaffold_modules:
  - id: module_sgd_conceptual_explanation_001
    type: conceptual_explanation
    title: Conceptual Explanation
    status: scaffolded

  - id: module_sgd_worked_example_001
    type: worked_example
    title: Manual SGD Update
    status: scaffolded

  - id: module_sgd_code_implementation_001
    type: code_implementation
    title: NumPy SGD Implementation
    status: scaffolded
```

A concept may have multiple modules of the same type.

Example:

```text
Worked Example: Manual SGD Update
Worked Example: SGD on Linear Regression
Worked Example: Mini-Batch Update Comparison
```

Each module should have its own ID.

---

## Concept Note Structure

Every concept note should have a universal top-level structure.

Example:

```md
# Stochastic Gradient Descent

## Concept Overview

## Prerequisites

## Module Index

## Scaffold Modules

### Conceptual Explanation

### Worked Example: Manual SGD Update

### Code Implementation: NumPy SGD

### Comparison: SGD vs Batch Gradient Descent

## Related Concepts

## Recommended Videos

## Open Questions / Gaps
```

The universal concept-level sections provide stable organization.

The scaffold modules provide concept-specific learning structure.

---

## Module Index

Every concept note should include a Module Index near the top.

The app UI should also include a side navigation panel generated from the note’s headings and module metadata.

The sidebar helps inside Studium.

The Markdown Module Index helps inside Obsidian and preserves portability.

Example:

```md
## Module Index

- [Conceptual Explanation](#conceptual-explanation)
- [Worked Example: Manual SGD Update](#worked-example-manual-sgd-update)
- [Code Implementation: NumPy SGD](#code-implementation-numpy-sgd)
- [Comparison: SGD vs Batch Gradient Descent](#comparison-sgd-vs-batch-gradient-descent)
```

---

## Create Input Structure

Create should include these core inputs:

```text
Concept name: required

Learning request: optional

Source type: required

Conditional source fields:
- source title/name
- source unit type
- source unit
- section
- link
- attached file
```

The learning request field should be optional.

If it is blank, the agent should generate a broad concept-learning scaffold based on the inferred concept subtype.

Example blank request:

```text
Concept: Stochastic Gradient Descent
Learning request:
```

The agent may infer:

```text
Concept subtype: ml_concept

Recommended modules:
- conceptual_explanation
- worked_example
- code_implementation
- comparison
```

If the learning request is provided, it should strongly influence the module plan.

Example:

```text
Concept: Stochastic Gradient Descent
Learning request: Help me understand how learning rate affects SGD updates.
```

The agent may recommend:

```text
Target existing or new SGD concept note
Add conceptual explanation module focused on learning rate
Add worked example module comparing different learning rates
Add misconception/debugging module for too-small vs too-large learning rates
```

---

## Source Type Behavior

`source_type` should be required for every Create session.

Allowed source types may include:

```text
none
self_study
backlog
chatbot
book
video
paper
class
work
project
documentation
article
podcast
imported_note
other
```

If the user selects:

```text
none
```

then no source fields should appear, and the note should have:

```yaml
learning_encounters: []
```

If the user later adds a meaningful source encounter, that first real source can become:

```yaml
role: primary
```

There should not be a separate top-level `primary_source` abstraction.

All source information should live inside `learning_encounters`.

Example:

```yaml
learning_encounters:
  - source:
      type: book
      title: Hands-On Machine Learning
      unit_type: chapter
      unit: Chapter 4
      section:
      link:
    role: primary
    contribution_status: pending
    content_attached: false
    content_id:
```

---

## Source Attachment Boundary

Phase 4 may allow users to attach a source file, imported note, PDF, transcript, or other material.

However, Phase 4 should not deeply analyze source content.

Phase 4 may:

- attach the file
    
- store source metadata
    
- assign a `content_id`
    
- mark the source as attached but unprocessed
    

Example:

```yaml
learning_encounters:
  - source:
      type: imported_note
      title: Original SGD Notes
      file_path: /_studium_sources/original_sgd_notes.md
    role: primary
    contribution_status: source_attached
    content_attached: true
    content_id: source_imported_note_sgd_abc123
    processed: false
```

Deep RAG/source-aware scaffold generation belongs to Phase 5: Source Content Intelligence.

---

## Create Workflow

The Create workflow should follow this sequence:

```text
User enters concept + learning request + source context
↓
Studium checks the graph and vault
↓
Studium infers workflow mode
↓
Studium proposes scaffold module plan
↓
User approves, removes, or adds modules
↓
Studium validates module requests for relevance and redundancy
↓
Studium generates scaffold draft
↓
User fills/edits scaffold in rich editor
↓
User approves metadata, relationships, and source encounter
↓
User saves to vault
```

---

## Inferred Workflow Modes

The user should not manually choose a workflow mode before entering the concept.

The agent should infer the workflow and show the inferred mode in the proposal.

Initial workflow modes:

```text
new_concept_scaffold
existing_concept_new_encounter
existing_concept_same_encounter
targeted_scaffold_addition
child_concept_creation
example_module_creation
comparison_module_creation
backlog_origin_concept
broad_map_note_candidate
clarification_needed
do_nothing_redundant
```

Removed from Phase 4 v1:

```text
reflection_note_creation
rough_note_paste_restructure
deep_source_note_restructure
```

Reflection should live inside scaffold modules.

Rough note paste can be a future enhancement.

Deep source-note restructuring belongs to Source Content Intelligence.

---

## Graph Check Before Recommendation

Before any Create proposal, Studium should use the Phase 2 graph intelligence to check:

```text
Does this concept already exist?
Is this an alias?
Is there a close semantic match?
Is the source already attached?
Is this better as a child concept?
Is the request really a module addition?
Is this redundant with an existing module?
Are likely prerequisites present or missing?
Are related concepts already in the vault?
```

This check is required for Phase 4.

It protects against duplicate notes and misplaced scaffolds.

---

## Search-to-Create Handoff

Create must accept handoff context from Phase 3 Search.

Example 1:

```text
Search query: Optimization
Search result: semantic cluster
Action: Send to Create
```

Create should understand:

```text
The user may want a concept/map note for Optimization using the discovered cluster as context.
```

Example 2:

```text
Search result: Stochastic Gradient Descent
Action: Create/add scaffold
```

Create should understand:

```text
Target the existing SGD concept note.
```

The handoff should preserve:

```yaml
handoff:
  source_phase: search
  query:
  selected_concept_id:
  selected_module_id:
  query_type:
  search_context:
    related_nodes:
    source_filter:
    graph_focus_mode:
```

This is not a stub in Phase 4. It is required functionality.

---

## Module Plan Proposal

Before generating the full scaffold, the agent should propose a module plan.

Example:

```text
Concept: Stochastic Gradient Descent
Learning request: blank

Detected workflow:
new_concept_scaffold

Inferred subtype:
ml_concept

Recommended modules:
[x] Conceptual Explanation
[x] Worked Example
[x] Code Implementation
[x] Comparison
[ ] Derivation
[ ] Application
[ ] Misconception Debugging
[ ] Implementation Notes
```

The user should be able to:

```text
approve recommended modules
remove modules
add modules
rename module titles
adjust module focus
```

---

## User-Added Module Requests

The user should be able to request additional scaffold modules before generation.

Example:

```text
Also include a module on learning rate schedules.
```

Studium should validate added module requests for:

```text
relevance to the concept
redundancy with existing proposed modules
redundancy with existing saved modules
appropriate module type
whether the request should be its own concept instead
whether the request should be a related concept or prerequisite
```

Example rejection/pushback:

```text
The requested module appears unrelated to Stochastic Gradient Descent.
It may belong to a separate concept note instead.
```

Example:

```text
Concept: Stochastic Gradient Descent
Requested module: line of succession for the House of Saul
```

Expected behavior:

```text
Reject or ask for clarification.
Do not add unrelated module.
```

---

## Scaffold Module Definitions

### Conceptual Explanation

Default learning scaffold for understanding the concept.

May include:

```text
purpose
intuition
core idea
key terms
symbols
mental model
light mathematical reconstruction
visual intuition prompts
common confusions
reflection prompts
```

### Worked Example

Guided example scaffold that forces the user to work through the mechanics.

May include:

```text
given setup
step-by-step blanks
calculation prompts
intermediate checks
final answer explanation
reflection on mistakes
```

### Code Implementation

Guided implementation scaffold.

May include:

```text
Python implementation
NumPy implementation
PyTorch implementation
test cases
expected outputs
debugging prompts
extension tasks
```

CUDA and lower-level optimization can be future enhancements.

### Implementation Notes

Practical engineering-oriented scaffold.

May include:

```text
how this concept appears in real libraries
API details
common implementation pitfalls
performance concerns
debugging tips
real-system usage
```

Example:

```text
How PyTorch optimizers represent parameter groups, momentum, weight decay, and learning rate schedulers.
```

### Comparison

Scaffold for contrasting related concepts.

May include:

```text
concept A vs concept B
similarities
differences
when to use each
failure modes
decision table
examples
```

Comparisons should usually live as modules inside a concept note.

They should not become graph nodes in Phase 4.

Relevant graph relationships should still be proposed between the compared concepts.

Example:

```yaml
relationships:
  - type: contrasts_with
    target: concept_batch_gradient_descent
  - type: variant_of
    target: concept_gradient_descent
```

### Derivation

Guided derivation scaffold.

May include:

```text
starting assumptions
target result
symbol definitions
step-by-step derivation blanks
explanation prompts
common algebra mistakes
final interpretation
```

Derivations should be standalone modules only when substantial enough. Smaller derivations can live inside conceptual explanation.

### Application

Scaffold for connecting a concept to real use.

May include:

```text
where this concept appears
why it matters
applied scenario
design decision
implementation context
limitations
reflection prompts
```

This module becomes more important later in advanced AI, systems, research, and work-related concepts.

### Misconception Debugging

Scaffold for correcting misunderstanding.

May include:

```text
stated misconception
why it seems plausible
where it breaks
counterexample
correct mental model
practice prompt
reflection
```

In Phase 4, users can request this manually.

Later, Retention can generate these automatically when repeated mistakes are detected.

---

## Universal Concept-Level Sections

All concept notes should share some top-level structure.

Recommended universal sections:

```text
Concept Overview
Prerequisites
Module Index
Scaffold Modules
Related Concepts
Recommended Videos
Open Questions / Gaps
```

These are concept-level sections, not necessarily repeated inside every module.

---

## Universal Module-Level Elements

Each scaffold module should include a minimal internal structure.

Recommended universal module-level elements:

```text
Module purpose
Guided prompts / blanks
Reflection
Completion status
```

The exact structure should vary by module type.

For example, a worked example does not need its own prerequisites section if the concept note already has one.

---

## Recommended Videos

Concept notes should support multiple recommended videos.

Example:

```md
## Recommended Videos

- [ ] Video 1:
  - Link:
  - Why this helps:
  - Concept coverage:

- [ ] Video 2:
  - Link:
  - Why this helps:
  - Concept coverage:
```

If the user provides a video source or video link, it should populate the first video entry.

Automatic video recommendation is a future enhancement.

---

## Rich Editor

Phase 4 should include an in-app rich editor for filling out scaffold notes.

The user should not need to know Markdown details to fill out a scaffold.

The editor should provide a rich text editing experience while saving clean Markdown-compatible output.

The editor should support:

```text
headings
paragraphs
bold
italic
inline code
code blocks
math blocks
checkboxes
bullet lists
numbered lists
links
module navigation sidebar
```

Tables can be added if easy, but are not essential for Phase 4.

The editor should treat scaffold prompts and blanks as normal editable text, not rigid form fields.

This keeps the note portable and avoids locking the user into a restrictive form system.

---

## Editor Navigation

The editor should include a side navigation panel.

The side navigation should allow the user to jump between:

```text
Concept Overview
Prerequisites
Module Index
Each scaffold module
Related Concepts
Recommended Videos
Open Questions / Gaps
```

The side navigation is generated from the note structure and module metadata.

The saved Markdown note should still include a Module Index for Obsidian and portability.

---

## Autosave and Save Behavior

Phase 4 should use:

```text
local autosave draft + manual Save to Vault
```

The user can generate and fill/edit a scaffold in the app editor.

Studium should autosave the draft locally to prevent loss of work.

The Markdown file should only be written to the vault when the user clicks:

```text
Save to Vault
```

Incomplete scaffolds should be allowed to save.

Possible statuses:

```yaml
status: scaffolded
review_status: not_submitted
```

or:

```yaml
status: in_progress
review_status: not_submitted
```

---

## Review Status

Create should prepare for Agent Review but not implement it.

Recommended metadata:

```yaml
status: scaffolded
review_status: not_submitted
```

Possible later values:

```text
not_submitted
ready_for_review
submitted
reviewed
needs_revision
approved
```

Phase 4 may include a placeholder or stub action:

```text
Submit for Agent Review
```

But the actual Agent Review workflow is implemented in Phase 6.

---

## Relationship Proposal

Create should propose relationships separately from scaffold content.

Relationships should not be silently added without user approval.

Proposal sections should include:

```text
Prerequisites
Related concepts
Similar concepts
Contrasts
Variants
Child concepts
Parent concepts
Applications
```

The proposal should separate:

```text
relationship type
```

from:

```text
vault availability
```

Example:

```yaml
concept_relationship_candidates:
  - title: Partial Derivatives
    relationship_type: depends_on
    role: prerequisite
    vault_status: missing
    backlog_candidate: true

  - title: Batch Gradient Descent
    relationship_type: variant_of
    role: related_variant
    vault_status: missing
    backlog_candidate: true

  - title: Learning Rate
    relationship_type: related_to
    role: supporting_concept
    vault_status: found
    backlog_candidate: false
```

Important distinction:

```text
Missing is not the relationship.
Missing is only the vault status.
```

A missing prerequisite is still conceptually a prerequisite.

If it does not exist in the vault, it may also become a backlog candidate later.

---

## Note Relationship Sections

The final concept note should include stable conceptual sections such as:

```md
## Prerequisites

- [[Partial Derivatives]]

## Related Concepts

- [[Batch Gradient Descent]]
- [[Stochastic Gradient Descent]]
- [[Learning Rate]]
```

The final note should not say:

```text
missing prerequisite
backlog candidate
```

Those are workflow states, not durable concept-note content.

If the user later learns the missing prerequisite, the concept note should not need to be rewritten just because the prerequisite is no longer missing.

---

## Proposal Approval UI

The proposal UI should be generated from agent output and should support modular approval.

Approval groups may include:

```text
Scaffold modules
Relationships
Source encounter
Metadata
Warnings
Backlog candidates
```

Example:

```text
Approve scaffold modules:
[x] Conceptual Explanation
[x] Worked Example
[x] Code Implementation
[ ] Comparison

Approve relationships:
[x] depends_on Partial Derivatives
[x] related_to Learning Rate
[ ] variant_of Batch Gradient Descent

Approve source encounter:
[x] Hands-On ML Chapter 4

Approve metadata:
[x] note_type: concept
[x] note_subtype: ml_concept
```

The user should be able to approve the scaffold while rejecting or modifying individual relationships.

---

## Backlog Candidate Handling

Phase 4 may display backlog candidates in the proposal.

It should not persist backlog items yet.

Example:

```text
Potential backlog candidates:
- Partial Derivatives — prerequisite for Gradient Descent, missing from vault
- Batch Gradient Descent — related variant, missing from vault
```

The UI may include a stub action:

```text
Send selected to Backlog
```

The real backlog lifecycle belongs to the Backlog phase.

Backlog candidate state should not be written into the concept note.

---

## Write Behavior

Phase 4 writes to the test vault only during development.

Use normal language in the UI:

```text
Save to Vault
```

Do not label it as “Save draft to test vault” in the app UI.

Implementation should still treat this as test-vault-only until later phases are complete.

Write behavior:

```text
New note:
save after approval

Existing note update:
create proposal/diff first
do not overwrite without approval
back up original before write

Incomplete note:
can be saved with status in_progress
```

---

## Amendment Notes for Prior Phases

This phase introduces a structural correction that should be reflected in earlier phases.

### Phase 1 Amendment

Concept notes are the primary note type.

Examples, reflections, comparisons, derivations, and code implementations should usually be scaffold modules inside concept notes, not top-level note types.

Source files and imported notes should be treated as source attachments/records, not durable concept graph nodes.

### Phase 2 Amendment

The graph should index concept notes as durable nodes.

Phase 2 should also parse scaffold module metadata inside concept notes.

Scaffold modules should be searchable and addressable, but not graph nodes.

Phase 2 should support:

```text
concept identity
concept relationships
module IDs
module types
module titles
module statuses
module search targets
```

### Phase 3 Amendment

Search should support module-level hits.

Example:

```text
Search: Manual SGD Computation Example
```

Expected behavior:

```text
Result: module inside Stochastic Gradient Descent
Graph centers on Stochastic Gradient Descent
Preview jumps to the matching module
```

Search should not center on a separate example node because examples are not graph nodes.

---

## Build Work

Implement the Create workflow.

This should include:

- Create input form
    
- required concept name field
    
- optional learning request field
    
- required source type field
    
- conditional source fields
    
- source attachment support
    
- Search-to-Create handoff handling
    
- Phase 2 graph check before recommendation
    
- inferred workflow mode
    
- module plan proposal
    
- user module approval/removal/addition
    
- module relevance validation
    
- module redundancy detection
    
- scaffold generation
    
- relationship proposal
    
- individual relationship approval toggles
    
- source encounter proposal
    
- metadata proposal
    
- rich editor
    
- module navigation sidebar
    
- local autosave draft
    
- Save to Vault action
    
- incomplete scaffold save
    
- review status placeholder
    
- Submit for Agent Review stub
    
- backup/diff behavior for existing note updates
    

---

## Phase 4 Use Cases

These use cases should be used as implementation checkpoints.

### UC-01: Create New Concept With Blank Learning Request

Input:

```text
Concept: Stochastic Gradient Descent
Learning request:
Source type: none
```

Expected behavior:

- graph check confirms no duplicate concept
    
- agent infers concept subtype
    
- agent proposes default module bundle
    
- user approves module plan
    
- scaffold is generated
    
- user edits/fills scaffold in rich editor
    
- user saves to vault
    
- note has empty `learning_encounters`
    

---

### UC-02: Create New Concept With Source Metadata

Input:

```text
Concept: Stochastic Gradient Descent
Learning request:
Source type: book
Source title: Hands-On Machine Learning
Unit: Chapter 4
```

Expected behavior:

- graph check confirms whether concept exists
    
- source encounter is proposed
    
- if this is the first meaningful source, role is `primary`
    
- scaffold modules are proposed
    
- user approves and saves to vault
    

---

### UC-03: Existing Concept With New Source Encounter

Input:

```text
Concept: Stochastic Gradient Descent
Source type: class
Source title: OMSCS Machine Learning
Unit: Lecture 3
```

Expected behavior:

- existing concept is detected
    
- new source encounter is detected
    
- agent recommends attaching source to existing concept
    
- no duplicate concept note is created
    
- source contribution remains pending unless source content is later analyzed
    

---

### UC-04: Existing Concept With Same Source Encounter

Input:

```text
Concept: SGD
Source: Hands-On ML Chapter 4
```

Expected behavior:

- alias resolves to Stochastic Gradient Descent
    
- existing source encounter is detected
    
- agent warns that this source is already attached
    
- user can open existing note, add a new module, or cancel
    

---

### UC-05: Targeted Scaffold Addition

Input:

```text
Concept: Stochastic Gradient Descent
Learning request: Add scaffolding around learning rate schedules.
```

Expected behavior:

- existing concept is detected
    
- agent recommends adding one or more modules to the existing concept note
    
- agent checks for redundant existing learning-rate modules
    
- user approves module addition
    
- editor opens existing note with new scaffold module inserted
    

---

### UC-06: User Adds Custom Module Request

Agent proposes:

```text
Conceptual Explanation
Worked Example
Code Implementation
```

User adds:

```text
Also include a module on learning rate schedules.
```

Expected behavior:

- agent checks relevance to the concept
    
- agent checks for redundancy
    
- if relevant, module is added to the plan
    
- if unrelated, agent pushes back or asks for clarification
    

---

### UC-07: Unrelated Custom Module Request

Input:

```text
Concept: Stochastic Gradient Descent
User-added module: line of succession for the House of Saul
```

Expected behavior:

- agent detects irrelevance
    
- module is not added
    
- user is asked to clarify or create a separate concept if intentional
    

---

### UC-08: Multiple Modules of Same Type

Input:

```text
Concept: SGD
Learning request: Include one worked example for a single update and one worked example comparing learning rates.
```

Expected behavior:

- agent allows multiple worked example modules
    
- each module receives a unique module ID
    
- module titles distinguish the examples
    

---

### UC-09: Concept Note With Module Navigation

User opens generated SGD scaffold in the editor.

Expected behavior:

- side navigation shows concept sections and scaffold modules
    
- user can jump directly to each module
    
- saved Markdown includes a Module Index
    

---

### UC-10: Code Implementation Module

Input:

```text
Concept: Stochastic Gradient Descent
Learning request: Help me implement SGD in NumPy.
```

Expected behavior:

- agent proposes or generates a code implementation module
    
- scaffold includes code blocks, TODOs, expected behavior, and test prompts
    
- user fills implementation in rich editor
    
- note saves as Markdown-compatible content
    

---

### UC-11: Implementation Notes Module

Input:

```text
Concept: SGD Optimizer
Learning request: Explain how this appears in PyTorch optimizers.
```

Expected behavior:

- agent proposes implementation notes module
    
- scaffold focuses on practical API/system details
    
- module is saved inside the concept note, not as separate graph node
    

---

### UC-12: Comparison Module

Input:

```text
Concept: Stochastic Gradient Descent
Learning request: Compare SGD, batch gradient descent, and mini-batch gradient descent.
```

Expected behavior:

- agent proposes comparison module
    
- relevant `contrasts_with` or `variant_of` relationships are proposed
    
- comparison lives inside concept note
    
- comparison does not become a separate graph node
    

---

### UC-13: Derivation Module

Input:

```text
Concept: Linear Regression
Learning request: Help me derive the gradient of MSE.
```

Expected behavior:

- agent proposes derivation module
    
- scaffold includes assumptions, target result, symbols, derivation blanks, and interpretation prompts
    
- derivation remains a module inside the concept note
    

---

### UC-14: Application Module

Input:

```text
Concept: Embeddings
Learning request: Help me understand how embeddings are used in search systems.
```

Expected behavior:

- agent proposes application module
    
- scaffold connects concept to applied system use
    
- relationships to related concepts may be proposed
    

---

### UC-15: Misconception Debugging Module

Input:

```text
Concept: Gradient Descent
Learning request: I keep confusing gradient descent with stochastic gradient descent.
```

Expected behavior:

- agent proposes misconception debugging and comparison modules
    
- scaffold asks user to identify the confusion, test it, and reconstruct the correct distinction
    
- relationship proposals distinguish related concepts
    

---

### UC-16: Source File Attached But Not Analyzed

Input:

```text
Concept: SGD
Source type: imported_note
Attached file: old_sgd_notes.md
```

Expected behavior:

- source file is stored as attached source
    
- `content_attached: true`
    
- `processed: false`
    
- deep source-aware scaffold generation is not performed until Phase 5
    

---

### UC-17: Search-to-Create Existing Concept Handoff

From Search:

```text
Selected concept: Stochastic Gradient Descent
Action: Create/add scaffold
```

Expected behavior:

- Create receives selected concept ID
    
- existing concept is targeted
    
- user can add new scaffold modules
    
- no duplicate concept is created
    

---

### UC-18: Search-to-Create Semantic Cluster Handoff

From Search:

```text
Search query: Optimization
Search result: semantic cluster
Action: Send to Create
```

Expected behavior:

- Create receives cluster context
    
- agent may recommend broad map/concept note
    
- user approves or cancels
    
- no note is created automatically
    

---

### UC-19: Missing Prerequisite Display

Input:

```text
Concept: Gradient Descent
```

Agent identifies:

```text
Partial Derivatives
```

Expected behavior:

- Partial Derivatives is shown as a prerequisite relationship candidate
    
- if missing from vault, it is also shown as a backlog candidate in the proposal
    
- final concept note includes it under Prerequisites if approved
    
- final note does not label it as missing or backlog
    

---

### UC-20: Related Variant Display

Input:

```text
Concept: Gradient Descent
```

Agent identifies:

```text
Batch Gradient Descent
Stochastic Gradient Descent
```

Expected behavior:

- these are shown as related variants or child/variant relationships
    
- if missing, they may be backlog candidates
    
- they are not mislabeled as prerequisites
    

---

### UC-21: Individual Relationship Approval

Agent proposes:

```text
depends_on Partial Derivatives
related_to Learning Rate
variant_of Batch Gradient Descent
```

Expected behavior:

- user can approve or reject each relationship individually
    
- rejected relationships are not written
    
- approved relationships are included in metadata and Markdown relationship sections
    

---

### UC-22: Incomplete Scaffold Save

User fills only part of the generated scaffold.

Expected behavior:

- user can still save to vault
    
- note status becomes `in_progress`
    
- review status remains `not_submitted`
    

---

### UC-23: Generated But Untouched Scaffold Save

User generates scaffold and saves without filling it.

Expected behavior:

- note can still save
    
- note status is `scaffolded`
    
- review status is `not_submitted`
    

---

### UC-24: Submit for Agent Review Stub

User saves a scaffold and sees:

```text
Submit for Agent Review
```

Expected behavior:

- button or status placeholder is visible
    
- actual review workflow is not implemented until Phase 6
    

---

### UC-25: Existing Note Update Requires Approval

User adds a new module to an existing concept note.

Expected behavior:

- Create generates a proposal/diff
    
- original note is backed up before write
    
- user must approve before Save to Vault modifies the note
    

---

## Outputs

By the end of this phase, Studium should be able to:

- accept concept name, learning request, and source context
    
- require source type for every session
    
- conditionally show source fields
    
- receive handoff context from Search
    
- check the vault before recommending creation/update
    
- infer workflow mode
    
- propose scaffold module plans
    
- support multiple scaffold modules per concept
    
- support multiple modules of the same type
    
- assign stable module IDs
    
- validate user-added module requests
    
- generate scaffolded concept notes
    
- provide an in-app rich editor
    
- provide module navigation sidebar
    
- save Markdown-compatible notes
    
- store source attachments without deep analysis
    
- propose relationships separately from scaffold content
    
- distinguish prerequisites from related concepts
    
- distinguish relationship type from vault availability
    
- display backlog candidates without persisting them
    
- support local autosave drafts
    
- save incomplete scaffolds
    
- prepare notes for future Agent Review
    

---

## Success Criteria

Phase 4 is successful when the user can start a learning session from a concept, source, learning request, or Search handoff and produce a structured Studium concept note.

The user should be able to:

- create a new concept scaffold
    
- add scaffold modules to an existing concept
    
- provide source metadata
    
- attach source files without deep analysis
    
- generate a module plan
    
- edit the module plan
    
- add relevant custom modules
    
- receive pushback on irrelevant modules
    
- fill out the scaffold in a rich editor
    
- navigate the concept note through a sidebar
    
- save incomplete or completed scaffolds to the vault
    
- preserve Markdown/Obsidian compatibility
    
- approve relationships individually
    
- see missing prerequisites as backlog candidates in the proposal
    
- avoid writing backlog/missing state into the final note
    
- prepare the note for future Agent Review
    

Phase 4 is complete when Create can generate, edit, and save scaffolded concept notes made of addressable scaffold modules without creating duplicate concept nodes or polluting the graph with module-level nodes.

---

## Dependencies

- Phase 1: Vault Storage Core
    
- Phase 2: Concept Graph Core
    
- Phase 3: Search
    

---

## Non-Goals

Phase 4 should not include:

- deep source-content analysis
    
- RAG over uploaded sources
    
- automatic source-aware scaffold generation
    
- Agent Review execution
    
- real backlog lifecycle
    
- persistent backlog management
    
- real-vault production use
    
- retention scheduling
    
- mastery scoring
    
- graph mastery visualization
    
- source comparison
    
- automatic video recommendation
    
- full Obsidian replacement editor
    
- module-level graph nodes
    

---

## Future Enhancements

- paste rough notes directly into Create
    
- source-aware scaffold generation through Phase 5
    
- automatic video recommendations
    
- richer editor blocks
    
- tables
    
- diagram blocks
    
- code execution cells
    
- PyTorch-specific implementation templates
    
- CUDA implementation templates
    
- automatic misconception module generation from Retention
    
- module completion scoring
    
- module-level review scheduling
    
- persistent drafts
    
- collaborative editing
    
- advanced scaffold template customization