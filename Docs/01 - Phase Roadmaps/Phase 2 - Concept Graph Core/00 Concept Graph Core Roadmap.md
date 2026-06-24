## Purpose

Build the concept intelligence layer that allows Studium to reason about what a note represents, how concepts relate, whether a concept already exists, and what should happen when the user enters a concept. This phase answers:

> How does Studium understand the knowledge structure inside the vault?

Phase 1 makes the vault readable and writable. Phase 2 makes the vault searchable, identifiable, relational, and useful for future workflows. This phase should not deeply analyze uploaded source content. That responsibility belongs to the later **Source Content Intelligence** phase.

---

## Why This Phase Comes Here

The Create workflow depends on concept intelligence. Before Studium can generate a useful scaffold or decide where a concept belongs, it needs to understand:
- what concepts already exist
- what aliases refer to the same concept
- what concepts are related
- what concepts are prerequisites
- which source encounters have already been recorded
- whether a request represents a new concept, existing concept, child concept, example, repeated source encounter, or vague input

This phase powers future phases:
- **Create** uses graph recommendations to decide what note action to take.
- **Source Content Intelligence** uses the graph to know which concept/source pair to analyze.
- **Agent Review** uses graph context to evaluate whether a filled scaffold connects to the right concepts.
- **Backlog** uses missing prerequisite candidates.
- **Retention** uses prerequisite and relationship structure.
- **Mastery Dashboard** visualizes the graph with mastery metadata layered on top.

---
## Planning Work

Define:
- concept identity rules
- concept matching rules
- alias matching rules
- semantic matching strategy
- relationship taxonomy
- relationship direction rules
- relationship confidence rules
- source encounter metadata rules
- duplicate detection rules
- new note vs existing note rules
- child concept rules
- example vs concept rules
- repeated source encounter rules
- broad concept / map-note handling
- vague input handling
- prerequisite detection rules
- backlog candidate output format
- graph data representation
- graph query requirements
- hybrid rule-based/LLM recommendation approach
- CLI/test-harness commands for graph behavior

---
## Build Work

Implement the first concept intelligence layer.
This should include:
- scanning the test vault for concept notes
- extracting concept IDs, titles, aliases, note types, subtypes, statuses, sources, and relationships
- building an internal concept index
- supporting hybrid keyword + embedding search
- detecting likely existing matches for a new concept
- detecting aliases and near-matches
- detecting parent, child, prerequisite, and related concepts
- representing typed relationships between concepts
- recognizing whether a source encounter already exists
- recommending new learning encounters when a known concept appears from a new source
- identifying possible prerequisites
- checking whether prerequisites exist in the vault
- returning backlog candidates for missing prerequisites
- distinguishing concepts from examples
- handling broad or vague concept requests
- generating structured recommendation objects for Create
- exposing graph behavior through CLI commands or a local test harness

---
## Concept Identity

Studium should identify concepts using a combination of fields.
Priority order:
1. Stable concept ID
2. `canonical_title`
3. First H1 heading
4. File name
5. Aliases
6. Semantic similarity

A concept ID should be stable and should not change simply because a note title changes.
Preferred ID format:
```yaml
id: concept_stochastic_gradient_descent_a1b2c3
```
This keeps IDs readable while reducing collision risk.

---
## Concept Matching

When the user enters a concept, Studium should search the vault automatically.
The user should not have to manually check whether a note already exists.
The matching process should consider:

- exact title match
- alias match
- slug/file-name match
- keyword overlap
- embedding similarity
- known relationships
- note type
- note subtype
- source encounter history

Example input:

```
SGD
```

Possible result:

```
Possible matches: 
1. Stochastic Gradient Descent — strong alias match
2. Gradient Descent — related parent concept
3. Mini-Batch Gradient Descent — related variant
```

The system investigates, the user decides.

---
## Relationship Taxonomy

