## 1. Technical Purpose

Phase 2 implements Studium’s first concept-intelligence layer.

Phase 1 established how concept notes are represented, validated, parsed, serialized, and safely written. Phase 2 builds a rebuildable derived index over those notes and introduces the retrieval and reasoning services needed to understand:

- which concepts already exist
    
- which terms are aliases
    
- which concepts are semantically related but distinct
    
- how concepts occupy the knowledge graph
    
- which content belongs inside an existing concept as a scaffold module
    
- whether a source encounter is new, repeated, or more specific than an existing encounter
    
- which prerequisites may exist or be missing
    
- what concept action should be recommended
    

The core pipeline is:

```text
Vault concept notes
↓
Persistent derived SQLite index
↓
Deterministic matching
↓
Weighted lexical retrieval
↓
Embedding retrieval
↓
Candidate fusion
↓
Task-specific LLM reasoning when required
↓
Deterministic verification and assembly
↓
Structured ConceptRecommendation
```

Phase 2 may write and rebuild derived SQLite state.

Phase 2 must not directly mutate concept-note Markdown in response to recommendations.

---

## 2. Roadmap Capabilities

The technical implementation must support the following roadmap capabilities:

- persistent local concept indexing
    
- incremental vault/index synchronization
    
- complete index rebuilds
    
- concept identity lookup
    
- alias lookup and alias proposals
    
- concept-domain indexing
    
- scaffold module indexing
    
- learning encounter indexing
    
- relationship indexing
    
- weighted SQLite full-text retrieval
    
- concept identity embeddings
    
- concept semantic embeddings
    
- scaffold module embeddings
    
- hybrid candidate retrieval
    
- configurable candidate fusion
    
- module-level result locations
    
- one-hop graph queries
    
- provider-agnostic LLM reasoning
    
- small local LLM evaluation
    
- structured LLM outputs
    
- deterministic recommendation assembly
    
- relationship direction inference
    
- learning-role inference
    
- prerequisite detection
    
- backlog candidate generation
    
- source encounter comparison
    
- action-specific recommendation models
    
- recommendation fallback behavior
    
- search and recommendation diagnostics
    
- CLI-based verification
    
- embedding and reasoning evaluation harnesses
    

---

## 3. Technical Scope

Phase 2 includes:

- schema version 2 for concept-note metadata
    
- amended relationship metadata
    
- optional typed external source identifiers
    
- SQLAlchemy Core database access
    
- repository abstractions
    
- SQLite-derived index
    
- SQLite FTS-based lexical retrieval
    
- vector search abstraction
    
- NumPy exact vector-search implementation
    
- benchmark of SQLite extension-backed vector search
    
- local embedding provider
    
- embedding input construction and hashing
    
- embedding batching
    
- incremental synchronization
    
- full index rebuild
    
- invalid/stale index record handling
    
- duplicate concept-ID detection
    
- search document materialization
    
- weighted full-text search
    
- reciprocal rank fusion
    
- concept search service
    
- graph query service
    
- source encounter matcher
    
- LLM provider abstraction
    
- OpenAI-compatible local model server adapter
    
- deterministic reasoning test provider
    
- versioned task-specific reasoning definitions
    
- one structured-output repair attempt
    
- recommendation assembler
    
- discriminated recommendation models
    
- recommendation failure model
    
- CLI diagnostics
    
- curated evaluation datasets
    
- model/configuration comparison reports
    

Phase 2 does not include:

- Search UI
    
- interactive knowledge graph rendering
    
- filesystem watching
    
- direct note mutation from recommendations
    
- recommendation approval UI
    
- scaffold content generation
    
- source-file parsing or source RAG
    
- source contribution analysis
    
- persistent backlog items
    
- persistent recommendation history
    
- recommendation caching
    
- graph-editing workflows
    
- multi-hop graph reasoning as a core requirement
    
- standalone example notes
    
- durable paper-note nodes
    
- generic knowledge-node abstractions
    

---

## 4. System Components

### 4.1 Configuration Layer

The configuration layer should define:

- active vault path
    
- application data directory
    
- index database location
    
- active embedding provider
    
- active embedding model identifier
    
- embedding batch size
    
- embedding dimensions when configurable
    
- vector backend
    
- lexical result limits
    
- semantic result limits
    
- module result limits
    
- final reasoning candidate limit
    
- reciprocal-rank-fusion configuration
    
- local LLM server endpoint
    
- local LLM model identifier
    
- reasoning timeouts
    
- structured-output repair timeout
    
- SQLite busy timeout
    
- diagnostics/logging settings
    
- evaluation configuration
    

Configuration should be validated before services initialize.

Configuration must not be scattered across service modules.

---

### 4.2 Application Data and Vault Identity

The SQLite database should live outside the Obsidian vault.

Recommended logical location:

```text
<Studium application data>/
  indexes/
    <vault_identifier>/
      concept-index.sqlite
```

The vault remains portable Markdown knowledge.

The derived database may create SQLite-specific supporting files such as write-ahead-log files and should not appear as ordinary vault content.

Phase 2 should structurally support more than one indexed vault while allowing the CLI to configure one active vault at a time.

Initial vault identity may derive from the canonical vault path. The design should allow a persisted vault identifier later without changing service contracts.

The index should retain the canonical vault path for diagnostics.

---

### 4.3 Database Engine and Runtime Configuration

SQLAlchemy Core should manage SQLite connections, table definitions, transactions, and query execution.

Repository abstractions should own database operations.

The project should not use a full ORM entity model for the derived index.

SQLite-specific search and vector operations may use explicit SQL where SQLAlchemy abstractions are insufficient.

Recommended SQLite connection settings:

```text
foreign_keys = ON
journal_mode = WAL
synchronous = NORMAL
busy_timeout = configured value
```

Purpose:

- `foreign_keys = ON` enforces parent/child index integrity.
    
- `journal_mode = WAL` allows readers to continue using a committed index snapshot while synchronization writes changes.
    
- `synchronous = NORMAL` balances performance and durability for rebuildable derived data.
    
- `busy_timeout` allows brief lock contention to resolve before failing.
    

Connection hooks should apply these settings centrally.

Individual services should not create unmanaged database connections.

---

### 4.4 Index Schema Manager

The concept-note schema version and the SQLite index schema version are independent.

```text
Concept-note schema version
= Markdown/YAML storage format

Index schema version
= derived SQLite representation
```

Concept notes move to:

```yaml
schema_version: 2
```

The index should maintain its own integer schema version.

Because SQLite is fully rebuildable, Phase 2 should not implement index database migrations.

If the configured index schema version differs from the database version:

```text
Reject normal index use
↓
Require index rebuild
↓
Delete/recreate derived schema
↓
Rescan vault
```

The schema manager should:

- create a new index
    
- inspect the current index schema version
    
- reject incompatible index schemas
    
- rebuild an index
    
- preserve no irreplaceable data in SQLite
    

---

### 4.5 Repository Layer

Repositories should provide focused database access without embedding business logic.

Broad repositories may include:

- index metadata repository
    
- indexed-file repository
    
- concept repository
    
- alias repository
    
- domain repository
    
- learning encounter repository
    
- relationship repository
    
- scaffold module repository
    
- search-document repository
    
- FTS repository
    
- embedding repository
    
- invalid-record repository
    

Repositories should:

- execute SQL
    
- map rows into typed records
    
- support transactions
    
- enforce expected query boundaries
    
- avoid deciding recommendation behavior
    

Services should not contain raw SQL except through a clearly justified SQLite-specific adapter.

---

### 4.6 Vault Scanner and Index Synchronizer

The vault scanner discovers Phase 1/Phase 2 concept-note files.

The synchronizer compares discovered files with existing indexed-file records.

Normal synchronization should be incremental.

For each file:

```text
Discover file
↓
Calculate file hash
↓
Compare with indexed file record
├── unchanged → skip
├── new → parse, validate, project, embed, index
├── changed → parse, validate, project, regenerate affected data
└── removed → delete derived index records
```

The synchronizer should recognize moves and renames through stable concept ID:

```text
same concept_id
different file_path
→ update path for same concept
```

It should not treat a move as a concept deletion and recreation.

A separate rebuild operation should:

- remove or recreate the index
    
- recreate all tables and search structures
    
