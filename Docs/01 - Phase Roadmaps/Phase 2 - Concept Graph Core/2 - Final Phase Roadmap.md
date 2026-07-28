# Phase 2: Concept Graph Core

## 1. Purpose

Phase 2 builds the concept intelligence layer that allows Studium to understand the knowledge structure represented by concept notes in the vault.

Phase 1 established how concept knowledge is stored. Phase 2 introduces persistent indexing, semantic retrieval, graph-aware concept matching, and provider-agnostic LLM reasoning so Studium can identify what a concept represents, how it relates to existing knowledge, and what action should be recommended when the user introduces a concept or learning context.

This phase answers:

> How does Studium understand what concepts already exist, how they occupy the knowledge graph, and what should happen when new learning intent enters the system?

---

## 2. Phase Outcome

By the end of this phase, Studium should be able to:

- scan the vault and build a persistent local concept index
    
- index concept identity, taxonomy, source encounters, relationships, and scaffold module metadata
    
- identify concepts by stable ID, canonical title, alias, file metadata, and semantic similarity
    
- perform working hybrid lexical and embedding-based concept retrieval
    
- reason over narrowed concept candidates with a provider-agnostic LLM layer
    
- distinguish strong existing matches from new concepts
    
- identify likely parent, child, variant, prerequisite, and related concept positions
    
- recommend concept types and concept domains for new concepts
    
- identify repeated and new learning encounters
    
- identify likely missing prerequisites and return backlog candidates
    
- recommend adding scaffold modules to existing concept notes
    
- produce structured `ConceptRecommendation` objects for future Create workflows
    
- expose concept intelligence through CLI or a local test harness
    

Phase 2 should recommend changes but should not directly mutate concept notes.

---

## 3. Why This Phase Comes Now

Phase 1 established the durable concept note storage model, including stable IDs, concept taxonomy, learning encounters, scaffold module metadata, relationships, validation, and safe write primitives.

Phase 2 can now build intelligence on top of that structure.

Search cannot provide meaningful ranked concept exploration without concept indexing and semantic retrieval.

Create cannot determine whether to create a concept, reuse an existing concept, add a learning encounter, or add a scaffold module without concept intelligence.

Source Content Intelligence needs concept and source encounter identity before comparing source content against existing knowledge.

Agent Review, Backlog, Retention, and Mastery all eventually depend on meaningful relationship structure.

Phase 2 therefore acts as the reasoning layer between durable storage and future user workflows.

---

## 4. Core Principles for This Phase

- The system investigates; the user ultimately decides.
    
- Concept notes remain the durable graph nodes.
    
- Scaffold modules are addressable content inside concept notes, not graph nodes.
    
- Concept domains represent spaces in the knowledge graph, not individual graph nodes.
    
- A domain label may share a name with a concept note without becoming the same object.
    
- Semantic similarity narrows candidates; it does not prove conceptual equivalence or relationship direction.
    
- LLM reasoning should operate on narrowed candidate sets rather than the full vault.
    
- Deterministic rules should handle deterministic decisions.
    
- Embeddings should handle semantic retrieval and ranking.
    
- LLM reasoning should handle judgment-heavy concept decisions.
    
- LLM integrations should remain provider-agnostic.
    
- Small, capable reasoning models should be preferred where they satisfy the required behavior.
    
- Phase 2 produces recommendations and proposals, not direct concept-note mutation.
    
- Source contribution must not be inferred without source content or explicit user-provided context.
    
- Broad concepts are valid concepts.
    
- Vague input should not create low-quality concepts.
    
- Graph relationships should be meaningful and learning-oriented rather than maximized for link count.
    

---

## 5. Core Features / Capabilities Introduced

### 5.1 Persistent Concept Index

Phase 2 should build a persistent local index representing the concept knowledge available in the vault.

The index should be generated from Phase 1-compatible concept notes and remain synchronized with the current vault state.

This feature should support indexing:

- stable concept ID
    
- canonical title
    
- aliases
    
- concept type
    
- concept domains
    
- note lifecycle state
    
- file location
    
- H1 heading where useful
    
- learning encounter metadata
    
- relationship metadata
    
- scaffold module metadata
    
- concept text selected for semantic embedding
    

Important behavior:

- the vault remains the durable knowledge source
    
- the index is a derived local representation
    
- the index should be rebuildable from the vault
    
- stale or removed concept notes should not remain indefinitely in the index
    
- concept notes remain the graph nodes
    
- scaffold modules should be indexed as searchable/addressable content under their parent concept
    

Important constraints:

- exact SQLite schema and synchronization strategy belong in the Technical Plan
    
- index records should not become an alternative source of truth for concept-note content
    
- graph visualization is not implemented in Phase 2
    

---

### 5.2 Concept Identity Resolution

Phase 2 should consistently determine the identity of indexed concepts.

Concept identity should use:

1. stable concept ID
    
2. canonical title
    
3. aliases
    
4. H1 heading
    
5. file name or slug
    
6. semantic similarity
    

Stable ID is authoritative when already known.

This feature should support:

- exact concept ID lookup
    
- exact canonical title matching
    
- normalized title matching
    
- alias matching
    
- file-name/slug matching
    
- semantic candidate retrieval
    

Important behavior:

- title changes should not change concept identity
    
- aliases should improve concept discovery
    
- an alias match may represent the same concept
    
- semantic similarity should return candidates, not automatically merge concepts
    

Important constraints:

- Phase 2 should not silently combine concept notes
    
- duplicate resolution should remain recommendation-based
    

---

### 5.3 Hybrid Lexical and Embedding Retrieval

Phase 2 should implement working semantic retrieval.

Concept retrieval should combine deterministic lexical signals with embeddings.

The retrieval system should consider:

- canonical title
    
- aliases
    
- selected concept overview content
    
- concept type
    
- concept domains
    
- existing relationships where relevant
    

The core retrieval flow should be:

```text
Concept query
↓
Rule-based lexical matching
↓
Embedding retrieval and similarity ranking
↓
Candidate score combination
↓
Narrowed concept candidate set
```

This feature should support:

- exact matches
    
- alias matches
    
- keyword overlap
    
- semantic concept similarity
    
- ranked concept candidates
    
- configurable candidate limits for later LLM reasoning
    

Important behavior:

- working embeddings are a Phase 2 completion requirement
    
- the exact embedding model should be selected in the Technical Plan
    
