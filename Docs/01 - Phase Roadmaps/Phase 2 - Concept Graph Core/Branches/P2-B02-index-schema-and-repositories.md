## 1. Goal

Incorporate the beginnings of a SQLite-derived index foundation using SQLAlchemy Core. Here we will implement a centralized SQLite connection settings (concepts learned below) and define tables that will live within the SQLite DB. 

---

## 2. Branch Context

This section should be written before Cursor creates the detailed implementation plan.

### Main System Area

This branch primarily affects:

- SQLite indexing
- SQLAlchemy Core tables

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

#### SQLAlchemy Core Vs SQLAlchemy ORM (not used in relational mapping)

##### SQLAlchemy Core
- The underlying foundational database toolkit and low-level SQL abstraction layer for the SQLAlchemy ecosystem. It allows you to manage database connectivity, define database structures, and programmatically construct SQL queries using Python expressions instead of writing row SQL strings. 

##### SQLAlchemy ORM (Object-Relational Mapper)
- High-level, data-mapping abstraction layer built on top of SQLAlchemy Core that translates relational database tables into custom Python classes. It applies the Data Mapper pattern, allowing you to interact with a database using clean, object-oriented Python code instead of dealing with relational schemas, tables, and rows directly. 

##### Core vs. ORM Visual Analogy
- Core handles data as database rows (similar to Python tuples). ORM handles data as instances of your custom Python classes.
- **SQLAlchemy Core (Table-Centric)**: You think in database structures. You tell the system: _"Go to the `users` table, find the row where `id` equals 5, and update the `email` column to 'xyz'."_
- **SQLAlchemy ORM (Object-Centric)**: You think in Python applications. You tell the system: _"Fetch the user object with ID 5. Now change its `.email` attribute."_ The ORM automatically figures out the correct SQL statement to update the database behind the scenes.

#### Repository pattern 
- A design pattern that mediates between the domain (business logic) and data mapping layers of an application. Essentially acts as the middle man for fetching or saving data so business logic is completely cut off from specific details of data access, databases, or API clients.  

#### SQLite WAL
- By default, SQLite uses a "Rollback Journal" (DELETE mode), where writing data blocks all database reads, and reading data blocks all writes. Switching to WAL mode breaks this bottleneck, allowing readers and a writer to operate simultaneously without blocking each other. 

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

Branch: Index Schema and Repositories

Branch goal: Set up the foundation for hosting a SQLite DB for indexing and define necessary tables that reflect the metadata defined in previous branches. Incorporate validation for the creation of this layer of the applciation through CRUD calls. 

Expected outcome:
SQLAlchemy Core schema, repositories, database runtime configuration, and index version handling.