- rescan all valid notes
    
- regenerate all required embeddings
    
- produce a full `SyncReport`
    

---

### 4.7 Index Projection Builder

The projection builder converts a parsed concept note into the exact derived records needed by the index.

It should construct:

- concept record
    
- alias records
    
- domain records
    
- learning encounter records
    
- relationship records
    
- scaffold module records
    
- concept search document
    
- module search documents
    
- embedding documents
    
- hash inputs
    
- source fingerprints
    

It should not reimplement Markdown parsing.

It should consume Phase 1 parser/schema outputs.

A projected index representation should be deterministic: the same valid note should produce the same projected records and hash inputs.

---

### 4.8 Text Normalization Service

Matching normalization should include:

- Unicode normalization
    
- case folding
    
- leading/trailing whitespace removal
    
- repeated whitespace collapsing
    
- underscore-to-space normalization
    
- hyphen-to-space normalization for lookup
    
- non-semantic surrounding punctuation removal
    

Original strings must remain unchanged for display and metadata proposals.

Initial normalization should not aggressively:

- stem words
    
- remove plural forms
    
- rewrite technical terminology
    
- invent aliases
    
- change durable metadata
    

Normalization supports matching; it does not alter the source note.

---

### 4.9 Full-Text Search Layer

SQLite full-text search should provide ranked lexical retrieval without manually scanning every concept in Python.

The system should materialize derived search documents.

#### Concept search document

Should contain separately weighted fields such as:

- canonical title
    
- aliases
    
- concept domains
    
- Concept Overview plaintext
    

#### Module search document

Should contain:

- module title
    
- module type
    
- module focus
    
- module body plaintext or initial indexed segment
    

Full-text weighting priority should initially favor:

1. canonical title
    
2. aliases
    
3. module title
    
4. concept overview
    
5. domains
    
6. module body
    

Exact title and alias equality remain outside FTS and should be treated as stronger deterministic evidence.

FTS retrieves lexical candidates; it must not determine concept identity by itself.

---

### 4.10 Embedding Provider

The embedding provider should expose provider-independent operations equivalent to:

```text
embed_query(text)
embed_documents(texts)
model_metadata()
```

Batch document embedding is required.

The first implementation should run locally and offline on the development machine.

All stored vectors and query vectors used in a comparison must come from the same embedding space.

The provider should expose:

- model identifier
    
- model revision
    
- vector dimension
    
- normalization behavior
    
- maximum supported input length
    
- batch behavior
    

Embedding model selection should be empirical through the Phase 2 evaluation harness.

The selected model should prioritize:

- local execution
    
- low memory use
    
- short technical-text retrieval quality
    
- batch performance
    
- stable model/version identification
    
- acceptable Recall@K and MRR
    
- operational simplicity
    

---

### 4.11 Embedding Input Builder

Phase 2 should maintain distinct embedding purposes.

#### Identity embedding

Purpose:

> Determine whether a query may refer to a particular concept identity.

Input:

```text
Title: <canonical title>
Aliases: <aliases>
```

#### Semantic concept embedding

Purpose:

> Represent what the concept means and retrieve related concepts.

Input:

```text
Title: <canonical title>
Aliases: <aliases>
Concept Type: <concept type>
Domains: <concept domains>
Overview: <Concept Overview plaintext>
```

#### Scaffold module embedding

Purpose:

> Retrieve focused content contained inside a concept note.

Input:

```text
Module Title: <module title>
Module Type: <module type>
Focus: <module focus>
Body: <indexed module segment>
```

#### Query embedding

Generated at query time from the normalized user query.

Query embeddings do not need to be persisted.

---

### 4.12 Embedding Documents and Segments

The vector schema should not assume that one module will always equal one vector.

Use an embedding-document representation with:

- owner type
    
- owner ID
    
- parent concept ID
    
- segment ID
    
- embedding type
    
- source text
    
- source location metadata
    

Initial owner types may include:

```text
concept
scaffold_module
```

Initial embedding types may include:

```text
concept_identity
concept_semantic
module_semantic
```

For Phase 2:

```text
one module
→ one segment
→ one module embedding
```

The schema should already support:

```text
one module
→ multiple segments
→ multiple vectors
```

This prepares for future long-module chunking without implementing the full chunking strategy now.

Search results must retain:

```text
segment
→ module
→ parent concept
```

Even when module hits collapse under the parent concept for concept-level ranking, the exact matched module and segment must remain available.

---

### 4.13 Embedding Hashes

Different vector types should have independent hashes based on their exact input text.

Required hash layers:

#### `file_hash`

Hash of the complete Markdown file.

Detects any file change.

#### `index_projection_hash`

Hash of all parsed values represented in the derived index.

Determines whether normalized index records changed.

#### `identity_input_hash`

Hash of the identity-embedding input.

Changes when the canonical title or aliases change.

#### `semantic_input_hash`

Hash of the semantic concept-embedding input.

Changes when title, aliases, concept type, domains, or Concept Overview change.

#### `module_input_hash`

One per module segment.

Changes only when the indexed module input changes.

The synchronizer should regenerate only vectors whose input hash or model metadata changed.

Examples:

```text
Overview changed
→ semantic concept embedding regenerated
→ identity embedding reused
→ module embeddings reused
```

```text
Alias added
→ identity embedding regenerated
→ semantic concept embedding regenerated
→ module embeddings reused
```

```text
One module changed
→ that module embedding regenerated
→ unrelated module/concept embeddings reused
```

---

### 4.14 Vector Store and Search Abstraction

Vector storage and retrieval should sit behind a `VectorStore` or `VectorSearchBackend` interface.

The technical implementation should benchmark:

#### NumPy exact search

- vectors persisted in SQLite
    
- relevant vectors loaded into memory
    
- vectors normalized
    
- cosine similarity implemented as normalized dot product
    
- exact top-K retrieval performed with NumPy
    

#### SQLite extension-backed search

- vectors stored and queried through a compatible SQLite vector extension
    
- extension installation and Apple Silicon compatibility tested
    
- indexed nearest-neighbor support evaluated where available
    

The chosen Phase 2 backend should be based on:

- installation reliability
    
- local compatibility
    
- search correctness
    
- warm and cold latency
    
- memory use
    
- rebuild speed
    
- implementation complexity
    
- expected personal-vault scale
    

Services must not depend directly on a particular vector extension.

Normalized cosine similarity should be the default metric unless the selected embedding model explicitly requires a different approach.

---

### 4.15 Hybrid Retrieval and Rank Fusion

Lexical and vector retrieval should run independently and may execute in parallel.

```text
Weighted FTS ────────────────┐
Identity vector search ──────┤
Semantic vector search ──────┼→ candidate merge
Module vector search ────────┘
```

The result lists use incompatible raw-score scales.

Initial candidate fusion should therefore use weighted reciprocal rank fusion.

Conceptually:

```text
fused_score(candidate)
=
sum over retrieval channels:
channel_weight / (constant + rank)
```

The exact constant and weights should be configurable.

Deterministic matches are not ordinary fusion inputs:

- stable ID match
    
- normalized canonical-title match
    
- approved-alias match
    

These are authoritative evidence and should follow the deterministic fast path.

Fusion should:

- merge duplicate concept candidates by concept ID
    
- preserve every retrieval channel that supported the candidate
    
- preserve component ranks and scores
    
- collapse module hits under their parent concept for concept ranking
    
- retain exact module and segment locations
    
- preserve exact deterministic matches
    
- obey configurable candidate limits
    

Sophisticated candidate diversification is deferred.

---

### 4.16 Graph Query Service

The graph query service should operate over indexed relationship records.

Initial graph query support should include:

- direct relationships for a concept
    
- relationships grouped by type
    
- relationships grouped by learning role
    
- parent candidates
    
- child candidates
    
- variants
    
- prerequisites
    
- concepts that depend on a concept
    
- direct one-hop neighborhood
    
- target vault status
    
- derived inverse relationships
    

Only one asserted relationship should be stored.

Example asserted relationship:

```text
Backpropagation depends_on Chain Rule
```

The inverse graph view may derive:

```text
Chain Rule prerequisite_for Backpropagation
```

The inverse must not be persisted as a duplicate relationship.

Multi-hop graph traversal is not a Phase 2 completion requirement.