- embedding model complexity should match the relatively focused retrieval task
    
- concept embeddings should be reusable rather than regenerated unnecessarily
    
- retrieval should provide score/evidence information to downstream reasoning
    

Important constraints:

- embedding similarity does not establish relationship direction
    
- embedding similarity alone should not decide whether concepts are identical
    
- Phase 2 should not require a heavyweight embedding model without evidence that it improves the use cases
    

---

### 5.4 Concept Domain Indexing and Suggestion

Phase 2 should index `concept_domains` as flexible knowledge-space labels.

Example:

```yaml
concept_domains:
  - machine_learning
  - optimization
```

Domains describe the conceptual space occupied by a concept.

A domain is not automatically a graph node.

For example:

```text
machine_learning
```

may exist as a domain label while:

```text
Machine Learning
```

may independently exist as a concept note if the user chooses to learn it.

This feature should support:

- indexing existing domain labels
    
- locating concepts in similar domain spaces
    
- collecting domain candidates from nearby concepts
    
- suggesting domains for new concepts
    
- allowing the reasoning layer to propose new domain labels when existing domains are insufficient
    

Recommended domain suggestion flow:

```text
New concept query
↓
Retrieve semantically nearby concepts
↓
Collect indexed domain labels from nearby concepts
↓
Provide concept + candidate domains to reasoning layer
↓
Reuse, remove, or propose domain labels
↓
Return suggested domains in ConceptRecommendation
```

Important behavior:

- domain suggestions are proposed metadata
    
- new domain strings may be proposed
    
- concept domains do not directly generate relationships
    
- Phase 2 does not create domain graph nodes
    

Important constraints:

- domain values remain flexible strings
    
- domain normalization rules should be defined in the Technical Plan
    
- broader agent-driven domain inference may be refined during productization
    

---

### 5.5 Scaffold Module Indexing

Phase 2 should index scaffold module metadata stored inside concept notes.

Scaffold modules remain part of their parent concept note.

This feature should support indexing:

- module ID
    
- parent concept ID
    
- module type
    
- module title
    
- module status
    
- module origin when present
    
- module focus when present
    

Important behavior:

- module-level matches should resolve back to the parent concept
    
- modules should be searchable/addressable
    
- modules should not become graph nodes
    
- a user query may match a module more strongly than the parent concept title
    

Example:

```text
Query:
Manual SGD computation example

Matched module:
Manual SGD Update

Parent concept:
Stochastic Gradient Descent
```

Important constraints:

- Phase 2 does not generate module content
    
- Phase 2 does not review module quality
    
- Phase 2 only indexes and reasons about module placement
    

---

### 5.6 Provider-Agnostic LLM Reasoning Layer

Phase 2 should implement a working provider-agnostic LLM reasoning layer.

The LLM should operate after deterministic matching and semantic retrieval have narrowed the candidate set.

Core pipeline:

```text
Rule-based matching
↓
Embedding retrieval and ranking
↓
Narrowed candidate concepts/modules
↓
LLM reasoning
↓
Structured ConceptRecommendation
```

The LLM reasoning layer should help determine:

- whether two concept labels likely represent the same concept
    
- whether a concept has independent identity
    
- whether a new concept is likely positioned above or below an existing concept
    
- whether a concept is a variant of another concept
    
- whether user intent is better served by a scaffold module in an existing note
    
- likely prerequisites
    
- likely relationship types and direction
    
- learning role of proposed relationships
    
- proposed concept type
    
- proposed concept domains
    
- whether input is vague and needs clarification
    
- whether a concept is broad but still valid
    

Important behavior:

- the interface should not be tightly coupled to a single LLM vendor
    
- small LLMs should be considered for narrowed reasoning tasks
    
- structured outputs should be used
    
- LLM reasoning should receive retrieved context rather than scan the whole vault
    
- deterministic tests should use controlled/mocked reasoning responses where necessary
    

Important constraints:

- LLM output is a recommendation
    
- LLM output should not directly mutate concept notes
    
- LLM output should be validated before becoming a `ConceptRecommendation`
    
- the LLM should not claim knowledge of source contribution without source content or supplied context
    

---

### 5.7 Concept Matching and Existing Concept Detection

When a user enters a concept, Studium should automatically investigate the vault.

The matching process should consider:

- stable concept ID when available
    
- exact title match
    
- normalized title match
    
- alias match
    
- file/slug match
    
- keyword overlap
    
- embedding similarity
    
- nearby concepts
    
- concept type
    
- concept domains
    
- indexed scaffold modules
    
- learning encounter history
    

Example:

```text
Input:
SGD
```

Potential ranked evidence:

```text
1. Stochastic Gradient Descent — exact alias match
2. Gradient Descent — semantic/relationship candidate
3. Mini-Batch Gradient Descent — semantic variant candidate
```

This feature should support:

- strong existing match detection
    
- possible match ranking
    
- same-concept recommendations
    
- ambiguity detection
    
- duplicate prevention
    

Important behavior:

- exact alias/title matches should receive strong deterministic weight
    
- semantic candidates should be supplied to the reasoning layer
    
- the system investigates and recommends
    
- the user is not required to manually search for an existing note
    

---

### 5.8 Relationship Intelligence

Phase 2 should reason about typed relationships between concepts.

The Phase 1 relationship taxonomy remains:

```text
depends_on
prerequisite_for
related_to
variant_of
parent_of
child_of
contrasts_with
```

Phase 2 should amend relationship metadata to support learning intelligence.

Recommended relationship shape:

```yaml
relationships:
  - relationship_type: depends_on
    target_id:
    target_title: Chain Rule
    vault_status: missing
    learning_role: mathematical_prerequisite
    confidence: high
    status: agent_suggested
```

This feature should support:

- relationship type
    
- target ID
    
- target title
    
- vault status
    
- learning role
    
- confidence
    
- persistent confirmation status
    

Important behavior:

- relationship direction matters
    
- semantic similarity does not establish direction
    
- LLM reasoning may propose direction
    
- reciprocal graph implications may be derived or proposed where appropriate
    

Example:

```text
Backpropagation depends_on Chain Rule

Inverse graph meaning:
Chain Rule prerequisite_for Backpropagation
```

Important constraints:

- relationship semantic correctness is recommendation-based
    
- Phase 2 should not directly persist proposed relationship changes to notes
    
- relationship write behavior is deferred to Phase 4 or later approval workflows
    

