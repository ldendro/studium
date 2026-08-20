# Studium

Studium is an AI-assisted learning system built around Markdown/Obsidian-compatible
concept notes, concept graphs, scaffold generation, source-aware learning workflows,
and agent-based review.

This repository implements **Phase 1: Vault Storage Core** and **Phase 2: Concept
Graph Core** — durable Markdown notes plus a derived SQLite concept index, hybrid
retrieval, graph/encounter queries, local LLM reasoning, recommendations, evaluation,
and a `studium graph` CLI.

## Requirements

- [uv](https://docs.astral.sh/uv/) for environment and dependency management
- Python 3.12 (uv can install it automatically)

## Setup

```bash
uv sync --extra dev      # create the virtualenv and install dependencies
uv run pre-commit install  # enable git pre-commit hooks
```

If Python 3.12 is not yet available locally:

```bash
uv python install 3.12
```

## Common commands

```bash
uv run pytest            # run tests (with coverage)
uv run ruff check .      # lint
uv run ruff format .     # format
uv run pyright           # type check
uv run pre-commit run --all-files  # run all pre-commit hooks
```

A `Makefile` provides shortcuts: `make install`, `make test`, `make lint`,
`make typecheck`, `make check`.

## CLI (Phase 1)

After `uv sync --extra dev`, use the `studium` console script:

```bash
# Create a concept note (prints write proposal, then commits unless --dry-run)
uv run studium create-concept "Stochastic Gradient Descent" --vault /tmp/studium-test-vault

# Preview a create without writing
uv run studium create-concept "Stochastic Gradient Descent" --vault /tmp/studium-test-vault --dry-run

# Validate one note (vault-relative path)
uv run studium validate-note concepts/stochastic-gradient-descent.md --vault /tmp/studium-test-vault

# Validate an entire vault directory
uv run studium validate-vault tests/fixtures/test_vault
```

Default create path is `concepts/<hyphen-slug>.md`. Exit code `1` means critical validation or write errors; warnings alone still exit `0`.

## Derived concept index (Phase 2)

Valid concept notes are projected into a rebuildable SQLite index **outside** the
Obsidian vault:

```text
<Studium application data>/indexes/<vault_identifier>/concept-index.sqlite
```

Application data defaults to the OS user data directory for `studium`
(`platformdirs`). Tests and tooling can override the root. The index schema is
versioned independently from concept-note `schema_version`; incompatible indexes
must be rebuilt rather than migrated.

Library entrypoints:

- `studium.index.sync_vault(vault, engine, config)` — incremental vault → index sync
- `studium.index.rebuild_vault_index(vault, config, existing_engine=...)` — dispose,
  recreate empty schema, full sync
- `studium.index.resolve_concept_identity(engine, query)` — deterministic ID / title /
  alias lookup (no FTS)
- `studium.index.search_concepts_fts` / `search_modules_fts` — weighted BM25 over FTS5
- `studium.index.search_concepts_lexical(engine, query)` — lookup first, then FTS
- `studium.index.process_embedding_work(engine, work, provider)` — batch-embed sync work
- `studium.index.enumerate_embedding_work(engine)` — rebuild work from current projections
- `studium.index.sync_and_embed(...)` — sync then embed (defaults to current projections)
- `studium.index.embed_query(provider, text)` — ephemeral query vector
- `studium.index.search_concept_identity_vectors` / `search_concept_semantic_vectors` /
  `search_module_semantic_vectors` — cosine top-K over persisted embeddings
- `studium.index.create_vector_backend(engine, name=...)` — `"numpy"` (default) or
  `"sqlite_vec"`
- `studium.index.search_concepts(engine, query)` — Tier 0 identity + Tier 1 hybrid RRF
- `studium.index.graph.*` — one-hop relationships and encounter comparison
- `studium.llm.run_reasoning_task` / `reason_identity` — structured local reasoning
- `studium.recommend.recommend(...)` — action-specific recommendations (no note mutation)
- `studium.evaluate.*` — retrieval/recommendation harness over `evals/phase2/cases`

## Graph CLI (Phase 2)

```bash
uv run studium graph sync --vault /path/to/vault --json
uv run studium graph status --vault /path/to/vault
uv run studium graph find "stochastic gradient" --vault /path/to/vault --json
uv run studium graph propose "SGD" --vault /path/to/vault --json
uv run studium graph evaluate-retrieval --vault /path/to/vault
```

Also: `rebuild`, `candidates`, `inspect`, `modules`, `relationships`,
`evaluate-recommendations`. Flags: `--json`, `--diagnostics`, `--app-data`.

Local embedding models (optional):

```bash
uv sync --extra embeddings
```

Optional sqlite-vec backend (benchmark / opt-in tests):

```bash
uv sync --extra vector-ext
uv run pytest -m vector_ext
```

Use `FakeEmbeddingProvider` in tests; `SentenceTransformersEmbeddingProvider` for
real MiniLM-class models on a machine with the optional extra installed. Real-model
and live-LLM tests are excluded by default:

```bash
uv run pytest -m embedding
uv run pytest -m llm
```

See `Docs/01 - Phase Roadmaps/Phase 2 - Concept Graph Core/5 - Phase Completion Note.md`
for selected models/backends and known limits.

## Project structure

```
src/studium/
  vault/          # safe vault file access (P1-B2)
  schemas/        # Pydantic metadata models (P1-B3)
  parsing/        # Markdown + YAML frontmatter parsing (P1-B4)
  serialization/  # concept note generation/serialization (P1-B5)
  validation/     # critical-error / warning validation (P1-B6)
  writes/         # safe write proposals + vault writes (P1-B7)
  cli/            # Phase 1 + graph CLI (P1-B8, P2-B13)
  index/          # SQLite index, sync, search, embeddings, graph (P2)
  llm/            # provider-agnostic structured LLM + reasoning tasks
  recommend/      # ConceptRecommendation assembly
  evaluate/       # evaluation harness
evals/phase2/     # curated Phase 2 evaluation cases
tests/            # pytest test suite
```

Phase planning and design documents live under `Docs/`.
