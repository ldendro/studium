## 1. Branch Plan Purpose

This document divides Phase 2 into implementation branches that progressively build Studium’s concept-intelligence layer.

Each branch should:

- implement one cohesive technical capability
    
- depend only on completed earlier branches
    
- include appropriate deterministic or real-model testing
    
- preserve the vault as the durable source of truth
    
- keep SQLite as rebuildable derived state
    
- avoid direct concept-note mutation
    
- produce code and documentation that can be understood, tested, and improved independently
    

Phase 2 is intentionally divided more finely than Phase 1 because it introduces several independently complex systems:

- schema evolution
    
- relational indexing
    
- incremental synchronization
    
- full-text search
    
- embedding generation
    
- vector search
    
- hybrid retrieval
    
- graph queries
    
- source encounter matching
    
- LLM infrastructure
    
- reasoning tasks
    
- recommendation assembly
    
- model evaluation
    

The branches should remain implementation-oriented rather than research-only. Any branch involving model or backend comparison must finish with a working selected implementation.

---

## 2. Phase Completion Target

By the end of the final branch, Studium should have a working local concept-intelligence layer that can:

- scan and incrementally synchronize a Markdown concept vault
    
- rebuild a persistent SQLite concept index
    
- detect invalid and conflicting concept notes
    
- identify concepts through IDs, titles, aliases, lexical retrieval, and semantic retrieval
    
- retrieve relevant scaffold modules and preserve their locations
    
- perform one-hop graph queries
    
- compare learning encounters
    
- reason over narrowed candidates with a local provider-agnostic LLM layer
    
- produce validated action-specific `ConceptRecommendation` objects
    
- propose aliases, relationships, domains, graph positions, prerequisites, learning encounters, and scaffold modules
    
- return clear fallback or failure objects when reasoning cannot complete
    
- evaluate embedding models, vector backends, LLMs, prompts, and retrieval configurations
    
- expose all core behavior through CLI commands and test harnesses
    
- satisfy approved quality, latency, memory, and structured-output thresholds
    

Phase 2 recommendations must not directly modify concept-note Markdown.

---

## 3. Branch Sequence Overview

| Branch | Name                                            | Main Goal                                                                      | Key Output                                                                                                                     |
| ------ | ----------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| 01     | `P2-B01-schema-v2-amendments`                   | Amend the Phase 1 storage schema for Phase 2 relationship and source metadata. | Schema-v2 models, fixtures, validation, and compatibility updates.                                                             |
| 02     | `P2-B02-index-schema-and-repositories`          | Establish the persistent SQLite index foundation.                              | SQLAlchemy Core schema, repositories, database runtime configuration, and index version handling.                              |
| 03     | `P2-B03-vault-index-synchronization`            | Synchronize valid vault notes into the derived index.                          | Incremental sync, full rebuild, selective embedding-change detection, invalid-state handling, and `SyncReport`.                |
| 04     | `P2-B04-weighted-full-text-search`              | Implement deterministic and weighted lexical retrieval.                        | Exact lookup, materialized search documents, SQLite FTS, and concept/module lexical search.                                    |
| 05     | `P2-B05-embedding-pipeline-and-model-selection` | Implement local embedding generation and empirically select the initial model. | Embedding provider, input builders, batching, selective regeneration, benchmark report, and selected model.                    |
| 06     | `P2-B06-vector-search-backend`                  | Implement and select the vector storage/search backend.                        | NumPy exact search, SQLite-extension benchmark, selected backend, and vector-search abstraction.                               |
| 07     | `P2-B07-hybrid-retrieval-and-search-contract`   | Combine deterministic, lexical, concept-vector, and module-vector retrieval.   | Reciprocal rank fusion, execution tiers, `ConceptSearchQuery`, and `ConceptSearchResult`.                                      |
| 08     | `P2-B08-graph-and-source-encounter-queries`     | Implement graph intelligence and learning-encounter comparison.                | One-hop graph queries, inverse relationships, source fingerprints, and encounter outcomes.                                     |
| 09     | `P2-B09-llm-provider-and-task-framework`        | Establish provider-agnostic structured LLM infrastructure.                     | Local server adapter, deterministic provider, health checks, task assets, validation, repair, and timeout behavior.            |
| 10     | `P2-B10-reasoning-tasks-and-model-selection`    | Implement concept reasoning tasks and select the initial local LLM.            | Identity, new-concept, module, relationship, alias, source ambiguity, and clarification reasoning.                             |
| 11     | `P2-B11-recommendation-models-and-assembly`     | Convert retrieval and reasoning evidence into safe recommendations.            | Discriminated recommendation models, deterministic assembler, confidence rules, metadata suggestions, fallbacks, and failures. |
| 12     | `P2-B12-integrated-evaluation-harness`          | Evaluate the complete retrieval and recommendation system.                     | Curated evaluation set, quality metrics, model/configuration comparison, and approved thresholds.                              |
| 13     | `P2-B13-cli-and-phase-verification`             | Expose and verify the complete Phase 2 system.                                 | Final graph CLI, diagnostic outputs, end-to-end verification, and phase completion report.                                     |

---

## 4. Branch Details

## Branch 01: `P2-B01-schema-v2-amendments`

### Goal

Amend the Phase 1 concept-note schema to support the relationship intelligence and source identity required by Phase 2.

### Why This Branch Comes Here

Every later Phase 2 component must index, validate, query, and reason over the same finalized metadata model.

The schema must therefore be updated before the SQLite index is designed.

### Technical Plan Areas Addressed

- Concept-Note Schema Version 2
    
- Relationship Metadata
    
- Learning Role
    
- Typed External Identifier
    
- Schema-v2 Validation
    
- Documentation Updates
    

### Roadmap Capabilities Addressed

- relationship learning roles
    
- relationship confidence
    
- persistent relationship confirmation status
    
- stable external source identifiers
    
- schema-versioned metadata evolution
    

### Implementation Focus

- change newly generated and validated notes to `schema_version: 2`
    
- add required relationship fields:
    
    - `learning_role`
        
    - `confidence`
        
    - `status`
        
- define and validate the initial `learning_role` enum
    
- define and validate relationship confidence values
    
- define and validate persistent relationship statuses
    
- add optional typed `external_id`
    
- update Phase 1 Pydantic models
    