Studium should support typed relationships between concepts. Initial relationship types may include:
```
depends_on  
prerequisite_for  
part_of  
has_part  
variant_of  
parent_of  
child_of  
contrasts_with  
confused_with  
example_of  
applied_in  
related_to
```
The goal is not to create as many links as possible. The goal is to create meaningful links that help Studium reason about learning, prerequisites, review, and mastery.

---
## Relationship Direction

Relationships should have clear direction.
Examples:
```
relationships:
  - type: depends_on
    target: concept_gradient_descent_x1y2z3

  - type: prerequisite_for
    target: concept_backpropagation_a9b8c7

  - type: variant_of
    target: concept_gradient_descent_x1y2z3
```
Direction matters because later features depend on it.
For example:
- Backlog uses `depends_on` and `prerequisite_for`.
- Retention uses prerequisite and weak-prerequisite relationships.
- Mastery Dashboard uses prerequisite direction for left-to-right concept flow.

---
## Relationship Confidence

Relationships should support confidence and confirmation status.
Example:
```
relationships:
	- type: depends_on
	  target: concept_partial_derivatives_m3n4p5
	  confidence: high 
	  status: agent_suggested
```
Initial confidence levels:
```
low
medium
high
confirmed
```
Initial relationship statuses:
```
agent_suggested
user_confirmed
rejected
deferred
```
User-confirmed relationships should be treated as more reliable than agent-supported relationships

---

## Prerequisite Detection
Phase 2 should identify likely prerequisites and check whether they exist in the vault
If a prerequisite exists, Studium should propose a relationship
If a prerequisite does not exist, Studium should return a backlog candidate
Example:
```
Concept: Backpropagation  
  
Likely prerequisites:  
- Chain Rule  
- Partial Derivatives  
- Gradient Descent  
- Loss Functions
```
Vault check:
```
Chain Rule: missing
Partial Derivatives: missing
Gradient Descent: found
Loss Functions: found
```
Recommendation output:
```
proposed_relationships:  
- type: related_to  
target_title: Gradient Descent  
confidence: medium  
  
- type: related_to  
target_title: Loss Functions  
confidence: medium  
  
backlog_candidates:  
- title: Chain Rule  
reason: Likely prerequisite for Backpropagation  
priority: high  
  
- title: Partial Derivatives  
reason: Likely prerequisite for Backpropagation  
priority: high
```
Phase 2 should only produce backlog candidates. The full backlog lifecycle belongs to the later Backlog phase

---
## Source Encounter Metadata
Phase 1 stores and parses source encounters. Phase 2 recognizes source encounters as part of concept history.

If the user enters a concept that already exists but provides a new source, Studium should recommend adding a new learning encounter to the existing concept note. Studium should not infer what the source contributed unless source content, user notes, a transcript, uploaded material, or a user-written summary is available. 

Example:
```
Concept: Stochastic Gradient Descent
Source: OMSAI Machine Learning - Lecture 3
```
If an existing note is found:
```
Existing concept: Stochastic Gradient Descent
Existing source: Hands-On ML Chapter 4
```
Studium should recommend:
```
Attach this as a new learning encounter to the existing Stochastic Gradient Descent note
```
The learning encounter should be stored with pending contribution status:
```
learning_encounters:
	- type: class
	  nam: OMSAI Machine Learning
	  locatio: Lecture 3
	  role: additional 
	  contribution_status: pending
	  content_attached: false
	  content_id:
	  contribution summary:
```
Possible contribution statuses:
```
pending
user_described
source_attached
soruce_analyzed
integrated
redundant
```
Phase 2 may set:
```
pending
user_described
```
It should not set:
```
source_analyzed
```

The act of analyzing a new source to provide additional scaffolding to a note will belong to the Source Content Intelligence Phase. Phase 2 will provide the backbone for this phase

---
## Source Content Boundary

Phase 2 should prepare for source content, but not perform full source-content analysis

Phase 2 may store metadata such as:
```
source_content:
	content_attached
	content_id
	content_type:
	processed: false
```

