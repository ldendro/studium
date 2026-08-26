.PHONY: install test lint format typecheck check build dev app e2e web-lint web-test

UV ?= uv
WEB := cd web &&

install:
	$(UV) sync --extra dev
	$(UV) run pre-commit install
	$(WEB) npm install
	$(WEB) npx playwright install chromium

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

typecheck:
	$(UV) run pyright

web-lint:
	$(WEB) npm run lint

web-test:
	$(WEB) npm run test

build:
	$(WEB) npm run build

check: lint typecheck test web-lint web-test build

dev:
	$(WEB) npm run dev

app: build
	$(UV) run studium serve --replace --frontend "$(CURDIR)/web/dist"

e2e: build
	$(WEB) npm run e2e