Relevant context:
Within the Phase 2 - Concept Graph Core folder, the files 2 - Final Phase Roadmap, 3 - Technical Plan, and 4 - Branch Plan. Disregard 1 - Initial Phase Roadmap

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
8. Key concepts to understand before implementation
9. Questions or decisions needed before implementation
```

---

## 5. Cursor Implementation Plan

Paste or summarize Cursor’s implementation plan here before implementation begins.

### 1. Summary of proposed approach

Add a new **`studium.index`** package that owns the **rebuildable derived SQLite index**: path resolution, SQLAlchemy Core engine/connection setup, table DDL, schema-version gate, and thin repositories for CRUD.

This branch does **not** sync vault Markdown into the index (that is P2-B03). It only proves that an empty index can be created outside the vault, version-checked, and exercised with repository insert/query/delete under real SQLite FK + transaction behavior.

**Design principles**
- SQLAlchemy **Core** only (tables + `insert`/`select`/`update`/`delete`) — no ORM mapped entities.
- Repositories own SQL; no sync, search ranking, or embedding generation logic here.
- Do **not** store full YAML frontmatter blobs; store **normalized columns** derived from schema-v2 metadata fields.
- Concept-note `schema_version` (Markdown) and index `INDEX_SCHEMA_VERSION` (SQLite) stay independent.
- Incompatible index schema → reject use and require rebuild (delete/recreate). No Alembic / migration framework.
- FTS **virtual** tables (`concept_fts`, `module_fts`) deferred to **P2-B04**; B02 still creates **materialized search-document** tables so later FTS has a place to read from.

**Central runtime PRAGMAs** (on every connection):
```text
foreign_keys = ON
journal_mode = WAL
synchronous = NORMAL
busy_timeout = <configured ms>
```

---

### 2. Files likely to be created or modified

| Path | Action | Role |
|------|--------|------|
| `pyproject.toml` | **Modify** | Add `sqlalchemy>=2` dependency |
| `src/studium/index/__init__.py` | **Create** | Public exports |
| `src/studium/index/errors.py` | **Create** | `IndexError`, `IndexSchemaMismatchError`, `IndexNotInitializedError`, … |
| `src/studium/index/paths.py` | **Create** | App-data root, vault id, `concept-index.sqlite` path |
| `src/studium/index/config.py` | **Create** | `IndexConfig` (paths, busy_timeout, schema version constant) |
| `src/studium/index/engine.py` | **Create** | Engine factory + connection PRAGMA event hook |
| `src/studium/index/schema.py` | **Create** | `MetaData` + all Core `Table` definitions + indexes |
| `src/studium/index/schema_manager.py` | **Create** | create / inspect version / reject mismatch / rebuild |
| `src/studium/index/transactions.py` | **Create** | `session`/`connection` transaction helper |
| `src/studium/index/normalize.py` | **Create** | Small helpers (e.g. title normalization for indexed columns) |
| `src/studium/index/repositories/*.py` | **Create** | Focused CRUD repositories (one module per aggregate, or grouped thinly) |
| `tests/index/conftest.py` | **Create** | Temp DB fixtures |
| `tests/index/test_paths.py` | **Create** | Vault id + path layout |
| `tests/index/test_schema_manager.py` | **Create** | Init / version mismatch / rebuild |
| `tests/index/test_engine.py` | **Create** | PRAGMA enforcement |
| `tests/index/test_repositories.py` | **Create** | CRUD + FK + cascade + rollback |
| `README.md` | **Modify lightly** | Note derived index location (optional, if you want discoverability) |

**Out of scope files:** sync service, FTS virtual tables, embedding generation, CLI graph commands, vault write paths.

---

### 3. Step-by-step implementation sequence

#### Step 1 — Dependency + package skeleton
- Add SQLAlchemy 2.x to project dependencies.
- Create `studium.index` package with errors and config constants:
  - `INDEX_SCHEMA_VERSION = 1` (first derived schema; bump only on incompatible DDL changes).

#### Step 2 — Paths and vault identity
Implement:
```text
resolve_application_data_dir(override: Path | None) -> Path
derive_vault_identifier(vault_root: Path) -> str
index_db_path(app_data: Path, vault_id: str) -> Path
  → <app_data>/indexes/<vault_id>/concept-index.sqlite
```
- Default app-data via **`platformdirs.user_data_dir("studium")`** (or explicit override always required in tests).
- Vault id: hex digest of **resolved absolute vault path** (recommend SHA-256 truncated, e.g. 16–32 chars) so path strings stay filesystem-safe; store full canonical vault path in `index_metadata` for diagnostics.

#### Step 3 — Engine + PRAGMAs
- `create_index_engine(db_path, busy_timeout_ms) -> Engine`
- Register `connect` listener that runs the four PRAGMAs.
- Ensure directory exists before connect.
- Expose `begin_connection(engine)` / context manager for transactions.

#### Step 4 — Table DDL (`schema.py`)
Define normalized tables (exact columns in §4 below). Key rules:
- Integer PKs where helpful for child FKs; stable business keys (`concept_id`, `module_id`, vault-relative `file_path`) UNIQUE where appropriate.
- `ON DELETE CASCADE` from parent concept / indexed file to children.
- No full YAML dump columns.
- Include `embeddings` and search-document tables now (empty usage OK); **skip FTS virtual tables** until B04.

#### Step 5 — Schema manager
- `initialize_index(engine)` → `create_all` + insert `index_metadata` row with `schema_version`, vault path, created timestamp.
- `read_index_schema_version(engine) -> int | None`
- `ensure_compatible_index(engine)` → raise `IndexSchemaMismatchError` if version ≠ `INDEX_SCHEMA_VERSION`.
- `rebuild_index(engine)` → drop all application tables (or delete DB file + recreate) then `initialize_index`. Prefer **file replace** for simplicity when safe; in-process drop/create is fine for tests.

#### Step 6 — Repositories
Thin classes/functions taking a SQLAlchemy `Connection` (or engine + begin internally for single-ops). Minimum surface:
- upsert/get/delete by natural key
- list-by-parent where needed (aliases by concept, relationships by source concept, …)
- no “sync a note” methods

Suggested modules:
`index_metadata`, `indexed_files`, `concepts`, `aliases`, `domains`, `learning_encounters`, `relationships`, `scaffold_modules`, `search_documents`, `embeddings`, `invalid_records`.

#### Step 7 — Tests
Temp sqlite files under `tmp_path`; assert PRAGMAs, version gate, CRUD, FK reject, cascade delete, rollback.

#### Step 8 — Verify
```bash
uv sync
uv run ruff check .
uv run pyright
uv run pytest tests/index -q
uv run pytest
```

---

### 4. Data model or schema changes

**Concept-note Markdown schemas:** no change (already v2 from B01).

**New derived SQLite schema (proposed columns — refine only if needed during impl):**

| Table | Purpose / key columns |
|-------|------------------------|
| `index_metadata` | singleton-ish: `schema_version`, `vault_path`, `vault_identifier`, `created_at`, `updated_at`, optional `last_rebuild_at` |
| `indexed_files` | `file_path` (unique), `concept_id` nullable, `note_schema_version`, `file_hash`, `projection_hash`, `mtime_ns`/`mtime_iso`, `index_state` (`valid`/`invalid`/`duplicate_id_conflict`/`removed`), `last_success_revision`, `invalid_since_revision`, `validation_errors_json`, `indexed_at` |
| `concepts` | `concept_id` (unique), `canonical_title`, `normalized_title`, `concept_type`, `status`, `review_status`, `vault_status`, `file_path`, `h1_title`, `overview_markdown`, `overview_plaintext`, `identity_input_hash`, `semantic_input_hash`, `note_schema_version`, `validity_state`, `indexed_revision`, `note_created_at`, `note_updated_at` |
| `concept_aliases` | FK → concept, `alias`, `normalized_alias`; unique `(concept_id, normalized_alias)` |
| `concept_domains` | FK → concept, `domain`; unique `(concept_id, domain)` |
| `learning_encounters` | FK → concept; source fields flattened (`source_type`, `source_title`, `unit_*`, `link`, `external_id_type`, `external_id_value`); `role`, `contribution_status`, `content_attached`, `content_id`; optional `fingerprint` |
| `relationships` | FK → source concept; `relationship_type`, `target_id`, `target_title`, `vault_status`, `learning_role`, `confidence`, `status` |
| `scaffold_modules` | FK → concept; `module_id` unique, `type`, `title`, `normalized_title`, `status`, `origin`, `focus`, `heading`, `anchor`, `segment_count`, `indexed_revision` |
| `concept_search_documents` | FK → concept; `document_text`, `field_weights_json` or separate weight columns later, `indexed_revision` |
| `module_search_documents` | FK → module/concept; `document_text`, `indexed_revision` |
| `embeddings` | `owner_type`, `owner_id`, `parent_concept_id`, `segment_id`, `embedding_type`, `vector` BLOB, `dimension`, `model_id`, `model_revision`, `input_hash`, `created_at`, `indexed_revision` |
| `invalid_index_records` | `file_path`, `concept_id` nullable, `reason_code`, `message`, `details_json`, `since_revision`, `recorded_at` |

**Indexes (minimum):**
- `concepts(normalized_title)`, `concept_aliases(normalized_alias)`, `relationships(source_concept_id)`, `relationships(target_id)`, `scaffold_modules(concept_id)`, `indexed_files(concept_id)`, `embeddings(owner_type, owner_id)`, `embeddings(input_hash)`

**Cascade:** deleting a `concepts` row deletes aliases, domains, encounters, relationships (as source), modules, search docs, embeddings for that owner; deleting `indexed_files` does not invent business rules beyond FK needs — sync (B03) owns lifecycle.

**FTS:** not created in B02.

---

### 5. Important functions / classes / modules

| Symbol | Role |
|--------|------|
| `INDEX_SCHEMA_VERSION` | Code’s expected SQLite schema integer |
| `IndexConfig` | Paths + busy timeout + overrides for tests |
| `derive_vault_identifier` | Stable filesystem-safe id from vault path |
| `create_index_engine` | Engine + PRAGMA hooks |
| `metadata` / table objects | Core DDL |
| `SchemaManager` / functions | create, inspect, ensure, rebuild |
| `IndexSchemaMismatchError` | Incompatible DB → rebuild required |
| `*Repository` | CRUD only |
| `normalize_title(text) -> str` | Lowercase / whitespace collapse for equality lookup columns |

No CLI changes required for B02 success (optional smoke later in B13).

---

### 6. Tests / verification steps

- **Paths:** vault id stable for same resolved path; DB path ends with `indexes/<id>/concept-index.sqlite`; override app-data root works.
- **Init:** empty DB created; `index_metadata.schema_version == INDEX_SCHEMA_VERSION`.
- **Mismatch:** manually set DB version to `999` → `ensure_compatible` raises; rebuild restores current version.
- **PRAGMAs:** after connect, `PRAGMA foreign_keys` / `journal_mode` / `synchronous` match expected (WAL may report `wal`).
- **FK:** insert child with missing parent → fails when FKs on.
- **Cascade:** insert concept + alias + relationship; delete concept; children gone.
- **Transactions:** insert then raise before commit → rollback leaves table empty.
- **Repository CRUD:** round-trip concept, aliases, domains, encounters (with optional external_id columns), relationships (v2 fields), modules, search docs, embedding blob, invalid record.
- **WAL smoke (light):** open second connection and read while first holds a short write transaction (optional, not flaky timing-heavy).

**Commands:** `uv run ruff check .`, `uv run pyright`, `uv run pytest`.

---

### 7. Risks, edge cases, or assumptions

| Risk | Mitigation |
|------|------------|
| Scope creep into sync | Explicitly no vault scan/write in B02 |
| ORM temptation | Core tables + repositories only |
| Storing YAML snapshots | Forbidden; normalized columns only |
| FKs silently off in SQLite | Central connect hook + test |
| App-data path OS differences | `platformdirs` + always-overridable root for tests/CLI later |
| Truncated vault id collisions | Extremely unlikely with 16+ hex of SHA-256; full path stored in metadata |
| Embedding BLOB unused until B05/B06 | Still define table now so schema version stays stable |
| Over-wide repositories | Keep methods small; sync service composes them in B03 |
| Dropping FTS from B02 | Document deferral; B04 owns virtual tables + FTS repo |

**Assumptions**
- B01 schema v2 is merged/available.
- One SQLite file per vault id is enough for Phase 2.
- Rebuild may delete the DB file; nothing in SQLite is irreplaceable.
- Title normalization is a simple deterministic function for now (refine in search branches if needed).

---

### 8. Key concepts to understand before implementation

See §3 above. Short version:

1. **Derived index** ≠ source of truth; vault Markdown is.
2. **SQLAlchemy Core** = schema + SQL expression language, not declarative ORM models.
3. **Repository** = persistence API only.
4. **WAL + foreign_keys** must be set on each connection.
5. **Index schema version** mismatch ⇒ rebuild, never migrate.
6. **Normalized tables** mirror query needs (aliases/domains/relationships as rows), not document dumps.

---

### 9. Questions or decisions needed before implementation

| # | Decision | Recommendation |
|---|----------|----------------|
| 1 | App-data directory | Use **`platformdirs`** (`user_data_dir("studium")`) + **`IndexConfig.app_data_dir` override** for tests/CLI. Add `platformdirs` dependency. |
| 2 | Vault identifier | **SHA-256 of resolved absolute vault path**, hex **prefix 32 chars**; store full path in `index_metadata`. |
| 3 | Initial `INDEX_SCHEMA_VERSION` | **`1`**. |
| 4 | FTS virtual tables in B02? | **No — defer to B04**. Include `concept_search_documents` / `module_search_documents` only. |
| 5 | Repository style | **One small module per table/aggregate**, shared connection; no Unit-of-Work framework. |
| 6 | Rebuild strategy | **Delete DB file (and `-wal`/`-shm` if present) then re-initialize** when mismatch/rebuild requested; simpler than partial DROP. |
| 7 | Title normalization | **casefold + collapse whitespace**; no unicode NFKC unless you prefer it now (can upgrade later with schema bump). |
| 8 | Embeddings table now? | **Yes** (empty CRUD tests with a tiny BLOB) so later embedding work does not force an early schema bump. |
| 9 | README / docs | Light README note on index location; no Phase 1 history rewrite. |

### Plan Review Notes

Decisions 1–9 approved as recommended (2026-07-28). FTS virtual tables deferred to B04.

### Approved to Implement?

- [x] Yes
    
- [ ] No, revise plan first
    

---

## 6. Implementation Notes

Complete this during or immediately after implementation.

### Files Changed

### New Files Added

### Important Functions / Classes / Modules Added or Changed

### Data Model or Schema Changes

### UI Changes

### Agent Behavior Changes

### Other Important Changes

---

## 7. Code Understanding

Complete this after the implementation satisfies the branch goal.

The purpose of this section is not to document every line of code.  
The purpose is to prove that I understand the implementation well enough to move on.

### Main Implementation Flow

Explain the main flow in my own words.

### Key Files and Responsibilities

- `<file>` —
    
- `<file>` —
    
- `<file>` —
    

### Important Logic I Need to Understand

Explain the parts of the implementation that are most important, non-obvious, or easy to misunderstand.

### Key Design Decisions

What implementation choices matter for future branches?

### How This Branch Fits the Phase

Explain how this branch moves the current phase closer to completion.

---

## 8. Tests and Verification

### Automated Checks

-  Ruff
    
-  Pyright
    
-  pytest
    
-  coverage
    
-  frontend tests, if applicable
    
-  other:
    

### Tests Added or Updated

### Manual Verification

Steps used to verify this branch manually:

### Verification Result

### Testing Gaps / Follow-Up

Anything not tested yet that should be remembered:

---

## 9. Branch Reflection

Write this after implementation.

### What I Learned

### What Was Confusing

### What I Would Improve Later

### Follow-Up Backlog Items

Add these to the appropriate Backlog file if they should not be handled in this branch.

### Documentation Updates Needed

-  Concepts
    
-  Data Schemas
    
-  System Models
    
-  Agent Behavior
    
-  UI UX
    
-  Technical Architecture
    
-  Backlog
    
-  Decisions / ADRs
    
-  None
    

Notes:

---

## 10. Final Branch Summary

Short final summary after the branch is complete:

```text
This branch added <summary>. It changed <main files/areas>. The main implementation flow is <brief explanation>. It was verified by <tests/manual checks>. Remaining follow-ups are <items or none>.
```