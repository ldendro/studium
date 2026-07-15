## Branch Summary

**Phase:** 1 - Vault Storage Core
**Branch:** 8 - CLI and phase verification
**Status:** `in_progress`

---

## 1. Goal

Add CLI commands to interact with completed workflows for phase 1, including using these commands and an example fixture. These commands will consist of creating a concept note, validating a note, and validate the vault directory. These commands will be used on test fixtures for verifying the command and its underlying functionality implemented in prior branches works as intended. Not intended to add advanced CLI workflows just yet as we are still missing core functionality from phase 2. 

---
## 2. Branch Context

### Main System Area

This branch primarily affects:

- Test vault fixtures
- Minimal CLI 
- Create and validation workflows

### Branch Dependencies

Culmination of phase 1, considered the gateway to phase 2.  

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

### argparse (stdlib)
- A built-in Python standard library module used to parse command-line arguments. It allows scripts to easily accept user inputs, flags, and options directly from the terminal.   
- Example:
```Python
import argparse 
# 1. Create the parser 
parser = argparse.ArgumentParser(description="A simple greeting script.") 
# 2. Define arguments
parser.add_argument("name", type=str, help="The name of the user to greet.") parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.") 
# 3. Parse the arguments 
args = parser.parse_args() 
# 4. Use the arguments 
if args.verbose: 
	print(f"Hello there, {args.name}! Welcome to the script.") 
else: 
	print(f"Hello, {args.name}!")
```
If the script above is saved as `greet.py`, you can run it in your terminal with the following results:
- **Basic usage:** `python greet.py Alice`  
    Output: `Hello, Alice!`
- **Using a flag:** `python greet.py Alice -v`  
    Output: `Hello there, Alice! Welcome to the script.`
- **Auto-generated help:** `python greet.py --help`  
    Output: Displays a clean menu showing the required `name` argument and the optional `-v` flag. 

---

## 4. Cursor Implementation Planning Prompt

Use this prompt to ask Cursor for a detailed implementation plan **before any code is generated**.

Cursor should not implement yet. The goal of this step is to produce a clear plan that I can review, question, and approve.

```text
We are planning the implementation for a single branch of Studium.

Do not implement code yet.

Project context:
Studium is an AI-assisted learning system built around Markdown/Obsidian-compatible notes, concept graphs, scaffold generation, source-aware RAG, local/source library processing, and agent-based note review.

Phase: 1 - Vault Storage Core

Branch: 8 - CLI and Phase Verification

Branch goal:
Add CLI commands to interact with completed workflows for phase 1, including using these commands and an example fixture. These commands will consist of creating a concept note, validating a note, and validate the vault directory. These commands will be used on test fixtures for verifying the command and its underlying functionality implemented in prior branches works as intended. Not intended to add advanced CLI workflows just yet as we are still missing core functionality from phase 2. 

Expected outcome:
At least 3 CLI commands (potentially more after agent feedback) that work in validating the create and validation layers implemented in prior branches, with test fixtures enabling such validatio. 

Relevant context:
4 - Branch Plan, 3 - Technical Plan, and 2 - Final Phase Roadmap. 

Known constraints:
- Keep implementation scoped to this branch.
- Do not introduce broad architecture changes unless you explicitly explain why they are necessary.
- If you believe a schema, system model, or architecture decision needs to change, call that out before implementation.
- Prefer clear, maintainable code over clever abstractions.
- Favor code I can understand and explain.
- Include tests or verification steps where appropriate.
- Assume I will review and approve this plan before implementation.

Please produce a branch implementation plan with:

1. Summary of your proposed approach
2. Files likely to be created or modified
3. Step-by-step implementation sequence
4. Data model or schema changes, if any
5. Important functions/classes/modules likely needed
6. Tests or verification steps to add
7. Risks, edge cases, or assumptions
8. Questions or decisions needed before implementation
```

---

## 5. Cursor Implementation Plan

### 1. Summary of proposed approach

Add a **thin CLI** in `src/studium/cli/` that wires existing B2–B7 APIs into three commands. B8 should not reimplement create, parse, validate, or write logic — it should compose them and print readable results.

**Commands**

| Command | Behavior |
|---------|----------|
| `studium create-concept "<title>"` | Resolve vault + default path → build create proposal via B7 → commit if safe → print path / warnings / errors |
| `studium validate-note <path>` | Read one Markdown file (vault-relative or absolute under vault) → `parse_and_validate(..., PARSE)` → print criticals/warnings → exit non-zero on criticals |
| `studium validate-vault <path>` | Open vault at directory → `list_markdown_files()` → validate each with PARSE → summary + per-file issues → exit non-zero if any criticals |

**Also in B8 (phase verification, not just CLI glue)**

