## Branch Summary

**Phase:** 1 - Vault Storage Core
**Branch:** 7 - Write Proposals and Vault Writes
**Status:** `in_progress`

---

## 1. Goal

Implement structured safe write proposals and committed file writes to the test vault. This will enable file mutation and creation as inspectable and validated using the existing validation layer. The implementation focus for this branch consists of building create-note and update-note write proposals, include before/after content within the proposal specifically for the update-note write proposal, include warnings and critical errors in the proposal, detect create collisions that would corrupt the test vault, and commit write proposals that aren't blocked because of critical errors and stale update commits. 

---
## 2. Branch Context

### Main System Area

This branch primarily affects:

-  Safe Write Proposal Layer
- Write / Mutation Behavior
- Vault Access Layer
- Validation and Error Handling

### Branch Dependencies

B6 is necessary for validating Studium operations necessary for these write proposals. 

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

- **Stale File Detection** detects instances where the file that is being updated doesn't exist or has been changed in its perceived location. In **Studium**, stale file detection should ensure that concept notes being updated actually exist within the test vault and that there hasn't been any changes to the file without update proposals before hand, or else they are blocked from being committed to the vault. 
- **Collision Detection** detects instances where a file created already exists in the perceived location. In **Studium**, collision detection should ensure that concept notes created don't already exist in the test vault, or else committing the write proposal will fail becasuse it already exists.
- **SHA-256 Full Hex** is a unique 64-character "fingerprint" used to verify that a file hasn't been altered or corrupted. Even the smallest change to a file produces a completely different result. 


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

Branch: 7 - Write Proposals and Vault Writes

Branch goal:
Implement structured safe write proposals and committed file writes to the test vault. This will enable file mutation and creation as inspectable and validated using the existing validation layer. The implementation focus for this branch consists of building create-note and update-note write proposals, include before/after content within the proposal specifically for the update-note write proposal, include warnings and critical errors in the proposal, detect create collisions that would corrupt the test vault, and commit write proposals that aren't blocked because of critical errors and stale update commits.  

Expected outcome:
Write proposals can be created and committed when safe to the test vault. Create operations do not overwrite existing files and update operations detect stale file changes. Its impoortant that writes remain scoped to the test vault for this phase. 

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

Build a thin **writes layer** in `src/studium/writes/` that sits on top of the existing **Vault** (B2), **validation** (B6), and **serialization** (B5) APIs. B7 does not add new Pydantic schemas; it orchestrates what already exists.

**Core idea:** every file mutation goes through a `WriteProposal` object first. Builders populate the proposal (content, validation issues, safety flags, and hash); `commit_write_proposal` performs the actual write only when the proposal is safe at commit time.

**Create path**

1. Resolve `target_path` through `Vault` (path-escape protection).
2. Detect whether the target already exists → collision critical error if so.
3. Validate `after_content` with `ValidationOperation.CREATE` via `parse_and_validate`.
4. Return a `WriteProposal` with `operation=CREATE_NOTE`, `before_content=None`, and populated `would_*` flags.

**Update path**

1. Read existing file via `vault.read_markdown` (missing file → critical error on the proposal).
2. Capture `before_content` and compute `expected_existing_hash`.
3. Validate `after_content` with `ValidationOperation.UPDATE`.
4. Return a `WriteProposal` with before/after content and `would_update=True`.

**Commit path**

1. Reject if `proposal.critical_errors` is non-empty.
2. Re-check collision (create) or hash match (update) against live vault state — do not trust the proposal alone (TOCTOU protection).
3. Write `after_content` to the resolved vault path (UTF-8).
4. Raise a typed `WriteError` when commit is blocked; return nothing on success.

**Convenience builders** (thin wrappers, not separate systems):

- `build_create_note_proposal_from_title(...)` — calls `create_concept_note_markdown` then the core create builder (wires B5 → B7 for the Flow 1 path in the Technical Plan).
- `build_metadata_update_proposal(...)` — reads + parses existing note, applies metadata (and optional body) changes, re-serializes, then calls the core update builder (covers UC-09 “simple metadata update” without inventing a body-patching DSL).

**Out of scope for B7** (per branch plan and prior branches): UI approval, CLI commands (B8), vault-wide fixture directories, backup/version history, relationship graph resolution, arbitrary hand-edited body patching beyond “replace metadata and/or pass a full new body string.”

---

### 2. Files likely to be created or modified

