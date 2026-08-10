## 1. Goal

Convert search evidence and bounded reasoning into safe, validated, action-specific `ConceptRecommendation` objects (discriminated union) via a deterministic assembler that verifies index facts — without mutating concept-note Markdown.

---

## 2. Branch Context

### Main System Area

- Recommendation envelope and action payloads
- Deterministic verification / confidence / fallbacks
- Alias suggestions and backlog candidates

### Branch Dependencies

- P2-B07 (search result)
- P2-B08 (encounters / graph)
- P2-B09 / P2-B10 (optional LLM path)

### Risks / Things to Watch

- LLM must not invent unchecked vault IDs
- Missing prerequisites become backlog candidates (not persisted)
- No Markdown writes from this package

---

## 3. Concepts I Need to Understand

- `[[Discriminated recommendation union]]`
- `[[Deterministic recommendation assembler]]`
- `[[Evidence vs diagnostics]]`
- `[[RecommendationFailure stages]]`

Questions I should be able to answer:

- Which facts must the assembler verify before accepting an LLM claim?
- What happens on ambiguous identity without an LLM?
- Why is “no mutation” an explicit success criterion?

---

## 4. Cursor Implementation Planning Prompt

_(See Branch Plan B11 and Technical Plan §§4.19, 4.26–4.28, 5.12–5.16.)_

---

## 5. Cursor Implementation Plan

### Summary of approach

1. Package `studium.recommend` with envelope + seven action variants + `RecommendationFailure`
2. `recommend(engine, search=..., provider=..., source_*=...)` path selection
3. Deterministic paths: exact use-existing, ambiguous clarification, encounter add/update/redundant, module shortcut, fallback create-new
4. LLM path when provider supplied: identity → clarification → new-concept analysis
5. `assemble_alias_suggestion` with collision downgrade

### Files created / modified

| Path | Role |
|------|------|
| `src/studium/recommend/models.py` | Discriminated models |
| `src/studium/recommend/service.py` | Assembler + `recommend` |
| `tests/recommend/test_recommend.py` | Exact / ambiguous / fallback / no-mutation |

### Approved to Implement?

- [x] Yes (implemented 2026-08-10)

---

## 6. Implementation Notes

### Shipped

- Actions: use-existing, create-new, add/update learning encounter, add scaffold module, mark redundant, request clarification
- Deterministic exact identity → high-confidence `use_existing_concept`
- Ambiguous identity → `request_clarification` without LLM
- Explicit no-mutation test (concept row unchanged after `recommend`)
- Phase 4 still owns approval and persistence

### Out of scope

- CLI wrapping (B13)
- Full golden fixtures for every edge path (extend as eval cases grow)

---