1. **`default_concept_path(title)`** — deferred from B7; e.g. `concepts/{slug}.md` for create-concept.
2. **Committed `tests/fixtures/test_vault/`** — representative valid/invalid notes for vault-wide validation and E2E proofs.
3. **CLI integration + end-to-end tests** that satisfy the Phase 1 technical completion standard (Technical Plan §15).

**Design principles**

- CLI stays thin: argparse (stdlib) entrypoint → small command handlers → existing `Vault` / `writes` / `validation` APIs.
- No update CLI (explicitly out of scope for Phase 1).
- No approval UI; create-concept commits when the proposal has no critical errors (proposal remains inspectable in process / tests).
- Write tests must not mutate committed fixtures — use `tmp_path` copies or separate temp vaults for create/commit flows.

---

### 2. Files likely to be created or modified

| Path | Action | Role |
|------|--------|------|
| `src/studium/cli/__init__.py` | **Modify** | Export `main` / public CLI entry |
| `src/studium/cli/main.py` | **Create** | `argparse` root parser + `main(argv) -> int` |
| `src/studium/cli/create_concept.py` | **Create** | `create-concept` command handler |
| `src/studium/cli/validate_note.py` | **Create** | `validate-note` command handler |
| `src/studium/cli/validate_vault.py` | **Create** | `validate-vault` command handler |
| `src/studium/cli/formatting.py` | **Create** | Shared human-readable issue / proposal printers |
| `src/studium/cli/paths.py` | **Create** | `default_concept_path(title)`, vault-relative path helpers |
| `pyproject.toml` | **Modify** | `[project.scripts] studium = "studium.cli.main:main"` (or equivalent) |
| `README.md` | **Modify** | Document CLI usage |
| `tests/fixtures/test_vault/` | **Create** | Committed fixture vault notes |
| `tests/cli/test_create_concept.py` | **Create** | CLI create integration |
| `tests/cli/test_validate_note.py` | **Create** | CLI validate-note |
| `tests/cli/test_validate_vault.py` | **Create** | CLI validate-vault |
| `tests/cli/test_e2e_phase1.py` | **Create** | create → commit → parse → validate; fixture vault sweep |
| `tests/cli/conftest.py` | **Create** | CLI runner helpers (`main([...])`, temp vault seeding) |

Optional small shared helper (if preferred over CLI-only):

| Path | Action | Role |
|------|--------|------|
| `src/studium/writes/paths.py` or keep in `cli/paths.py` | **Create** | `default_concept_path` — recommend **CLI package first**; promote later if reused |

**No changes expected:** schemas, validation rules, vault write semantics, proposal builders (beyond calling them).

---

### 3. Step-by-step implementation sequence

#### Step 1 — Path helpers

- Implement `default_concept_path(canonical_title: str) -> str`.
  - **Recommendation:** `concepts/{slugify_title(title).replace("_", "-")}.md` to match roadmap examples (`stochastic-gradient-descent.md`), **or** keep underscores for consistency with concept IDs — decide in §8.
- Helper: resolve CLI path args against `--vault` root (reject escapes via existing `Vault.resolve_path`).

#### Step 2 — Output formatting

- `format_validation_issue(issue) -> str` — severity, optional code/field, message.
- `format_validation_result(path, result) -> str` — header + criticals + warnings.
- `format_create_result(proposal, committed: bool) -> str` — target path, warnings, criticals, commit status.
- Keep output plain text, stable enough for tests to assert substrings (not a full TTY UI).

#### Step 3 — `create-concept`

```text
studium create-concept "Title" --vault <dir> [--path <vault-relative.md>] [--dry-run]
```

Flow:

1. `Vault(Path(vault))`
2. `target_path = --path or default_concept_path(title)`
3. `proposal = build_create_note_proposal_from_title(vault, target_path, title)`
4. **Always print** the proposal (target path, would_* flags, warnings, criticals; preview of after_content as needed)
5. If critical errors → exit `1` (do not write)
6. If `--dry-run` → exit `0` after printing (no commit) when there are no criticals; exit `1` if criticals
7. Else `commit_write_proposal(vault, proposal)` → print commit success, exit `0`
8. Catch `CollisionError` / `WriteProposalBlockedError` / `VaultError` → readable message, exit `1`

#### Step 4 — `validate-note`

```text
studium validate-note <path> --vault <dir>
```

Flow:

1. Open vault; resolve `path` as vault-relative (preferred) or allow absolute only if under vault root.
2. `raw = vault.read_markdown(path)`
3. `_, result = parse_and_validate(raw, ValidationOperation.PARSE)`
4. Print formatted result; exit `0` if `result.is_valid` else `1`

#### Step 5 — `validate-vault`