- update serializer behavior
    
- update parsing and validation behavior
    
- update Phase 1 valid and invalid fixtures
    
- update golden Markdown fixtures
    
- update affected documentation
    

### Expected Output

- all project fixtures use schema version 2
    
- schema-v2 concept notes parse and validate
    
- relationship metadata requires the complete Phase 2 shape
    
- invalid learning roles, confidence values, statuses, and external identifiers fail validation
    
- Phase 1 storage behavior remains functional under the amended schema
    

### Testing / Verification

- valid schema-v2 relationship tests
    
- missing `learning_role` tests
    
- missing confidence tests
    
- missing relationship-status tests
    
- invalid and empty enum tests
    
- typed external-identifier tests
    
- parser compatibility tests
    
- serializer golden tests
    
- full Phase 1 regression suite
    

### Branch Success Criteria

-  Concept notes use `schema_version: 2`.
    
-  Relationship learning role, confidence, and status are required and validated.
    
-  Typed optional external source identifiers are supported.
    
-  All Phase 1 fixtures are updated to schema version 2.
    
-  Existing parsing, serialization, validation, and write tests continue to pass.
    
-  Affected schema documentation reflects the new format.
    

### Notes / Risks

- No v1 migration framework is needed because there are no durable v1 user notes.
    
- Schema changes must not be silently folded into an existing schema version in future phases.
    
- Rejected or deferred proposals must not become active relationship statuses.
    

---

## Branch 02: `P2-B02-index-schema-and-repositories`

### Goal

Create the persistent SQLite-derived index foundation using SQLAlchemy Core and repository abstractions.

### Why This Branch Comes Here

Synchronization, search, embeddings, graph queries, and recommendation evidence all require stable database records and transaction boundaries.

### Technical Plan Areas Addressed

- Application Data and Vault Identity
    
- Database Engine and Runtime Configuration
    
- Index Schema Manager
    
- Repository Layer
    
- Derived Index Records
    
- Index Schema Versioning
    

### Roadmap Capabilities Addressed

- persistent local concept index
    
- normalized concept metadata records
    
- independently versioned index schema
    
- multi-vault-ready index organization
    
- rebuildable derived state
    

### Implementation Focus

- determine application-data index location
    
- derive initial vault identifier
    
- configure SQLAlchemy Core
    
- implement centralized SQLite connection settings:
    
    - foreign keys
        
    - WAL
        
    - synchronous mode
        
    - busy timeout
        
- define normalized tables:
    
    - index metadata
        
    - indexed files
        
    - concepts
        
    - aliases
        
    - domains
        
    - learning encounters
        
    - relationships
        
    - scaffold modules
        
    - search documents
        
    - embeddings
        
    - invalid records
        
- define indexes and foreign keys
    
- define cascading deletion behavior
    
- implement index schema version inspection
    
- require rebuild on incompatible index schema
    
- implement focused repository interfaces
    
- implement transaction helpers
    

### Expected Output

- an empty index can be initialized outside the vault
    
- the current index schema version can be inspected
    
- incompatible indexes are rejected with a rebuild requirement
    
- normalized records can be inserted, queried, and deleted
    
- repository operations use centrally configured connections
    
- foreign-key and transaction behavior is enforced
    

### Testing / Verification

- temporary-database integration tests
    
- schema initialization tests
    
- index-version mismatch tests
    
- foreign-key enforcement tests
    
- cascade-deletion tests
    
- transaction rollback tests
    
- repository CRUD tests
    
- vault-identifier and path tests
    
- concurrent read/write smoke tests under WAL
    

### Branch Success Criteria

-  SQLite index creation works outside the vault.
    
-  SQLAlchemy Core tables and repositories cover all planned derived records.
    
-  SQLite runtime configuration is applied centrally.
    
-  Index schema versioning and rebuild-required behavior work.
    
-  Foreign-key and transaction guarantees are tested.
    
-  Repository code remains separate from business logic.
    

### Notes / Risks

- Avoid adopting a full ORM entity model.
    
- Avoid putting complete YAML metadata snapshots into SQLite.
    
- Do not implement synchronization behavior in this branch.
    
- Exact table columns may be refined while preserving the normalized model.
    

### Likely Technical Concepts

- SQLAlchemy Core
    
- repository pattern
    
- normalized derived indexes
    
- SQLite WAL
    
- SQLite transactions
    
- foreign-key enforcement
    

---

## Branch 03: `P2-B03-vault-index-synchronization`

### Goal

Implement incremental synchronization and complete rebuilds between the Markdown vault and the SQLite-derived index.

### Why This Branch Comes Here

The index schema now exists, but it is not useful until valid vault notes can populate and maintain it safely.

### Technical Plan Areas Addressed

- Vault Scanner and Index Synchronizer
    
- Index Projection Builder
    
- Embedding Hashes
    
- Incremental Synchronization Flow
    
- Duplicate-ID Flow
    
- Invalid-Record Lifecycle
    
- Full Rebuild
    
- `SyncReport`
    

### Roadmap Capabilities Addressed

- vault scanning
    
- incremental index updates
    
- full index rebuilds
    
- invalid-note exclusion
    
- duplicate-ID detection
    
- file-move detection
    
- index revisions
    
- selective future embedding regeneration
    

### Implementation Focus

- scan vault Markdown files
    
- reuse Phase 1 parser and validation layer
    
- build deterministic index projections
    
- calculate:
    
    - file hash
        
    - index projection hash
        
    - identity input hash
        
    - semantic input hash
        
    - module input hashes
        
- classify files:
    
    - new
        
    - changed
        
    - unchanged
        
    - moved
        
    - removed
        
    - invalid
        
    - duplicate-ID conflict
        
- update valid projections atomically
    
- preserve diagnostic invalid records
    
- exclude invalid/stale records from normal queries
    
- detect moves using stable concept IDs
    
- remove deleted concept projections
    
- increment index revision when usable state changes
    
- produce typed `SyncReport`
    
- implement full rebuild operation
    
- prepare embedding-work requests without yet requiring the real embedding provider
    

### Expected Output

- valid concept notes populate normalized index records
    
- unchanged notes are skipped
    
- moved notes retain concept identity
    
- changed notes update atomically
    
- deleted notes remove derived data
    
- invalid notes are reported and excluded
    