---

### 5.9 Learning Role

`learning_role` describes what the target concept represents in relation to the source concept from a learning perspective.

It is distinct from `relationship_type`.

Example:

```yaml
relationship_type: depends_on
learning_role: mathematical_prerequisite
```

The graph relationship answers:

> How are these concepts structurally connected?

The learning role answers:

> What does this target concept represent for learning the current concept?

Potential learning roles may include:

- `mathematical_prerequisite`
    
- `conceptual_prerequisite`
    
- `implementation_prerequisite`
    
- `foundational_theory`
    
- `broader_parent_concept`
    
- `specialized_child_concept`
    
- `alternative_variant`
    
- `comparison_target`
    
- `supporting_concept`
    
- `application_context`
    

The exact initial enum should be finalized in the Technical Plan.

Important behavior:

- learning roles should describe the target concept's learning purpose relative to the current concept
    
- they should not merely duplicate relationship type names
    
- learning roles may later support Backlog, Retention, Review, and Mastery behavior
    

---

### 5.10 Relationship Confidence and Status

Relationship proposals should include confidence.

Initial confidence levels:

```text
low
medium
high
```

`confirmed` should not be a confidence level. Confirmation is a relationship status.

Persistent relationship statuses should initially include:

```text
agent_suggested
user_confirmed
```

A proposed relationship starts as:

```yaml
status: agent_suggested
```

After a later approval workflow:

```yaml
status: user_confirmed
```

Rejected or deferred recommendations should not be stored in the durable concept note relationship list.

Those represent recommendation-history state, not active concept relationships.

Important behavior:

- user-confirmed relationships should be treated as more reliable
    
- confidence represents model/system certainty
    
- status represents relationship confirmation state
    
- confidence and status should remain separate
    

---

### 5.11 Prerequisite Detection and Backlog Candidates

Phase 2 should identify likely prerequisites for concepts.

Example:

```text
Concept:
Backpropagation

Likely prerequisites:
Chain Rule
Partial Derivatives
Gradient Descent
Loss Functions
```

The system should compare proposed prerequisites against the indexed vault.

Example:

```text
Chain Rule: missing
Partial Derivatives: missing
Gradient Descent: found
Loss Functions: found
```

If a prerequisite exists:

- propose an appropriate relationship
    
- include relationship direction
    
- include learning role
    
- include confidence
    

If a prerequisite is missing:

- return a backlog candidate
    
- do not create a backlog item
    

Example:

```yaml
backlog_candidates:
  - title: Chain Rule
    reason: Likely mathematical prerequisite for Backpropagation
    priority: high
```

Important behavior:

- Phase 2 produces backlog candidates only
    
- full backlog persistence and management belongs to Phase 7
    
- missing concepts should not be silently created
    
- prerequisite detection should use reasoning, not semantic similarity alone
    

---

### 5.12 Learning Encounter Recognition

Phase 1 stores `learning_encounters`.

Phase 2 should recognize learning encounter history when evaluating concept intent.

If the concept already exists and the provided source metadata does not match an existing encounter, Studium should recommend adding a learning encounter.

Source encounter comparison should consider:

- `source.type`
    
- `source.title`
    
- `source.unit_type`
    
- `source.unit`
    
- `source.section`
    
- `source.link` when available
    

Example:

```text
Concept:
Stochastic Gradient Descent

New source:
MSAI Machine Learning
Lecture 3
```

Existing note:

```text
Hands-On Machine Learning
Chapter 4
```

Recommendation:

```text
Add a new learning encounter to the existing Stochastic Gradient Descent concept.
```

The proposed encounter should use:

```yaml
role: additional
contribution_status: pending
```

Important behavior:

- repeated source encounters should not be duplicated
    
- external source metadata may exist without attached content
    
- source contribution remains unknown when content is unavailable
    
- Phase 2 does not analyze source files
    

---

### 5.13 Optional User-Provided Source Context

Phase 2 may preserve user-provided context about a learning encounter.

Example:

```text
Source:
MSAI ML Lecture 5

User-provided context:
This clarified L1 vs L2 regularization for me.
```

The system may preserve the supplied context and propose:

```yaml
contribution_status: user_described
```

Important behavior:

- Studium should not require the user to summarize sources
    
- this is optional input handling
    
- the user description is not source-verified content
    
- the reasoning layer should not claim the source itself contains facts beyond the supplied context
    
- automatic source contribution analysis belongs to Phase 5
    

Important constraints:

- this is not a core Phase 2 success criterion
    
- Phase 2 should not create friction by requesting source summaries by default
    

---

### 5.14 New Concept vs Existing Concept Recommendation

Studium should recommend using an existing concept when:

- there is a strong title or alias match
    
- reasoning determines candidate labels represent the same concept
    
- the user introduces a new learning encounter for an existing concept
    
- the user query targets existing scaffold content
    

Studium should recommend creating a new concept when:

- no strong existing identity match exists
    
- the concept has independent conceptual identity
    
- the concept warrants its own knowledge node
    
- the concept may be referenced from multiple learning contexts
    
- the concept occupies a distinct graph position
    

A new concept recommendation may include:

- suggested concept type
    
- suggested concept domains
    
- suggested scope
    
- suggested graph position
    
- proposed relationships
    
- missing prerequisite backlog candidates
    

Important behavior:

- Phase 2 should avoid duplicate concept recommendations
    
- Phase 2 should not merge concept notes automatically
    
- Phase 2 should not create notes directly
    

---

### 5.15 Parent, Child, and Variant Graph Position

Creating a parent or child concept does not require a separate recommendation action.

These are graph positions associated with `create_new_concept`.

Example parent recommendation:

```yaml
action: create_new_concept

suggested_concept:
  canonical_title: Gradient Descent

suggested_graph_position: parent

proposed_relationships:
  - relationship_type: parent_of
    target_title: Stochastic Gradient Descent
```

Example child/variant recommendation:

```yaml
action: create_new_concept

suggested_concept:
  canonical_title: Mini-Batch Gradient Descent

suggested_graph_position: child

proposed_relationships:
  - relationship_type: variant_of
    target_title: Gradient Descent
```

Potential graph positions:

```text
parent
child
peer
variant
independent
```

The exact representation should be finalized in the Technical Plan.

Important behavior:

- graph position belongs to the recommendation object
    
- graph position does not require a separate note type
    
- graph position should be supported by proposed relationships
    