The following responsibilities belong to Source Content Intelligence:
	- parsing uploaded PDFs, transcripts, slides, or documents
	- chunking source content
	- retrieving source chunks relevant to a concept
	- comparing source content against an existing note
	- determining what the source contributed
	- generating source-aware scaffold sections
	- proposing note additions based on source material
	- citing source-specific content
	- marking a source encounter as **source_analyzed**
	
Studium should not pretend to understand a source unless source content has actually been provided and processed

---

## New Note vs Existing Note

Studium should recommend creating a new note when:
- no existing concept has a strong title, alias, or semantic match
- the concept has independent identity
- the concept will likely be referenced in multiple future contexts
- the concept has its own prerequisites, examples, or applications
- the concept would make an existing note too large or unfocused

Studium should recommend attaching to an existing concept note when:
- the concept already exists 
- the new material comes from a new source encounter
- the new material does not justify a duplicate concept note
If the concept exists and the source is new, Studium should default to adding a learning encounter.

Studium should recommend creating a child concept when:
- the concept is a specialized version of a broader concept
- the concept has enough depth to require its own scaffold
- the parent note would become bloated if all details were included inline

Studium should recommend marking a concept request as likely redundant only when:
- the concept already exists
- the source is not new 
- the user has not provided new material, source context, or a reason to revisit the concept

---

## Example vs Concept

Studium should distinguish between a concept and an example. A worked example should live inside the parent concept note by default.
A worked example may become standalone when:
- it is too large for the parent note
- it is reusable across multiple concepts
- it contains significant cod, derivation, or multi-step analysis
- it acts as a reference artifact on its own
Default behavior:
`Manual one-step SGD update -> add as example inside Stochastic Gradient Descent`
Standalone behavior:
`Create standalone example note if the example is large, reusable, or code-heavy.`

---
## Broad or Vague Concept Handling

Studium should recognize when a concept request is too broad or too vague.

Example broad input:
`Artificial Intelligence`
Possible recommendation:
`Create a map/overview note or narrow the concept.`
Example vague input:
`optimization stuff`
Possible response
```
Studium found several possible meanings:
1. Mathematical Optimization
2. Gradient Descent
3. Convex Optimization
4. Model Training Optimization
5. Performance Optimization in Software
   
Recommendation:
Clarify the intended concept before creating or attaching a note.
```
Studium should not create low-quality notes from vague input

---
## Recommendation Strategy

Studium should use a hybrid recommendation system, with both Rule-based logic handling deterministic checks, and LLM reasoning helping with judgement-heavy decisions:

Rule-based:
- exact title match
- alias match
- ID match
- file-name match 
- known relationship match
- note type/subtype match
- existing source encounter match 
Embedding-based search should support semantic matching. 

LLM reasoning:
- whether two concepts are truly the same
- whether a concept should be a child concept
- whether an example should become standalone
- whether a user-provided source summary suggests a note update
- what prerequisites are likely relevant 
The LLM should not claim tom know what a source contributed unless source content or a user-provided description is available. The LLM layer should be provider-agnostic. Local LLM use is a technical preference, but the system should allow fallback to API-based models if needed. 

---

## Recommendation Object

Phase 2 should produce structured recommendation objects that the Create workflow can consume. 

