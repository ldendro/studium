## 1. Goal

Incorporate functionality for syncing valid vault notes into the derived index created form the SQLAlchemy DB. This constitutes implementing a full rebuild command from indexing the entire vault to the new DB, with selective and incremental sync also incorporated. 

---

## 2. Branch Context

- Calculating hashes for files and aspects of files
	- Identifying new, changed, unchanged, moved, removed, invalid, or duplicate-ID conflict
- Syncing index from vault

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

- `[[Incremental synchronization]]` — compare vault files to indexed-file records; only reproject what changed
    
- `[[Index projection]]` — deterministic mapping from a valid parsed note into normalized SQLite rows
    
- `[[Content hashing layers]]` — `file_hash` vs `index_projection_hash` vs embedding input hashes
    
- `[[Atomic concept projection]]` — replace one concept and its children in a single transaction
    
- `[[Index revision]]` — monotonic integer bumped when usable derived state changes
    
- `[[SyncReport]]` — typed outcome of a sync/rebuild (success / partial / failed / no_changes)
    
- `[[Duplicate-ID conflict]]` — same `concept_id` in multiple files; exclude all, pick no winner
    

Questions I should be able to answer:

- Why must invalid notes not leave stale last-valid content searchable?
    
- How does a file move differ from delete+create?
    
- Why generate embedding *work requests* without calling an embedding provider yet?
    
- When does the index revision increment?
    

---

## 4. Cursor Implementation Planning Prompt

Use this prompt to ask Cursor for a detailed implementation plan **before any code is generated**.

Cursor should not implement yet. The goal of this step is to produce a clear plan that I can review, question, and approve.

