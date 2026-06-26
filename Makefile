.PHONY: install test lint format typecheck check

install:
	uv sync --extra dev
	uv run pre-commit install

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run pyright

check: lint typecheck test