- duplicate IDs exclude all conflicting files
    
- index revisions and sync reports behave correctly
    
- full rebuild reconstructs the index from the vault
    

### Testing / Verification

- initial empty-vault sync
    
- first concept sync
    
- unchanged-file sync
    
- changed metadata sync
    
- moved-file sync
    
- deleted-file sync
    
- invalid new note
    
- previously valid note becoming invalid
    
- invalid note becoming valid
    
- duplicate IDs
    
- partial success
    
- no-change sync
    
- index rebuild
    
- per-concept rollback
    
- hash-change tests
    
- revision increment tests
    

### Branch Success Criteria

-  Incremental synchronization correctly handles all expected file states.
    
-  Full index rebuild reconstructs all valid derived records.
    
-  Invalid and duplicate-ID notes are excluded and clearly reported.
    
-  Each concept projection updates atomically.
    
-  Hashes correctly identify which derived and embedding inputs changed.
    
-  `SyncReport` accurately records success, partial success, failure, and no-change outcomes.
    

### Notes / Risks

- Embeddings are not generated yet, but synchronization must identify which embedding inputs need regeneration.
    
- Invalid current files must not remain searchable through stale last-valid content.
    
- Rebuild should avoid replacing a usable index with a partially constructed one where feasible.
    

### Likely Technical Concepts

- incremental synchronization
    
- content hashing
    
- semantic hashing
    
- atomic projections
    
- rebuildable derived state
    

---

## Branch 04: `P2-B04-weighted-full-text-search`

### Goal

Implement deterministic concept identity lookup and weighted SQLite full-text retrieval for concepts and scaffold modules.

### Why This Branch Comes Here

A complete lexical baseline should exist before semantic embeddings are introduced. It provides immediate search capability and a baseline for measuring embedding improvements.

### Technical Plan Areas Addressed

- Text Normalization Service
    
- Full-Text Search Layer
    
- Materialized Search Documents
    
- Exact Search
    
- Weighted Full-Text Ranking
    

### Roadmap Capabilities Addressed

- exact ID lookup
    
- normalized title lookup
    
- approved-alias lookup
    
- keyword search
    
- concept overview search
    
- concept-domain search
    
- scaffold module lexical search
    

### Implementation Focus

- implement query/title/alias normalization
    
- avoid aggressive stemming
    
- materialize concept search documents
    
- materialize module search documents
    
- configure SQLite FTS tables
    
- determine and implement initial FTS tokenizer configuration
    
- implement weighted concept fields
    
- implement weighted module fields
    
- implement exact deterministic lookup
    
- implement alias-collision detection
    
- return lexical component scores and ranks
    
- preserve module heading, anchor, segment, and parent-concept location
    
- integrate search-document updates with synchronization
    

### Expected Output

- exact IDs, titles, and approved aliases resolve deterministically
    
- lexical concept results are ranked
    
- module lexical results preserve their location
    
- title and alias matches receive stronger weighting than overview/body matches
    
- alias collisions remain queryable but ambiguous
    
- FTS documents stay synchronized with concept projections
    

### Testing / Verification

- normalization tests
    
- exact ID tests
    
- normalized title tests
    
- approved alias tests
    
- alias collision tests
    
- title-weight tests
    
- alias-weight tests
    
- overview lexical tests
    
- domain lexical tests
    
- module-title tests
    
- module-body tests
    
- synchronized FTS update/delete tests
    

### Branch Success Criteria

-  Deterministic ID, title, and approved-alias lookup works.
    
-  Weighted concept FTS returns useful ranked results.
    
-  Weighted module FTS returns parent concept and precise module location.
    
-  Alias collisions produce ambiguity rather than false unique identity.
    
-  FTS documents update and delete with synchronized concept projections.
    
-  Lexical retrieval diagnostics expose component ranks and scores.
    

### Notes / Risks

- FTS similarity must not establish concept identity.
    
- Exact deterministic matches should remain separate from ordinary ranked retrieval.
    
- Initial field weights may be tuned later by the evaluation harness.
    

### Likely Technical Concepts

- SQLite FTS
    
- materialized search documents
    
- lexical normalization
    
- weighted field ranking
    

---

## Branch 05: `P2-B05-embedding-pipeline-and-model-selection`

### Goal

Implement the local embedding pipeline and empirically select the initial embedding model.

### Why This Branch Comes Here

Semantic retrieval requires reproducible vector generation before a vector-search backend can be selected and hybrid retrieval can be built.

### Technical Plan Areas Addressed

- Embedding Provider
    
- Embedding Input Builder
    
- Embedding Documents and Segments
    
- Embedding Hashes
    
- Embedding Batching
    
- Embedding Model Evaluation
    

### Roadmap Capabilities Addressed

- working local embeddings
    
- concept identity embeddings
    
- concept semantic embeddings
    
- scaffold module embeddings
    
- query embeddings
    
- selective embedding regeneration
    
- model evaluation
    

### Implementation Focus

- define provider-independent embedding interface
    
- implement initial local provider adapters needed for candidate comparison
    
- build identity embedding inputs
    
- build semantic concept inputs
    
- build module embedding documents
    
- preserve segment/module/concept hierarchy
    
- batch document embeddings
    
- embed user queries
    
- store model metadata and dimensions
    
- connect input hashes to selective regeneration
    
- define maximum initial module input length
    
- ensure schema supports future multi-segment modules
    
- create initial retrieval evaluation subset
    
- compare candidate local embedding models
    
- measure:
    
    - correctness
        
    - Recall@K
        
    - MRR
        
    - batching behavior
        
    - load time
        
    - warm/cold latency
        
    - memory use
        
- select and configure the initial model
    

### Expected Output

- a selected local model generates all Phase 2 embedding types
    
- vector dimensions and model identity are recorded
    
- unchanged embedding inputs reuse stored vectors
    
- changed inputs regenerate only affected vectors
    
- module embeddings retain location hierarchy
    
- the selected model is justified by a documented benchmark
    

### Testing / Verification

- fake provider unit tests
    
- real provider integration tests
    
- deterministic input-construction tests
    
- batch ordering tests
    
- dimension/model metadata tests
    
- identity hash regeneration tests
    
- semantic hash regeneration tests
    
- module hash regeneration tests
    
- long-module handling tests
    
- candidate-model comparison report
    