---

### 5.16 Scaffold Module Recommendation

Examples, comparisons, derivations, code implementations, and targeted explanations should remain inside concept notes as scaffold modules.

Phase 2 should recommend adding a scaffold module when user intent targets content that belongs inside an existing concept.

Example:

```text
Input:
Learning rate schedule in SGD
```

Existing concept:

```text
Stochastic Gradient Descent
```

Potential recommendation:

```yaml
action: add_scaffold_module_to_existing_concept

target_concept:
  id: concept_stochastic_gradient_descent_a1b2c3
  title: Stochastic Gradient Descent

suggested_module:
  type: conceptual_explanation
  title: Learning Rate Schedules in SGD
  origin: user_requested
  focus: learning_rate_schedules
```

Another:

```text
Input:
Manual SGD computation example
```

Potential module type:

```text
worked_example
```

Important behavior:

- examples should not become standalone notes in the current system
    
- module recommendations should identify the parent concept
    
- the reasoning layer may suggest module type, title, and focus
    
- actual scaffold generation belongs to Create
    

---

### 5.17 Broad and Vague Concept Handling

Broadness and vagueness should be treated differently.

A broad concept may still be a valid concept.

Examples:

```text
Artificial Intelligence
Machine Learning
Calculus
Linguistics
```

Phase 2 may recommend:

```yaml
action: create_new_concept
suggested_scope: broad
```

A warning may explain:

```text
This is a broad concept and may become a major parent concept for more focused concepts.
```

Broadness should remain recommendation metadata and should not be stored as durable concept YAML in Phase 2.

Vague input should trigger clarification.

Example:

```text
optimization stuff
```

Potential interpretations:

```text
Mathematical Optimization
Gradient Descent
Convex Optimization
Model Training Optimization
Software Performance Optimization
```

Recommended action:

```yaml
action: request_clarification
```

Important behavior:

- broad does not mean invalid
    
- vague input should not produce a concept recommendation prematurely
    
- broad concepts remain ordinary concept notes
    

---

### 5.18 Structured Concept Recommendation

The primary output of Phase 2 should be a structured `ConceptRecommendation`.

Recommended actions:

```text
use_existing_concept
create_new_concept
add_learning_encounter
add_scaffold_module_to_existing_concept
mark_redundant
request_clarification
```

Example:

```yaml
recommendation:
  action: create_new_concept
  confidence: high

  suggested_concept:
    canonical_title: Backpropagation
    concept_type: algorithm
    concept_domains:
      - machine_learning
      - calculus

  suggested_scope: focused
  suggested_graph_position: peer

  possible_matches:
    - concept_id: concept_gradient_descent_x1y2z3
      title: Gradient Descent
      match_type: semantic_related
      score: 0.84

  reasoning:
    - No existing concept appears to represent Backpropagation.
    - Backpropagation has independent conceptual identity.
    - Retrieved concepts provide relevant graph context.

  proposed_relationships:
    - relationship_type: depends_on
      target_id:
      target_title: Chain Rule
      vault_status: missing
      learning_role: mathematical_prerequisite
      confidence: high
      status: agent_suggested

    - relationship_type: related_to
      target_id: concept_gradient_descent_x1y2z3
      target_title: Gradient Descent
      vault_status: found
      learning_role: supporting_concept
      confidence: high
      status: agent_suggested

  backlog_candidates:
    - title: Chain Rule
      reason: Likely mathematical prerequisite for Backpropagation
      priority: high

  warnings:
    - Some prerequisite concepts are not currently present in the vault.
```

Important behavior:

- recommendation output should be structured and validated
    
- recommendations should include evidence or reasoning
    
- possible matches should retain retrieval/match evidence
    
- recommendation objects should be consumable by Phase 4 Create
    
- recommendation objects should not mutate concept notes
    

---

### 5.19 Graph and Query Data Interface

Phase 2 should expose graph/query data needed by later phases.

This feature should support:

- ranked concept search
    
- alias lookup
    
- concept ID lookup
    
- concept-domain lookup
    
- scaffold module search
    
- learning encounter lookup
    
- relationship lookup
    
- graph neighborhood queries
    
- relationship grouping
    
- prerequisite queries
    
- parent/child/variant candidate queries
    
- semantic candidate retrieval
    

Important behavior:

- graph data should be accessible without visualization
    
- Phase 3 should be able to consume this interface for Search and graph rendering
    
- module-level hits should return parent concept context
    
- query results should provide evidence and confidence where applicable
    

Important constraints:

- no interactive graph visualization
    
- no user-facing Search interface
    
- no graph editing UI
    

---

### 5.20 CLI / Local Test Harness

Phase 2 should remain testable before the Phase 3 UI.

Potential command direction:

```text
studium graph scan
studium graph find "SGD"
studium graph inspect "Stochastic Gradient Descent"
studium graph modules "manual SGD computation"
studium graph propose "Backpropagation"
studium graph propose "Regularization" --source-type class --source-title "MSAI Machine Learning" --unit "Lecture 5"
studium graph relationships "Backpropagation"
```

Exact commands should be finalized in the Technical Plan.

Important behavior:

- CLI should exercise actual graph/index/recommendation services
    
- CLI should remain a verification harness
    
- CLI should not contain graph business logic
    

---

## 6. Key System Behaviors

By the end of Phase 2, Studium should be able to:

- rebuild a persistent concept index from the vault
    
- update the derived index when concept notes change
    
- retrieve exact concept matches
    
- retrieve alias matches
    
- retrieve semantically similar concept candidates using embeddings
    
- index and retrieve scaffold module metadata
    
- index concept domain labels without creating domain nodes
    
- narrow concept candidates before LLM reasoning
    
- use working LLM reasoning to generate structured recommendations
    
- suggest concept type and concept domains
    
- distinguish an existing concept from a new concept
    
- recommend new graph positions for concepts
    
- detect repeated source encounters
    
- recommend new learning encounters
    
- identify likely prerequisites
    
- identify missing prerequisite concepts
    
- return backlog candidates
    
- recommend scaffold modules instead of standalone example notes
    
- treat broad concepts as valid concepts
    
- request clarification for vague input
    
- return validated `ConceptRecommendation` objects
    
- expose graph/query behavior without visualization
    
- avoid direct concept-note mutation
    

---

## 7. Data and State Introduced

Phase 2 introduces:

- persistent local concept index
    
- concept index records
    
