## 1. Goal

Establish provider-agnostic structured LLM infrastructure: local OpenAI-compatible adapter, deterministic test provider, versioned task assets, structured validation, exactly one repair attempt, health/timeouts, and privacy-aware diagnostics — without selecting the final reasoning model or implementing full concept tasks yet (those are B10).

---

## 2. Branch Context

### Main System Area

- Local model-server integration
- Structured generation / repair
- Deterministic CI reasoning stubs

### Branch Dependencies

- P2-B07 / P2-B08 provide search/graph context that later tasks consume

### Risks / Things to Watch

- Default pytest must not require a live server
- Raw private prompts must not be logged by default
- Exactly one repair attempt (no unbounded retries)

---

## 3. Concepts I Need to Understand

- `[[Provider-agnostic LLM interface]]`
- `[[Structured output validation and repair]]`
- `[[OpenAI-compatible local servers]]` — Ollama / LM Studio / llama.cpp
- `[[Versioned task assets]]` — task id, prompt, schema, config

Questions I should be able to answer:

- Why is a deterministic provider required for CI?
- What happens after one failed repair?
- Why omit raw prompts from diagnostics by default?

---

## 4. Cursor Implementation Planning Prompt

_(See Branch Plan B09 and Technical Plan §§4.21–4.25.)_

---

## 5. Cursor Implementation Plan

### Summary of approach

1. Package `studium.llm`
2. Protocol + `DeterministicLLMProvider` + `OpenAICompatibleProvider` (stdlib HTTP)
3. `TaskDefinition` / `TaskConfig` + `run_reasoning_task` (validate → one repair)
4. Pytest marker `llm` excluded from default suite

### Files created / modified

| Path | Role |
|------|------|
| `src/studium/llm/protocol.py` | Provider protocol + result types |
| `src/studium/llm/deterministic.py` | Scripted JSON provider |
| `src/studium/llm/openai_compat.py` | Local `/v1` chat client |
| `src/studium/llm/tasks.py` | Task assets |
| `src/studium/llm/runner.py` | Structured generate + repair |
| `tests/llm/test_llm.py` | Repair, health, JSON extract |
| `pyproject.toml` | `llm` marker |

### Approved to Implement?

- [x] Yes (implemented 2026-08-10)

---

## 6. Implementation Notes

### Shipped

- `run_reasoning_task(provider, task, prompt_values)` with privacy `prompt_omitted` diagnostics
- No new required HTTP dependency (urllib); optional live tests via `-m llm`
- B09 intentionally did not finalize the default model (B10 sets `DEFAULT_REASONING_MODEL`)

### Out of scope

- Full reasoning task schemas/prompts (B10)
- Recommendation assembly (B11)

---