Example:
```
recommendation:
  action: attach_learning_encounter
  confidence: high

  target_concept:
    id: concept_stochastic_gradient_descent_a1b2c3
    title: Stochastic Gradient Descent

  possible_matches:
    - title: Stochastic Gradient Descent
      match_type: exact
      confidence: high

  reason:
    - The entered concept matches an existing concept.
    - The provided source is not currently listed as a learning encounter.
    - Studium cannot determine the source contribution without uploaded material or user notes.

  proposed_updates:
    - add_learning_encounter

  learning_encounter:
    type: class
    name: OMSCS Machine Learning
    location: Lecture 3
    role: additional
    contribution_status: pending
    content_attached: false
    content_id:

  proposed_relationships: []

  backlog_candidates: []

  warnings: []

  user_options:
    - approve
    - create_new_note_anyway
    - create_child_concept
    - cancel
```
Another example (new concept):
```
recommendation:
  action: create_new_concept
  confidence: medium

  target_concept:
    title: Backpropagation
    suggested_subtype: ml_concept

  possible_matches:
    - title: Gradient Descent
      match_type: related
      confidence: medium
    - title: Neural Networks
      match_type: related_parent_area
      confidence: medium

  reason:
    - No strong existing concept match was found.
    - Backpropagation appears to have independent identity.
    - It will likely connect to gradient descent, chain rule, neural networks, and loss functions.

  proposed_updates:
    - create_concept_note
    - add_relationships

  proposed_relationships:
    - type: related_to
      target_title: Gradient Descent
      confidence: medium
      status: agent_suggested

  backlog_candidates:
    - title: Chain Rule
      reason: Likely prerequisite for Backpropagation
      priority: high

    - title: Partial Derivatives
      reason: Likely prerequisite for Backpropagation
      priority: high

  warnings:
    - Some prerequisite concepts may not exist in the vault yet.

  user_options:
    - approve
    - attach_to_existing_note
    - create_child_concept
    - add_to_backlog_candidates
    - cancel
```
The user should approve, modify, or reject the recommendation before meaningful graph mutation occurs. 

--- 
## CLI / Test Harness Direction

Phase 2 should be testable without the full Create UI. Possible CLI commands may include:
```
studium graph scan
studium graph find "SGD"
studium graph inspect "Stochastic Gradient Descent"
studium graph propose "SGD" --source "Hands-On ML Chapter 4"
studium graph propose "Regularization" --source "OMSCS ML Lecture 5" --summary "Clarified L1 vs L2"
studium graph relationships "Backpropagation"
```
Exact commands should be defined in the Phase 2 implementation plan. The purpose of the CLI is to validate graph logic before building the Create interface. 

---
## Phase 2 Use Cases

These use cases should be used as implementation checkpoints.

### UC-01: Exact Existing Concept Match

Input:
`Stochastic Gradient Descent`

Expected behavior:
- detect existing concept note
- recommend using existing note
- avoid duplicate note creation

---
### UC-02: Alias Match 

Input:
`SGD`

Expected behavior:
- map alias to `Stochastic Gradient Descent`
- recommend using existing concept note

---

### UC-03: Existing Concept + New Source Encounter