- concept embedding records/references
    
- embedding metadata needed to determine whether embeddings are stale
    
- indexed domain labels
    
- indexed scaffold module records
    
- retrieval scores/evidence
    
- concept candidate records
    
- `ConceptRecommendation`
    
- recommendation action
    
- suggested concept metadata
    
- suggested concept type
    
- suggested concept domains
    
- suggested scope
    
- suggested graph position
    
- possible match records
    
- proposed relationships
    
- relationship `learning_role`
    
- relationship `confidence`
    
- relationship persistent `status`
    
- backlog candidate records
    
- clarification candidates
    
- optional user-provided source context
    
- LLM reasoning request/response structures
    

Phase 2 amends the durable relationship model with:

```yaml
learning_role:
confidence:
status:
```

Persistent relationship status values initially include:

```text
agent_suggested
user_confirmed
```

Recommendation rejection/defer state should not be stored as an active relationship in concept-note YAML.

Full schema details should be finalized in `01 Technical Plan.md` and relevant `Data Schemas/` documentation.

---

## 8. User/System Workflow

Main concept recommendation workflow:

```text
Concept/query input
↓
Normalize input
↓
Run deterministic identity and alias matching
↓
Retrieve semantic candidates using embeddings
↓
Retrieve matching scaffold modules
↓
Collect graph, domain, relationship, and learning encounter context
↓
Narrow candidate set
↓
Run provider-agnostic LLM reasoning
↓
Validate structured reasoning output
↓
Build ConceptRecommendation
↓
Return recommendation without mutating notes
```

New concept prerequisite workflow:

```text
New concept candidate
↓
Retrieve nearby concepts/domains
↓
Reason about concept identity and likely prerequisites
↓
Check prerequisite candidates against concept index
↓
Found concepts → proposed relationships
↓
Missing concepts → backlog candidates
↓
Return ConceptRecommendation
```

Learning encounter workflow:

```text
Concept + source metadata
↓
Match concept
↓
Compare source metadata against existing learning encounters
↓
Existing encounter → avoid duplicate
↓
New encounter → recommend add_learning_encounter
↓
Contribution remains pending unless optional user context is supplied
```

Module recommendation workflow:

```text
User query
↓
Match existing concept/module context
↓
Determine query targets sub-concept learning content
↓
Suggest scaffold module type/title/focus
↓
Return add_scaffold_module_to_existing_concept recommendation
```

---

## 9. Scope of This Phase

This phase includes:

- persistent local concept indexing
    
- SQLite-backed index direction
    
- vault scanning and index synchronization
    
- concept identity indexing
    
- concept domain indexing
    
- scaffold module indexing
    
- lexical concept matching
    
- embedding generation
    
- semantic candidate retrieval
    
- hybrid candidate ranking
    
- provider-agnostic LLM reasoning
    
- narrowed-candidate reasoning
    
- structured LLM outputs
    
- existing concept detection
    
- duplicate recommendation prevention
    
- relationship suggestion
    
- relationship direction reasoning
    
- relationship learning roles
    
- relationship confidence
    
- relationship confirmation status model
    
- prerequisite detection
    
- backlog candidate output
    
- learning encounter comparison
    
- optional user-supplied source context preservation
    
- concept type/domain suggestions
    
- graph position suggestions
    
- scaffold module recommendations
    
- broad concept handling
    
- vague input clarification
    
- `ConceptRecommendation`
    
- graph/query data interfaces
    
- CLI/test harness verification
    

---

## 10. Non-Goals

This phase does not include:

- direct concept note mutation from recommendations
    
- user approval UI
    
- Create interface
    
- scaffold content generation
    
- source file parsing
    
- PDF processing
    
- video processing
    
- transcript processing
    
- source chunking
    
- source RAG
    
- automatic source contribution analysis
    
- interactive graph visualization
    
- Search UI
    
- graph editing UI
    
- Backlog persistence/lifecycle
    
- Agent Review
    
- Retention logic
    
- Mastery scoring
    
- domain graph nodes
    
- standalone example notes
    

---

## 11. Relationship to Other Phases

### Depends On

- Phase 1: Vault Storage Core
    

### Enables

- Phase 3: Search
    
- Phase 4: Create
    
- Phase 5: Source Content Intelligence
    
- Phase 6: Agent Review
    
- Phase 7: Backlog
    
- Phase 8: Retention
    
- Phase 9: Mastery Dashboard
    

### Later Phase Dependencies

- Phase 3 depends on Phase 2 because Search needs ranked concept/module retrieval and graph/query interfaces.
    
- Phase 4 depends on Phase 2 because Create needs `ConceptRecommendation` to determine the appropriate learning workflow.
    
- Phase 5 depends on Phase 2 because source analysis requires concept and learning encounter identity.
    
- Phase 6 depends on Phase 2 because relationship review requires indexed graph context.
    
- Phase 7 depends on Phase 2 because missing prerequisites become backlog candidates.
    
- Phase 8 depends on Phase 2 because retention may use prerequisite and supporting concept structure.
    
- Phase 9 depends on Phase 2 because Mastery needs stable graph structure and concept domains.
    

---

## 12. Risks and Design Concerns

- SQLite synchronization may become unnecessarily complex if the index attempts to become a second source of truth.
    
- Embedding model choice may affect semantic match quality and local performance.
    
- Embedding similarity may over-rank adjacent concepts as duplicate concepts.
    
- LLM reasoning may produce unstable recommendations if prompts and structured outputs are not tightly designed.
    
- Small LLMs may not reliably reason about relationship direction for difficult technical concepts.
    
- Provider abstraction may become overengineered if too many model-provider capabilities are anticipated early.
    
- Concept domain labels may become inconsistent without normalization.
    
- Concept domains may be confused with concepts of the same name.
    
- Relationship learning roles may become overly specific or duplicate structural relationship semantics.
    
- Recommendation actions may become too numerous if graph position and workflow behavior are modeled as separate actions.
    
- Prerequisite detection may produce excessive backlog candidates.
    
- Source metadata comparison may produce duplicate encounters if normalization rules are weak.
    
- Broad concept detection may incorrectly discourage valid parent concepts.
    
- Recommendation confidence needs a clear meaning and should not imply calibrated probability unless actually calibrated.
    
- Testing LLM reasoning requires deterministic test strategies that do not depend on live model variability.
    

---

## 13. Phase Decisions / Amendments

