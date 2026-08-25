## 1. Goal

Implement bounded concept-reasoning tasks (identity, new-concept, module intent, relationships/prerequisites, source ambiguity, alias proposal, clarification) with identity-first orchestration, and select a default local OpenAI-compatible reasoning model for Phase 2.

---

## 2. Branch Context

### Main System Area

- Concept identity and judgment-heavy decisions over narrowed candidates
- Task schemas and versioned prompts
- Default local reasoning model configuration

### Branch Dependencies

- P2-B09 (provider + repair framework)
- P2-B07 / P2-B08 (search/graph context)

### Risks / Things to Watch

- Skip LLM on deterministic exact identity
- No concurrent LLM calls initially
- Compact candidate context only (no full vault/notes)

---

## 3. Concepts I Need to Understand

- `[[Identity-first orchestration]]`
- `[[Bounded structured reasoning decisions]]`
- `[[Small local LLM selection]]` — ~sub-1B–3B class on personal hardware

Questions I should be able to answer:

- When must identity reasoning run before new-concept analysis?
- Why are reasoning decisions not final recommendations?
- What default model did Phase 2 select and why?

---

## 4. Cursor Implementation Planning Prompt

_(See Branch Plan B10 and Technical Plan §§4.22–4.23, 5.13.)_

---

## 5. Cursor Implementation Plan

### Summary of approach

1. Decision schemas under `studium.llm.reasoning.schemas`
2. Versioned tasks in `reasoning/registry.py`
3. Orchestration helpers (`reason_identity`, etc.) with deterministic skip path
4. Set `DEFAULT_REASONING_MODEL = "llama3.2:3b"` and default base URL for Ollama-compatible servers
5. Deterministic fixtures cover schemas without a live server

### Files created / modified

| Path | Role |
|------|------|
| `src/studium/llm/reasoning/` | schemas, registry, orchestrate |
| `src/studium/index/config.py` | `DEFAULT_REASONING_MODEL`, `DEFAULT_LLM_BASE_URL` |
| `tests/llm/test_llm.py` | identity skip + repair coverage |

### Approved to Implement?

- [x] Yes (implemented 2026-08-10)

---

## 6. Implementation Notes

### Shipped

- Seven task families registered (`concept_identity_v1`, `new_concept_analysis_v1`, …)
- `reason_identity` returns deterministic `same_concept` on Tier 0 exact match (no provider call)
- Default model: **`llama3.2:3b`** via `http://127.0.0.1:11434/v1` — selected as a practical ~3B OpenAI-compatible default for personal local servers; full multi-model bake-off deferred to live `llm` marker / B12 runs when a server is available

### Out of scope

- Recommendation envelope assembly (B11)
- Large curated live-model comparison report (expand under B12 when hardware available)

---