| Path | Action | Role |
|------|--------|------|
| `src/studium/writes/errors.py` | **Create** | `WriteError` hierarchy for blocked commits |
| `src/studium/writes/hashing.py` | **Create** | `hash_file_content(content) -> str` |
| `src/studium/writes/proposal.py` | **Create** | Proposal builders + internal issue helpers |
| `src/studium/writes/commit.py` | **Create** | `commit_write_proposal`, `proposal_can_be_committed` |
| `src/studium/writes/__init__.py` | **Modify** | Public exports |
| `tests/writes/test_hashing.py` | **Create** | Hash determinism |
| `tests/writes/test_create_proposal.py` | **Create** | Create builder + collision |
| `tests/writes/test_update_proposal.py` | **Create** | Update builder + before/after + missing file |
| `tests/writes/test_commit.py` | **Create** | Commit success/failure paths |
| `tests/writes/conftest.py` | **Create** | `tmp_path` vault helpers, fixture note seeding |
| `src/studium/schemas/write_proposal.py` | **No change** | Schema is sufficient (B3) |
| `src/studium/vault/vault.py` | **No change** (preferred) | Use `resolve_path` + `exists` / `read_markdown`; keep writes in `writes/` |
| `src/studium/validation/*` | **No change** | B6 APIs are ready |

Optional small addition only if commit logic gets repetitive: `Vault.write_markdown(relative_path, content)` mirroring `read_markdown`. Not required for B7 if `writes/commit.py` writes via `vault.resolve_path(...)`.

---

### 3. Step-by-step implementation sequence

#### Step 1 — Errors and hashing

- Add `WriteError` base and specific subclasses, e.g. `WriteProposalBlockedError` (carries the proposal or issue list), `StaleFileError`, `CollisionError`.
- Implement `hash_file_content(content: str) -> str` using **SHA-256 hex digest of UTF-8 bytes** (full digest; distinct from the 6-char hash in concept IDs).

#### Step 2 — Internal proposal assembly helper

- `_build_write_proposal(...)` private function that constructs `WriteProposal` from parts.
- `_storage_critical_issue(code, message)` helper producing `ValidationIssue` with `ValidationSeverity.CRITICAL`.
- `proposal_can_be_committed(proposal) -> bool` — `not proposal.critical_errors`.

#### Step 3 — Create proposal builder

- `build_create_note_proposal(vault, target_path, after_content) -> WriteProposal`
  - Validate `.md` extension on `target_path` (critical issue or `VaultTypeError` at resolve time — pick one and stay consistent).
  - `vault.exists(target_path)` → add `target_file_exists` critical; set `would_overwrite=True`.
  - `parse_and_validate(after_content, ValidationOperation.CREATE)` → merge warnings/criticals onto proposal.
  - Set `would_create=not exists`, `would_update=False`, `expected_existing_hash=None`.

#### Step 4 — Create-from-title convenience

- `build_create_note_proposal_from_title(vault, target_path, canonical_title, **metadata_overrides) -> WriteProposal`
  - `after_content = create_concept_note_markdown(canonical_title, **metadata_overrides)`
  - Delegate to `build_create_note_proposal`.

#### Step 5 — Update proposal builder

- `build_update_note_proposal(vault, target_path, after_content) -> WriteProposal`
  - If not `vault.exists(target_path)`: critical `target_file_missing`; `before_content=None`, `expected_existing_hash=None`, `would_create=True`.
  - Else: read `before_content`, set `expected_existing_hash=hash_file_content(before_content)`.
  - `parse_and_validate(after_content, ValidationOperation.UPDATE)` → merge issues.
  - Set `would_update` / `would_overwrite` from existence.

#### Step 6 — Metadata update convenience

- `build_metadata_update_proposal(vault, target_path, metadata, *, body: str | None = None) -> WriteProposal`
  - Read + `parse_concept_note` existing file.
  - Use provided `body` or keep `parsed.body`.
  - Bump `updated_at` on metadata (UTC, matching serializer normalization).
  - `after_content = serialize_concept_note(metadata, body)`.
  - Delegate to `build_update_note_proposal`.

#### Step 7 — Commit