The original Phase 2 roadmap has been amended based on finalized Phase 1 schemas and later roadmap decisions.

Decisions/amendments:

- Phase 2 introduces a persistent local concept index.
    
- SQLite is the expected index direction, with implementation details deferred to the Technical Plan.
    
- Working embeddings are a Phase 2 requirement.
    
- Semantic retrieval should operate over concept titles, aliases, selected overview content, and relevant metadata.
    
- Phase 2 implements actual provider-agnostic LLM-assisted reasoning.
    
- The recommendation pipeline is rule-based matching → embedding retrieval → narrowed candidate set → LLM reasoning → structured recommendation.
    
- Small LLMs should be evaluated for narrowed concept reasoning tasks.
    
- Phase 3 consumes concept intelligence rather than introducing LLM concept reasoning.
    
- `note_subtype` references are removed.
    
- Phase 2 uses `concept_type` and `concept_domains`.
    
- Concept domains are graph-space labels, not graph nodes.
    
- A domain label and concept note may share the same name.
    
- Phase 2 may suggest new concept domains.
    
- Domain inference combines nearby indexed domains with LLM reasoning.
    
- Scaffold modules are indexed and searchable but are not graph nodes.
    
- Examples never become standalone example notes.
    
- Example intent should become a scaffold module recommendation.
    
- “Attach as section” is replaced by “add scaffold module to existing concept.”
    
- Relationship `role` remains removed.
    
- Phase 2 introduces `learning_role`.
    
- Learning roles should describe what the target concept represents for learning the current concept.
    
- Phase 2 introduces relationship confidence.
    
- Phase 2 introduces persistent relationship statuses `agent_suggested` and `user_confirmed`.
    
- Rejected and deferred recommendations should not be stored as active concept relationships.
    
- Phase 2 produces recommendation objects but does not mutate concept notes.
    
- Broad concepts are valid concepts.
    
- No overview/map note type or recommendation action is needed.
    
- Broadness may be included as recommendation metadata.
    
- Parent and child concept creation use `create_new_concept` plus graph position and proposed relationships.
    
- `create_parent_concept` and `create_child_concept` actions are not needed.
    
- User-provided source context is supported optionally but is not required or a core success criterion.
    
- Automatic source contribution analysis remains Phase 5.
    
- Backlog candidates are produced but not persisted.
    
- Graph/query data is built in Phase 2.
    
- Graph visualization remains Phase 3.
    

Foundational ADR candidates after implementation:

- Use SQLite as a rebuildable derived concept index.
    
- Use hybrid lexical and embedding retrieval.
    
- Use narrowed-candidate LLM reasoning for concept recommendations.
    
- Keep LLM reasoning provider-agnostic.
    
- Treat concept domains as graph-space labels rather than graph nodes.
    
- Index scaffold modules under parent concept nodes.
    
- Store relationship learning role, confidence, and confirmation status.
    
- Use structured `ConceptRecommendation` objects as the boundary between concept intelligence and future Create workflows.
    

---

## 14. Expected Outputs

Expected outputs:

### Working code

- vault-to-index scanner
    
- persistent concept index
    
- index synchronization behavior
    
- concept identity lookup
    
- alias lookup
    
- concept domain indexing
    
- scaffold module indexing
    
- learning encounter indexing
    
- relationship indexing
    
- embedding generation
    
- embedding persistence/reference behavior
    
- semantic candidate search
    
- hybrid candidate ranking
    
- provider-agnostic LLM reasoning interface
    
- working reasoning implementation
    
- structured reasoning validation
    
- concept matching service
    
- relationship recommendation service
    
- prerequisite detection
    
- backlog candidate generation
    
- learning encounter comparison
    
- scaffold module recommendation
    
- `ConceptRecommendation` generation
    
- graph/query interfaces
    
- CLI/local test harness
    

### Documentation

- amended Phase 2 roadmap
    
- Phase 2 Technical Plan
    
- Phase 2 Branch Plan
    
- branch implementation docs
    
- concept notes for important technical concepts
    
- architecture/decision updates after implementation
    

### Schemas/models

- concept index record
    
- indexed scaffold module record
    
- embedding metadata model
    
- concept candidate model
    
- match evidence model
    
- LLM reasoning request model
    
- structured reasoning response model
    
- `ConceptRecommendation`
    
- proposed relationship model
    
- relationship `learning_role`
    
- relationship confidence
    
- relationship status amendment
    
- backlog candidate model
    
- graph position recommendation model
    
- clarification candidate model
    

### Tests/fixtures

- exact concept match fixtures
    
- alias match fixtures
    
- semantic near-match fixtures
    
- semantically related but distinct concept fixtures
    
- domain suggestion fixtures
    
- scaffold module match fixtures
    
- existing source encounter fixtures
    
- new source encounter fixtures
    
- prerequisite found/missing fixtures
    
- parent concept candidate fixtures
    
- child/variant concept fixtures
    
- broad concept fixtures
    
- vague input fixtures
    
- mocked/deterministic LLM reasoning fixtures
    
- structured recommendation golden tests
    
- index rebuild/synchronization tests
    
- embedding retrieval tests
    
- end-to-end recommendation tests
    

---

## 15. Completion Standard

Phase 2 is complete when Studium can build and query a persistent concept intelligence layer over the Phase 1 vault.

More specifically, Phase 2 is complete when:

- the test vault can be scanned into a persistent local concept index
    
- the index can be rebuilt from the vault
    
- concept identities, aliases, domains, relationships, learning encounters, and scaffold modules are indexed
    
- exact and alias matches work
    
- working embeddings are generated and used for semantic concept retrieval
    
- hybrid retrieval returns useful narrowed concept candidates
    
- provider-agnostic LLM reasoning operates over narrowed candidates
    
- a working LLM implementation can produce validated structured reasoning output
    
- the system can distinguish likely existing concepts from new concepts
    
- concept type and domain suggestions can be produced
    
- parent, child, variant, peer, and independent graph positions can be suggested
    
- prerequisite relationships can be proposed with correct direction
    
- proposed relationships can include learning role, confidence, and `agent_suggested` status
    
- missing prerequisites produce backlog candidates
    
- existing and new learning encounters can be distinguished
    
- scaffold module intent can be distinguished from new concept intent
    
- examples are recommended as scaffold modules rather than standalone notes
    
- broad valid concepts can be recommended for creation
    