---

### 4.17 Source Encounter Matcher

The source encounter matcher should normalize and compare:

- source type
    
- source title
    
- unit type
    
- unit
    
- section
    
- link
    
- typed external ID
    

Source identity priority:

1. typed external ID
    
2. normalized source type and title
    
3. normalized link where appropriate
    
4. title/type similarity with reasoning when incomplete
    

The derived index should store source and encounter fingerprints.

Matching outcomes:

```text
exact_same_encounter
same_source_enrich_existing
same_source_new_unit
different_source
ambiguous
```

Examples:

```text
Existing:
Hands-On Machine Learning
unit: none

New:
Hands-On Machine Learning
unit: Chapter 4

Outcome:
same_source_enrich_existing
```

```text
Existing:
Hands-On Machine Learning
unit: Chapter 4

New:
Hands-On Machine Learning
unit: Chapter 6

Outcome:
same_source_new_unit
```

The matcher should not analyze source contents.

It only compares metadata and optional user-provided context.

---

### 4.18 Concept Search Service

`ConceptSearchService` is responsible for retrieval, not action recommendation.

It should support execution tiers.

#### Tier 0: deterministic lookup

- stable concept ID
    
- normalized canonical title
    
- approved alias
    

No embeddings or LLM are required when the caller only needs identity resolution and no additional intent classification is needed.

#### Tier 1: hybrid retrieval

When deterministic identity resolution fails:

- weighted FTS retrieval
    
- concept identity-vector retrieval
    
- concept semantic-vector retrieval
    
- scaffold segment retrieval
    
- candidate fusion
    
- graph/context enrichment
    

Retrieval channels should run in parallel where safe and useful.

The service should return a typed `ConceptSearchResult`.

It should not invoke the LLM implicitly.

A workflow or recommendation orchestrator decides whether retrieval is sufficient or should continue into reasoning.

---

### 4.19 Concept Recommendation Service

`ConceptRecommendationService` consumes:

- user query
    
- optional source context
    
- optional user context
    
- `ConceptSearchResult`
    

It determines which reasoning tasks are required and produces either:

- a validated action-specific recommendation
    
- a fallback recommendation
    
- a typed `RecommendationFailure`
    

The recommendation service should not repeat search when a current `ConceptSearchResult` was supplied.

Typical Create flow:

```text
ConceptSearchService
↓
ConceptRecommendationService
↓
ConceptRecommendation
```

Potential Search flow in Phase 3:

```text
ConceptSearchService
↓
Display useful results
or
Explicitly invoke ConceptRecommendationService for no-result/ambiguous cases
```

---

### 4.20 Workflow Orchestration Boundary

Search and recommendation remain separate services.

A future workflow layer decides whether to stop at retrieval.

Examples:

#### Search tab

```text
Search query
↓
Retrieve exact/related concepts and modules
↓
Useful results exist?
├── yes → display them
└── no/ambiguous → optionally request a recommendation
```

#### Create tab

```text
Create intent
↓
Retrieve concept evidence
↓
Always evaluate the appropriate recommendation path
```

This boundary keeps ordinary search fast while allowing Search and Create to share the same retrieval foundation.

---

### 4.21 LLM Provider

The reasoning provider should use a provider-independent interface equivalent to:

```text
generate_structured(
    task,
    prompt_input,
    response_schema
)
```

Initial providers:

- local model server provider
    
- deterministic test provider
    

Possible future providers:

- API model provider
    
- remote self-hosted provider
    
- alternate local-runtime provider
    

The initial working runtime should be a local model server exposing an OpenAI-compatible HTTP protocol.

This provides:

- reusable loaded models
    
- isolation from the application process
    
- support for running models on additional hardware
    
- similar request boundaries for future providers
    
- reduced CLI startup overhead when the server remains running
    

The provider should include a lightweight health/model-readiness check.

A short-lived provider health state may avoid repeatedly waiting for long network timeouts after an observed failure.

This is provider-health caching, not recommendation caching.

---

### 4.22 Reasoning Model Evaluation

The initial reasoning-model evaluation range should include quantized instruction models approximately between sub-1B and 3B parameters.

The chosen model should be the smallest model that satisfies approved thresholds for:

- concept identity decisions
    
- concept-versus-module intent
    
- structured-output validity
    
- relationship direction
    
- prerequisite suggestions
    
- alias proposals
    
- domain suggestions
    
- warm latency
    
- memory use
    

A strict sub-1B maximum should not override clearly superior quality from a slightly larger quantized model.

Model selection belongs to the evaluation process, not hard-coded assumptions.

---

### 4.23 Reasoning Tasks

Reasoning should use bounded, versioned tasks instead of one universal prompt.

Initial task families:

- `ConceptIdentityDecision`
    
- `NewConceptAnalysis`
    
- `ScaffoldModuleIntentDecision`
    
- `RelationshipAndPrerequisiteAnalysis`
    
- `SourceEncounterAmbiguityDecision`
    
- `AliasProposalDecision`
    
- `ClarificationDecision`
    

Tightly related tasks may be combined into one call where this reduces latency and preserves output reliability.

#### Identity decision

Output classifications:

```text
same_concept
distinct_related_concept
insufficient_information
```

Broader analysis should not run until uncertain identity is resolved.

#### New concept analysis

May produce:

- concept type
    
- concept domains
    
- concept scope
    
- graph position
    
- relationships
    
- prerequisites
    

These should generally be returned in one bounded structured output rather than several sequential model calls.

#### Module intent decision

Determines whether focused user intent belongs in an existing concept as a scaffold module.

#### Alias proposal decision

Produces a proposed alias, classification, confidence, and evidence.

#### Clarification decision

Returns candidate interpretations for vague or ambiguous input.

---

### 4.24 Task Configuration and Prompt Assets

Generation controls should belong to task configuration rather than orchestration services.

Task configuration may include:

- prompt/task version
    
- temperature
    
- maximum output tokens
    
- timeout
    
- structured-output behavior
    
- repair behavior
    
- model-mode preferences
    
- required input fields
    
- output schema identifier
    

Reasoning task assets should be maintained independently from service classes.

Each task definition should pair:

- version identifier
    
- prompt template
    
- task configuration
    
- input schema
    
- output schema
    

Example identifiers:

```text
concept_identity_v1
new_concept_analysis_v1
module_intent_v1
alias_proposal_v1
```

Task and prompt versions must be included in evaluation results and diagnostics.

---

### 4.25 Structured Output and Repair

All LLM decisions must use schema-constrained outputs.

Flow:

```text
Generate structured decision
↓
Validate against task output schema
├── valid → continue
└── invalid → one constrained repair attempt
                     ↓
                 validate again
                 ├── valid → continue
                 └── invalid → fallback/failure
```

Only one repair attempt should be allowed initially.

Repeated retries increase latency and conceal model reliability problems.

Raw LLM output must not directly become a final recommendation.

---

### 4.26 Deterministic Recommendation Assembler

The LLM produces bounded semantic judgments.

The deterministic assembler produces the final recommendation.

Example:

```text
LLM proposes:
Chain Rule is a likely prerequisite.

Assembler:
- searches index for Chain Rule
- resolves target ID if found
- assigns vault_status
- validates relationship direction
- applies confidence rules
- builds proposed relationship
- creates backlog candidate if missing
```

The assembler owns factual index verification.

The LLM must not determine:

- whether a concept physically exists
    
- the stable ID of an indexed concept without verification
    
- the current index revision
    
- whether a source encounter is already indexed
    
- whether a proposed alias collides
    
- whether a target vault status is found or missing
    

---

### 4.27 Confidence Assembly

Confidence values remain qualitative:

```text
low
medium
high
```

They are not calibrated probabilities.

Final recommendation confidence should be assembled from:

- deterministic evidence strength
    
- retrieval-channel agreement
    
- candidate ambiguity
    
- LLM confidence
    
- structured-output validity
    
- alias collisions
    
- verification outcomes
    
- provider fallback state
    
- warnings
    

The aggregation should be rule-based and configurable.

The assembler may downgrade model confidence.

Example:

```text
LLM confidence: high
Retrieved support: weak
No lexical or graph evidence
Final confidence: medium
```

The downgrade should produce structured evidence or a warning.

---

### 4.28 Alias Proposal