```text
studium validate-vault <vault-dir>
```

(`--vault` may be omitted if positional path *is* the vault root.)

Flow:

1. `Vault(Path(vault_dir))`
2. For each path from `list_markdown_files()`:
   - read → `parse_and_validate(..., PARSE)`
   - collect failures / warning counts
3. Print per-file summaries + final tally (`N files, C critical, W warnings`)
4. Exit `1` if any file has critical errors

#### Step 6 — Entrypoint wiring

- `main(argv: list[str] | None = None) -> int` with subparsers for the three commands.
- Register console script in `pyproject.toml`:

```toml
[project.scripts]
studium = "studium.cli.main:main"
```

- Ensure `main` is callable both as console script and `python -m studium.cli` (optional `__main__.py`).

#### Step 7 — Fixture vault

Create `tests/fixtures/test_vault/` with a small, intentional set (reuse/adapt existing parsing fixtures where possible):

| Fixture | Purpose |
|---------|---------|
| `concepts/valid_concept_note.md` | Happy-path PARSE valid |
| `concepts/studium_origin_concept.md` | Default Studium encounter |
| `concepts/external_source_concept.md` | External source encounter, no content attach |
| `concepts/concept_with_scaffold_modules.md` | Scaffold module metadata |
| `concepts/concept_with_missing_relationship_target.md` | Relationship `vault_status: missing` |
| `concepts/missing_canonical_section.md` | PARSE warning (valid with warnings) |
| `concepts/unknown_metadata_field.md` | PARSE warning |
| `concepts/invalid_yaml_note.md` | Critical parse failure |

Keep invalid notes **inside** the fixture vault so `validate-vault` exercises mixed outcomes. Do not put write-mutation targets only in committed fixtures — copy to `tmp_path` for create tests.

#### Step 8 — Tests + README

- CLI tests invoke `main([...])` directly (no subprocess required; optional one smoke subprocess).
- E2E: create in temp vault → read → parse_and_validate → assert valid.
- E2E: `validate-vault` over committed fixture vault (read-only).
- Update README with CLI examples.
- Run `uv run ruff check .`, `uv run pyright`, `uv run pytest`.

---

### 4. Data model or schema changes

| Topic | Recommendation |
|-------|----------------|
| Pydantic schemas | **No change** |
| `WriteProposal` / validation models | **No change** |
| New models | **None** — CLI is orchestration + formatting |
| `pyproject.toml` scripts | **Yes** — add `studium` entry point |
| Dependencies | **Prefer stdlib `argparse`** — avoid Click/Typer unless you want richer UX now |

No architecture change required. Optional: add `python -m studium.cli` via `__main__.py` for `uv run` without relying solely on the installed script.

---

### 5. Important functions / classes / modules

| Symbol | Role |
|--------|------|
| `main(argv) -> int` | CLI entry; parse args, dispatch, return exit code |
| `cmd_create_concept(args) -> int` | Create + commit flow |
| `cmd_validate_note(args) -> int` | Single-note validation |
| `cmd_validate_vault(args) -> int` | Vault-wide validation |
| `default_concept_path(title) -> str` | `concepts/...md` convention (B7 deferral) |
| `format_validation_result(...)` | Readable critical/warning output |
| `format_create_result(...)` | Create success/failure messaging |

**Existing APIs used (no duplication):**

| API | Used by |
|-----|---------|
| `Vault`, `resolve_path`, `read_markdown`, `list_markdown_files`, `exists` | All commands |
| `build_create_note_proposal_from_title`, `commit_write_proposal` | `create-concept` |
| `parse_and_validate`, `ValidationOperation.PARSE` | validate commands |
| `slugify_title` | `default_concept_path` |

**Explicitly out of scope**

| Item | Why |
|------|-----|
| Update / delete CLI | Phase 1 Branch Plan: no update CLI |
| Metadata flags on create (`--domain`, etc.) | Decision in §8; default title-only |
| Approval / dry-run UI | Write proposals stay storage primitives |
| Real Obsidian vault config | Test vault / `--vault` path only |
| Graph / search / agent commands | Later phases |

---

### 6. Tests / verification steps

#### Unit / focused

- `default_concept_path("Stochastic Gradient Descent")` matches chosen convention.
- Formatters include severity + message for critical and warning issues.

#### `test_create_concept.py`

- Creates note under temp vault at expected path.
- File content parses and validates (PARSE or CREATE as appropriate).
- Collision: second create to same path exits `1`, no overwrite.
- Empty title / validation criticals: exit `1`, no file written.
- Warnings-only (e.g. empty domains): still commits, exit `0`, warnings printed.

#### `test_validate_note.py`