- `commit_write_proposal(vault, proposal) -> None`
  - Raise `WriteProposalBlockedError` if `proposal.critical_errors`.
  - Branch on `proposal.operation`:
    - **CREATE_NOTE:** if `vault.exists(target_path)` → `CollisionError` (file appeared since proposal).
    - **UPDATE_NOTE:** re-read file; if missing → critical path error; if `hash_file_content(current) != proposal.expected_existing_hash` → `StaleFileError`.
  - `resolved = vault.resolve_path(proposal.target_path)`; `resolved.parent.mkdir(parents=True, exist_ok=True)`; `resolved.write_text(proposal.after_content, encoding="utf-8")`.

#### Step 8 — Public exports and integration smoke

- Wire `studium.writes.__init__.py` exports.
- Run `uv run ruff check .`, `uv run pyright`, `uv run pytest`.

---

### 4. Data model or schema changes

| Topic | Recommendation |
|-------|----------------|
| `WriteProposal` | **No structural change.** B3 fields cover B7 needs. |
| `ValidationIssue` | **No change.** Add stable `code` values from the writes layer (see below). |
| `Vault` | **No change preferred.** Writes use existing resolve/read/exists APIs. |
| New exception types | **Yes** — `studium.writes.errors`, not schema models. |

**Proposed storage-layer issue codes** (in addition to B6 validation codes):

| Code | When |
|------|------|
| `target_file_exists` | Create proposal when path already occupied |
| `target_file_missing` | Update proposal when path has no file |
| `stale_file_hash` | Commit-time hash mismatch (may also appear on proposal if re-built) |
| `invalid_target_extension` | Target path is not `.md` |

---

### 5. Important functions / classes / modules

| Symbol | Role |
|--------|------|
| `hash_file_content(content)` | Stable SHA-256 UTF-8 digest for stale detection |
| `build_create_note_proposal(vault, target_path, after_content)` | Core create proposal |
| `build_create_note_proposal_from_title(vault, target_path, title, **overrides)` | Title → markdown → create proposal |
| `build_update_note_proposal(vault, target_path, after_content)` | Core update proposal with before/after |
| `build_metadata_update_proposal(vault, target_path, metadata, *, body=None)` | Simple metadata update path (UC-09) |
| `proposal_can_be_committed(proposal)` | `not critical_errors` guard |
| `commit_write_proposal(vault, proposal)` | Safe vault write |
| `WriteError`, `CollisionError`, `StaleFileError`, `WriteProposalBlockedError` | Commit failure types |

**Dependencies used (no duplication):**

| Existing API | Used for |
|--------------|----------|
| `Vault.resolve_path`, `exists`, `read_markdown` | Path safety + I/O |
| `parse_and_validate` | Content validation on proposals |
| `parse_concept_note`, `serialize_concept_note` | Metadata update convenience |
| `create_concept_note_markdown` | Create-from-title convenience |

**Explicitly deferred to B8+**

| Symbol | Branch |
|--------|--------|
| `studium create-concept` CLI | B8 |
| `validate_write_proposal(proposal)` as standalone validator | Optional; B7 can inline checks in builders + commit |
| Committed `tests/fixtures/test_vault/` tree | B8 per B2 notes |

---

### 6. Tests / verification steps

#### `test_hashing.py`

- Same content → same hash.
- Different content → different hash.
- UTF-8 content (non-ASCII titles in body) hashes deterministically.

#### `test_create_proposal.py`

- Empty vault + valid `after_content` → `would_create=True`, no critical errors, warnings allowed.
- `build_create_note_proposal_from_title` on empty vault → valid proposal, `after_content` parses.
- Target already exists → `target_file_exists` critical, `would_overwrite=True`, `proposal_can_be_committed` is False.
- Invalid generated content (e.g. empty title path) → B6 critical errors on proposal.
- Path traversal in `target_path` → `VaultPathError` propagates from vault layer.

#### `test_update_proposal.py`

- Existing fixture note → `before_content` populated, `expected_existing_hash` set, `would_update=True`.
- Missing file → `target_file_missing` critical.
- `build_metadata_update_proposal` changes metadata, preserves body, `before_content != after_content`.
- Proposed invalid update content → B6 critical errors merged onto proposal.

#### `test_commit.py`

- **Happy create:** proposal on empty path → commit → `vault.read_markdown` matches `after_content`.
- **Happy update:** commit → file content equals `after_content`; hash of old content would have mismatched after external edit.
- **Collision block:** create proposal built when safe, file created externally before commit → `CollisionError`.
- **Stale block:** update proposal built, file modified before commit → `StaleFileError`.
- **Critical block:** proposal with validation critical errors → `WriteProposalBlockedError`, file unchanged.
- **Warnings-only commit:** proposal with warnings but no criticals commits successfully.

