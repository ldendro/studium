# Studium

Studium is a **local-first learning workspace**. It keeps an Obsidian-compatible
Markdown vault as the durable knowledge source, then layers a typed local service
and a React application for search, creation, source grounding, review,
retention, mastery, and a personal learning model.

This repository now implements the complete product through Phase 11:

- **Markdown vault + safe writes** — every durable note mutation is a visible
  `WriteProposal` that re-syncs the derived concept index
- **Local application** — FastAPI service, versioned SQLite app database, and a
  production React/Vite client served by `studium serve`
- **Learning loops** — Search/graph, Create, Sources, Agent Review, Backlog,
  Retention, Mastery, and Profile (`soul.md`)
- **Local productization** — onboarding, privacy/provider controls, export,
  backup/restore-to-copy, job recovery, content-safe logs, and data deletion

There is no fake auth, cloud, or sync layer. Secrets never enter the database;
API keys stay in environment variables named from Settings.

## Requirements

- [uv](https://docs.astral.sh/uv/) for environment and dependency management
- Python 3.12 (uv can install it automatically)
- Node.js 22+ for the React client

## Setup

```bash
make install
```

Equivalent steps:

```bash
uv sync --extra dev
uv run pre-commit install
cd web && npm install && npx playwright install chromium
```

If Python 3.12 is not yet available locally:

```bash
uv python install 3.12
```

## Run the application

Build the client and serve the local product (API + production frontend):

```bash
make app
```

This runs `studium serve --frontend web/dist` at http://127.0.0.1:8765. On first
launch the onboarding screen can open an existing vault, create a new one, or
import a ZIP. Checking **Seed the guided demonstration workspace** creates a
coherent vault that exercises alias search, graph context, sources, review,
backlog, retention, mastery, and profile.

Development UI with Vite (proxies `/api` to the local service):

```bash
uv run studium serve --no-open-browser
cd web && npm run dev
```

Useful CLI flags:

```bash
uv run studium serve --vault /path/to/vault --app-data /path/to/app-data
uv run studium serve --no-open-browser --frontend web/dist
uv run studium seed-demo --vault /tmp/studium-demo --app-data /tmp/studium-demo-data
```

If `--vault` is omitted, Studium reopens the last vault remembered in
application data.

## Verification

```bash
make check          # Ruff, Pyright, pytest, OXLint, Vitest, production build
make e2e            # Playwright + axe-core at desktop and mobile sizes
make test           # Python tests only
make lint
make typecheck
```

Frontend-only:

```bash
cd web && npm run lint && npm run test && npm run build
cd web && npm run e2e
```

## CLI (vault, index, and graph)

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

Default create path is `concepts/<hyphen-slug>.md`. Exit code `1` means critical
validation or write errors; warnings alone still exit `0`.

## Derived concept index (Phase 2)

Valid concept notes are projected into a rebuildable SQLite index **outside** the
Obsidian vault:

```text
<Studium application data>/indexes/<vault_identifier>/concept-index.sqlite
```

Application data defaults to the OS user data directory for `studium`
(`platformdirs`). Tests and tooling can override the root. The index schema is
versioned independently from concept-note `schema_version`; incompatible indexes
must be rebuilt rather than migrated. The application database (jobs, sources,
review, learning history, settings) is migrated separately.

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
uv run python evals/phase2/seed_vault.py /tmp/studium-phase2-eval-vault
uv run studium graph sync --vault /tmp/studium-phase2-eval-vault
uv run studium graph evaluate-retrieval --vault /tmp/studium-phase2-eval-vault
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
  vault/          # safe vault file access
  schemas/        # Pydantic metadata models
  parsing/        # Markdown + YAML frontmatter parsing
  serialization/  # concept note generation/serialization
  validation/     # critical-error / warning validation
  writes/         # safe write proposals + vault writes
  cli/            # vault, graph, serve, and seed-demo CLI
  index/          # SQLite index, sync, search, embeddings, graph
  llm/            # provider-agnostic structured LLM + reasoning tasks
  recommend/      # ConceptRecommendation assembly
  evaluate/       # evaluation harness
  app/            # workspace, jobs, providers, productization, learning
  api/            # FastAPI local service
  sources/        # source library, adapters, retrieval
  create/         # recommendation-led create workflow
  review/         # agent review inside Create
evals/phase2/     # curated Phase 2 evaluation cases
web/              # React/Vite application
tests/            # pytest test suite
```

Phase planning and design documents live under `Docs/`.