- vague inputs produce clarification recommendations
    
- structured `ConceptRecommendation` objects are produced
    
- recommendations do not directly mutate concept notes
    
- graph/query behavior can be verified through CLI commands or a local test harness
    

---

## 16. Use Cases / Criteria-Met Scenarios

### UC-01: Exact Existing Concept Match

**Scenario:**  
The vault contains `Stochastic Gradient Descent`. The user enters `Stochastic Gradient Descent`.

**Expected behavior:**

- deterministic title matching identifies the concept
    
- existing concept is ranked first
    
- recommendation action is `use_existing_concept`
    
- duplicate concept creation is not recommended
    

**Criteria met:**

- concept identity lookup
    
- exact matching
    
- duplicate prevention
    
- structured recommendation
    

---

### UC-02: Alias Match

**Scenario:**  
The vault contains `Stochastic Gradient Descent` with alias `SGD`. The user enters `SGD`.

**Expected behavior:**

- alias lookup identifies the existing concept
    
- recommendation action is `use_existing_concept`
    
- match evidence identifies the alias match
    

**Criteria met:**

- alias indexing
    
- alias matching
    
- recommendation evidence
    

---

### UC-03: Semantic Match With Distinct Concepts

**Scenario:**  
The vault contains `Gradient Descent` and `Mini-Batch Gradient Descent`. The user enters `Stochastic Gradient Descent`.

**Expected behavior:**

- embedding retrieval returns semantically nearby concepts
    
- reasoning determines the concepts are related but not identical
    
- new concept creation may be recommended
    
- graph position and relationships are proposed
    

**Criteria met:**

- embedding retrieval
    
- narrowed candidate reasoning
    
- same-vs-related concept reasoning
    
- graph position suggestion
    

---

### UC-04: Existing Concept With New Learning Encounter

**Scenario:**  
`Stochastic Gradient Descent` exists with a Hands-On Machine Learning Chapter 4 encounter. The user introduces the concept with `MSAI Machine Learning - Lecture 3`.

**Expected behavior:**

- existing concept is identified
    
- source metadata does not match the existing encounter
    
- recommendation action is `add_learning_encounter`
    
- proposed contribution status is `pending`
    
- source contribution is not inferred
    

**Criteria met:**

- concept match
    
- learning encounter comparison
    
- new encounter recommendation
    
- source-content boundary
    

---

### UC-05: Existing Concept With Repeated Learning Encounter

**Scenario:**  
The concept already contains the same source type, title, and unit metadata provided by the user.

**Expected behavior:**

- existing concept is identified
    
- existing encounter is identified
    
- duplicate encounter is not recommended
    
- recommendation may be `mark_redundant` or `use_existing_concept` depending on additional intent
    

**Criteria met:**

- learning encounter indexing
    
- source metadata comparison
    
- duplicate encounter prevention
    

---

### UC-06: New Concept With Existing Related Concepts

**Scenario:**  
The user enters `Backpropagation`.

The vault contains:

```text
Gradient Descent
Neural Networks
Loss Functions
Chain Rule
Partial Derivatives
```

**Expected behavior:**

- no existing Backpropagation identity match is found
    
- semantic retrieval returns relevant candidate concepts
    
- LLM reasoning recommends `create_new_concept`
    
- concept type and domains are suggested
    
- relevant graph relationships are proposed
    

**Criteria met:**

- semantic retrieval
    
- LLM reasoning
    
- concept metadata suggestion
    
- relationship suggestion
    

---

### UC-07: New Concept With Missing Mathematical Prerequisites

**Scenario:**  
The user enters `Backpropagation`.

The vault does not contain:

```text
Chain Rule
Partial Derivatives
```

**Expected behavior:**

- reasoning identifies likely prerequisite concepts
    
- index lookup determines they are missing
    
- proposed relationships include `learning_role: mathematical_prerequisite`
    
- missing concepts become backlog candidates
    
- no backlog items are persisted
    

**Criteria met:**

- prerequisite reasoning
    
- learning roles
    
- vault existence checking
    
- backlog candidate generation
    

---

### UC-08: Correct Relationship Direction

**Scenario:**  
The reasoning layer identifies Chain Rule as necessary for understanding Backpropagation.

**Expected behavior:**

- recommendation proposes `Backpropagation depends_on Chain Rule`
    
- inverse graph meaning can represent `Chain Rule prerequisite_for Backpropagation`
    
- direction is not determined from embedding similarity alone
    

**Criteria met:**

- relationship reasoning
    
- direction handling
    
- LLM-assisted semantic judgment
    

---

### UC-09: Relationship Learning Role

**Scenario:**  
Backpropagation has relationships to Chain Rule and Neural Networks.

**Expected behavior:**

- Chain Rule may receive `learning_role: mathematical_prerequisite`
    
- Neural Networks may receive `learning_role: foundational_theory` or another appropriate learning role
    
- learning roles describe the target concept's purpose for learning the source concept
    

**Criteria met:**

- learning role model
    
- relationship intelligence
    
- structured proposed relationships
    

---

### UC-10: New Parent Concept Candidate

**Scenario:**  
The vault contains `Stochastic Gradient Descent`, but does not contain `Gradient Descent`. The user enters `Gradient Descent`.

**Expected behavior:**

- semantic retrieval finds Stochastic Gradient Descent
    
- reasoning identifies Gradient Descent as a broader concept
    
- action remains `create_new_concept`
    
- suggested graph position is `parent`
    
- a parent/child or variant relationship is proposed
    

**Criteria met:**

- semantic retrieval
    
- parent graph position suggestion
    
- unified create-new-concept action
    

---

### UC-11: New Child or Variant Concept Candidate

**Scenario:**  
The vault contains `Gradient Descent`. The user enters `Mini-Batch Gradient Descent`.

**Expected behavior:**

- system does not collapse the input into Gradient Descent
    
- action is `create_new_concept`
    
- suggested graph position is `child` or `variant`
    
- `variant_of` or another appropriate relationship is proposed
    

**Criteria met:**

- related-but-distinct concept reasoning
    
- graph position suggestion
    
- relationship proposal
    

---

### UC-12: Targeted Scaffold Module Request

**Scenario:**  
The vault contains `Stochastic Gradient Descent`. The user enters `Learning rate schedules in SGD`.

**Expected behavior:**

- existing concept is identified
    
- reasoning determines the request targets focused learning content inside the concept
    