#### End-to-end integration (in `test_commit.py` or dedicated test)

```text
build_create_note_proposal_from_title → commit → read → parse_and_validate(PARSE) → valid
build_metadata_update_proposal → commit → read back → metadata change present
```

#### Verification commands

```bash
uv run ruff check .
uv run pyright
uv run pytest tests/writes -q
uv run pytest   # full suite regression
```

---

### 7. Risks, edge cases, and assumptions

| Risk | Mitigation |
|------|------------|
| TOCTOU: file state changes between build and commit | Re-check existence/hash at commit time |
| Duplicating validation logic | Builders call B6 only; storage rules add separate critical issues |
| `would_overwrite` semantics unclear | **CREATE + exists** → `would_overwrite=True`; **UPDATE** on existing file → `would_overwrite=True` (matches existing schema test) |
| Parent directory missing for nested paths | `mkdir(parents=True)` on commit |
| Symlink targets inside vault | Inherit B2 `resolve_path` behavior; hash/read use resolved content |
| Non-`.md` target paths | Reject with critical issue or `VaultTypeError` consistently |
| Large files / performance | Acceptable for Phase 1 test vaults; full-file read/hash is intentional |

**Assumptions**

- B2, B5, and B6 are stable and merged.
- `target_path` is a **vault-relative POSIX path** (e.g. `concepts/stochastic-gradient-descent.md`), not an absolute filesystem path.
- Callers supply `target_path`; B7 does not auto-derive paths from titles (B8 CLI may convention `concepts/{slug}.md`).
- Update proposals always carry **full file markdown** in `after_content`; partial section editing is out of scope.
- `expected_existing_hash` is captured at **proposal build time** from `before_content`; commit compares against live file.
- Warnings on a proposal do not block commit; only `critical_errors` and commit-time safety checks do.

---

### 8. Resolved decisions (approved for implementation)

| # | Decision | Resolution |
|---|----------|------------|
| 1 | `default_concept_path(title)` helper | **Defer to B8.** B7 callers supply `target_path`; tests use explicit paths. |
| 2 | Parent directory creation on commit | **Yes** — `resolved.parent.mkdir(parents=True, exist_ok=True)` before write. |
| 3 | Hash algorithm | **SHA-256 full hex digest** of UTF-8 content. |
| 4 | Update validation mode | **`ValidationOperation.UPDATE`** for update proposal build. |
| 5 | Missing file on update | **Return a proposal** with `target_file_missing` critical (do not raise from builder). |
| 6 | `Vault.write_markdown` | **No** — keep all write I/O in `writes/commit.py` via `vault.resolve_path`. |
| 7 | Re-validation on commit | **No content re-validation** — trust proposal-time B6 results; commit re-checks storage safety only (existence/hash). |
| 8 | Empty / whitespace-only title on create-from-title | **No extra B7 check** — B6 `CREATE` validation surfaces critical errors on the proposal. |

**Status:** Plan approved. Ready for implementation.

---

## 6. Code Explanation

### `proposal_can_be_committed`

| Aspect       | Detail                                                  |
| ------------ | ------------------------------------------------------- |
| Purpose      | Quick guard: can this proposal be committed?            |
| Inputs       | `proposal: WriteProposal`                               |
| Output       | `bool` — `True` when `critical_errors` is empty         |
| Vault I/O    | None                                                    |
| Validation   | None (reads issues already on the proposal)             |
| Delegates to | None                                                    |
| Typical use  | Pre-commit check before calling `commit_write_proposal` |

---

### `_storage_critical_issue` (internal)

|Aspect|Detail|
|---|---|
|Purpose|Build a storage-layer critical `ValidationIssue`|
|Inputs|`code: str`, `message: str`|
|Output|`ValidationIssue` with `severity=CRITICAL`|
|Vault I/O|None|
|Validation|None|
|Issue codes produced|`invalid_target_extension`, `target_file_exists`, `target_file_missing`|
|Delegates to|None|

---

### `_extension_issue` (internal)

|Aspect|Detail|
|---|---|
|Purpose|Reject non-`.md` target paths|
|Inputs|`target_path: str`|
|Output|`ValidationIssue \| None`|
|Vault I/O|None|
|Validation|None|
|On failure|Returns issue with code `invalid_target_extension`|
|Delegates to|`_storage_critical_issue`|

---

### `_build_write_proposal` (internal)