Phase 2 should identify and propose aliases.

Phase 2 should not write them into concept-note YAML.

A valid alias proposal should require semantic reasoning plus supporting evidence.

Embedding similarity alone must not propose an alias.

Potential support includes:

- acronym derived from canonical-title initials
    
- alternate spelling
    
- established abbreviation supplied by the user
    
- strong same-concept identity decision
    
- recurring equivalent label
    
- supporting source/user context
    

Alias suggestions should be represented as typed metadata suggestions available across recommendation actions.

Example:

```yaml
metadata_suggestions:
  aliases_to_add:
    - alias: SGD
      target_concept_id: concept_stochastic_gradient_descent_a1b2c3
      classification: acronym
      confidence: high
      evidence:
        - type: acronym_derivation
          message: The initials of Stochastic Gradient Descent form SGD.
```

The assembler must verify:

- alias is non-empty
    
- alias is not already present
    
- alias is not equivalent to the canonical title
    
- target concept exists
    
- collision state is known
    
- acronym derivation is consistent when classified as an acronym
    

Ambiguous aliases may exist across concepts.

The index should allow collisions but flag them.

A colliding alias should not be recommended without a warning or clarification requirement.

Phase 4 may later present and persist accepted alias suggestions.

---

## 5. Data Models and Schemas

### 5.1 Concept-Note Schema Version 2

Every Phase 2-compatible concept note should use:

```yaml
schema_version: 2
```

The project currently has no real v1 vault content requiring migration.

Phase 1 fixtures should be updated to schema v2 during implementation.

Future concept-note format changes, including small schema changes, should introduce a new schema version rather than silently altering the meaning of an existing version.

---

### 5.2 Relationship Metadata

Schema-v2 relationship fields:

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

Required non-empty fields:

- `relationship_type`
    
- `target_title`
    
- `vault_status`
    
- `learning_role`
    
- `confidence`
    
- `status`
    

`target_id` remains optional when the target is not found.

Initial relationship types remain:

```text
depends_on
prerequisite_for
related_to
variant_of
parent_of
child_of
contrasts_with
```

Initial confidence values:

```text
low
medium
high
```

Initial persistent relationship statuses:

```text
agent_suggested
user_confirmed
```

Rejected and deferred proposals are not active relationships and should not be placed in the concept note’s relationship list.

---

### 5.3 Learning Role

`learning_role` describes what the target concept represents for learning the current concept.

Initial values:

```text
mathematical_prerequisite
conceptual_prerequisite
implementation_prerequisite
foundational_theory
broader_parent_concept
specialized_child_concept
alternative_variant
comparison_target
supporting_concept
application_context
```

All values are interpreted from source/current concept toward target concept.

Example:

```text
Backpropagation → Chain Rule
learning_role: mathematical_prerequisite
```

Example:

```text
Stochastic Gradient Descent → Gradient Descent
learning_role: broader_parent_concept
```

The learning role should not merely repeat the relationship type.

---

### 5.4 Typed External Identifier

Source metadata should add an optional external identifier:

```yaml
external_id:
  type: doi
  value: 10.1234/example
```

The type remains flexible enough to support future identifiers such as:

- DOI
    
- ISBN
    
- video ID
    
- chatbot conversation ID
    
- course-content ID
    
- documentation ID
    

Both type and value must be non-empty when `external_id` is provided.

---

### 5.5 Derived Index Records

Broad normalized tables/records:

```text
index_metadata
indexed_files
concepts
concept_aliases
concept_domains
learning_encounters
relationships
scaffold_modules
concept_search_documents
module_search_documents
concept_fts
module_fts
embeddings
invalid_index_records
```

The Technical Plan defines broad responsibilities; exact columns should be finalized during implementation planning.

---

### 5.6 Indexed File Record

Potential fields:

- file path
    
- concept ID when valid
    
- note schema version
    
- file hash
    
- index projection hash
    
- file modification metadata
    
- current index state
    
- last successful revision
    
- invalid-since revision
    
- validation errors
    
- indexed timestamp
    

Possible states:

```text
valid
invalid
duplicate_id_conflict
removed
```

Removed records may be deleted after being included in the sync report rather than retained permanently.

---

### 5.7 Concept Index Record

Potential fields:

- concept ID
    
- canonical title
    
- normalized title
    
- concept type
    
- lifecycle status
    
- review status
    
- vault status
    
- file path
    
- H1 title
    
- Concept Overview raw Markdown
    
- Concept Overview plaintext
    
- identity input hash
    
- semantic input hash
    
- note schema version
    
- current validity state
    
- indexed revision
    
- created/updated metadata from source note
    

Repeated metadata belongs in normalized child tables.

---

### 5.8 Scaffold Module Index Record

Potential fields:

- module ID
    
- parent concept ID
    
- module type
    
- title
    
- normalized title
    
- status
    
- origin
    
- focus
    
- heading
    
- anchor
    
- initial segment count
    
- indexed revision
    

Modules remain addressable content owned by a concept.

They are not concept graph nodes.

---

### 5.9 Embedding Record

Potential fields:

- embedding record ID
    
- owner type
    
- owner ID
    
- parent concept ID
    
- segment ID
    
- embedding type
    
- vector
    
- dimension
    
- model identifier
    
- model revision
    
- input hash
    
- source location metadata
    
- created timestamp
    
- indexed revision
    

If the model identifier, revision, dimension, or input hash changes, the vector must be regenerated.

Vectors generated by different models must not be directly compared.

---

### 5.10 Search Query

`ConceptSearchQuery` should include:

```text
text
filters
limits
include_modules
include_diagnostics
```

Initial filters:

- concept domains
    
- concept types
    
- vault statuses
    
- review statuses
    
- include modules
    

Phase 2 should support configurable result limits without implementing a full pagination system.

---

### 5.11 Concept Search Result

Common shape:

```text
query
index_revision
search_status
resolution_state
exact_matches
ranked_concepts
module_hits
evidence
warnings
diagnostics
```

#### Search status

```text
complete
partial
fallback
```

#### Resolution state

```text
exact_match
related_results
ambiguous_results
no_results
```

#### Exact matches

Potential match types:

```text
stable_id
canonical_title
approved_alias
```

#### Ranked concept candidate

Should retain:

- concept ID/title
    
- aliases where useful
    
- concept type/domains
    
- short overview excerpt
    
- lifecycle status
    
- retrieval channels
    
- matched fields
    
- component ranks
    
- component scores
    
- fused rank
    
- matching modules
    
- structured evidence
    

#### Module hit

Should retain:

- parent concept ID/title
    
- module ID/title/type
    
- segment ID
    
- heading
    
- anchor
    
- segment index
    
- snippet
    
- lexical/vector component scores
    

#### Evidence

Structured support such as:

```text
approved_alias_match
lexical_match
identity_similarity
semantic_similarity
module_match
relationship_context
domain_context
```

#### Diagnostics

May include:

- execution path
    
- timings
    
- candidate limits
    
- model identifiers
    
- vector backend
    
- FTS backend
    
- raw component scores
    
- fusion configuration
    

---

### 5.12 Structured Evidence

Evidence should be typed.

Potential fields:

- evidence type
    
- concept ID
    
- module ID
    
- relationship ID/reference
    
- source encounter ID/reference
    
- message
    
- optional score
    
- retrieval channel
    
- task version
    

Evidence explains why a result or recommendation exists.

Raw calculations belong in diagnostics.

---

### 5.13 Reasoning Decision Models

Each reasoning task should have its own bounded output schema.

Examples:

#### Concept identity decision

```text
classification
selected candidate
confidence
evidence
```

#### New concept analysis

```text
suggested concept type
suggested domains
suggested scope
suggested graph position
proposed relationship judgments
prerequisite candidates
confidence
evidence
```

#### Scaffold module intent

```text
target concept
module intent classification
suggested module type
suggested title
suggested focus
confidence
evidence
```

#### Alias proposal decision

```text
alias
target concept
alias classification
confidence
evidence
```

---

### 5.14 Recommendation Envelope

Every successful recommendation should include:

```text
recommendation_id
created_at
action
confidence
completion_status
reasoning_mode
index_revision
evidence
warnings
diagnostics
metadata_suggestions
action-specific payload
```

Reasoning modes:

```text
deterministic
llm
fallback
```

Completion statuses:

```text
complete
partial
fallback
```

`diagnostics` may be omitted from ordinary serialized output unless requested.

---

### 5.15 Action-Specific Recommendation Models

Use a Pydantic discriminated union.

Initial variants:

- `UseExistingConceptRecommendation`
    
- `CreateNewConceptRecommendation`
    
- `AddLearningEncounterRecommendation`
    
- `UpdateLearningEncounterRecommendation`
    
- `AddScaffoldModuleRecommendation`
    
- `MarkRedundantRecommendation`
    
- `RequestClarificationRecommendation`
    

This prevents invalid field combinations.

#### Use existing concept

Contains:

- target concept
    
- match classification
    
- optional alias suggestions
    
- relevant module matches
    
- evidence
    

#### Create new concept

Contains:

- suggested concept metadata
    
- suggested graph position
    
- suggested scope
    
- proposed relationships
    
- backlog candidates
    
- possible matches
    
- evidence
    

#### Add learning encounter

Contains:

- target concept
    
- proposed new encounter
    
- encounter comparison outcome
    
- evidence
    

#### Update learning encounter

Contains:

- target concept
    
- existing encounter
    
- proposed metadata enrichment
    
- evidence
    

#### Add scaffold module

Contains:

- target concept
    
- suggested module type
    
- title
    
- focus
    
- origin
    
- matching existing modules
    
- evidence
    

#### Mark redundant

Contains:

- target concept/encounter/module
    
- redundancy reason
    
- evidence
    

#### Request clarification

Contains:

- ambiguity type
    
- candidate interpretations
    
- clarification message
    
- evidence
    

---

### 5.16 Recommendation Failure

A failed recommendation attempt should return a separate typed result.

Potential fields:

```text
failure_id
created_at
query
index_revision
failure_stage
error_code
message
evidence
diagnostics
recoverable
fallback_search_result
```

Failure stages:

```text
search
candidate_assembly
reasoning
structured_output_validation
deterministic_verification
recommendation_assembly
timeout
```

A successful search result should be preserved when recommendation generation fails.

---

### 5.17 Sync Report

`SyncReport` should include:

- sync ID
    
- start/end times
    
- status
    
- revision before/after
    
- scanned-file count
    
- created concepts
    
- updated concepts
    
- unchanged concepts
    
- removed concepts
    
- invalid concepts
    
- duplicate-ID conflicts
    
- embeddings created
    
- embeddings reused
    
- embeddings removed
    
- warnings
    
- errors
    
- diagnostics
    

Statuses:

```text
success
partial_success
failed
no_changes
```

A partial synchronization that changes usable index state increments the index revision.

---

### 5.18 Evaluation Case and Result Models

Evaluation cases should use human-editable YAML.

Potential case fields:

- case ID
    
- query
    
- vault fixture
    
- optional source context
    
- acceptable actions
    
- required candidates
    
- prohibited identity matches
    
- expected graph positions
    
- expected relationship directions
    
- expected learning roles
    
- expected module intent
    
- expected clarification behavior
    

Evaluation results should record:

- embedding model/version
    
- LLM model/version
    
- quantization/runtime information
    
- prompt/task versions
    
- retrieval configuration
    
- vector backend
    
- metrics
    
- warm/cold latency
    
- model-load time
    
- memory use
    
- structured-output failures
    
- fallback rate
    
- per-case outputs
    

---

## 6. Data Flow / System Flow

### 6.1 Incremental Synchronization

```text
Start synchronization
↓
Inspect index schema/version
↓
Scan vault for Markdown concept notes
↓
Calculate file hashes
↓
Compare files against indexed records
↓
Classify new / changed / unchanged / moved / removed
↓
Parse and validate new/changed notes
├── invalid → mark invalid/stale, record errors, exclude from search
└── valid → build deterministic index projection
↓
Calculate projection and embedding-input hashes
↓
Determine which embeddings require generation
↓
Batch-generate embeddings outside DB transaction
↓
For each concept, open transaction
↓
Atomically replace concept and child derived records
↓
Update FTS documents and embeddings
↓
Remove derived records for deleted concepts
↓
Increment index revision if usable state changed
↓
Return SyncReport
```

---

### 6.2 Duplicate Concept-ID Flow

```text
Scan detects same concept ID in multiple files
↓
Create duplicate-ID conflict
↓
Do not select an authoritative file
↓
Mark both files conflicted
↓
Exclude both from normal search
↓
Preserve concise diagnostics
↓
Continue synchronizing unrelated valid notes
↓
Return partial-success SyncReport
```

---

### 6.3 Invalid Previously Indexed Note

```text
Previously valid file changes
↓
Parsing/schema validation fails
↓
Retain diagnostic index record
↓
Mark concept invalid/stale
↓
Record last valid revision and invalid-since revision
↓
Exclude stale concept from normal queries
↓
Do not silently serve previous content as current truth
↓
Continue synchronization
```

---

### 6.4 Full Rebuild

```text
Validate vault/configuration
↓
Create temporary/replacement index
↓
Create current index schema and FTS structures
↓
Scan and parse all notes
↓
Report invalid/conflicting files
↓
Project valid notes
↓
Batch-generate all required embeddings
↓
Insert all derived records
↓
Commit rebuilt index
↓
Set initial/new revision
↓
Return SyncReport
```

The rebuild should avoid leaving the application with a partially constructed active database where feasible.

---

### 6.5 Exact Search

```text
Receive ConceptSearchQuery
↓
Normalize query
↓
Check stable ID
↓
Check normalized canonical title
↓
Check approved aliases
↓
Exact match found?
├── yes → assemble exact ConceptSearchResult
└── no → continue to hybrid retrieval
```

If the caller only needs search, exact lookup stops here.

If the caller requests a recommendation with additional intent, identity may be resolved deterministically while intent reasoning continues.

---

### 6.6 Hybrid Search

```text
No deterministic identity match
↓
Run weighted FTS retrieval
Run identity-vector retrieval
Run semantic-vector retrieval
Run module-vector retrieval
↓
Merge concept/module candidates
↓
Apply weighted reciprocal rank fusion
↓
Load concise concept, domain, relationship, and module context
↓
Determine resolution state
↓
Return ConceptSearchResult
```

FTS and vector retrieval should run independently and in parallel where feasible.

---

### 6.7 Recommendation Generation

```text
Receive ConceptRecommendationRequest
↓
Use supplied current ConceptSearchResult or run search
↓
Determine recommendation path
↓
Can deterministic evidence resolve action?
├── yes → assemble deterministic recommendation
└── no → select task-specific reasoning schema
↓
Send compact candidate context to local LLM provider
↓
Validate decision
├── invalid → one repair attempt
│              ├── valid → continue
│              └── invalid → fallback/failure
└── valid → continue
↓
Deterministically verify all vault/index facts
↓
Assemble action-specific recommendation
↓
Apply confidence rules
↓
Attach evidence, warnings, diagnostics
↓
Return recommendation without mutating Markdown
```

---

### 6.8 New Concept Analysis

```text
No existing identity match
↓
Retrieve related concepts/modules/domains
↓
Identity reasoning confirms distinct concept
↓
Run NewConceptAnalysis
↓
Receive type/domain/scope/position/prerequisite judgments
↓
Verify candidate concepts against index
↓
Found targets → proposed relationships
↓
Missing targets → backlog candidates
↓
Validate directions and learning roles
↓
Assemble CreateNewConceptRecommendation
```

---

### 6.9 Alias Proposal

```text
User query resolves to existing concept
↓
Query label is not an existing alias
↓
Alias reasoning task evaluates equivalence/classification
↓
Assembler validates alias and collision state
↓
Add typed alias metadata suggestion
↓
Return recommendation
↓
Do not edit concept note
```

---

### 6.10 Module Intent

```text
Resolve concept identity or retrieve strong parent concept
↓
Retrieve module candidates
↓
Classify concept-vs-module intent
↓
Existing module already covers request?
├── yes → use existing / mark redundant
└── no → suggest module type/title/focus
↓
Return AddScaffoldModuleRecommendation
```

---

### 6.11 Source Encounter Comparison