```text
We are planning the implementation for a single branch of Studium.

Do not implement code yet.

Project context:
Studium is an AI-assisted learning system built around Markdown/Obsidian-compatible notes, concept graphs, scaffold generation, source-aware RAG, local/source library processing, and agent-based note review.

Phase: 2

Branch: Vault Index Synchronization

Branch goal:
Implement all aspects of syncing functionality between the vault and index, including vault scanning, incremental index updates, full index rebuilds, invalid-note, duplicate-ID detection, and file-move detection, index revisions, to enable embedding-work requests in the future. 

Expected outcome:
See Branch Plan Expect Output for this branch

Relevant context:
Within Phase 2 - Concept Graph Core folder, the files 2 - Final Phase Roadmap, 3 - Technical Plan, and 4 - Branch Plan. Ignore 1 - Initial Phase Roadmap. 

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

Paste or summarize Cursor’s implementation plan here before implementation begins.

### 1. Summary of proposed approach

Add a **`studium.index.sync`** package that turns vault Markdown into the B02 SQLite index.

**Core loop (incremental `sync_vault`)**
1. Ensure index schema is compatible (`ensure_compatible_index`).
2. Scan vault Markdown via existing `Vault.list_markdown_files()` (+ read content).
3. Hash each file (`file_hash`, reuse `writes.hashing.hash_file_content` / SHA-256).
4. Compare to `indexed_files` rows → classify: **new / changed / unchanged / moved / removed**.
5. Detect **duplicate `concept_id`** across current valid parses; mark *all* conflicting paths `duplicate_id_conflict` and exclude them.
6. For new/changed (and non-duplicate) files: Phase 1 `parse_and_validate(..., PARSE)`  
   - invalid → diagnostic `invalid_index_records` + `indexed_files.index_state=invalid`; **remove or mark stale** any prior searchable concept projection for that path/id  
   - valid → build **deterministic projection** + hashes → **atomic upsert** of concept + children + search docs
7. For removed paths: delete concept projection (if owned by that path) and indexed-file row.
8. For moves (`same concept_id`, new path): update paths; do not delete/recreate identity.
9. Compute **embedding work requests** from identity/semantic/module input-hash diffs (no provider calls).
10. If usable state changed → increment **index revision**; return typed **`SyncReport`**.

**Full rebuild**
- Prefer **side-file / temp DB → dispose old engine → atomic replace** (or delete+recreate via existing `rebuild_index` + full sync), so a failed rebuild does not leave a half-written active index.
- Rebuild = empty compatible schema + project every current valid note + SyncReport.

**Out of scope for B03**
- Real embedding generation / vector backends (B05–B06)
- FTS virtual tables / ranked lexical search (B04) — still write/update **materialized** `concept_search_documents` / `module_search_documents`
- CLI sync commands (optional thin wrapper OK; B13 owns full graph CLI)
- Recommendation / graph query APIs

**Design principles**
- Sync orchestrates; repositories stay CRUD-only.
- One concept projection = one DB transaction (no half-written child rows).
- Invalid/duplicate notes must not remain queryable via stale last-valid content.
- Same valid note → same projection hashes (deterministic serialization of projected fields).

---

### 2. Files likely to be created or modified

| Path | Action | Role |
|------|--------|------|
| `src/studium/index/schema.py` | **Modify** | Add `index_revision` (and maybe `last_sync_at`) on `index_metadata` |
| `src/studium/index/config.py` | **Modify** | Bump `INDEX_SCHEMA_VERSION` to `2` |
| `src/studium/index/schema_manager.py` | **Modify** | `get_index_revision` / `increment_index_revision`; rebuild helpers aware of revision |
| `src/studium/index/repositories/projections.py` | **Create** | Atomic upsert/remove of full concept projection |
| `src/studium/index/repositories/*.py` | **Modify as needed** | Small helpers (list all indexed files, find by concept_id, etc.) |
| `src/studium/index/sync/__init__.py` | **Create** | Public sync API |
| `src/studium/index/sync/models.py` | **Create** | `SyncReport`, file classification enums, `EmbeddingWorkRequest` |
| `src/studium/index/sync/hashes.py` | **Create** | file / projection / identity / semantic / module hashes |
| `src/studium/index/sync/scan.py` | **Create** | Vault scan → path + content + file_hash |
| `src/studium/index/sync/classify.py` | **Create** | new/changed/unchanged/moved/removed + duplicate-id grouping |
| `src/studium/index/sync/project.py` | **Create** | `project_concept_note` → row payloads + search docs + hash inputs |
| `src/studium/index/sync/embedding_inputs.py` | **Create** | Deterministic identity/semantic/module input text builders |
| `src/studium/index/sync/synchronizer.py` | **Create** | `sync_vault`, `rebuild_vault_index` orchestration |
| `src/studium/index/__init__.py` | **Modify** | Export sync entrypoints |
| `tests/index/sync/` | **Create** | Fixture vaults + sync/rebuild/hash/revision tests |
| `README.md` | **Modify lightly** | Mention sync/rebuild library API |

**Reuse (no reimplementation):** `Vault`, `parse_and_validate`, `ValidationOperation.PARSE`, B02 engine/repos, `hash_file_content`.

---

### 3. Step-by-step implementation sequence

#### Step 1 — Schema bump for revisions
- Add `index_revision INTEGER NOT NULL DEFAULT 0` to `index_metadata`.
- Bump `INDEX_SCHEMA_VERSION` **1 → 2** (incompatible; existing DBs must rebuild — already required by B02 mismatch policy).
- Add `get_index_revision(engine) -> int` and `increment_index_revision(engine) -> int`.

#### Step 2 — Sync models
```text
FileSyncClass: new | changed | unchanged | moved | removed | invalid | duplicate_id_conflict
SyncStatus: success | partial_success | failed | no_changes
EmbeddingWorkRequest: owner_type, owner_id, embedding_type, input_hash, input_text, parent_concept_id, ...
SyncReport: sync_id, times, status, revision_before/after, counts, embedding work lists, warnings/errors
```

#### Step 3 — Hashing + embedding input builders
- `file_hash`: SHA-256 of raw file bytes/text (align with `hash_file_content`).
- `index_projection_hash`: SHA-256 of canonical JSON (or similar) of projected index fields only.
- `identity_input_hash` / `semantic_input_hash` / `module_input_hash`: hash of exact input strings from Technical Plan §4.11.
- Keep builders pure and tested for stability.

#### Step 4 — Projection builder
From `ConceptNoteMetadata` + body sections (overview plaintext/markdown, module titles):
- concept / aliases / domains / encounters / relationships / modules
- materialized search document text (simple join of title+aliases+overview / module fields — enough for B04 later)
- **Do not** insert real embedding vectors; only compute hashes + work requests

#### Step 5 — Classification
- Load all `indexed_files`.
- Match by path + `file_hash` for unchanged.
- Match by `concept_id` across paths for moves.
- Paths only in index → removed.
- After parse, group by `concept_id`; size>1 → duplicate conflict for those files.

#### Step 6 — Atomic projection upsert/remove
In one transaction per concept:
1. Delete previous children by `concept_id` (or replace via delete+insert).
2. Upsert concept + aliases/domains/encounters/relationships/modules/search docs.
3. Upsert `indexed_files` with hashes, state=`valid`, revision stamps.
4. Clear invalid records for that path when recovering to valid.

Invalid path transaction:
- Upsert `indexed_files` state=`invalid`
- Insert/replace `invalid_index_records`
- **Remove** searchable concept projection for that concept_id if this file was the prior owner (so stale content is not served)

Duplicate conflict:
- Mark all conflicting paths; remove their searchable projections; continue other files → typically `partial_success`.

#### Step 7 — `sync_vault` / `rebuild_vault_index`
- `sync_vault(vault, engine, config) -> SyncReport`
- `rebuild_vault_index(config, existing_engine=...) -> (Engine, SyncReport)`  
  dispose existing engine → recreate empty schema (B02 `rebuild_index`) → run full sync over empty index → set revision / `last_rebuild_at`

#### Step 8 — Tests + verify
Temp vaults under `tmp_path`; cover Branch Plan test list. Run ruff/pyright/pytest.

---

### 4. Data model or schema changes

| Change | Detail |
|--------|--------|
| `index_metadata.index_revision` | New integer; starts at 0; increments when usable state changes |
| `INDEX_SCHEMA_VERSION` | **2** |
| Concept-note Markdown schema | No change (still v2) |
| Embedding rows | Not populated with real vectors in B03; work requests only |
| FTS virtual tables | Still deferred to B04 |

Optional (only if needed during impl): store `module_input_hash` on `scaffold_modules` (column add ⇒ already covered by schema v2 bump). Prefer adding it now so module hash tracking does not force another bump before B05.

---

### 5. Important functions / classes / modules

| Symbol | Role |
|--------|------|
| `sync_vault(...)` | Incremental synchronizer entrypoint |
| `rebuild_vault_index(...)` | Safe full rebuild + sync |
| `scan_vault(...)` | Discover Markdown paths + content + file hashes |
| `classify_files(...)` | new/changed/unchanged/moved/removed |
| `find_duplicate_concept_ids(...)` | Conflict detection |
| `project_concept_note(...)` | Deterministic projection payloads |
| `calculate_projection_hashes(...)` | projection + embedding input hashes |
| `build_identity/semantic/module_embedding_input(...)` | Hash/input text builders |
| `upsert_concept_projection(...)` | Atomic replace of derived rows |
| `remove_concept_projection(...)` | Cascade-safe removal |
| `mark_index_record_invalid(...)` | Invalid lifecycle |
| `get/increment_index_revision(...)` | Revision control |
| `SyncReport` / `EmbeddingWorkRequest` | Typed results |

---

### 6. Tests / verification steps

| Scenario | Expectation |
|----------|-------------|
| Empty vault sync | `no_changes` or success with 0 concepts; revision unchanged |
| First valid concept | creates concept + children; revision +1 |
| Unchanged re-sync | skipped; `no_changes`; revision unchanged |
| Metadata/body change | updates projection; revision +1; embedding work for changed hashes only |
| Move/rename same id | path updated; concept retained; not counted as delete+create |
| Delete file | projection removed |
| Invalid new note | reported; no searchable concept |
| Valid → invalid | diagnostics; concept excluded/removed from searchable tables |
| Invalid → valid | projection restored |
| Duplicate IDs | both excluded; `partial_success` |
| Partial success | unrelated valid notes still sync |
| Hash stability | same note → same hashes |
| Atomic rollback | forced DB error mid-upsert leaves no partial children |
| Full rebuild | empty then full population; matches incremental ground truth |
| Revision rules | only usable-state changes bump revision |

**Commands**
```bash
uv run ruff check .
uv run pyright
uv run pytest tests/index -q
uv run pytest
```

---

### 7. Risks, edge cases, or assumptions

| Risk | Mitigation |
|------|------------|
| Stale valid content after note becomes invalid | Always remove/exclude searchable projection for that concept when current file is invalid/conflicted |
| Treating moves as delete+create | Classify by `concept_id` before removals |
| Partial rebuild corrupts active DB | Dispose engine + recreate schema (B02) before projecting; or build temp DB then replace |
| Scope creep into embeddings/FTS | Work requests + materialized search docs only |
| Non-deterministic projection hashes | Canonical key order / JSON serialization in hash helper; golden tests |
| PARSE vs WRITE validation | Sync uses **PARSE** for hand-authored vault notes (same as CLI validate) |
| Multiple concepts in one file | Out of scope — one note = one concept metadata id |
| `create_all` won’t migrate old DBs | Schema version 2 forces rebuild (already policy) |

**Assumptions**
- B01/B02 are available and stable.
- Vault root is the same path bound in `IndexConfig`.
- Overview/module body extraction can use existing parsing section detection; if overview plaintext helper is thin, add a small sync-local extractor rather than rewriting the parser.
- Embedding provider absence is expected; SyncReport lists work that B05 will consume.

---

### 8. Questions or decisions needed before implementation

| # | Decision | Recommendation |
|---|----------|----------------|
| 1 | Rebuild strategy | **Dispose existing engine → `rebuild_index` (empty schema) → full `sync_vault`**. Simpler than dual-file swap; still avoids projecting into a live half-migrated schema. Optional later: temp DB + `os.replace`. |
| 2 | Schema version | **Bump to 2** for `index_revision` (+ optional `module_input_hash` on modules). |
| 3 | Validation mode | **`ValidationOperation.PARSE`**. |
| 4 | Search documents in B03 | **Yes — write simple materialized text now**; FTS virtual tables still B04. |
| 5 | Embeddings in B03 | **Work requests + input hashes only**; do not write vector BLOBs. |
| 6 | Revision bump rules | Bump when any created/updated/removed/invalidated/conflict change affects usable derived state; **not** on pure unchanged/`no_changes`. |
| 7 | Duplicate-ID policy | **Exclude all conflicting files**; no winner. |
| 8 | CLI | **Library API first**; optional thin `studium sync-vault` only if you want manual verification now — otherwise defer to B13. |
| 9 | Overview extraction | Prefer existing body section parser; plaintext = strip simple Markdown lightly or store raw overview section text for v1 of semantic hash. |

### Plan Review Notes

Decisions 1–9 approved as recommended (2026-07-28):

1. Rebuild = dispose → `rebuild_index` → full `sync_vault`
2. `INDEX_SCHEMA_VERSION` 1 → 2 (`index_revision`, `module_input_hash`)
3. Validation mode: `ValidationOperation.PARSE`
4. Write materialized search documents now; FTS still B04
5. Embedding work requests + input hashes only (no vector BLOBs)
6. Revision bumps only when usable derived state changes
7. Duplicate concept IDs → exclude all conflicting files
8. Library API only (CLI deferred to B13)
9. Overview extraction: reuse section parsing + light normalization for `semantic_input_hash`

### Approved to Implement?

- [x] Yes
    
- [ ] No, revise plan first
