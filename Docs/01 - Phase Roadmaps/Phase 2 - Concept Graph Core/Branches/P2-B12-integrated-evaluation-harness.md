## 1. Goal

Provide a reproducible evaluation harness for Phase 2 retrieval and recommendations: curated YAML cases, metric calculation (Recall@K, MRR, action/structured validity), report generation, and documented approved thresholds — with default CI remaining deterministic.

---

## 2. Branch Context

### Main System Area

- Retrieval and recommendation quality measurement
- Configuration comparison hooks
- Threshold documentation for Phase 2 completion

### Branch Dependencies

- P2-B07 (search)
- P2-B11 (recommendations)
- Optional live providers for real-model runs

### Risks / Things to Watch

- Avoid overfitting a tiny synthetic set to one model
- Keep normal pytest free of live models
- Provisional Technical Plan thresholds may need amendment with evidence

---

## 3. Concepts I Need to Understand

- `[[Recall@K]]` / `[[Mean Reciprocal Rank (MRR)]]`
- `[[Acceptable-action evaluation]]` — soft targets vs exact prose
- `[[Cold vs warm latency]]` (reported when live runs are available)

Questions I should be able to answer:

- How many cases does Phase 2 require?
- Which thresholds are approved in code?
- Why are synthetic cases insufficient alone for production gates?

---

## 4. Cursor Implementation Planning Prompt

_(See Branch Plan B12 and Technical Plan §§5.18, 10.8–10.11.)_

---

## 5. Cursor Implementation Plan

### Summary of approach

1. Package `studium.evaluate`
2. 40–60 YAML cases under `evals/phase2/cases/`
3. `load_evaluation_cases`, retrieval/recommendation runners, `generate_evaluation_report`, Markdown report helper
4. `APPROVED_THRESHOLDS` constants matching Technical Plan provisional values

### Files created / modified

| Path | Role |
|------|------|
| `src/studium/evaluate/` | models + harness |
| `evals/phase2/cases/*.yaml` | 45 multi-domain synthetic cases |
| `tests/evaluate/test_evaluate.py` | load + metric smoke tests |

### Approved to Implement?

- [x] Yes (implemented 2026-08-10)

---

## 6. Implementation Notes

### Shipped

- **45** YAML cases (`p2-001` … `p2-045`) across ml/math/systems/biology/history domains
- Metrics: Recall@5 hit-rate aggregation, MRR, exact-lookup accuracy, action accuracy, structured validity
- Approved thresholds in code:
  - exact lookup accuracy: **1.0**
  - Recall@5: **≥ 0.90**
  - structured validity: **1.0**
  - action accuracy: **≥ 0.85**
  - relationship-direction accuracy: **≥ 0.90** (tracked for live expansion)

### Known limits

- Cases are synthetic and primarily wire the harness; they do not yet prove live MiniLM/LLM quality on a real vault
- Expand with vault-backed fixtures and `-m embedding` / `-m llm` runs before treating `thresholds_met` as a production release gate

---