Input:
`Concept: Stockastic Gradient Descent
`Source: MSAI Machine Learning - Lecture 3`

Expected behavior:
- detect existing concept
- detect new source
- recommend adding learning encounter
- set contribution status to pending
- do not infer source contribution 

---
### UC-04: Existing Concept + Same Source Encounter

Input:
```
Concept: SGD
Source: Hands-On ML - Chapter 4
```

Expected behavior:
- detect existing concept
- detect existing source encounter
- avoid duplicate learning encounter 

---

## UC-05: New Concept with Existing Related Concepts

Input:
`Backpropagation`

Vault contains:
```
Gradient Descent
Neural Networks
Loss Functions
Chain Rule
Partial Derivatives 
```

Expected behavior:
- detect no existing Backpropagation note
- recommend creating new concept note
- suggest relationship to existing concepts

---
### UC-06: New Concept With Missing Prerequisites

Input:
`Backpropagation`

Vault contains:
```
Gradient Descent
Loss Functions
Neural Networks
```

Vault does not contain:
```
Chain Rule
Partial Derivatives 
```

Expected behavior:
- recommend creating new Backpropagation concept note 
- suggest relationships to existing concepts
- return backlog candidates for missing prerequisites

--- 
### UC-07: Existing Broad Parent + New Child Concept

Input: 
`Mini-Batch Gradient Descent`

Vault contains:
`Gradient Descent`

Expected behavior:
- avoid collapsing into Gradient Descent
- recommend creating child concept note
- suggest `variant_of: Gradient Descent`

---
### UC-08: Attach as Section Instead of New Note

Input:
`Learning rate schedule in SGD`

Vault contains:
`Stochastic Gradient Descent`

Expected behavior:
- recommend adding as section/scaffold block inside SGD
- offer child concept note as alternative 

---
### UC-09: Large Reusable Example

Input:
`Manual SGD computation example`

Expected behavior:
- classify as example, not core concept 
- recommend adding inside SGD by default 
- allow standalone example note is large/reusable/code-heavy

---
### UC-10 Broad Concept / Map Candidate

Input:
`Artificial Intelligence`

Expected behavior:
- recognize as broad domain 
- recommend map/overview note or ask user to narrow concept

---
### UC-11: Vague or Ambiguous Input

Input:
`optimization stuff`

Expected behavior:
- do not create not immediately 
- suggest possible interpretations
- ask user to clarify

---
### UC-12: Relationship Direction

Input:
`Backpropagation`

Detected prerequisite:
`Chain Rule`

Expected behavior:
- create/suggest correct direction:
	- `Backpropagation depends_on Chain Rule`
	- `Chain Rule prerequisite_for Backpropagation`
- avoid reversed relationship

---
### UC-13: User Confirmation Before Graph Mutation

Input:
`Backpropagation depends_on Chain Rule`

Expected behavior:
- relationship starts as `agent_suggested`
- user can confirm, reject, change, or defer
- confirmed relationships are more trusted 

---
### UC-14: Source Metadata Without Source Content

Input:
```
Concept: Regularization
Source: MSAI ML Lecture 5
```

Expected behavior:
- add learning encounter
- set contribution status to pending
- do not infer source contribution

---
### UC-15: User-Provided Source Summary

Input:
```
Concept: Regularization
Source: MSAI ML Lecture 5
Summary: This lecture clarified the difference between L1 and L2 regularization 
```

Expected behavior:
- add learning encounter
- set contribution status to `user described`
- preserve user-described contribution 
- optionally suggest child concepts such as L1 Regularization and L2 Regularization 

---
## Outputs

By the end of this phase, Studium should be able to:

- scan the test vault for concept notes
- build an internal concept index
- identify concepts by ID, title, H1, file name, and aliases
- perform hybrid keyword + embedding search
- detect likely existing matches for a new concept
- represent typed relationships between concepts
- recognize existing source encounters
- recommend adding a new source encounter when a known concept appears from a new source
- identify likely prerequisites
- check whether prerequisites exist in the vault
- return backlog candidates for missing prerequisites
- distinguish new concepts from repeated encounters
- distinguish examples from concepts
- handle broad or vague inputs
- recommend whether to create, attach, update, mark redundant, or create child concepts
- produce structured recommendation objects
- expose graph behavior through CLI or a local test harness

---

## Success Criteria

Phase 2 is successful when Studium can behave like a cautious concept librarian.

It should be able to say:

- this concept already exists
- this term is an alias for an existing concept
- this is a new source encounter
- this source encounter already exists
- this should probably be a new concept note
- this should probably be a child concept
- this should probably be a section inside an existing note
- this is an example, not a core concept
- this concept likely depends on these prerequisites
- these prerequisites exist in the vault
- these prerequisites are missing and should become backlog candidates
- this input is too broad
- this input is too vague
- this relationship direction should be X, not Y
- this relationship is agent-suggested and needs user confirmation
- source contribution is unknown unless source content or a user summary is provided

Phase 2 is complete when the use cases above can be tested through CLI commands or a local test harness and produce structured recommendation objects suitable for the future Create workflow.

---

## Dependencies

- Phase 1: Vault Storage Core

---

## Future Enhancements

- source content upload and analysis through Source Content Intelligence
- stronger semantic matching
- improved concept clustering
- relationship inference from note content
- contradiction detection across notes
- confidence calibration for recommendations
- graph visualization
- automatic relationship cleanup
- relationship conflict detection
- better source encounter comparison once source content is attached
- domain-specific relationship logic