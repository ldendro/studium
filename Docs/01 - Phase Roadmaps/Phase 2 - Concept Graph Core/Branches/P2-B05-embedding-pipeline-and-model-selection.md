## 1. Goal

To implement the embedding layer necessary for dense retrieval which will include vector generation and the incorporation of a hybrid retrieval system by empirically evaluating potential embedding models. The embedding-interface will be provider independent, allowing the application to easily switch embedding models which will be necessary for empirical evaluation and future changes. 

---

## 2. Branch Context

This branch primarily affects the retrieval layer and is a pivotal part of the applications search capabilities, as semantic meaning will be evaluated through the embeddings of every part of a concept note in comparison with an embedding of the user query 

### Risks / Things to Watch

Potential issues, tradeoffs, or fragile areas: Latency, Correctness

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

- `[[Dense embedding]]` — map text to a fixed-length vector that encodes meaning for similarity search
    
- `[[Embedding space / model identity]]` — comparable vectors must share the same model, revision, and dimension
    
- `[[Cosine similarity and L2 normalization]]` — how closeness is scored once vectors exist (search itself is B06)
    
- `[[Contrastive / retrieval fine-tuning (bi-encoder)]]` — why “sentence” models work for query↔document ranking
    
- `[[Batching and throughput]]` — encode many documents per forward pass to amortize model load
    
- `[[Selective regeneration via input hashes]]` — only re-embed when input text or model metadata changes
    
- `[[Recall@K and MRR]]` — metrics for choosing a model on a small retrieval eval set
    

Questions I should be able to answer:

- Why must query and document vectors come from the same embedding space?
    
- What is the difference between identity, semantic, and module embeddings?
    
- Why does B05 generate vectors but defer vector *search* to B06?
    
- How do `EmbeddingWorkRequest`s from B03 connect to actual provider calls?
    
- What does “smallest model that meets quality needs” mean for an 8GB MacBook Air?
    

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

Branch: Embedding Pipeline and Model Selection

Branch goal: To implement provider-independent local embedding generation for identities, semantic concepts, modules, and queries, enabling hybrid search. An embedding model will be empirically selected for my use case as it pertains to the use of a MacBook Air with 8GB application memory, although it is necessary that the embedding interface is provider independent as stronger embedding models will be used in the future once hardware becomes less of a concern. 

Expected outcome: A selected local model generates all Phase 2 embedding types for use in later branches when hybrid retrieval is finalized. 

Relevant context:
Within Phase 2 - Concept Graph Core, the files 2 - Final Phase Roadmap, 3 - Technical Plan, and 4 - Branch Plan. Ignore 1 - Initial Phase Roadmap. 

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
   