```text
Resolve target concept
↓
Normalize provided source metadata
↓
Build source/encounter fingerprint
↓
Compare external ID, title/type, unit, section, and link
↓
Classify encounter outcome
├── exact same → use existing / redundant
├── enrich existing → UpdateLearningEncounterRecommendation
├── new unit → AddLearningEncounterRecommendation
├── different source → AddLearningEncounterRecommendation
└── ambiguous → reasoning/clarification
```

---

### 6.12 Graceful Fallback

```text
LLM unavailable or times out
↓
Preserve deterministic and retrieval results
↓
Do not fabricate semantic judgment
↓
Can a safe fallback recommendation be assembled?
├── yes → completion_status: fallback
│         reasoning_mode: fallback
│         downgrade confidence
│         add warning
└── no → return RecommendationFailure with fallback search result
```

---

## 7. Validation and Error Handling

### 7.1 Schema-v2 Validation

Schema v2 should strictly validate:

- schema version
    
- relationship type
    
- target title
    
- target ID shape when present
    
- vault status
    
- learning role
    
- confidence
    
- relationship status
    
- external identifier type/value
    
- all existing Phase 1 metadata constraints
    

Empty required enum values should fail.

Unknown enum values should fail writes and generated schema-v2 structures according to the established Phase 1 validation rules.

---

### 7.2 Synchronization Validation

Synchronization should distinguish:

- valid note
    
- invalid note
    
- duplicate-ID conflict
    
- unsupported schema version
    
- parse failure
    
- projection failure
    
- embedding failure
    
- database write failure
    

One invalid note should not fail synchronization of unrelated valid notes.

Each concept update must be atomic.

Partial success must be reported explicitly.

---

### 7.3 Per-Concept Transaction Boundary

All derived records for a concept should update within one transaction:

- concept
    
- aliases
    
- domains
    
- learning encounters
    
- relationships
    
- modules
    
- FTS search documents
    
- embedding records
    

Embeddings should be generated before the transaction opens.

This prevents long model inference from holding database locks.

If the transaction fails, no partial new projection should remain.

The record should remain marked invalid/stale or retain the previous valid revision according to the synchronization failure mode, but it must be excluded when it no longer represents current valid vault content.

---

### 7.4 Search Failure Handling

Search channels may fail independently.

Examples:

```text
FTS succeeds
Concept embeddings succeed
Module vector backend fails
```

The result may return:

```text
search_status: partial
```

with a structured warning.

A complete search failure should return a typed search failure rather than an empty result that appears successful.

---

### 7.5 LLM Output Validation

LLM output must pass:

- JSON/structured parsing
    
- task-schema validation
    
- enum validation
    
- candidate-reference validation
    
- required evidence validation
    
- deterministic fact verification
    

One repair attempt is allowed for schema-invalid output.

Semantic contradictions discovered during deterministic verification should not be repaired silently by trusting the model.

The assembler should correct verifiable derived facts or reject the decision.

---

### 7.6 Timeouts

Separate configurable timeouts should exist for:

- search
    
- LLM generation
    
- structured-output repair
    
- overall recommendation
    

Timeout failures should identify their stage.

Successful search evidence must be preserved when recommendation reasoning times out.

---

### 7.7 Alias Collision Handling

The alias index may contain the same normalized alias for multiple concepts.

Collisions should:

- remain queryable
    
- produce ambiguity evidence
    
- prevent deterministic unique identity resolution
    
- trigger warning or clarification behavior
    
- not corrupt the index
    
- not automatically block all future alias use
    

---

### 7.8 Confidence Downgrading

The deterministic assembler may lower confidence when:

- retrieval signals disagree
    
- only weak semantic evidence exists
    
- aliases collide
    
- LLM provider falls back
    
- candidate ambiguity remains
    
- some optional analysis fails
    
- validation repair was required
    
- source matching is incomplete
    

Confidence increases should require strong supporting evidence rather than model assertion alone.

---

### 7.9 Privacy-Aware Logging

Structured logs may record:

- task version
    
- model/provider identifiers
    
- timings
    
- counts
    
- failure codes
    
- fallback state
    
- validation results
    
- index revision
    

Default logs should avoid:

- complete note bodies
    
- full source material
    
- raw private prompts
    
- complete LLM payloads
    

Detailed payload logging should require an explicit diagnostics setting.

---

## 8. Write / Mutation Behavior

Phase 2 may write:

- SQLite index state
    
- FTS derived state
    
- embedding records
    
- evaluation reports
    
- optional serialized recommendation fixtures
    
- updated Phase 1/2 test fixtures during implementation
    

Phase 2 must not write recommendation changes into concept-note Markdown.

This includes:

- aliases
    
- concept domains
    
- concept type suggestions
    
- relationships
    
- learning roles
    
- learning encounters
    
- scaffold modules
    

These remain recommendations until a later user-approved Create workflow performs the mutation.

`ConceptRecommendation` objects should normally be returned in memory.

They may be serialized for:

- golden tests
    
- CLI `--json` output
    
- evaluation reports
    
- debugging
    

They should not be persisted as application recommendation history in Phase 2.

---

## 9. Interfaces / APIs / Functions

Exact class/file names may be refined during branch planning, but the following capabilities should exist.

### Database/index

```text
initialize_index(...)
inspect_index_schema(...)
rebuild_index(...)
get_index_revision(...)
increment_index_revision(...)
```

### Synchronization

```text
sync_vault(...)
scan_vault(...)
project_concept_note(...)
calculate_projection_hashes(...)
build_sync_report(...)
```

### Repositories

```text
upsert_concept_projection(...)
remove_concept_projection(...)
mark_index_record_invalid(...)
find_duplicate_concept_ids(...)
find_concept_by_id(...)
find_concept_by_normalized_title(...)
find_concepts_by_alias(...)
```

### Embeddings

```text
build_identity_embedding_input(...)
build_semantic_embedding_input(...)
build_module_embedding_documents(...)
embed_query(...)
embed_documents(...)
search_vectors(...)
```

### Lexical search

```text
search_concepts_fts(...)
search_modules_fts(...)
materialize_concept_search_document(...)
materialize_module_search_document(...)
```

### Candidate retrieval

```text
retrieve_concept_candidates(...)
merge_candidates(...)
fuse_ranked_results(...)
load_candidate_context(...)
```

### Search

```text
search_concepts(query: ConceptSearchQuery) -> ConceptSearchResult
inspect_concept(...)
find_module_hits(...)
```

### Graph

```text
get_direct_relationships(...)
get_one_hop_neighborhood(...)
get_prerequisites(...)
get_parent_child_candidates(...)
derive_inverse_relationship(...)
```

### Source encounters

```text
normalize_source_identity(...)
build_source_fingerprint(...)
build_encounter_fingerprint(...)
compare_learning_encounter(...)
```

### Reasoning

```text
run_reasoning_task(...)
validate_reasoning_decision(...)
repair_reasoning_output(...)
check_provider_health(...)
```

### Recommendations

```text
recommend(request: ConceptRecommendationRequest)
assemble_recommendation(...)
assemble_recommendation_failure(...)
assemble_alias_suggestion(...)
calculate_recommendation_confidence(...)
```

### Evaluation

```text
load_evaluation_cases(...)
run_retrieval_evaluation(...)
run_recommendation_evaluation(...)
compare_model_configurations(...)
generate_evaluation_report(...)
```

---

### 9.1 CLI Direction

Potential commands:

```text
studium graph sync
studium graph rebuild
studium graph status
studium graph find "SGD"
studium graph candidates "stochastic optimization"
studium graph inspect "Stochastic Gradient Descent"
studium graph modules "manual SGD update"
studium graph relationships "Backpropagation"
studium graph propose "Backpropagation"
studium graph propose "Regularization" --source-type class --source-title "MSAI Machine Learning" --unit "Lecture 5"
studium graph evaluate-retrieval <config>
studium graph evaluate-recommendations <config>
```

Output modes:

```text
default human-readable
--json
--diagnostics
```

CLI commands should call application services.

They should not reimplement index, search, or reasoning logic.

---

## 10. Testing Strategy

### 10.1 Normal Pytest Suite

Normal tests should use:

- temporary vaults
    
- temporary SQLite databases
    
- deterministic embedding provider
    
- deterministic reasoning provider
    
- controlled clocks/IDs where needed
    
- representative schema-v2 Markdown fixtures
    