- retrieval baseline metrics
    

### Branch Success Criteria

-  Provider-independent local embedding generation works.
    
-  Identity, semantic concept, module, and query embeddings are implemented.
    
-  Batch embedding and selective regeneration work correctly.
    
-  Embedding records preserve model, dimension, owner, segment, and hash metadata.
    
-  Candidate models are evaluated on quality, latency, loading, and memory use.
    
-  One embedding model is selected and implemented as the Phase 2 default.
    

### Notes / Risks

- The selected model should be the smallest model that meets quality needs, not simply the smallest available.
    
- All comparable vectors must use the same model space.
    
- Long-module chunking remains deferred, but the segment schema must support it later.
    
- Real-model tests remain separate from the normal pytest suite.
    

### Likely Technical Concepts

- embedding input design
    
- semantic vectors
    
- cosine similarity
    
- batching
    
- Recall@K
    
- MRR
    

---

## Branch 06: `P2-B06-vector-search-backend`

### Goal

Implement the vector-search abstraction, build NumPy exact search, benchmark an SQLite extension-backed option, and select the Phase 2 vector backend.

### Why This Branch Comes Here

Vectors can now be generated consistently. The next step is determining how those vectors should be stored and searched locally.

### Technical Plan Areas Addressed

- Vector Store and Search Abstraction
    
- NumPy Exact Search
    
- SQLite Extension-Backed Search
    
- Vector Backend Comparison
    
- Similarity Metric
    

### Roadmap Capabilities Addressed

- concept identity-vector retrieval
    
- concept semantic-vector retrieval
    
- module-vector retrieval
    
- local vector persistence
    
- configurable vector backend
    

### Implementation Focus

- define vector storage/search interface
    
- persist embedding vectors and metadata
    
- normalize vectors appropriately
    
- implement NumPy exact top-K search
    
- support filtering by embedding type and owner state
    
- benchmark a compatible SQLite vector extension
    
- compare:
    
    - installation
        
    - Apple Silicon compatibility
        
    - search correctness
        
    - warm/cold latency
        
    - memory usage
        
    - rebuild speed
        
    - development complexity
        
- implement contract tests across viable backends
    
- select and configure the default backend
    
- document the alternative
    

### Expected Output

- identity, semantic, and module vectors can be searched
    
- NumPy exact search is fully understood and tested
    
- at least one extension-backed option is evaluated where locally viable
    
- one backend is selected through benchmark evidence
    
- retrieval services depend only on the backend abstraction
    

### Testing / Verification

- vector serialization tests
    
- normalization tests
    
- cosine/dot-product correctness tests
    
- top-K ranking tests
    
- filtering tests
    
- stale-model-vector exclusion tests
    
- NumPy backend contract tests
    
- extension backend tests where available
    
- benchmark report
    
- backend selection record
    

### Branch Success Criteria

-  A stable vector-search abstraction exists.
    
-  NumPy exact vector retrieval works correctly.
    
-  A viable SQLite-extension option is benchmarked or its incompatibility is documented.
    
-  Search quality and performance are compared on the development machine.
    
-  One backend is selected and configured as the Phase 2 default.
    
-  Retrieval services are not directly coupled to one backend.
    

### Notes / Risks

- Extension-backed search should not be selected merely because it appears more scalable.
    
- NumPy exact search may be preferable for a personal-sized vault.
    
- Model/version/dimension mismatches must exclude incompatible vectors.
    

### Likely Technical Concepts

- NumPy vector search
    
- cosine similarity
    
- exact nearest-neighbor search
    
- vector database extensions
    
- vector normalization
    

---

## Branch 07: `P2-B07-hybrid-retrieval-and-search-contract`

### Goal

Combine deterministic lookup, weighted FTS, concept vectors, and module vectors into the complete Phase 2 search layer.

### Why This Branch Comes Here

Every retrieval channel now works independently. This branch establishes the shared search contract consumed by Phase 3 and the recommendation service.

### Technical Plan Areas Addressed

- Hybrid Retrieval and Rank Fusion
    
- Concept Search Service
    
- Execution Tiers
    
- Search Query
    
- Concept Search Result
    
- Structured Evidence
    
- Search Failure Handling
    

### Roadmap Capabilities Addressed

- hybrid concept retrieval
    
- ranked candidate sets
    
- module-level search results
    
- fast exact-search path
    
- search filters
    
- diagnostic search evidence
    
- search/recommendation boundary
    

### Implementation Focus

- implement `ConceptSearchQuery`
    
- implement `ConceptSearchResult`
    
- implement search statuses and resolution states
    
- implement deterministic Tier 0
    
- implement hybrid Tier 1
    
- run independent retrieval channels in parallel where useful
    
- implement weighted reciprocal rank fusion
    
- preserve raw component scores and ranks
    
- merge duplicate concept candidates
    
- collapse module hits under parent concepts for concept ranking
    
- preserve module and segment locations
    
- implement filters:
    
    - domains
        
    - concept types
        
    - vault statuses
        
    - review statuses
        
    - modules
        
- implement configurable retrieval limits
    
- implement structured evidence
    
- separate evidence from diagnostics
    
- support complete, partial, and fallback search outcomes
    
- return typed failures for complete search failure
    

### Expected Output

- exact searches return near-instant deterministic results
    
- uncertain searches combine lexical and semantic channels
    
- module matches contribute to parent concept ranking without losing location
    
- component scores and fusion ranks are inspectable
    
- search can stop after retrieval without invoking an LLM
    
- recommendation services can reuse the search result without repeating retrieval
    

### Testing / Verification

- Tier 0 execution tests
    
- Tier 1 execution tests
    
- retrieval parallelism tests
    
- reciprocal rank fusion tests
    
- channel-weight configuration tests
    
- duplicate-candidate merge tests
    
- module-collapse/location tests
    
- filter tests
    
- limit tests
    
- resolution-state tests
    
- partial backend-failure tests
    
- performance benchmark tests
    
- golden `ConceptSearchResult` tests
    

### Branch Success Criteria

-  `ConceptSearchQuery` and `ConceptSearchResult` are fully implemented.
    
-  Deterministic search bypasses embeddings and reasoning when appropriate.
    
-  Hybrid retrieval combines FTS and vector channels through weighted rank fusion.
    
