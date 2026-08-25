# Phase 2 Completion Note

**Date:** 2026-08-10  
**Scope:** Branches B01–B13 delivered as library + CLI (no per-branch docs for B07–B13).

## Selected configuration

| Knob | Value |
|------|--------|
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (optional extra); tests use `FakeEmbeddingProvider` |
| Vector backend | `numpy` (`DEFAULT_VECTOR_BACKEND`) |
| RRF | constant `60`, weights fts/identity/semantic/module = 1.0 / 1.0 / 1.2 / 0.8 |
| Reasoning model | `llama3.2:3b` via OpenAI-compatible server (`DEFAULT_REASONING_MODEL`, base `http://127.0.0.1:11434/v1`) |
| Default CI LLM | `DeterministicLLMProvider` |

## Delivered surfaces

- Hybrid search: `studium.index.search_concepts` → `ConceptSearchResult`
- Graph + encounters: `studium.index.graph`
- LLM + reasoning: `studium.llm`
- Recommendations: `studium.recommend.recommend` (no Markdown mutation)
- Eval harness: `studium.evaluate` + `evals/phase2/cases` (45 YAML cases)
- CLI: `studium graph {sync,rebuild,status,find,candidates,inspect,modules,relationships,propose,evaluate-retrieval,evaluate-recommendations}`

## Approved eval thresholds (harness)

See `APPROVED_THRESHOLDS` in `studium.evaluate.harness` (exact lookup 100%, Recall@5 ≥ 0.90, structured validity 100%, action accuracy ≥ 0.85). Synthetic cases wire the harness; live-model threshold confirmation remains an opt-in `llm` / `embedding` exercise on a machine with local providers.

## Known limits

- Vector channels in hybrid search require provider/vectors + `ModelSpaceFilter` or search is FTS-only (`partial`)
- Real LLM model comparison is adapter-ready; CI stays deterministic
- Eval case set is multi-domain but synthetic — expand with vault fixtures before claiming production quality gates
- Recommendation approval/persistence remains Phase 4