|Aspect|Detail|
|---|---|
|Purpose|Assemble a `WriteProposal` from precomputed parts|
|Inputs|`operation`, `target_path`, `before_content`, `after_content`, `warnings`, `critical_errors`, `would_*` flags, `expected_existing_hash`|
|Output|`WriteProposal`|
|Vault I/O|None|
|Validation|None|
|Delegates to|`WriteProposal(...)` constructor|
|Typical use|Shared by create/update builders after checks and validation|

---

### `build_create_note_proposal`

|Aspect|Detail|
|---|---|
|Purpose|Core create proposal from full markdown content|
|Inputs|`vault`, `target_path`, `after_content`|
|Output|`WriteProposal` with `operation=CREATE_NOTE`|
|Vault I/O|`resolve_path`, `exists`|
|Storage checks|`.md` extension; collision if file already exists (`target_file_exists`)|
|Validation|`parse_and_validate(after_content, CREATE)`|
|Proposal fields|`before_content=None`; `expected_existing_hash=None`; `would_create=not exists`; `would_overwrite=exists`|
|Delegates to|`_extension_issue`, `parse_and_validate`, `_build_write_proposal`|
|Typical use|Caller already has the full proposed note as markdown|

---

### `build_create_note_proposal_from_title`

|Aspect|Detail|
|---|---|
|Purpose|Convenience create: title → generated note → create proposal|
|Inputs|`vault`, `target_path`, `canonical_title`, `**metadata_overrides`|
|Output|`WriteProposal` (same shape as create proposal)|
|Vault I/O|Via `build_create_note_proposal`|
|Storage checks|Same as `build_create_note_proposal`|
|Validation|B5 generation, then B6 `CREATE` via delegated builder|
|Content generation|`create_concept_note_markdown(canonical_title, **metadata_overrides)`|
|Delegates to|`create_concept_note_markdown` → `build_create_note_proposal`|
|Typical use|New concept note from a title (B8 CLI path)|

---

### `build_update_note_proposal`

|Aspect|Detail|
|---|---|
|Purpose|Core update proposal from full markdown content|
|Inputs|`vault`, `target_path`, `after_content`|
|Output|`WriteProposal` with `operation=UPDATE_NOTE`|
|Vault I/O|`resolve_path`, `exists`, `read_markdown` (if file exists)|
|Storage checks|`.md` extension; missing file (`target_file_missing`)|
|Stale-write prep|Hashes existing content → `expected_existing_hash`|
|Validation|`parse_and_validate(after_content, UPDATE)`|
|Proposal fields|`before_content` = current file (or `None` if missing); `would_update=exists`; `would_overwrite=exists`; `would_create=not exists`|
|Delegates to|`_extension_issue`, `hash_file_content`, `parse_and_validate`, `_build_write_proposal`|
|Typical use|Caller already has the full proposed updated file as markdown|

---

### `build_metadata_update_proposal`

|Aspect|Detail|
|---|---|
|Purpose|Convenience update: structured metadata + preserved body → update proposal|
|Inputs|`vault`, `target_path`, `metadata`, optional `body` override|
|Output|`WriteProposal` (same shape as update proposal)|
|Vault I/O|`exists`, `read_markdown` (if file exists)|
|Metadata handling|Bumps `updated_at` to now (UTC, microsecond stripped)|
|Body handling|If file exists: keep `parsed.body` unless `body` is passed. If missing: use `body` or `build_canonical_concept_body(metadata)`|
|Content assembly|`serialize_concept_note(updated_metadata, effective_body)` → `after_content`|
|Storage checks|Via delegated `build_update_note_proposal`|
|Validation|Full `UPDATE` validation on assembled `after_content` (not skipped)|
|Delegates to|`parse_concept_note`, `serialize_concept_note`, `build_update_note_proposal`|
|Typical use|Simple metadata changes (e.g. `status`) while preserving existing note body|

---

### Quick comparison (public builders)

|Function|Operation|Caller provides|Body source|Validation mode|
|---|---|---|---|---|
|`build_create_note_proposal`|Create|Full `after_content`|Caller|`CREATE`|
|`build_create_note_proposal_from_title`|Create|Title + optional metadata overrides|B5 generator|`CREATE`|
|`build_update_note_proposal`|Update|Full `after_content`|Caller|`UPDATE`|
|`build_metadata_update_proposal`|Update|`ConceptNoteMetadata` (+ optional `body`)|Vault body preserved, or canonical if missing|`UPDATE`|