- recommendation action is `add_scaffold_module_to_existing_concept`
    
- suggested module type, title, and focus are returned
    

**Criteria met:**

- module intent reasoning
    
- parent concept identification
    
- scaffold module recommendation
    

---

### UC-13: Worked Example Request

**Scenario:**  
The user enters `Manual SGD computation example`.

**Expected behavior:**

- the system identifies example intent
    
- the related parent concept is identified
    
- a `worked_example` scaffold module is recommended
    
- no standalone example note is recommended
    

**Criteria met:**

- scaffold module classification
    
- example handling
    
- concept-note-only graph model
    

---

### UC-14: Scaffold Module Search Match

**Scenario:**  
A concept note already contains a module titled `Manual SGD Update`. The user searches or proposes `manual SGD computation`.

**Expected behavior:**

- indexed scaffold module is retrieved
    
- parent concept is returned
    
- system recognizes potentially existing module content
    
- duplicate scaffold module creation is not blindly recommended
    

**Criteria met:**

- scaffold module indexing
    
- module-level semantic retrieval
    
- parent concept resolution
    

---

### UC-15: Concept Domain Suggestion From Existing Knowledge Space

**Scenario:**  
The user enters `Stochastic Gradient Descent`.

Nearby indexed concepts use:

```text
machine_learning
optimization
```

**Expected behavior:**

- embedding retrieval finds nearby concepts
    
- indexed domain labels become candidate domains
    
- reasoning evaluates the candidates
    
- recommendation suggests appropriate concept domains
    

**Criteria met:**

- domain indexing
    
- semantic neighborhood use
    
- LLM domain reasoning
    

---

### UC-16: New Domain Suggestion

**Scenario:**  
The user enters a valid concept from a knowledge area not yet represented in the vault.

**Expected behavior:**

- no useful existing domain labels are found
    
- reasoning may propose new domain strings
    
- proposed domains remain recommendation metadata
    
- no domain graph node is created
    

**Criteria met:**

- flexible domain model
    
- new domain suggestion
    
- domain/concept separation
    

---

### UC-17: Broad Valid Concept

**Scenario:**  
The user enters `Artificial Intelligence`.

**Expected behavior:**

- system recognizes a valid concept identity
    
- concept creation may be recommended
    
- suggested scope is `broad`
    
- system may warn that the concept is likely to become a major parent concept
    
- system does not require the user to narrow the concept
    

**Criteria met:**

- broad concept handling
    
- concept scope recommendation
    
- broad-vs-vague distinction
    

---

### UC-18: Vague Input

**Scenario:**  
The user enters `optimization stuff`.

**Expected behavior:**

- system does not immediately recommend creating a concept
    
- candidate interpretations are identified
    
- recommendation action is `request_clarification`
    
- no concept note mutation occurs
    

**Criteria met:**

- ambiguity detection
    
- semantic candidate retrieval
    
- clarification recommendation
    

---

### UC-19: Optional User-Provided Source Context

**Scenario:**  
The user provides a source and voluntarily adds context explaining what the encounter clarified.

**Expected behavior:**

- user-provided context is preserved
    
- proposed contribution status may be `user_described`
    
- reasoning may use the supplied context
    
- system does not claim the source itself has been analyzed
    

**Criteria met:**

- optional user context
    
- source-content boundary
    
- learning encounter recommendation
    

---

### UC-20: Provider-Agnostic LLM Reasoning

**Scenario:**  
A narrowed set of concept candidates is passed to the reasoning layer.

**Expected behavior:**

- reasoning request uses a provider-independent interface
    
- a configured LLM produces structured reasoning output
    
- output is validated against the expected schema
    
- invalid output is rejected or handled safely
    
- `ConceptRecommendation` is produced from valid reasoning
    

**Criteria met:**

- working LLM reasoning
    
- provider abstraction
    
- structured output
    
- safe output validation
    

---

### UC-21: No Direct Graph Mutation

**Scenario:**  
Studium recommends new relationships and a new learning encounter.

**Expected behavior:**

- `ConceptRecommendation` contains proposed updates
    
- indexed or Markdown concept data is not directly mutated
    
- later Create workflow can consume the recommendation
    

**Criteria met:**

- recommendation boundary
    
- mutation separation
    
- Phase 4 readiness
    

---

### UC-22: Persistent Index Rebuild

**Scenario:**  
The derived concept index is deleted or considered stale.

**Expected behavior:**

- Studium rescans Phase 1 concept notes
    
- concept, domain, module, relationship, and encounter records are rebuilt
    
- semantic index state can be regenerated
    
- the vault remains the durable source
    

**Criteria met:**

- persistent index
    
- rebuildable derived state
    
- vault source-of-truth principle
    

---

## 17. Future Enhancements

Future enhancements:

- richer semantic reranking
    
- improved embedding model evaluation
    
- relationship conflict detection
    
- contradiction detection across concepts
    
- calibrated recommendation confidence
    
- richer graph clustering
    
- domain normalization assistance
    
- relationship cleanup suggestions
    
- graph-wide anomaly detection
    
- learned recommendation ranking from user approval history
    
- specialized reasoning models for particular knowledge domains
    
- richer module-level semantic retrieval
    

---

## 18. Open Questions

Open questions for the Technical Plan:

- What SQLite tables and indexes are required?
    
- How should vault/index synchronization detect created, updated, moved, and deleted notes?
    
- What content should be embedded for each concept?
    
- Should title, aliases, and concept overview use one combined embedding or separate embeddings?
    
- What embedding model best fits local concept retrieval requirements?
    
- Where and how should embeddings be stored?
    
- How should stale embeddings be detected?
    
- How should lexical and embedding scores be combined?
    
- What candidate limit should be passed to LLM reasoning?
    
- What provider-agnostic LLM interface should be used?
    
- What small LLMs should be evaluated for narrowed concept reasoning?
    
- What structured output schema should the reasoning layer use?
    
- How should live LLM behavior be separated from deterministic tests?
    
- What exact initial `learning_role` values should be supported?
    
- How should relationship confidence be defined without implying calibrated probability?
    
- What exact match/source normalization rules should be used?
    
- How should concept domains be normalized?
    
- What exact graph position enum should be used?
    
- How should scaffold module content be represented in semantic retrieval?
    
- What exact `ConceptRecommendation` schema should Phase 2 expose?
    
- What CLI commands best validate the complete concept intelligence workflow?