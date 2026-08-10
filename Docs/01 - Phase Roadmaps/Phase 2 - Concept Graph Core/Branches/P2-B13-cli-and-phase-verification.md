## 1. Goal

Expose the complete Phase 2 concept-intelligence layer through a thin `studium graph` CLI (human / `--json` / `--diagnostics`), verify end-to-end sync→search→propose flows, update README, and record phase completion.

---

## 2. Branch Context

### Main System Area

- Graph/index/search/recommendation CLI
- Operator diagnostics and configuration visibility
- Phase completion documentation

### Branch Dependencies

- All prior Phase 2 branches (B01–B12)

### Risks / Things to Watch

- CLI must remain thin wrappers over library services
- No business logic in argparse handlers
- Recommendation approval/mutation remains Phase 4

---

## 3. Concepts I Need to Understand

- `[[Thin CLI over application services]]`
- `[[Human vs JSON vs diagnostics output modes]]`
- `[[Phase Technical Completion Standard]]`

Questions I should be able to answer:

- Which graph subcommands ship in Phase 2?
- Where is the selected embedding/vector/LLM configuration documented?
- What is still deferred to Phase 3/4?

---

## 4. Cursor Implementation Planning Prompt

_(See Branch Plan B13 and Technical Plan §9.1 / §15.)_

---

## 5. Cursor Implementation Plan

### Summary of approach

1. Add `studium graph` subcommands in `cli/main.py` + handlers in `cli/graph.py`
2. Commands: sync, rebuild, status, find, candidates, inspect, modules, relationships, propose, evaluate-retrieval, evaluate-recommendations
3. Integration tests for sync/status/find/propose
4. README + `5 - Phase Completion Note.md`

### Files created / modified

| Path | Role |
|------|------|
| `src/studium/cli/graph.py` | Thin command handlers |
| `src/studium/cli/main.py` | `graph` argparse group |
| `tests/cli/test_graph_cli.py` | End-to-end CLI smoke |
| `README.md` | Graph CLI + package map |
| `Docs/.../5 - Phase Completion Note.md` | Phase summary |

### Approved to Implement?

- [x] Yes (implemented 2026-08-10)

---

## 6. Implementation Notes

### Shipped commands

```text
studium graph sync|rebuild|status|find|candidates|inspect|modules|relationships|propose
studium graph evaluate-retrieval|evaluate-recommendations
```

Common flags: `--vault`, `--app-data`, `--json`, `--diagnostics`.

### Verification

- Default suite: **304 passed** (embedding / vector_ext / llm markers deselected)
- Phase completion note records selected defaults: NumPy vector backend, MiniLM embedding id, `llama3.2:3b` reasoning model, RRF weights

### Explicitly deferred

- Phase 3 Search UI / graph visualization
- Phase 4 recommendation approval and note mutation
- Large live-model threshold confirmation on a real vault

---