-  Module hits retain their exact module/segment locations.
    
-  Search filters, limits, evidence, diagnostics, and statuses work.
    
-  Search remains independent from recommendation reasoning.
    

### Notes / Risks

- Search should not silently create recommendations.
    
- Workflow orchestration in later phases decides when a search continues into recommendation.
    
- Sophisticated candidate diversity is deferred.
    
- Candidate limits and fusion weights remain configurable for evaluation.
    

### Likely Technical Concepts

- reciprocal rank fusion
    
- search-result aggregation
    
- retrieval orchestration
    
- component-score diagnostics
    

---

## Branch 08: `P2-B08-graph-and-source-encounter-queries`

### Goal

Implement graph queries over indexed relationships and structured comparison of learning encounters.

### Why This Branch Comes Here

Search results and later reasoning tasks require concise graph and source-history context from the normalized index.

### Technical Plan Areas Addressed

- Graph Query Service
    
- Source Encounter Matcher
    
- Relationship Direction
    
- Inverse Relationship Derivation
    
- Source Fingerprints
    
- Encounter Outcomes
    

### Roadmap Capabilities Addressed

- one-hop graph lookup
    
- prerequisite queries
    
- parent/child/variant lookup
    
- relationship grouping
    
- source encounter recognition
    
- duplicate encounter detection
    
- encounter enrichment detection
    

### Implementation Focus

#### Graph queries

- direct relationship lookup
    
- grouping by relationship type
    
- grouping by learning role
    
- prerequisite lookup
    
- parent/child/variant lookup
    
- concepts depending on a target
    
- one-hop neighborhood
    
- derived inverse relationships
    
- found/missing target handling
    

#### Source encounters

- normalize source identity
    
- support typed external IDs
    
- build source fingerprints
    
- build encounter fingerprints
    
- classify:
    
    - exact same encounter
        
    - same source, enrich existing
        
    - same source, new unit
        
    - different source
        
    - ambiguous
        
- preserve deterministic evidence
    
- expose ambiguity for later reasoning
    

### Expected Output

- graph context can be loaded for search and LLM tasks
    
- reciprocal meaning is derived without duplicate persisted relationships
    
- prerequisites and graph positions are queryable
    
- source encounter comparisons return typed outcomes
    
- source comparison does not analyze source content
    

### Testing / Verification

- direct relationship tests
    
- inverse derivation tests
    
- prerequisite direction tests
    
- parent/child/variant tests
    
- one-hop neighborhood tests
    
- missing-target tests
    
- typed external-ID tests
    
- exact encounter tests
    
- encounter enrichment tests
    
- new-unit tests
    
- different-source tests
    
- ambiguous metadata tests
    

### Branch Success Criteria

-  One-hop graph queries and relationship grouping work.
    
-  Inverse relationships are derived rather than duplicated.
    
-  Prerequisite and parent/child/variant queries return correct direction.
    
-  Source and encounter fingerprints are generated consistently.
    
-  All five encounter outcomes are distinguishable.
    
-  Graph and encounter services return concise context suitable for reasoning.
    

### Notes / Risks

- Multi-hop graph reasoning remains deferred.
    
- Source matching must not infer source contribution.
    
- Source normalization must avoid collapsing distinct units into one encounter.
    

---

## Branch 09: `P2-B09-llm-provider-and-task-framework`

### Goal

Implement the provider-agnostic infrastructure required for reliable structured local LLM reasoning.

### Why This Branch Comes Here

Search and index context now exist. Before implementing concept reasoning, Studium needs a tested provider, task, validation, repair, timeout, and fallback framework.

### Technical Plan Areas Addressed

- LLM Provider
    
- Local Model Server
    
- Reasoning Tasks
    
- Task Configuration
    
- Prompt Assets
    
- Structured Output and Repair
    
- Timeout Handling
    
- Privacy-Aware Logging
    

### Roadmap Capabilities Addressed

- provider-agnostic reasoning
    
- local model-server integration
    
- structured LLM outputs
    
- versioned prompts/tasks
    
- deterministic test reasoning
    
- graceful provider fallback
    

### Implementation Focus

- define reasoning-provider interface
    
- implement OpenAI-compatible local server adapter
    
- implement deterministic test provider
    
- implement health and readiness checks
    
- keep reusable model client/server connection
    
- define task asset structure
    
- define task and prompt version identifiers
    
- define task configuration:
    
    - temperature
        
    - token limit
        
    - timeout
        
    - schema
        
    - repair behavior
        
- implement structured-output parsing and validation
    
- implement one constrained repair attempt
    
- implement separate timeouts
    
- implement fallback and failure signals
    
- implement privacy-aware diagnostics/logging
    
- support provider model metadata
    

### Expected Output

- Studium can call a local model server through a generic interface
    
- tests can run without a real model
    
- task definitions are versioned and separate from service classes
    
- invalid structured output gets one repair attempt
    
- unavailable providers fail quickly and clearly
    
- no concept reasoning tasks are fully implemented yet
    

### Testing / Verification

- deterministic provider tests
    
- local server adapter integration tests
    
- health-check tests
    
- unavailable-server tests
    
- timeout tests
    
- valid structured-output tests
    
- invalid-output repair tests
    
- failed-repair tests
    
- task-version tests
    
- diagnostics/logging privacy tests
    

### Branch Success Criteria

-  A provider-independent structured generation interface exists.
    
-  A local OpenAI-compatible server adapter works.
    
-  A deterministic test provider supports normal tests.
    
-  Task assets and configurations are versioned and maintainable.
    
-  Structured validation permits only one repair attempt.
    
-  Health, timeout, fallback, and privacy behavior are tested.
    

### Notes / Risks

- This branch should not choose the final reasoning model yet.
    
- Provider-health state is acceptable; recommendation-result caching is not.
    
- Raw private prompt payloads should not be logged by default.
    

### Likely Technical Concepts

- provider-agnostic interfaces
    
- local LLM servers
    
- structured outputs
    
- prompt versioning
    
- schema-constrained generation
    

---

## Branch 10: `P2-B10-reasoning-tasks-and-model-selection`

### Goal

Implement the bounded concept-reasoning tasks and empirically select the initial local LLM.

### Why This Branch Comes Here

The provider framework is complete and can now be used to evaluate actual semantic judgment tasks over compact retrieved context.

