## Branch Summary

**Phase:** 1 - Vault Storage Core  
**Branch:** 2 - Vault Access Layer
**Status:** `in_progress`

---

## 1. Goal

This branch exists to provide the foundation for vaulting structure and ensure a layer of access is necessary for searching the vault for its contents. It enables the capability of reading and listing markdown files within a test vault through an access layer that prevents access outside the vault root. I'd nickname this branch the file system branch, as it ensures capabilities similar to that of searching up files within a 'finder' or other related indexing systems. 

---

## 2. Branch Context

### Main System Area

This branch primarily affects:

-  Vault storage
- Vault access

### Branch Dependencies

This branch depends on: 
- None, wouldn't consider the first branch a necessary dependency. 

### Risks / Things to Watch

- Ensure access is verified through tests. 

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

### Absolute Vs Relative Path:

#### Absolute Path
- An absolute path is like giving someone a full address for the destination of a file. It starts at `/`, the root of the filesystem. No matter where you currently are in the terminal or program, this path points to the same file.
		- Ex: /Users/lukas/Documents/project/main.py

#### Relative Path
- A relative path depends on your current working directory. Suppose your current folder is `Users/lukas/Documents/project` and inside that folder you have:
```
		project/
			main.py
			data/
				input.csv
```
	- From inside `project`, the relative path to `input.csv` is`data/input.csv`.
- `.` means current directory 
	- Ex: `./main.py` means the file `main.py` in the folder I am currently in. 
- `..` means parent directory
	- Ex: In `/Users/lukas/Documents/project/data` then `../main.py` means go up one folder to `project`, then find `main.py`.

### Recursive listing vs Top-level listing
- Top-level listing means showing only the files and folders directly inside one directory while recursive listing means showing everything inside that directory, including all nested folders and their contents. 

### What is a symlink?
- Short for symbolic link, is a aspecial file that points to another file or folder. Basically a shortcut or reference. 
- EX: Suppose you have this real file: `Users/lukas/Documents/project/config/settings.json`
- You could create a symlink somewhere else called:
	`Users/lukas/Desktop/settings.json` that points directly to the real file. 
    
---

## 4. Cursor Implementation Planning Prompt

Use this prompt to ask Cursor for a detailed implementation plan **before any code is generated**.

Cursor should not implement yet. The goal of this step is to produce a clear plan that I can review, question, and approve.

```text
We are planning the implementation for the next single branch of Studium.

Do not implement code yet.

Studium is an AI-assisted learning system built around Markdown/Obsidian-compatible concept notes, concept graphs, scaffold generation, source-aware learning workflows, and agent-based review.

Phase: `1 - Vault Storage Core`

Branch: `2 - Vault Access Layer`

Branch goal:
Implement safe file access for a configured test vault. This branch should allow Studium to resolve vault-relative paths, read Markdown files, list Markdown files, and prevent unsafe access outside the vault root.  

Expected outcome after this branch:
System enables safe and restricted access to the vault and reads/list markdown files without error. 

Relevant documents to read before planning:
- 2 - Final Phase Roadmap.md
- 3 - Technical Plan.md
- 4 - Branch Plan.md
- P1-B2-vault-access-layer

Relevant context from those documents:
- Gives insight into the implementation for the first phase of studium and the second branch of that phase. The documents provide a detailed plan for the initial version of its implementation. 

Known constraints:
- Keep implementation scoped to this branch.
- Do not implement work from later branches unless it is absolutely necessary, and explain why before including it in the plan.
- Do not introduce broad architecture changes unless you explicitly explain why they are necessary.
- If you believe a schema, system model, technical plan, or architecture decision needs to change, call that out before implementation.
- Prefer robust, maintainable, efficient code.
- Use abstractions when they clearly improve correctness, extensibility, or readability.
- Avoid unnecessary abstraction, framework complexity, or premature generalization.
- Explain any non-obvious design choices, especially if they trade simplicity for robustness or extensibility.
- Preserve the intent of the existing roadmap, technical plan, and branch plan.
- Include tests or verification steps appropriate to this branch.
- Assume I will review and approve this plan before implementation.

Please produce a branch implementation plan with:

1. Summary of proposed approach
2. Documents reviewed and assumptions taken from them
3. Files likely to be created or modified
4. Step-by-step implementation sequence
5. Data model or schema changes, if any
6. Important functions/classes/modules likely needed
7. Tests or verification steps to add
8. Risks, edge cases, or assumptions
9. Any questions or decisions needed before implementation
10. Anything that appears to conflict with the roadmap, technical plan, or branch plan
```

