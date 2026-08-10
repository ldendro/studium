## 1. Goal

Develop a stable vector-search abstraction that incorporates NumPy exact vector retrieval, a viable SQLite-extension option, and similarity metrics to enable determining how generated vectors should be stored and searched locally. 

---

## 2. Branch Context

### Main System Area

This branch primarily affects:

- Concept identity-vector retrieval
- Concept semantic-vector retrieval
- Module-vector retrieval
- Vector backend
---

## 3. Concepts I Need to Understand

- `[[Cosine similarity and L2 normalization]]` — default metric; cosine ≡ dot product of unit vectors
    
- `[[Exact top-K vs approximate nearest neighbor (ANN)]]` — NumPy does exact search; extensions may approximate
    
- `[[Vector search backend abstraction]]` — services depend on an interface, not NumPy or a SQLite extension
    
- `[[Embedding space / model identity]]` — only compare vectors with matching model_id, revision, dimension, normalize mode
    
- `[[Batch matrix similarity]]` — score one query against many stored vectors with one NumPy matmul
    

Questions I should be able to answer:

- Why must query and corpus vectors share the same embedding space?
    
- Why exclude `dimension == 0` rejection rows from search?
    
- Why does B06 ship channel APIs but leave hybrid RRF to B07?
    
- When is exact NumPy search “good enough” vs an extension for a personal vault?
    

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

Branch: Vector Search Backend

Branch goal: See the Goal section of the Branches/P2-B06-vector-search-backend

Expected outcome: Identity, semantic, and module vectors can be searched reliably and in an efficient manner. 