Test categories:

- unit tests
    
- repository tests
    
- parser/schema compatibility tests
    
- synchronization integration tests
    
- FTS integration tests
    
- vector-backend contract tests
    
- candidate-fusion tests
    
- graph query tests
    
- source encounter matching tests
    
- reasoning schema tests
    
- recommendation assembler tests
    
- CLI integration tests
    
- golden recommendation tests
    
- failure/fallback tests
    

---

### 10.2 Schema Tests

Cover:

- valid schema-v2 relationships
    
- missing learning role
    
- missing confidence
    
- missing relationship status
    
- invalid enums
    
- empty required values
    
- typed external identifiers
    
- unchanged Phase 1 constraints
    
- updated schema-v2 fixtures
    

---

### 10.3 Synchronization Tests

Cover:

- empty vault
    
- initial sync
    
- unchanged note
    
- changed note
    
- moved note with same concept ID
    
- removed note
    
- invalid new note
    
- valid note becoming invalid
    
- invalid note becoming valid
    
- duplicate concept IDs
    
- partial synchronization
    
- no-change synchronization
    
- index rebuild
    
- incompatible index schema
    
- per-concept rollback
    
- revision increments
    

---

### 10.4 Embedding Regeneration Tests

Cover:

- all vectors created initially
    
- unchanged inputs reuse embeddings
    
- alias change regenerates identity and semantic vectors
    
- overview change regenerates semantic vector only
    
- module change regenerates affected module segment only
    
- embedding-model change invalidates all comparable vectors
    
- model revision/dimension change forces regeneration
    
- batching preserves input/output mapping
    

---

### 10.5 Retrieval Tests

Cover:

- exact ID
    
- exact normalized title
    
- approved alias
    
- alias collision
    
- weighted title FTS
    
- overview FTS
    
- domain FTS
    
- identity vector
    
- semantic vector
    
- module vector
    
- module location preservation
    
- rank fusion
    
- duplicate candidate merging
    
- component scores
    
- filters
    
- configurable limits
    
- partial backend failures
    

---

### 10.6 Recommendation Tests

Cover all discriminated recommendation variants.

Deterministic cases should not invoke the LLM provider.

Tests should verify:

- correct task selection
    
- identity-first orchestration
    
- new-concept analysis
    
- relationship direction verification
    
- learning-role validation
    
- domain suggestion
    
- prerequisite found/missing behavior
    
- backlog candidate creation
    
- alias proposal and collision warnings
    
- source encounter outcomes
    
- module intent
    
- broad concept handling
    
- vague clarification
    
- confidence downgrade
    
- one repair attempt
    
- fallback behavior
    
- `RecommendationFailure`
    

---

### 10.7 Real-Model Integration Tests

Tests requiring real models should be marked separately.

They should not run during every ordinary pytest execution.

Separate suites:

```text
local embedding integration
local LLM integration
full recommendation integration
```

These tests validate provider compatibility and model/runtime behavior.

They should not be the sole verification of deterministic application logic.

---

### 10.8 Curated Evaluation Set

Create an initial 40–60-case evaluation dataset.

Include contrast cases for:

- acronym and full title
    
- same versus related concept
    
- broad parent versus child
    
- variant relationships
    
- semantically close but distinct concepts
    
- prerequisite direction
    
- learning roles
    
- concept versus scaffold module
    
- existing versus new encounter
    
- domain reuse
    
- new domain proposal
    
- broad versus vague input
    
- alias collisions
    
- fallback behavior
    

Expected outputs should allow semantically acceptable alternatives instead of requiring exact generated prose.

---

### 10.9 Retrieval Metrics

Measure:

- exact-match correctness
    
- Recall@K
    
- Mean Reciprocal Rank
    
- module-hit Recall@K
    
- candidate-set size
    
- lexical/vector overlap
    
- warm latency
    
- cold latency
    
- memory use
    
- index/rebuild time
    

Initial requirements:

- stable ID/title/approved alias fixtures: 100% correct
    
- semantic Recall@5: initial target at least 0.90, subject to formal approval after model baselines
    
- MRR: measured across candidate models and used in final selection
    

Any amended threshold should be documented in the evaluation report before phase completion.

---

### 10.10 Recommendation Metrics

Measure:

- action accuracy
    
- structured-output validity
    
- concept identity accuracy
    
- relationship direction accuracy
    
- learning-role accuracy
    
- prerequisite precision/recall
    
- module-intent accuracy
    
- alias-proposal accuracy
    
- domain-suggestion acceptance/appropriateness
    
- repair rate
    
- fallback rate
    
- warm latency
    
- cold latency
    
- model-load time
    
- memory usage
    

Initial targets:

- structured-output validity after one repair: 100%
    
- deterministic action cases: 100%
    
- graceful fallback behavior: 100%
    
- LLM-required action accuracy: provisional target of at least 85%
    
- relationship-direction accuracy: provisional target of at least 90%
    

Targets may be amended after the first documented baseline, but Phase 2 should not complete without approved measurable thresholds.

---

### 10.11 Model Comparison Harness

The harness should allow swapping:

- embedding model
    
- embedding dimensions where supported
    
- vector backend
    
- local LLM
    
- quantization
    
- reasoning task version
    
- prompt version
    
- retrieval limits
    
- FTS weights
    
- rank-fusion weights
    
- confidence configuration
    

Reports should include:

- configuration
    
- metrics
    
- per-case results
    
- failures
    
- cold/warm latency
    
- load time
    
- memory usage
    
- structured-output repair/failure rate
    

This harness is a first-class Phase 2 artifact.

---

## 11. Technical Concepts to Understand

Technical concept notes should be created as needed during implementation.

High-priority concepts:

- SQLAlchemy Core
    
- Repository Pattern
    
- SQLite Foreign Keys
    
- SQLite WAL
    
- SQLite Transactions
    
- Rebuildable Derived Indexes
    
- Normalized Relational Schemas
    
- Materialized Search Documents
    
- SQLite FTS
    
- Weighted Full-Text Ranking
    
- Incremental Synchronization
    
- Content and Semantic Hashing
    
- Embedding Input Design
    
- Embedding Batching
    
- Cosine Similarity
    
- Exact Vector Search With NumPy
    
- Approximate Nearest-Neighbor Search
    
- Reciprocal Rank Fusion
    
- Search Result Aggregation
    
- Provider-Agnostic Model Interfaces
    
- Local LLM Servers
    
- Model Quantization
    
- Structured LLM Outputs
    
- Pydantic Discriminated Unions
    
- Deterministic Recommendation Assembly
    
- Retrieval Evaluation
    
- Recall@K
    
- Mean Reciprocal Rank
    
- LLM Evaluation and Failure Analysis
    

These documents should explain actual implementation choices, not generic textbook summaries disconnected from the code.

---

## 12. Documentation Updates

During Phase 2, update or create:

- `00 Phase Roadmap.md`
    
- `01 Technical Plan.md`
    
- `02 Branch Plan.md`
    
- individual branch documents
    
- schema-v2 relationship documentation
    
- typed external identifier documentation
    
- concept index schema documentation
    
- search-result schema documentation
    
- recommendation schema documentation
    
- reasoning task documentation
    
- evaluation-case documentation
    
- model-comparison reports
    
- technical concept notes created during implementation
    

Phase 1 documentation should be amended where schema version 2 supersedes relationship metadata assumptions.

Final ADRs should be written after implementation, once the choices have been tested rather than merely planned.

---

## 13. Architecture Decisions / ADR Candidates

Potential ADRs after Phase 2 completes:

- Use SQLite as a rebuildable derived concept index.
    
- Keep SQLite index files outside the Obsidian vault.
    
- Use SQLAlchemy Core with repository abstractions.
    
- Rebuild incompatible index schemas instead of migrating them.
    
- Use SQLite FTS for weighted lexical retrieval.
    
- Use distinct concept identity, concept semantic, and module embeddings.
    
- Use embedding-input hashes for selective regeneration.
    
- Use one embedding model/space across indexed documents and queries.
    
- Use a vector-search abstraction with empirically selected backend.
    
- Use weighted reciprocal rank fusion.
    
- Keep Search and Recommendation as separate services.
    
- Use an explicit orchestration layer to chain retrieval and reasoning.
    
