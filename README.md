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
tests/            # pytest test suite
```

Phase planning and design documents live under `Docs/`.