Relevant context: See within Phase 2 - Concept Graph Core the files 2 - Final Phase Roadmap, 3 - Technical Plan, and 4 - Branch Plan. Ignore 1 - Initial Phase Roadmap

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
8. Questions or decisions needed before implementation (No obvious questions)
9. Important concepts related to this branch that I should know before implementation
```

---

## 5. Cursor Implementation Plan

Paste or summarize Cursor’s implementation plan here before implementation begins.

### 1. Summary of proposed approach

Add a **provider-independent vector search layer** that reads B05-persisted embeddings from SQLite and returns ranked identity / semantic / module hits for later hybrid fusion (B07).

**A. Backend protocol (no hybrid yet)**
1. Define `VectorSearchBackend` with typed search ops:
   - `search_concept_identity(query_vector, *, limit, model_filter) -> list[VectorConceptHit]`
   - `search_concept_semantic(...)`
   - `search_module_semantic(...) -> list[VectorModuleHit]`
2. Shared filter contract: only rows matching active `(model_id, model_revision, dimension, normalizes_embeddings)` and **`dimension > 0`** (exclude B05 rejection sentinels)
3. Default metric: **normalized cosine** = L2-normalize query + corpus (if not already normalized) then **dot product**; score in `[-1, 1]` (or `[0, 1]` after clamp — pick one and document)

**B. NumPy exact backend (Phase 2 default candidate)**
1. Load candidate rows for one `embedding_type` (+ model filter) from SQLite
2. Unpack float32 LE BLOBs via existing `unpack_vector`
3. Stack into `float32` matrix; optionally L2-normalize rows once
4. Exact top-K: `scores = matrix @ query`; `argpartition` / sort for top-K
5. Join owner metadata (concept title, module parent/heading/anchor) for hit enrichment — mirror lexical hit shape where practical
6. Keep corpus load **lazy / per-search** first; optional in-memory cache keyed by `(embedding_type, model_id, revision, dim)` only if benchmarks show need — avoid premature complexity

**C. SQLite-extension backend (benchmark, optional)**
1. Thin adapter behind the same protocol (e.g. sqlite-vec / sqlite-vss — pick one after installability check on Apple Silicon)
2. Must not be required for default `uv sync` / CI
3. Document install, rebuild, and ANN vs exact behavior
4. Run the same correctness contract tests as NumPy; compare latency/memory/rebuild at personal-vault scale

**D. Library facades (lexical-style)**
1. Thin engine-facing helpers similar to `search_concepts_fts`:
   - `search_concept_identity_vectors(engine, query_vector, ...)`
   - `search_concept_semantic_vectors(...)`
   - `search_module_semantic_vectors(...)`
2. Callers supply the query vector (from B05 `embed_query`); B06 does not call embedding providers by default
3. Optional convenience: `search_*_vectors_text(engine, provider, text, ...)` that embeds then searches — nice for tests/debug, not required for B07

**E. Empirical selection (weighted — do not pre-commit to NumPy)**
1. Small fixture vault + FakeEmbeddingProvider (deterministic) for correctness
2. Optional real-model micro-bench (gated like B05 `embedding` marker)
3. Run the same workload on NumPy exact **and** sqlite-vec (when installable): correctness, cold/warm latency, peak RSS, rebuild/load cost, packaging reliability on Apple Silicon
4. **Write a short selection report** in Implementation Notes stating which backend won and why (not “NumPy by default unless extension wins”)
5. Config knob: `DEFAULT_VECTOR_BACKEND` set to the **empirically chosen** winner (`"numpy"` or `"sqlite_vec"`)

**Scope boundary**
- B06 = search abstraction + NumPy exact + extension benchmark + **documented backend choice** + channel APIs
- **Not** RRF / `ConceptSearchService` (B07)
- **Not** re-doing embedding generation (B05)
- **Not** CLI search commands

**Reuse**
- B05 `pack_vector` / `unpack_vector`, `embeddings` table, `embed_query`, model metadata fields
- Lexical search Pydantic hit / facade style from B04

---

### 2. Files likely to be created or modified

| Path | Action | Role |
|------|--------|------|
| `src/studium/index/vector/` or `.../search/vector.py` | **Create** | Protocol, hit types, NumPy backend, facades |
| `src/studium/index/vector/numpy_backend.py` | **Create** | Exact top-K cosine |
| `src/studium/index/vector/sqlite_ext_backend.py` | **Create lightly** | Optional extension adapter (may stay stub + docs if install fails) |
| `src/studium/index/repositories/embeddings.py` | **Modify** | `list_embeddings_for_search(embedding_type, model_id, …)` excluding dim=0 |
| `src/studium/index/config.py` | **Modify** | `DEFAULT_VECTOR_BACKEND`, maybe batch load limits |
| `src/studium/index/__init__.py` / `search/__init__.py` | **Modify** | Export channel search APIs |
| `pyproject.toml` | **Modify** | Add `numpy` (recommend **core** dep — B06 is a Phase 2 completion requirement) |
| `tests/index/vector/` | **Create** | Cosine correctness, top-K order, model filter, dim=0 exclusion, backend contract |
| `Docs/.../P2-B06-...md` / short eval note | **Modify lightly** | Backend selection summary |
| `README.md` | **Modify lightly** | Vector search library entrypoints |

**Out of scope:** hybrid fusion, CLI, new embedding types, migrating away from SQLite BLOB storage.

---

### 3. Step-by-step implementation sequence

#### Step 1 — Hit types + backend protocol
- `VectorConceptHit` / `VectorModuleHit` (rank, score, ids, titles, embedding_type, model_id, optional segment_id)
- `VectorSearchBackend` protocol with the three search methods + model filter dataclass
- `ModelSpaceFilter(model_id, model_revision, dimension, normalizes_embeddings)`

#### Step 2 — Repository list-for-search
- Query embeddings by `embedding_type` + model filters; **`dimension > 0`**
- Return rows needed to unpack vectors + join owners (or two-step: vectors then metadata)

#### Step 3 — Similarity helpers + NumPy backend
- `l2_normalize`, `cosine_scores(matrix, query)` unit-tested without DB
- `NumpyVectorSearchBackend(engine)` implementing exact top-K
- Stable tie-break: `ORDER BY score DESC, owner_id` (and `segment_id` for modules)

#### Step 4 — Library facades + exports
- Mirror B04 naming; export from `studium.index`
- Document that query vectors must match corpus model space

#### Step 5 — Optional SQLite extension adapter
- Attempt one extension; if Apple Silicon / packaging is painful, ship adapter interface + “not selected” note rather than blocking the branch
- Same contract tests when extension available (`pytest.mark.vector_ext`)

#### Step 6 — Benchmarks + backend selection report
- Micro-bench both backends (when extension installs): load time, query latency, peak RSS at ~1k–10k vectors
- Score reliability, correctness, latency, memory, rebuild cost, packaging on Apple Silicon
- Set `DEFAULT_VECTOR_BACKEND` to the winner; write the selection report in Implementation Notes
- After implementation, document why cosine scores stay in **[-1, 1]** (decision 8)

#### Step 7 — Verify
- ruff / pyright / pytest (default CI without extension / without downloading models)

---

### 4. Data model / schema changes

| Change | Detail |
|--------|--------|
| `embeddings` table | **Keep as-is** (BLOB + metadata already sufficient) |
| Indexes | **Optional:** `(embedding_type, model_id)` if list-for-search is slow — only if measured |
| Schema version | **Prefer no bump** unless adding an index that requires rebuild policy |
| Concept-note Markdown | No change |

No architecture change beyond the new search package and NumPy dependency.

---

### 5. Important functions / classes / modules

| Symbol | Role |
|--------|------|
| `VectorSearchBackend` | Backend-independent protocol |
| `NumpyVectorSearchBackend` | Exact cosine top-K |
| `SqliteExtensionVectorSearchBackend` | Optional ANN/extension path |
| `ModelSpaceFilter` | Stale/mismatched vector exclusion |
| `VectorConceptHit` / `VectorModuleHit` | Ranked results for B07 channels |
| `search_*_vectors(...)` | Engine facades |
| `list_embeddings_for_search(...)` | Filtered corpus load |
| Existing `unpack_vector` / `embed_query` | Codec + query vectors |

---

### 6. Tests / verification steps

| Scenario | Expectation |
|----------|-------------|
| Cosine known vectors | Orthogonal → ~0; identical → ~1; opposite → ~-1 (if not clamped) |
| Top-K order | Highest similarity first; stable owner_id tie-break |
| Model filter | Different `model_id` / revision / dim excluded |
| Rejection rows | `dimension == 0` never returned |
| Type isolation | Identity search does not return semantic rows |
| Module hits | Include `concept_id`, `segment_id`, location fields |
| Empty corpus | Empty list, no crash |
| Backend contract | NumPy (and ext if present) agree on ranking for tiny fixture |
| Fake end-to-end | sync_and_embed → search recovers seeded concept |

**Commands**
```bash
uv run ruff check .
uv run pyright
uv run pytest tests/index -q
# opt-in if extension packaged:
uv run pytest -m vector_ext
```

---

### 7. Risks, edge cases, or assumptions

| Risk | Mitigation |
|------|------------|
| Loading all vectors into RAM | Start per-type load; personal vaults are small; add cache only if needed |
| Mixing embedding spaces | Strict `ModelSpaceFilter`; tests for exclusion |
| B05 dim-0 rejection sentinels | Always filter `dimension > 0` |
| Unnormalized stored vectors | Honor `normalizes_embeddings`; normalize at search if false |
| Extension install pain on macOS | Treat as a scored criterion in the selection report; if unusable, NumPy wins on reliability |
| Score scale vs FTS | Irrelevant for B06; B07 uses RRF ranks |
| Empty / missing query dim | Reject query vector whose length ≠ filter.dimension |
| Prematurely favoring NumPy | Benchmark both backends fairly; publish why the winner was chosen |

**Assumptions**
- Vectors remain in SQLite BLOBs from B05 (no separate vector DB file required for Phase 2)
- NumPy becomes a core dependency
- B07 will call the three channel APIs independently
- Library API only (align with B04/B05)

---

### 8. Questions or decisions needed before implementation

No blocking questions. Soft defaults to approve:

| # | Decision | Recommendation |
|---|----------|----------------|
| 1 | Package location | **`studium.index.vector`** (sibling of `search` / `embeddings`) |
| 2 | NumPy dependency | **Core** (not optional) — Phase 2 completion requirement |
| 3 | Default metric | **Normalized cosine** (dot of L2-normalized vectors) |
| 4 | Default backend | **Decide from weighted benchmark** of NumPy exact vs sqlite-vec; ship a written selection report (do not pre-rule out the extension) |
| 5 | Which SQLite extension | **Try `sqlite-vec` first** (simpler packaging); if install fails, report that and select NumPy |
| 6 | Schema bump | **Avoid** unless a new index is required |
| 7 | Query API shape | **Caller passes `query_vector` + `ModelSpaceFilter`**; text+provider helper optional |
| 8 | Score clamping | **Keep raw cosine in [-1, 1]**; do not force [0, 1] — **document the exact rationale after implementation** |
| 9 | CLI | **Library only** |

### Plan Review Notes

Decisions recorded (2026-08-07) — all recommendations approved with notes:

1. Package location → **`studium.index.vector`** (sibling of search & embeddings)
2. NumPy → **core dependency** (Phase 2 completion requirement)
3. Metric → **normalized cosine**
4. Backend choice → **weight the benchmark**; extension may win; **produce a selection report** explaining NumPy vs extension
5. Extension → **`sqlite-vec` first**
6. Schema bump → **avoid** unless needed
7. Query API → **`query_vector` + `ModelSpaceFilter`**
8. Scores → **raw cosine [-1, 1]**; explain precisely **after** implementation
9. CLI → **library only**

### Approved to Implement?

- [x] Yes
    
- [ ] No, revise plan first
    

---

## 6. Implementation Notes

### Shipped

- Package `studium.index.vector`: `ModelSpaceFilter`, `VectorConceptHit` /
  `VectorModuleHit`, `VectorSearchBackend`, `NumpyVectorSearchBackend`, optional
  `SqliteVecSearchBackend`, facades `search_concept_*_vectors` /
  `search_module_semantic_vectors`, `create_vector_backend`
- Repository helper `list_embeddings_for_search` (model-space filter + `dimension > 0`)
- Core dependency: **NumPy**; optional extra: **`vector-ext`** (`sqlite-vec`)
- Config: `DEFAULT_VECTOR_BACKEND = "numpy"`
- Schema: **no bump** (reuse B05 BLOB + metadata)
- Tests under `tests/index/vector/`; marker `vector_ext` for extension contract

### Backend selection report (2026-08-07, Apple Silicon)

Workload: 2 000 unit vectors × dim 384, 10 queries, top-20, both backends reading the
same `embeddings` BLOB rows (no schema bump; sqlite-vec used via
`vec_distance_cosine` scalar distance, not a persistent `vec0` index).

| Criterion | NumPy exact | sqlite-vec (optional) | Winner |
|-----------|-------------|------------------------|--------|
| Correctness (tiny fixture) | Exact cosine top-K | Agrees with NumPy within 1e-5 | Tie |
| Query latency (above workload) | ~453 ms/query | ~631 ms/query | **NumPy** |
| Peak traced memory | ~30.7 MB | ~30.5 MB | Tie |
| Rebuild / index maintenance | None (load BLOBs) | Same BLOB load + extension | **NumPy** (simpler) |
| Packaging / default CI | Core dep; always available | Optional `uv sync --extra vector-ext`; installs cleanly on this machine | **NumPy** (reliability for default) |
| ANN / large-scale upside | Exact only | Could add `vec0` later with schema/index work | sqlite-vec (future only) |

**Decision:** default backend is **`numpy`**. sqlite-vec remains an optional adapter for
contract tests and future ANN experiments; it did not win on latency or operational
simplicity when constrained to existing BLOB storage without a dedicated vector index.

### Why cosine scores stay in **[-1, 1]**

1. **Definitional fidelity** — Cosine similarity of unit vectors is the dot product;
   its natural range is `[-1, 1]`. Clamping to `[0, 1]` would no longer be cosine.
2. **Polarity is information** — Opposite / anti-aligned embeddings score near `-1`;
   forcing non-negative scores would erase that signal and compress mid-range values.
3. **B07 does not need absolute score scale** — Hybrid fusion will use reciprocal rank
   fusion over channel ranks, not raw cosine magnitudes, so preserving the true metric
   does not complicate fusion.
4. **Extension parity** — For unit vectors, sqlite-vec’s cosine *distance* converts as
   `similarity = 1 - distance`, which also lands in `[-1, 1]` and matches NumPy.

---