### Technical Plan Areas Addressed

- Reasoning Model Evaluation
    
- Concept Identity Decision
    
- New Concept Analysis
    
- Scaffold Module Intent
    
- Relationship and Prerequisite Analysis
    
- Alias Proposal
    
- Source Encounter Ambiguity
    
- Clarification Decision
    

### Roadmap Capabilities Addressed

- same-versus-related concept reasoning
    
- concept type and domain suggestion
    
- graph-position suggestion
    
- relationship direction
    
- learning-role suggestion
    
- prerequisite detection
    
- scaffold module intent
    
- alias proposal
    
- broad versus vague distinction
    

### Implementation Focus

- implement task-specific input/output schemas
    
- implement task-specific prompt assets
    
- implement identity-first orchestration
    
- implement:
    
    - concept identity task
        
    - new-concept analysis
        
    - scaffold module intent
        
    - relationship/prerequisite analysis
        
    - source ambiguity decision
        
    - alias proposal
        
    - clarification decision
        
- combine tightly related tasks where useful
    
- provide only narrowed candidate context
    
- avoid passing entire vaults or notes
    
- evaluate quantized models from sub-1B through roughly 3B
    
- measure:
    
    - task accuracy
        
    - structured-output validity
        
    - repair rate
        
    - latency
        
    - load time
        
    - memory usage
        
- select the initial local reasoning model
    
- document model/runtime configuration
    

### Expected Output

- all planned reasoning tasks produce validated bounded decisions
    
- deterministic identity cases skip LLM reasoning
    
- uncertain identity is resolved before broader analysis
    
- one selected local LLM satisfies approved preliminary quality requirements
    
- selected task versions and prompts are recorded
    
- reasoning decisions remain separate from final recommendations
    

### Testing / Verification

- deterministic task-schema tests
    
- controlled reasoning fixture tests
    
- identity decision cases
    
- graph-position cases
    
- relationship-direction cases
    
- learning-role cases
    
- domain suggestion cases
    
- prerequisite cases
    
- module-intent cases
    
- alias proposal/collision cases
    
- broad/vague cases
    
- source ambiguity cases
    
- model comparison report
    
- real-model integration tests
    

### Branch Success Criteria

-  Every planned reasoning task has a bounded versioned schema and prompt.
    
-  Identity-first reasoning prevents unnecessary broader analysis.
    
-  All reasoning outputs validate or fail safely after one repair attempt.
    
-  Alias proposals include sufficient evidence and collision awareness.
    
-  Candidate local LLMs are evaluated across quality, latency, loading, and memory.
    
-  One model is selected as the initial Phase 2 reasoning model.
    
-  Reasoning decisions contain no unverified vault-state claims.
    

### Notes / Risks

- Multiple local LLM calls should not run concurrently initially.
    
- Deterministic retrieval can still execute in parallel.
    
- Parallel LLM reasoning may be reconsidered after hardware benchmarks.
    
- Evaluation must include concepts outside only one narrow technical domain.
    

### Likely Technical Concepts

- small-model reasoning
    
- model quantization
    
- structured LLM evaluation
    
- task-specific prompting
    
- hallucination boundaries
    

---

## Branch 11: `P2-B11-recommendation-models-and-assembly`

### Goal

Convert deterministic evidence and bounded reasoning decisions into safe, validated, action-specific recommendations.

### Why This Branch Comes Here

Search, graph/source context, and reasoning decisions now exist independently. This branch creates the stable boundary that Phase 4 Create will eventually consume.

### Technical Plan Areas Addressed

- Recommendation Envelope
    
- Action-Specific Recommendation Models
    
- Recommendation Failure
    
- Deterministic Recommendation Assembler
    
- Confidence Assembly
    
- Alias Metadata Suggestions
    
- Evidence and Diagnostics
    
- Graceful Fallback
    

### Roadmap Capabilities Addressed

- structured `ConceptRecommendation`
    
- use-existing recommendations
    
- create-new recommendations
    
- learning encounter recommendations
    
- scaffold module recommendations
    
- redundancy recommendations
    
- clarification recommendations
    
- backlog candidates
    
- metadata suggestions
    
- no-mutation boundary
    

### Implementation Focus

- implement discriminated recommendation union:
    
    - use existing concept
        
    - create new concept
        
    - add learning encounter
        
    - update learning encounter
        
    - add scaffold module
        
    - mark redundant
        
    - request clarification
        
- implement common recommendation envelope
    
- implement `RecommendationFailure`
    
- implement structured evidence and diagnostics
    
- implement completion statuses
    
- implement reasoning modes
    
- implement deterministic recommendation assembler
    
- verify:
    
    - target IDs
        
    - vault status
        
    - source encounter existence
        
    - alias collisions
        
    - relationship direction
        
    - learning roles
        
    - prerequisite existence
        
- derive backlog candidates
    
- implement typed alias metadata suggestions
    
- implement configurable confidence aggregation
    
- allow confidence downgrades
    
- implement fallback recommendations
    
- enforce no Markdown mutation
    
- serialize recommendations for tests/CLI only
    

### Expected Output

- every recommendation action has a valid action-specific payload
    
- invalid field combinations are prevented
    
- LLM decisions are checked against deterministic index facts
    
- proposed aliases and relationships include evidence
    
- missing prerequisites become backlog candidates
    
- failed reasoning preserves usable search results
    
- recommendations never mutate notes
    

### Testing / Verification

- recommendation-union schema tests
    
- every action variant
    
- invalid payload combinations
    
- deterministic assembler tests
    
- hallucinated target verification tests
    
- relationship-direction tests
    
- learning-role tests
    
- alias suggestion tests
    
- alias collision warnings
    
- source encounter recommendation tests
    
- backlog candidate tests
    
- confidence downgrade tests
    
- fallback tests
    
- `RecommendationFailure` tests
    
- no-mutation tests
    
- golden recommendation fixtures
    

### Branch Success Criteria

-  All Phase 2 recommendation variants are implemented as discriminated models.
    
-  Deterministic assembly verifies every index-dependent fact.
    
-  Confidence, evidence, warnings, diagnostics, and completion status are consistent.
    
-  Alias, relationship, domain, type, graph-position, and backlog proposals are represented safely.
    
-  Fallback and failure results preserve completed search evidence.
    
