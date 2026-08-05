# Studium

Studium is an AI-assisted learning system built around Markdown/Obsidian-compatible
concept notes, concept graphs, scaffold generation, source-aware learning workflows,
and agent-based review.

This repository currently implements **Phase 1: Vault Storage Core** — a pure-Python
storage layer for reading, parsing, validating, serializing, and safely writing
Obsidian-compatible concept notes in a test vault.

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
- `studium.index.sync_and_embed(...)` — sync then embed with a provider
- `studium.index.embed_query(provider, text)` — ephemeral query vector

Lexical search and embedding generation are library-only in this phase (no CLI).
Vector search / hybrid fusion come in later branches.

Local embedding models (optional):

```bash
uv sync --extra embeddings
```

Use `FakeEmbeddingProvider` in tests; `SentenceTransformersEmbeddingProvider` for
real MiniLM-class models on a machine with the optional extra installed.

## Project structure

```
src/studium/
  vault/          # safe vault file access (P1-B2)
  schemas/        # Pydantic metadata models (P1-B3)
  parsing/        # Markdown + YAML frontmatter parsing (P1-B4)
  serialization/  # concept note generation/serialization (P1-B5)
  validation/     # critical-error / warning validation (P1-B6)
  writes/         # safe write proposals + vault writes (P1-B7)
  cli/            # minimal CLI (P1-B8)
  index/          # SQLite index, sync, lexical search, embeddings (P2-B02–B05)
tests/            # pytest test suite
```

Phase planning and design documents live under `Docs/`.
