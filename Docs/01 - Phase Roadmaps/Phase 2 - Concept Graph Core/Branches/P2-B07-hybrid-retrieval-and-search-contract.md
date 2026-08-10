## 1. Goal

Combine deterministic identity lookup, weighted FTS, and identity/semantic/module vector channels into a stable hybrid search contract (`ConceptSearchQuery` / `ConceptSearchResult`) using weighted reciprocal rank fusion — without invoking LLM reasoning.

---

## 2. Branch Context

### Main System Area

- Hybrid concept retrieval
- Ranked candidate sets and module hits
- Search diagnostics / evidence for Phase 3 and recommendations

### Branch Dependencies

- P2-B04 (lexical FTS + Tier 0 lookup)
- P2-B05 / P2-B06 (embeddings + vector channel APIs)

### Risks / Things to Watch

- Mixing raw FTS and cosine scores → use ranks via RRF, not raw scores
- Partial search when vector channels lack provider / `ModelSpaceFilter`
- Keep search independent of recommendation assembly (B11)

---

## 3. Concepts I Need to Understand

- `[[Reciprocal rank fusion (RRF)]]` — fuse incompatible channel score scales by rank
- `[[Search execution tiers]]` — Tier 0 exact identity bypasses hybrid fusion
- `[[ConceptSearchResult contract]]` — shared boundary for UI and recommendations
- `[[Module collapse under parent]]` — module hits contribute to concept ranking without losing location

Questions I should be able to answer:

- Why are deterministic ID/title/alias matches not ordinary RRF inputs?
- What does `SearchStatus.PARTIAL` mean when vectors are unavailable?
- Why preserve component ranks/scores alongside fused rank?

---

## 4. Cursor Implementation Planning Prompt

_(Planning done as part of the Phase 2 continuous push; see Branch Plan B07 and Technical Plan §§4.15, 5.10–5.11, 6.5–6.6.)_

---

## 5. Cursor Implementation Plan

### Summary of approach

1. Extend `studium.index.search` with hybrid models + `search_concepts`
2. Tier 0: reuse `resolve_concept_identity` → exact `ConceptSearchResult`
3. Tier 1: FTS + identity/semantic/module vectors → weighted RRF → enrich metadata
4. Configurable `DEFAULT_RRF_CONSTANT` / `DEFAULT_RRF_WEIGHTS`
5. Filters (domains, types, vault/review status) and limits

### Files created / modified

| Path | Role |
|------|------|
| `src/studium/index/search/models.py` | `ConceptSearchQuery` / `Result`, channels, evidence |
| `src/studium/index/search/rrf.py` | Weighted RRF helpers |
| `src/studium/index/search/hybrid.py` | `search_concepts`, `HybridSearchOptions` |
| `src/studium/index/config.py` | RRF defaults |
| `tests/index/search/test_hybrid.py` | Tier 0/1, filters, partial status |

### Approved to Implement?

- [x] Yes (implemented 2026-08-10 as part of Phase 2 completion push)

---

## 6. Implementation Notes

### Shipped

- Facade: `studium.index.search_concepts(engine, query, options=...)`
- Tier 0 exact / ambiguous paths without embeddings
- Tier 1 parallel vector channels when `embedding_provider` or query vectors + `ModelSpaceFilter` provided; otherwise FTS-only with `SearchStatus.PARTIAL`
- Module hits retain heading/anchor/segment; parents get `matching_modules`
- Tests: RRF math, exact match, fake-embedding hybrid path, concept-type filter

### Out of scope (later)

- Recommendation assembly (B11)
- CLI (B13)
- Live-model retrieval quality gates (B12 harness)

---