---

## 5. Cursor Implementation Plan

### 1. Summary of proposed approach

Introduce a small, explicit vault access API under [`src/studium/vault/`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/vault/) built on `pathlib.Path`:

1. Path safety first — every operation resolves a vault-relative path and verifies the result stays inside the vault root before touching the filesystem.
2. Thin `Vault` object — holds a resolved vault root `Path` and exposes `resolve_path`, `read_markdown`, `list_markdown_files`, and `exists`. This is a light wrapper over the Technical Plan's free-function signatures, not a new architecture layer.
3. Custom exceptions — structured errors for traversal escapes, missing vault root, missing files, and non-`.md` read attempts.
4. Tests with `tmp_path` — integration-style tests in temporary directories; no committed fixture vault yet (that is B8).
### 2. Documents reviewed and assumptions

|Document|Key takeaways for B2|
|---|---|
|[2 - Final Phase Roadmap.md](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/Docs/01%20-%20Phase%20Roadmaps/Phase%201%20-%20Vault%20Storage%20Core/2%20-%20Final%20Phase%20Roadmap.md) §5.1|Test vault only; all file ops scoped to vault root; path traversal blocked; read `.md` files|
|[3 - Technical Plan.md](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/Docs/01%20-%20Phase%20Roadmaps/Phase%201%20-%20Vault%20Storage%20Core/3%20-%20Technical%20Plan.md) §Vault Access|`resolve_vault_path`, `read_markdown_file`, `list_markdown_files`; path traversal = critical error; writes deferred to proposal layer|
|[4 - Branch Plan.md](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/Docs/01%20-%20Phase%20Roadmaps/Phase%201%20-%20Vault%20Storage%20Core/4%20-%20Branch%20Plan.md) §B2|Read, list, existence, traversal protection; temp-dir tests; no parsing|
|[P1-B2-vault-access-layer.md](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/Docs/01%20-%20Phase%20Roadmaps/Phase%201%20-%20Vault%20Storage%20Core/Branches/P1-B2-vault-access-layer.md)|Same scope; verify access through tests|
|B1 foundation ([`pyproject.toml`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/pyproject.toml), [`src/studium/vault/__init__.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/vault/__init__.py))|Package exists; build inside placeholder `vault` subpackage|

Assumptions:

- Listing is recursive (`**/*.md`) because Obsidian vaults are nested; returns vault-relative paths (POSIX-style strings, e.g. `concepts/foo.md`).
- Reads are UTF-8 text only.
- `relative_path` must be relative — reject absolute paths before joining (critical on POSIX where `vault_root / Path("/etc/passwd")` ignores the vault root).
- No environment-variable / config-file vault root yet; callers pass `Path` explicitly. CLI wiring is B8.
- `write_markdown_file_from_proposal` is out of scope despite appearing in the Technical Plan's Vault Access interface list.

### 3. Files likely to be created or modified

New

- [`src/studium/vault/errors.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/vault/errors.py) — exception hierarchy
- [`src/studium/vault/paths.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/vault/paths.py) — `resolve_vault_path`, internal `_is_under_root` helper
- [`src/studium/vault/vault.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/vault/vault.py) — `Vault` class
- [`tests/vault/test_paths.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/tests/vault/test_paths.py) — path resolution + traversal blocking
- [`tests/vault/test_vault.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/tests/vault/test_vault.py) — read, list, exists integration tests

Modified

- [`src/studium/vault/__init__.py`](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/src/studium/vault/__init__.py) — export public API (`Vault`, `resolve_vault_path`, exceptions)

Not changed

- Other `studium.*` subpackages, `pyproject.toml` (no new runtime deps), `Docs/`

---

### 4. Step-by-step implementation sequence

1. Define exceptions in `errors.py`:
    
    - `VaultError` (base)
    - `VaultPathError` — resolved path escapes vault root or absolute `relative_path` rejected
    - `VaultNotFoundError` — vault root or target file does not exist
    - `VaultTypeError` — read attempted on non-`.md` path
2. Implement path resolution in `paths.py`:
    
    - `resolve_vault_path(vault_root: Path, relative_path: str | Path) -> Path`
    - Normalize `vault_root` with `.resolve()`
    - Reject absolute `relative_path`
    - Join, `.resolve()`, then verify with `resolved.is_relative_to(vault_root)` (Python 3.12)
    - Raise `VaultPathError` on escape; `VaultNotFoundError` if vault root missing
3. Implement `Vault` class in `vault.py`:
    
    - `__init__(self, root: Path)` — store resolved root; fail fast if root is not an existing directory
    - `resolve_path(relative_path) -> Path` — delegate to `resolve_vault_path`
    - `exists(relative_path) -> bool` — safe resolve + `Path.is_file()`
    - `read_markdown(relative_path) -> str` — require `.md` suffix, safe resolve, `read_text(encoding="utf-8")`; raise `VaultNotFoundError` if missing
    - `list_markdown_files() -> list[str]` — `root.rglob("*.md")`, keep only paths under root, return sorted vault-relative POSIX strings
4. Wire public exports in `vault/__init__.py`.
    
5. Add tests (section 7).
    
6. Run verification: `uv run ruff check .`, `uv run pyright`, `uv run pytest`.
    

---

### 5. Data model or schema changes

None. This branch operates on filesystem paths and raw Markdown strings only. Concept-note metadata schemas remain B3.

---

### 6. Important functions / classes / modules

|Symbol|Responsibility|
|---|---|
|`VaultError` hierarchy|Clear, catchable failure modes for traversal and I/O|
|`resolve_vault_path(vault_root, relative_path) -> Path`|Core safety primitive reused by B7 writes|
|`Vault`|Configured vault root + safe read/list/exists API|
|`Vault.read_markdown`|Return raw file content (parsing is B4's job)|
|`Vault.list_markdown_files`|Discover all `.md` files under vault|
|`Vault.exists`|Safe existence check without reading|

Non-obvious design choice: reject absolute `relative_path` _before_ joining. Joining an absolute path discards `vault_root` on POSIX and would bypass containment checks if applied naively after resolve.

---

### 7. Tests / verification steps

Unit tests — `test_paths.py`

- Valid relative paths resolve correctly (`notes/foo.md`, nested paths)
- Traversal blocked: `../outside.md`, `notes/../../outside.md`, `..`
- Absolute `relative_path` rejected
- Missing vault root raises `VaultNotFoundError`

Integration tests — `test_vault.py` (using `tmp_path` fixture)

- Create temp vault tree with nested `.md` and non-`.md` files
- `read_markdown` returns expected UTF-8 content
- `read_markdown` on missing file → `VaultNotFoundError`
- `read_markdown` on `.txt` → `VaultTypeError`
- `list_markdown_files` returns all nested `.md` paths, sorted, vault-relative; excludes `.txt`
- `exists` true/false behavior
- Empty vault → `list_markdown_files` returns `[]`

Automated checks (existing toolchain)

- Ruff, Pyright (strict), pytest with coverage

Manual smoke (optional, no CLI yet):

from pathlib import Path

from studium.vault import Vault

v = Vault(Path("path/to/tmp/vault"))

v.list_markdown_files()

v.read_markdown("some/note.md")

---

### 8. Risks, edge cases, or assumptions

|Risk|Mitigation|
|---|---|
|Symlinks pointing outside vault|Document as known limitation for B2; B7 may tighten before writes|
|`is_relative_to` only available 3.9+|Safe — project requires 3.12|
|Windows drive-letter paths|Use `pathlib` consistently; add Windows-specific tests only if needed later|
|Recursive listing on large vaults|Acceptable for Phase 1 test vaults; indexing deferred to Phase 2|
|Confusion with metadata `vault_status` field|Unrelated — filesystem vault root vs note lifecycle field|

---

### 9. Questions / decisions needed before implementation

All have sensible defaults; flag if you want different behavior:

1. Recursive listing (recommended: yes) vs top-level only?
2. Return relative path strings (recommended) vs absolute `Path` objects from `list_markdown_files`?
3. Validate vault root at `Vault()` construction (recommended: yes, must exist and be a directory)?
4. Symlinks: block reads through symlinks that escape root (stricter), or document-only for B2 (simpler)?

Default plan: recursive listing, relative strings, validate root at construction, document symlink risk without extra logic unless you want stricter behavior.

---

### 10. Conflicts with roadmap, technical plan, or branch plan

|Item|Resolution|
|---|---|
|Technical Plan lists `write_markdown_file_from_proposal` under Vault Access|Deferred to B7 — Branch Plan B2 explicitly limits scope to read/list/existence|
|Branch Plan B2 references "Write / Mutation Behavior"|Only the _safety constraint_ (no access outside root) applies now; actual mutation is B7|
|P1-B2 doc says B1 "not a necessary dependency"|Practically B1 is done; this branch builds on its package/tooling foundation|
|Roadmap mentions committed test vault fixtures|Deferred to B8 — B2 uses `tmp_path` only, matching Branch Plan's "temp-directory-based tests"|

No schema or architecture changes required.

---

## 6. Implementation Notes

- 3 files added to src/studium/vault:

|Module|Purpose|
|---|---|
|`errors.py`|`VaultError`, `VaultPathError`, `VaultNotFoundError`, `VaultTypeError`|
|`paths.py`|`resolve_vault_path()`, `is_path_under_root()` — rejects absolute paths, traversal, and symlinks that resolve outside the vault|
|`vault.py`|`Vault` class with `read_markdown()`, `list_markdown_files()`, `exists()`, `resolve_path()`|
|`__init__.py`|Public exports|

---

## 7. Code Understanding
### Main Implementation Flow

The vault acts as the storage system for the notes to be written to it, so it is necessary that we implement an access layer for accessing this system in a reliable and efficient way. Calling the Vault class will instantiate a vault as it pertains to a user specified path on their computer. The we incorporate various methods within this class to resolve a specified relative path as it pertains to a file within the vault, ensuring a path that points to a supposed file in the vault actually points to an existing file, return a existing file within the vault (has to be md), and list all existing md files under the vault root as specified vault-relative paths. 

### Key Files and Responsibilities

- `errors.py` — Specifies the class of error that occurs against the access layer. Includes
	- `VaultError` - base exception that every vault error type calls on 
	- `VaultPathError` - raised when a path escapes the vault root via symlink 
	- `VaultNotFoundError` - raised when the vault root or file a path was pointing to doesn't exist
	- `VaultTypeError` - raised when a path targets a file without the markdown endpoint (.md)
- `paths.py` — Resolves a specified path against the errors defined in `errors.py`
    - `resolve_vault_path` - Takes in the vault root and specified relative path and returns an absolute path if the vault exists and the relative path doesn't escape the vault root.
- `vault.py` — Instantiates a vault, where the vault class lives. Methods outside of verifying and creating the root include:
	- `root()` - returns the vault root
	- `resolve_path()` - calls on the functions in `paths.py` that resolves a path and its root
	- `exists()` - Returns a boolean on whether a specified path points to an existing file
	- `read_markdown()` - returns a markdown files a path specifies if it has the markdown suffix and the file exists at that absolute path. 
	- `list_markdown_files()` - lists all markdown files under the vault root as vault-relative paths. 
    

---

## 8. Tests and Verification

- Two tests added within ./tests:
	- `test_paths.py` - which consists of tests verifying the access layer 
	- `test_vault.py` - which tests the instantiated vault class and its corresponding methods

---
## 9. Final Branch Summary

Short final summary after the branch is complete:

```text
This branch added the vault object important in storing and searching for notes in the future. It added three files within the vault subfolder. The main implementation flow is instantiating a vault and either reading existing markdown files within the vault or `ls`ing the files within the vault. It was verified by test_paths.py and test_vault.py.
```