-  Recommendation generation cannot mutate concept-note Markdown.
    
-  Golden recommendation fixtures cover every action path.
    

### Notes / Risks

- Avoid a universal model with many optional fields.
    
- Keep recommendation evidence meaningful and diagnostics technical.
    
- Phase 4 owns presentation, approval, and persistence.
    

### Likely Technical Concepts

- Pydantic discriminated unions
    
- deterministic recommendation assembly
    
- confidence aggregation
    
- evidence versus diagnostics
    

---

## Branch 12: `P2-B12-integrated-evaluation-harness`

### Goal

Create the complete evaluation system used to approve the Phase 2 retrieval and reasoning configuration.

### Why This Branch Comes Here

Individual model and backend comparisons have already occurred. This branch evaluates the integrated system across retrieval, reasoning, recommendations, failures, latency, and resource usage.

### Technical Plan Areas Addressed

- Curated Evaluation Set
    
- Retrieval Metrics
    
- Recommendation Metrics
    
- Model Comparison Harness
    
- Evaluation Case and Result Models
    
- Approved Quality Thresholds
    

### Roadmap Capabilities Addressed

- measurable semantic retrieval quality
    
- measurable recommendation quality
    
- model/backend/prompt comparison
    
- performance and memory reporting
    
- evidence-based configuration approval
    

### Implementation Focus

- create 40–60 YAML evaluation cases
    
- include diverse concept domains
    
- define acceptable outcomes rather than exact prose
    
- implement retrieval evaluation
    
- implement recommendation evaluation
    
- calculate:
    
    - Recall@K
        
    - MRR
        
    - action accuracy
        
    - structured-output validity
        
    - relationship-direction accuracy
        
    - learning-role accuracy
        
    - module-intent accuracy
        
    - alias accuracy
        
    - prerequisite precision/recall
        
    - repair rate
        
    - fallback rate
        
- record:
    
    - cold latency
        
    - warm latency
        
    - model-load time
        
    - memory use
        
    - index/rebuild time
        
- support swapping:
    
    - embedding models
        
    - vector backends
        
    - LLMs
        
    - quantization
        
    - prompts/tasks
        
    - FTS weights
        
    - rank-fusion weights
        
    - retrieval limits
        
- generate JSON and Markdown reports
    
- approve final Phase 2 configuration and thresholds
    
- document failure cases and tradeoffs
    

### Expected Output

- retrieval and recommendation quality can be measured reproducibly
    
- configuration comparisons are based on the same evaluation cases
    
- final embedding model, vector backend, LLM, prompt versions, and retrieval configuration are approved
    
- provisional thresholds are either confirmed or amended with evidence
    
- known failure modes are documented
    

### Testing / Verification

- YAML evaluation-case validation
    
- metric-calculation tests
    
- acceptable-alternative tests
    
- report-generation tests
    
- configuration-swap tests
    
- cold/warm measurement tests
    
- memory-measurement tests
    
- reproducibility tests
    
- end-to-end evaluation run
    

### Branch Success Criteria

-  A curated 40–60-case evaluation set exists.
    
-  Retrieval and recommendation metrics are calculated correctly.
    
-  Model, backend, prompt, and retrieval configurations can be compared.
    
-  Cold/warm latency, load time, memory, and rebuild time are reported.
    
-  Approved Phase 2 quality thresholds are documented.
    
-  The final selected configuration satisfies the approved thresholds.
    
-  Known failure cases and limitations are documented.
    

### Notes / Risks

- Avoid overfitting the evaluation set to the selected models or prompts.
    
- Include multiple knowledge domains and ambiguous cases.
    
- Real-model evaluation remains separate from normal deterministic pytest.
    

### Likely Technical Concepts

- Recall@K
    
- Mean Reciprocal Rank
    
- LLM evaluation
    
- failure analysis
    
- model benchmarking
    

---

## Branch 13: `P2-B13-cli-and-phase-verification`

### Goal

Expose the complete Phase 2 concept-intelligence layer through a thin CLI and verify every phase completion criterion.

### Why This Branch Comes Here

All application services and approved configurations now exist. The final branch provides manual inspection, integration verification, and a stable test harness before Phase 3 builds the UI.

### Technical Plan Areas Addressed

- CLI Direction
    
- Technical Completion Standard
    
- Phase-Level Integration
    
- Documentation Updates
    
- Final Verification
    

### Roadmap Capabilities Addressed

- index synchronization CLI
    
- search CLI
    
- module search CLI
    
- graph inspection CLI
    
- recommendation CLI
    
- evaluation CLI
    
- human-readable and diagnostic output
    
- complete Phase 2 verification
    

### Implementation Focus

Finalize commands such as:

```text
studium graph sync
studium graph rebuild
studium graph status
studium graph find
studium graph candidates
studium graph inspect
studium graph modules
studium graph relationships
studium graph propose
studium graph evaluate-retrieval
studium graph evaluate-recommendations
```

Implement:

- human-readable default output
    
- complete `--json` output
    
- technical `--diagnostics` output
    
- clear partial/fallback/failure rendering
    
- local-provider readiness reporting
    
- active-model/backend reporting
    
- full end-to-end fixtures
    
- manual verification workflow
    
- phase completion report
    
- final documentation reconciliation
    
- ADR candidate collection for post-phase finalization
    

### Expected Output

- every Phase 2 service can be manually exercised
    
- search and recommendation evidence can be inspected
    
- synchronization failures are understandable
    
- model/backend configuration is visible
    
- end-to-end behavior satisfies the Technical Plan completion standard
    
- Phase 3 has stable service contracts to consume
    

### Testing / Verification

- CLI integration tests
    
- sync/rebuild/status tests
    
- exact and hybrid search tests
    
- module-location output tests
    
- graph-query tests
    
- source encounter tests
    
- recommendation action tests
    
- fallback/failure rendering tests
    
- JSON output schema tests
    
- diagnostics output tests
    
- complete end-to-end workflows
    
- phase criteria coverage audit
    

### Branch Success Criteria

-  All approved graph/index/search/recommendation CLI commands work.
    
-  Human-readable, JSON, and diagnostic output modes work.
    
-  The selected embedding, vector, and LLM configurations are exercised end to end.
    
-  Search, graph, source encounter, and recommendation workflows pass integration verification.
    