- Valid fixture → exit `0`, no criticals in output.
- Invalid YAML fixture → exit `1`, criticals printed.
- Missing section fixture → exit `0` under PARSE (warnings only) — assert warning text present.
- Path outside vault → exit `1` with vault path error.

#### `test_validate_vault.py`

- Fixture vault: exit `1` if any invalid notes present (expected if invalid fixtures included).
- Temp vault with only valid notes → exit `0`.
- Empty vault → exit `0` (0 files).
- Summary line includes file counts.

#### `test_e2e_phase1.py`

- create-concept → validate-note on written path → success.
- Library-level: create proposal → commit → read → parse → validate (covers Phase 1 completion without depending on stdout formatting).
- Optional: validate-vault against fixture vault asserts known invalid files are reported.

#### Manual verification

```bash
uv sync --extra dev
uv run studium create-concept "Stochastic Gradient Descent" --vault /tmp/studium-test-vault
uv run studium validate-note concepts/stochastic-gradient-descent.md --vault /tmp/studium-test-vault
uv run studium validate-vault tests/fixtures/test_vault
```

#### Verification commands

```bash
uv run ruff check .
uv run pyright
uv run pytest tests/cli -q
uv run pytest
```

---

### 7. Risks, edge cases, and assumptions

| Risk | Mitigation |
|------|------------|
| CLI grows business logic | Keep handlers &lt; ~40 lines; all mutation via B7 |
| Mutating committed fixtures | Create/write tests use `tmp_path` only |
| Slug path vs ID slug mismatch (`-` vs `_`) | Explicit §8 decision; document in README |
| `validate-vault` noisy on mixed fixtures | Structured summary + per-file sections; exit code based on criticals only |
| Absolute vs relative path confusion | Prefer vault-relative for note paths; `--vault` always required for create/validate-note |
| Console script not installed in editable env | Document `uv run studium ...`; tests call `main()` directly |
| Duplicate fixture content vs `tests/fixtures/parsing/` | Prefer copying/adapting known-good fixtures; avoid drift by noting source in comments or shared loaders |

**Assumptions**

- B2–B7 are merged and stable.
- Create always prints the proposal; commits when safe unless `--dry-run`.
- `validate-*` uses **PARSE** strictness (hand-authored / fixture notes), not CREATE/WRITE.
- Vault root is always an explicit filesystem path for Phase 1 (no config file / env yet).
- Concepts section for CLI concepts (stale/collision/hash) in the branch doc front-matter is leftover from B7; B8 concepts are CLI entrypoints, fixture vaults, and exit-code semantics — consider updating §3 when implementing.

---

### 8. Resolved decisions (approved for implementation)

| # | Decision | Resolution |
|---|----------|------------|
| 1 | CLI framework | **stdlib `argparse`** — no Click/Typer. |
| 2 | Vault path | **Required** — `--vault` for create/validate-note; positional vault dir for `validate-vault`. No env/config in Phase 1. |
| 3 | Default path slug | **Hyphens** — `concepts/{slug-with-hyphens}.md` (e.g. `concepts/stochastic-gradient-descent.md`). Concept IDs keep underscores. |
| 4 | Create metadata flags | **Title only** — no `--concept-type` / `--domain` flags in Phase 1. |
| 5 | Proposal visibility on create | **Print proposal before commit**; support `--dry-run` to print the proposal and exit without writing. |
| 6 | `validate-vault` / `validate-note` exit code | **Fail on criticals only** — warnings are printed but do not change exit code. |
| 7 | Fixture vault layout | **`tests/fixtures/test_vault/concepts/`** subdirectory. |
| 8 | Invalid fixtures in vault | **Yes** — include invalid notes; full fixture vault `validate-vault` is expected to exit `1`. |
| 9 | Extra commands | **No** — only `create-concept`, `validate-note`, `validate-vault`. |

**Status:** Plan approved. Ready for implementation.

---

## Summary of Implementation
### CLI (`src/studium/cli/`)

|Command|Behavior|
|---|---|
|`studium create-concept "<title>" --vault <dir> [--path ...] [--dry-run]`|Builds proposal, always prints it, commits unless `--dry-run` or criticals|
|`studium validate-note <path> --vault <dir>`|PARSE validation; exit `1` on criticals|
|`studium validate-vault <vault-dir>`|Validates all `.md` files; summary + exit `1` if any criticals|

Also added:

- `default_concept_path` → `concepts/{hyphen-slug}.md`
- Console script in `pyproject.toml`
- README CLI section
- `python -m studium.cli` via `__main__.py`

### Fixtures

`tests/fixtures/test_vault/concepts/` with 8 notes (valid, studium origin, external source, scaffold modules, missing relationship, missing section, unknown field, invalid YAML). Full vault `validate-vault` exits `1` as expected (1 critical).