In the direct chat recommend AI/ML concepts for me to better understand as it pertains to the branch in implementation as seen with the first concept in 10-Concepts/BM25 (Best Matching 25)
```

---

## 5. Cursor Implementation Plan

Paste or summarize Cursor’s implementation plan here before implementation begins.

### 1. Summary of proposed approach

Add a **provider-independent embedding layer** that turns B03’s deferred `EmbeddingWorkRequest`s into persisted vectors, plus ephemeral query embedding for later hybrid search.

**A. Provider protocol (no search yet)**
1. Define a small interface: `embed_documents(texts)`, `embed_query(text)`, `model_metadata()`
2. Ship a **fake/deterministic** provider for unit tests
3. Ship **one or more local adapters** for candidate comparison (e.g. sentence-transformers / ONNX / mlx — final stack chosen after decision §8)
4. Record model id, revision, dimension, normalization behavior, max length, batch behavior

**B. Work consumer + persistence**
1. Consume `SyncReport.embedding_work` (and optional rebuild path)
2. Batch by embedding type; call provider **outside** long DB write locks where practical
3. Upsert into `embeddings` keyed by `(owner_type, owner_id, embedding_type, segment_id)` when `input_hash` or model metadata changes
4. Serialize vectors as a documented BLOB format (recommend little-endian float32)
5. Preserve `parent_concept_id` + `segment_id` hierarchy (`module_id:0` for Phase 2 single-segment)

**C. Selective regeneration**
1. B03 already emits work only when input hashes change
2. B05 also regenerates when **active model id/revision/dimension** differs from stored rows (model upgrade path)
3. Unchanged inputs reuse stored vectors (no provider call)

**D. Module body policy (minimal)**
1. Define `MAX_MODULE_EMBED_CHARS` (truncate with stable hash of truncated input)
2. Optionally extract a cheap Scaffold Modules section body if already available without a parser rewrite; otherwise keep focus/title-only until extraction is cheap — call out in decisions
3. Schema already allows multi-segment later; Phase 2 remains **one module → one segment → one vector**

**E. Empirical model selection (8GB MacBook Air)**
1. Build a small retrieval eval subset (queries + expected concept/module ids from vault fixtures or curated notes)
2. Compare candidate local models on Recall@K, MRR, load time, warm/cold latency, peak memory, batch throughput
3. Document a benchmark report and set the Phase 2 default in config
4. Prefer **smallest model that meets quality**, not the absolute smallest

**Scope boundary**
- B05 = generate + store + select model + query embed API
- **Not** NumPy/SQLite vector search (B06)
- **Not** hybrid fusion / `ConceptSearchService` (B07)
- **Not** full long-module chunking

**Reuse**
- B03 `embedding_inputs.py`, hashes, `EmbeddingWorkRequest`, `embeddings` table + repository CRUD
- Library-only API (align with B03/B04); CLI can wait for B13 unless a tiny debug helper is useful

---

### 2. Files likely to be created or modified

| Path | Action | Role |
|------|--------|------|
| `src/studium/index/embeddings/` or `src/studium/embeddings/` | **Create** | Provider protocol, metadata types, fake provider, local adapter(s) |
| `src/studium/index/embeddings/serialize.py` | **Create** | float32 BLOB pack/unpack + dimension checks |
| `src/studium/index/embeddings/pipeline.py` | **Create** | Consume work requests → batch embed → upsert rows |
| `src/studium/index/embeddings/config.py` or extend `index/config.py` | **Modify/Create** | Active provider, model id, batch size, max module chars, optional dims |
| `src/studium/index/repositories/embeddings.py` | **Modify** | Upsert/replace-by-owner-type-segment; delete stale; list by model |
| `src/studium/index/sync/synchronizer.py` | **Modify lightly** | Hook: after sync, optionally run embedding pipeline (or export seam only) |
| `src/studium/index/sync/embedding_inputs.py` / `project.py` | **Modify if needed** | Module body truncation / extraction for `Body:` |
| `src/studium/index/schema.py` / `config.py` | **Modify only if required** | Prefer no schema bump; unique constraint or index for upsert if missing |
| `pyproject.toml` | **Modify** | Optional extra e.g. `embeddings` for ML deps; keep core lean |
| `tests/index/embeddings/` | **Create** | Fake provider, serialize, selective regen, batch order |
| `tests/index/embeddings/integration/` or marked suite | **Create** | Real-model tests (opt-in, not default pytest) |
| `Docs/.../eval/` or `artifacts/` | **Create lightly** | Candidate comparison report (checked-in summary, not huge binaries) |
| `README.md` | **Modify lightly** | Embedding library API + optional install |

**Out of scope files:** vector store backends, RRF, hybrid search service, CLI search commands, LLM providers.

---

### 3. Step-by-step implementation sequence

#### Step 1 — Provider interface + fake provider
- Define `EmbeddingProvider` protocol / ABC with `embed_documents`, `embed_query`, `model_metadata`
- `EmbeddingModelMetadata`: model_id, model_revision, dimension, normalizes_embeddings, max_input_chars, batch_size_hint
- Fake provider: deterministic hash→vector (fixed dim) for tests
- Unit-test batch order preservation (output[i] corresponds to texts[i])

#### Step 2 — Vector serialization + repository upsert
- Document BLOB layout: little-endian float32 × dimension
- `upsert_embedding(...)` / `replace_embeddings_for_owner(...)` so regen is idempotent
- Delete embeddings when concept/module projection removed (cascade may already cover FK parent; verify module owner cleanup)

#### Step 3 — Embedding pipeline
```text
process_embedding_work(engine, work: list[EmbeddingWorkRequest], provider, *, indexed_revision) -> EmbeddingProcessReport
```
- Skip items whose stored row already matches `(input_hash, model_id, model_revision, dimension)`
- Batch remaining texts; write rows with owner/segment/parent/type metadata
- Expose `embed_query(provider, text) -> vector` (no persistence)

#### Step 4 — Wire to sync (thin)
- Prefer: `sync_vault` returns work as today; caller or optional `sync_and_embed(...)` runs pipeline after commit
- Alternative (also fine): optional flag on `sync_vault` — decide in §8
- Rebuild path: after full sync, process all emitted work

#### Step 5 — Module input length policy
- Constant `MAX_MODULE_EMBED_CHARS` (e.g. 2–8k chars — decide in §8)
- Truncate body before hash if body is added; ensure hash is of **exactly** embedded text
- Keep `segment_id = f"{module_id}:0"` and `segment_count = 1`

#### Step 6 — Local candidate adapters + config
- Implement 2–3 candidate adapters behind the same interface
- Config selects active provider/model without code changes in search (B07 later)
- Optional dependency group so default `uv sync` stays light

#### Step 7 — Evaluation subset + model selection
- Curate small query set (identity + semantic + module intents)
- Measure Recall@5 / MRR, latency, load, peak RSS on MacBook Air 8GB
- Write short benchmark report; set default model in config
- Real-model tests gated (`pytest -m embedding` or env flag)

#### Step 8 — Verify
- Cover Branch Plan checklist; ruff/pyright; default pytest without downloading models

---

### 4. Data model / schema changes

| Change | Detail |
|--------|--------|
| `embeddings` table | **Likely keep as-is** (already has owner, segment, type, BLOB, dim, model, hash, revision) |
| Unique key for upsert | **Recommended:** unique on `(owner_type, owner_id, embedding_type, segment_id)` — if missing, schema bump **3 → 4** (rebuild policy) |
| Concept-note Markdown | No change |
| Multi-segment chunking | Schema-ready only; not implemented |
| Query embeddings | Ephemeral; not stored |

No architecture change required beyond optional unique constraint and embedding config fields.

---

### 5. Important functions / classes / modules

| Symbol | Role |
|--------|------|
| `EmbeddingProvider` | Provider-independent protocol |
| `FakeEmbeddingProvider` | Deterministic tests |
| `Local*EmbeddingProvider` | Candidate local model adapter(s) |
| `model_metadata()` | Space identity for regen + B06 |
| `pack_vector` / `unpack_vector` | BLOB codec |
| `process_embedding_work(...)` | Work → batch → upsert |
| `embed_query(...)` | Query-time vector |
| `upsert_embedding` / list/delete helpers | Persistence |
| `MAX_MODULE_EMBED_CHARS` | Truncation policy |
| Existing `build_*_embedding_input` / `EmbeddingWorkRequest` | Reused from B03 |

---

### 6. Tests / verification steps

| Scenario | Expectation |
|----------|-------------|
| Fake batch order | `embed_documents` preserves input order |
| Serialize round-trip | pack/unpack same floats + dim check |
| Identity hash regen | title/alias change → new identity (+ semantic) work and row |
| Semantic hash regen | overview change → semantic only |
| Module hash regen | one module change → that module only |
| Model upgrade | same input_hash but new model_id → regenerate |
| Skip unchanged | second sync with no edits → no provider calls / no row churn |
| Query embed | returns vector of declared dimension; not persisted |
| Long module | truncation stable; hash matches truncated input |
| Fake vs real | default CI uses fake; real models opt-in |

**Commands**
```bash
uv run ruff check .
uv run pyright
uv run pytest tests/index -q
# opt-in:
uv run pytest -m embedding
```

---

### 7. Risks, edge cases, or assumptions

| Risk | Mitigation |
|------|------------|
| 8GB RAM OOM with large models | Small candidates first; measure peak RSS; optional deps |
| Mixing embedding spaces | Store model_id/revision/dim; regen on mismatch; B06 must filter |
| Empty module `Body:` weak vectors | Define truncation + optional cheap body extract; document limitation |
| Embedding inside DB transaction | Generate outside locks; write short upserts |
| Heavy deps in core install | Optional `embeddings` extra |
| Overfitting tiny eval set | Keep set diverse; treat Recall@5 ≥ 0.90 as aspirational until approved |
| Schema unique constraint missing | Add with version bump if upsert races |

**Assumptions**
- B03 work-request seam remains the source of truth for *what* to embed
- B06 will load BLOBs and implement search; B05 only needs a stable codec
- One active Phase 2 default model after evaluation
- Library API only for now

---

### 8. Questions or decisions needed before implementation

| # | Decision | Recommendation |
|---|----------|----------------|
| 1 | Where does embedding live in the package? | **`studium.index.embeddings`** (next to sync/search) |
| 2 | Sync integration | **Separate `process_embedding_work` + optional `sync_and_embed`** (keeps sync testable without ML) |
| 3 | Local stack for 8GB Air | **Start with small sentence-transformers / ONNX candidates** (e.g. MiniLM-class); compare 2–3; avoid large instruct models |
| 4 | Optional deps | **Yes — `[project.optional-dependencies] embeddings = [...]`** |
| 5 | Unique constraint on embeddings | **Add + schema bump to 4** if not enforceable today |
| 6 | Module body text | **Truncate empty/focus-first now**; add cheap section extract only if low-cost |
| 7 | `MAX_MODULE_EMBED_CHARS` | **Start at 4000–8000** chars; tune after memory benchmarks |
| 8 | Vector dtype | **float32 little-endian** |
| 9 | Eval set size | **~20–40 queries** for B05 selection; fuller harness stays B12 |
| 10 | Recall@5 ≥ 0.90 | **Aspirational gate**; select best feasible on 8GB if unmet |
| 11 | CLI | **Library only** (debug script ok under tests/tools) |

### Plan Review Notes

Decisions recorded (2026-08-04) — all recommendations approved:

1. Package location → **`studium.index.embeddings`**
2. Sync integration → **`process_embedding_work` + optional `sync_and_embed`**
3. Local stack → **small sentence-transformers / ONNX candidates** (MiniLM-class first)
4. Optional deps → **`embeddings` extra**
5. Unique constraint → **add + schema bump to 4**
6. Module body → **truncate empty/focus-first**; cheap section extract only if low-cost
7. `MAX_MODULE_EMBED_CHARS` → **4000–8000** (tune after memory benchmarks)
8. Vector dtype → **float32 little-endian**
9. Eval set → **~20–40 queries** for B05; fuller harness stays B12
10. Recall@5 ≥ 0.90 → **aspirational**; pick best feasible on 8GB if unmet
11. CLI → **library only**

### Approved to Implement?

- [x] Yes
    
- [ ] No, revise plan first
    

---

## 6. Implementation Notes

Shipped (2026-08-04):

- Schema **v4**: `embeddings.segment_id` NOT NULL (default `""`) + unique
  `(owner_type, owner_id, embedding_type, segment_id)`
- Package `studium.index.embeddings`: protocol, float32 LE serialize, fake provider,
  `SentenceTransformersEmbeddingProvider` (optional extra), `process_embedding_work`,
  `embed_query`, `sync_and_embed`
- Config: `MAX_MODULE_EMBED_CHARS=4000`, `DEFAULT_EMBEDDING_MODEL_ID` MiniLM,
  `DEFAULT_EMBEDDING_BATCH_SIZE=32`
- Optional dep: `uv sync --extra embeddings`; pytest marker `embedding`
- Default CI uses `FakeEmbeddingProvider` only (no model download)

Deferred to later branches / follow-ups:

- Full ~20–40 query empirical model bake-off report (B05 light eval / B12 harness)
- ONNX / mlx adapters beyond sentence-transformers
- Vector search (B06) and hybrid fusion (B07)

---