-  Failure, fallback, invalid-note, and conflict behavior are visible and understandable.
    
-  Every Phase 2 Technical Completion Standard criterion is covered by tests or documented verification.
    
-  Phase 2 documentation accurately reflects the implemented system.
    
-  Service contracts are ready for Phase 3 Search and graph visualization.
    

### Notes / Risks

- CLI commands must remain thin wrappers around application services.
    
- Do not embed business logic into command handlers.
    
- Interactive UI behavior belongs to Phase 3.
    
- Recommendation approval and mutation remain Phase 4 responsibilities.
    

---

## 5. Phase Criteria Coverage

|Phase Criterion|Covered By Branches|Notes|
|---|---|---|
|Schema version 2 is supported|P2-B01|Includes relationship intelligence and typed source identifiers.|
|Phase 1 behavior remains valid|P2-B01|Existing storage tests and fixtures are updated and rerun.|
|SQLite index exists outside the vault|P2-B02|Application-data and vault-identity handling are established.|
|Index schema is independently versioned|P2-B02|Incompatible versions require rebuild rather than migration.|
|Normalized repositories exist|P2-B02|Includes concepts, aliases, domains, encounters, relationships, modules, search documents, embeddings, and invalid records.|
|Incremental synchronization works|P2-B03|Covers new, changed, unchanged, moved, removed, invalid, and conflicting files.|
|Full index rebuild works|P2-B03|Recreates all valid derived state from Markdown.|
|Invalid notes are excluded and reported|P2-B03|Includes stale-state diagnostics and partial-success reports.|
|Duplicate concept IDs are handled safely|P2-B03|All conflicting files are excluded.|
|Index revisions and sync reports work|P2-B03|Includes successful and partial-success updates.|
|Exact ID/title/alias lookup works|P2-B04|Deterministic fast path.|
|Weighted concept FTS works|P2-B04|Title, alias, overview, and domain weighting.|
|Weighted module FTS works|P2-B04|Preserves module and parent-concept locations.|
|Local embedding generation works|P2-B05|Includes identity, semantic, module, and query embeddings.|
|Selective embedding regeneration works|P2-B03, P2-B05|Hash detection begins in sync; generation is completed in the embedding branch.|
|Initial embedding model is empirically selected|P2-B05|Supported by retrieval and resource benchmarks.|
|Vector-search abstraction works|P2-B06|Services do not depend on one backend.|
|NumPy exact vector search works|P2-B06|Core local implementation and learning objective.|
|Vector backend is selected empirically|P2-B06|NumPy and extension-backed options are compared.|
|Hybrid retrieval works|P2-B07|Combines deterministic, lexical, concept-vector, and module-vector channels.|
|Reciprocal rank fusion works|P2-B07|Component ranks and scores remain available.|
|`ConceptSearchResult` is stable|P2-B07|Shared boundary for Phase 3 and recommendations.|
|Module hits preserve exact location|P2-B04, P2-B05, P2-B07|Includes heading, anchor, module, and segment metadata.|
|One-hop graph queries work|P2-B08|Includes inverse relationship derivation.|
|Learning encounter comparison works|P2-B08|Includes exact, enrich, new-unit, different, and ambiguous outcomes.|
|Provider-agnostic LLM infrastructure works|P2-B09|Includes local server and deterministic test providers.|
|Structured-output repair and fallback work|P2-B09|One repair attempt only.|
|Reasoning tasks work|P2-B10|Covers identity, new concepts, modules, relationships, aliases, source ambiguity, and clarification.|
|Initial LLM is empirically selected|P2-B10|Selected through task quality and resource benchmarks.|
|Action-specific recommendation models work|P2-B11|Uses discriminated unions.|
|Recommendation assembler verifies facts|P2-B11|Prevents model hallucinations from becoming index facts.|
|Alias proposals work|P2-B10, P2-B11|LLM proposes; assembler verifies; no note mutation occurs.|
|Relationship direction and learning roles work|P2-B10, P2-B11|Proposed and deterministically validated.|
|Missing prerequisites become backlog candidates|P2-B10, P2-B11|Backlog items are not persisted.|
|Scaffold module intent works|P2-B10, P2-B11|Examples remain inside concept notes.|
|Graceful fallback and failures work|P2-B09, P2-B11|Preserves usable search evidence.|
|Recommendations do not mutate Markdown|P2-B11|Verified explicitly.|
|Evaluation harness exists|P2-B12|Covers retrieval, reasoning, recommendations, and resources.|
|Approved thresholds are satisfied|P2-B12|Final configuration is evidence-based.|
|CLI exercises complete Phase 2 behavior|P2-B13|Includes human, JSON, and diagnostic modes.|
|Phase completion is verified end to end|P2-B13|Covers every Technical Completion Standard criterion.|

---

## 6. Real-Model and Hardware Milestones

|Branch Range|Runtime Expectations|
|---|---|
|P2-B01–P2-B04|Fully deterministic implementation and tests; no live models required.|
|P2-B05|Real local embedding models and memory/latency benchmarking begin.|
|P2-B06|Real vector-backend performance benchmarking begins.|
|P2-B07–P2-B08|Approved embedding/vector configuration is integrated; no LLM required.|
|P2-B09|Local LLM server connectivity and structured-output infrastructure begin.|
|P2-B10|Real local LLM reasoning and model comparison begin.|
|P2-B11|Approved reasoning configuration is integrated into recommendation assembly.|
|P2-B12|Full-system real-model evaluation and resource measurement occur.|
|P2-B13|Approved models and backends are exercised through final CLI workflows.|

---

## 7. Branch Planning Rules

For each Phase 2 branch:

- tests should be developed alongside implementation
    
- research-only completion is insufficient
    
- benchmark branches must end with a working selected implementation
    
- normal pytest should remain deterministic and model-independent
    
- real-model integration tests should use separate markers or commands
    
- benchmark and evaluation results should be reproducible
    
- implementation decisions should be documented after evidence is collected
    
- technical concept notes should be created only where they materially improve understanding
    
- branch success criteria should focus on outcomes rather than individual coding tasks
    
- broad architecture changes must be identified before implementation
    
- future-phase work should not be added unless technically necessary and explicitly justified
    

Typical branches should have four to six meaningful success criteria.

Complex integration branches may have up to eight.