- Use a local OpenAI-compatible model server as the first reasoning provider.
    
- Use versioned task-specific structured reasoning.
    
- Use one structured-output repair attempt.
    
- Use deterministic verification and recommendation assembly.
    
- Store one asserted relationship and derive inverse relationships.
    
- Treat scaffold modules as searchable child content, not graph nodes.
    
- Allow alias collisions but expose ambiguity.
    
- Keep recommendations transient in Phase 2.
    
- Treat the vault as durable truth and SQLite as reconstructable state.
    

---

## 14. Risks, Tradeoffs, and Remaining Implementation Questions

### Risks

- SQLite may accidentally become treated as a second knowledge source.
    
- Index synchronization may mishandle manual file edits.
    
- Invalid notes may disappear from user awareness if diagnostics are poor.
    
- FTS ranking weights may overfavor titles or body content.
    
- Embeddings may confuse related concepts with identical concepts.
    
- A small LLM may struggle with subtle relationship direction.
    
- Structured-output repair may hide weak model selection if overused.
    
- Alias proposals may create ambiguous abbreviations.
    
- Flexible domain strings may fragment into near-duplicates.
    
- One embedding per long module will eventually become insufficient.
    
- Vector extensions may create installation or portability problems.
    
- NumPy exact search may require loading too much vector state as the vault grows.
    
- Local model-server startup and model-load latency may affect development.
    
- Recommendation confidence may appear more precise than it is.
    
- Evaluation fixtures may overfit to machine-learning concepts.
    
- Prompt changes may improve one task while degrading another.
    
- Module-result collapsing may hide valuable segment-level context if location data is discarded.
    

### Tradeoffs

- Normalized tables increase schema complexity but improve queryability.
    
- Materialized FTS documents duplicate derived text but simplify search.
    
- Multiple embeddings improve retrieval semantics but increase index work.
    
- Task-specific prompts improve reliability but increase orchestration complexity.
    
- A local model server adds operational setup but reduces repeated model loading.
    
- Strict schema versioning increases update overhead but makes format changes explicit.
    
- One-segment modules simplify Phase 2 but defer inevitable long-module chunking.
    
- Rebuilding index schemas is simple because data is derived, but may become slower for large vaults.
    
- Weighted rank fusion is robust across retrievers but initially requires empirical tuning.
    

### Implementation questions to resolve during branches

- Exact normalized SQLite tables and indexes
    
- Exact index schema version value
    
- Exact application data-path implementation by operating system
    
- Exact hashing algorithm and canonical hash-input serialization
    
- Exact FTS tokenizer configuration
    
- Initial FTS field weights
    
- Initial reciprocal-rank-fusion constant and weights
    
- Concrete vector backend after benchmark
    
- Concrete embedding model after evaluation
    
- Initial embedding batch size
    
- Maximum module text indexed before chunking
    
- Concrete local LLM server/runtime
    
- Concrete reasoning model and quantization
    
- Task prompt text
    
- Exact reasoning timeouts
    
- Final candidate limits
    
- Final confidence rules
    
- Approved evaluation thresholds after baseline
    
- Exact CLI command names/options
    

These questions do not block the branch plan. They should be assigned to the branch where evidence can be gathered.

---

## 15. Technical Completion Standard

Phase 2 is technically complete when:

### Schema

- concept notes use schema version 2
    
- relationship learning role, confidence, and status are validated
    
- typed external source IDs are supported
    
- Phase 1 fixtures are updated and remain valid
    

### Persistent index

- SQLite index is stored outside the vault
    
- index schema is independently versioned
    
- incompatible schemas require rebuild
    
- index can be fully rebuilt from the vault
    
- incremental synchronization works
    
- file moves preserve concept identity
    
- deletions remove all derived records
    
- duplicate IDs are reported and excluded
    
- invalid notes are marked stale/invalid and excluded
    
- partial synchronization produces a complete report
    
- index revisions behave correctly
    

### Lexical search

- exact ID/title/approved-alias matching works
    
- weighted concept FTS works
    
- weighted module FTS works
    
- search filters and configurable limits work
    
- materialized search documents remain synchronized
    

### Embeddings

- one local embedding provider works
    
- identity concept embeddings work
    
- semantic concept embeddings work
    
- module embeddings work
    
- query embeddings use the same model space
    
- vectors store model/version/dimension metadata
    
- selective embedding regeneration works
    
- batch embedding works
    
- a vector backend is selected through documented benchmark results
    

### Hybrid retrieval

- lexical and vector retrieval can run independently
    
- retrieval channels can run in parallel
    
- weighted reciprocal rank fusion works
    
- component scores/ranks are retained
    
- module hits preserve module and segment locations
    
- exact matches bypass ordinary rank fusion
    
- semantic retrieval meets approved evaluation thresholds
    

### Graph/query intelligence

- one-hop relationship queries work
    
- inverse relationships are derived
    
- prerequisites and parent/child/variant relationships are queryable
    
- concept domains remain labels rather than graph nodes
    
- scaffold modules remain children of concepts rather than graph nodes
    

### Reasoning

- one local model-server provider works
    
- deterministic test provider works
    
- provider health/fallback works
    
- task-specific structured reasoning works
    
- one repair attempt is enforced
    
- reasoning tasks and prompts are versioned
    
- LLM model selection is supported by evaluation results
    

### Recommendations

- action-specific discriminated recommendations work
    
- deterministic recommendation assembly verifies index facts
    
- alias proposals work without mutating notes
    
- relationship direction and learning roles are validated
    
- source encounter outcomes are distinguished
    
- backlog candidates are produced but not persisted
    
- vague input produces clarification
    
- fallback recommendations lower confidence and include warnings
    
- failed recommendations return `RecommendationFailure`
    
- recommendations include structured evidence
    
- recommendations do not mutate Markdown
    

### Evaluation

- 40–60 curated evaluation cases exist
    
- retrieval metrics are produced
    
- recommendation metrics are produced
    
- model comparison supports embeddings, LLMs, prompts, and retrieval configuration
    
- cold latency, warm latency, load time, and memory usage are reported
    
- approved quality thresholds are documented and satisfied
    

### CLI/test harness

- index sync/rebuild/status can be tested
    
- concept retrieval can be inspected
    
- module hits can be inspected
    
- relationships can be inspected
    
- recommendations can be generated
    
- human-readable, JSON, and diagnostic outputs work
    
- normal pytest suite does not require live models
    
- real-model integration/evaluation runs separately
    

---

## 16. Cursor / Implementation Constraints

Cursor should follow these constraints when planning and implementing Phase 2 branches:

- Read the Phase 2 Roadmap, Technical Plan, Branch Plan, current branch document, relevant schema documentation, and completed prior branch documents.
    
- Reuse Phase 1 parsing, validation, and vault-access behavior rather than duplicating it.
    
- Keep the vault as the durable source of truth.
    
- Treat SQLite as rebuildable derived state.
    
- Do not place the SQLite database inside the Obsidian vault.
    
- Use SQLAlchemy Core and repository abstractions.
    
- Do not introduce a full ORM without explicit architectural approval.
    
- Keep raw SQL isolated to justified SQLite-specific adapters.
    
- Keep Search and Recommendation as separate services.
    
- Do not hide LLM reasoning inside ordinary search calls.
    
- Do not directly mutate concept notes.
    
- Do not persist recommendation history.
    
- Do not add recommendation caching.
    
- Do not generalize the concept index into generic future node types.
    
- Do not create standalone example nodes.
    
- Preserve module/segment result locations.
    
- Generate embeddings only when relevant inputs or model metadata change.
    
- Generate embeddings outside database transactions.
    
- Apply each concept projection atomically.
    
- Use task-specific structured LLM outputs.
    
- Permit one structured-output repair attempt only.
    
- Verify LLM claims against deterministic index facts.
    
- Preserve evidence and diagnostics separately.
    
- Prefer robust, efficient, maintainable implementations.
    
- Use abstractions where they improve correctness, testability, extensibility, or measurable performance.
    
- Explain non-obvious complexity and tradeoffs.
    
- Benchmark performance-sensitive alternatives rather than assuming one backend is superior.
    
- Keep live-model tests separate from normal deterministic tests.
    
- Update technical documentation as meaningful implementation decisions become final.