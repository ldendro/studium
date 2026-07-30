## 1. Goal

The purpose of this branch is to implement the sparse retrieval aspect of the overall retrieval system, including implementing deterministic and weighted lexical retrieval of note content based on user query. This branch includes the use of weighted SQLite full-text retrieval for concepts and scaffolds modules, which will be reviewed up for further understanding in this document. 

---

## 2. Branch Context

- Mainly involves the sparse retrieval side of the overall retrieval system, so exact ID lookup, normalized title lookup, approved-alias lookup, keyword search, concept overview search, concept-domain search, and scaffold module lexical search. 

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

- `[[Deterministic identity lookup]]` — exact ID / normalized title / approved alias before ranked search
    
- `[[SQLite FTS5]]` — virtual tables + BM25 ranking over materialized search documents
    
- `[[Weighted field ranking]]` — title/alias outweigh overview/body; module title outweighs body
    
- `[[Lexical normalization]]` — matching-only transforms; display strings stay original
    
- `[[Alias collision]]` — same normalized alias on multiple concepts → ambiguous, not unique identity
    
- `[[Materialized search documents]]` — derived rows (already from B03) that feed FTS

Questions I should be able to answer:

- Why must exact title/alias matches stay outside ordinary FTS ranking?
    
- How do FTS documents stay in sync when sync removes or invalidates a concept?
    
- Why avoid aggressive stemming for technical concept titles?
    
- What belongs in B04 vs full hybrid `ConceptSearchService` (B07)?
    

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

Branch: Weighted Full Text Search

Branch goal:
Implement determinstic concept identiy lookup and weighted SQLite full-text retrieval for concepts and scaffold modules to not only incorporate as part of the entire retrieval system but to also utilize as a baseline when implementing the embedding pipeline for retrieval in later branches.

Expected outcome:
The sparse retrieval side of the retreival system is fully functional, where exact IDs, titles, and approved aliases resolve deterministically. 

Relevant context:
Within the Phase 2 - Concept Graph Core folder, the fiels 2- Final Phase Roadmap, 3 - Technical Plan, and 4 - Branch Plan. 

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

Add a **lexical search layer** on top of the B02/B03 index that does two distinct jobs:

**A. Tier 0 — deterministic identity lookup (no FTS)**
1. Exact `concept_id` match
2. Normalized canonical-title equality (`normalize_for_lookup`)
3. Approved-alias equality on `concept_aliases.normalized_alias`
4. If multiple concepts share the same normalized alias → **ambiguous** (return all; do not pick a winner)

**B. Tier 1a — weighted SQLite FTS5 (lexical only)**
1. Keep/enrich materialized `concept_search_documents` / `module_search_documents` with **per-field text** (not one flat blob)
2. Create FTS5 virtual tables (content= or external-content sync) with separately weighted columns
3. Rank with BM25 + column weights: title > aliases > module title > overview > domains > module body
4. Return ranked concept hits and module hits with parent concept + location metadata + component scores/ranks

**Scope boundary**
- B04 = deterministic lookup + weighted FTS + lexical result types + sync integration
- **Not** hybrid fusion, vectors, or full `ConceptSearchService` orchestration → those are B07 (after embeddings/vector backend)
- Provide a thin `search_concepts_lexical(...)` / lookup API that B07 will compose later

**Reuse**
- B03 already writes materialized search docs and keeps them atomic with concept projection
- Existing `normalize_title` is a starting point; extend into a fuller matching normalizer
- Repositories stay CRUD-ish; search logic lives in `studium.index.search`

---

### 2. Files likely to be created or modified

| Path | Action | Role |
|------|--------|------|
| `src/studium/index/normalize.py` | **Modify** | Expand matching normalization (Unicode, hyphen/underscore, light punctuation) |
| `src/studium/index/schema.py` | **Modify** | Document FTS virtual-table names/columns (or keep DDL in schema_manager) |
| `src/studium/index/schema_manager.py` | **Modify** | Create FTS5 tables; rebuild-aware; bump schema version |
| `src/studium/index/config.py` | **Modify** | `INDEX_SCHEMA_VERSION` **2 → 3** |
| `src/studium/index/sync/project.py` | **Modify** | Materialize per-field search payloads + `field_weights_json` |
| `src/studium/index/repositories/search_documents.py` | **Modify** | Helpers for fielded documents; FTS sync helpers if needed |
| `src/studium/index/repositories/fts.py` | **Create** | Insert/delete/rebuild FTS rows; run MATCH queries |
| `src/studium/index/repositories/concepts.py` / `aliases.py` | **Modify** | Exact lookup helpers (`by_id`, `by_normalized_title`, `by_normalized_alias`) |
| `src/studium/index/repositories/projections.py` | **Modify** | After upsert/remove, keep FTS rows in the same transaction |
| `src/studium/index/search/__init__.py` | **Create** | Public lexical search API |
| `src/studium/index/search/models.py` | **Create** | Query/result types for lookup + lexical hits |
| `src/studium/index/search/weights.py` | **Create** | Initial field-weight constants |
| `src/studium/index/search/lookup.py` | **Create** | Deterministic ID/title/alias resolution + collision detection |
| `src/studium/index/search/fts.py` | **Create** | Weighted concept/module FTS search |
| `src/studium/index/search/service.py` | **Create** | Thin orchestrator: lookup first, else FTS (lexical-only) |
| `src/studium/index/__init__.py` | **Modify** | Export lookup/search entrypoints |
| `tests/index/search/` | **Create** | Normalization, lookup, weight, collision, sync tests |
| `README.md` | **Modify lightly** | Mention lexical search library API |

**Out of scope files:** embedding providers, vector backends, RRF fusion, recommendation assembler, CLI search commands (unless a tiny debug helper is useful; prefer library-only like B03).

---

### 3. Step-by-step implementation sequence

#### Step 1 — Matching normalization
- Extend `normalize_for_lookup(text)` per Technical Plan §4.8:
  - Unicode NFKC (or NFC) + casefold
  - trim / collapse whitespace
  - `_` and `-` → space
  - strip light surrounding punctuation
- **Do not** stem or rewrite technical terms
- Keep `normalize_title` as a thin wrapper or migrate call sites carefully
- Unit-test stability and non-mutation of originals

#### Step 2 — Enrich materialized search documents
B03 currently joins title+aliases+overview into one `document_text`. For weighted FTS, materialize **fielded** content:
- Concept: `title`, `aliases`, `domains`, `overview` (plaintext)
- Module: `title`, `type`, `focus`, `body` (empty OK until richer body extraction exists)
- Store structured JSON in `field_weights_json` **or** dedicated columns; keep a concatenated `document_text` for debugging if useful
- Projection hash must include the fielded representation so content changes invalidate correctly

#### Step 3 — Schema bump + FTS5 virtual tables
- Bump `INDEX_SCHEMA_VERSION` to **3** (incompatible; rebuild required — already policy)
- Create FTS5 tables, e.g.:
  - `concept_fts(concept_id UNINDEXED, title, aliases, domains, overview)`
  - `module_fts(module_id UNINDEXED, concept_id UNINDEXED, title, type, focus, body)`
- Tokenizer recommendation: `unicode61` with **no** porter stemming (tunable later)
- Wire creation into `initialize_index` / `rebuild_index`
- Prefer **external-content or explicit sync** from materialized docs so projection delete removes FTS rows in the same transaction

#### Step 4 — Keep FTS synchronized with projections
- On `upsert_concept_projection`: upsert FTS rows for concept + modules
- On `remove_concept_projection` / invalidation: delete FTS rows for that concept/modules
- Add tests that valid→invalid and file delete leave no searchable FTS residue

#### Step 5 — Deterministic lookup API
```text
resolve_concept_identity(engine, query_text) -> IdentityResolution
```
- Try exact ID
- Else normalized title (unique / none / multi)
- Else approved aliases (unique / ambiguous collision / none)
- Return match type: `stable_id` | `canonical_title` | `approved_alias` + collision list when ambiguous

#### Step 6 — Weighted FTS search API
```text
search_concepts_fts(engine, query, *, limit, filters?) -> list[LexicalConceptHit]
search_modules_fts(engine, query, *, limit, filters?) -> list[LexicalModuleHit]
```
- Escape/sanitize user query for FTS MATCH safely
- Apply BM25 with column weights (Technical Plan priority order)
- Module hits must include `concept_id`, module id/title, and available location fields (`heading`/`anchor` when present)
- Attach diagnostics: matched fields, bm25/component score, rank

#### Step 7 — Thin lexical search facade
```text
search_concepts_lexical(engine, query) -> LexicalSearchResult
```
- If deterministic identity resolves uniquely → `resolution_state=exact_match`
- If alias collision → `ambiguous_results` (still include ranked FTS optionally or separately)
- Else run concept (+ optional module) FTS → `related_results` / `no_results`
- **Do not** invent hybrid fusion here

#### Step 8 — Tests + verify
Cover Branch Plan checklist. Run ruff/pyright/pytest.

---

### 4. Data model / schema changes

| Change | Detail |
|--------|--------|
| `INDEX_SCHEMA_VERSION` | **3** |
| FTS5 virtual tables | `concept_fts`, `module_fts` (names TBD) |
| Materialized search docs | Fielded text / weights metadata (enrich existing tables) |
| Concept-note Markdown schema | No change |
| Full `ConceptSearchQuery`/`ConceptSearchResult` | **Defer full contract to B07**; B04 uses smaller lexical-specific models that B07 can wrap |

Initial field weights (constants, tunable later):

| Field | Relative priority |
|-------|-------------------|
| concept title | highest |
| aliases | very high |
| module title | high |
| concept overview | medium |
| domains | lower |
| module body/focus | lowest |

---

### 5. Important functions / classes / modules

| Symbol | Role |
|--------|------|
| `normalize_for_lookup(...)` | Matching normalization |
| `resolve_concept_identity(...)` | Tier 0 deterministic resolution |
| `search_concepts_fts(...)` / `search_modules_fts(...)` | Weighted FTS |
| `search_concepts_lexical(...)` | Thin lookup-then-FTS facade |
| `sync_concept_fts_rows(...)` / delete helpers | Keep FTS aligned with projections |
| `LexicalSearchResult` / `IdentityResolution` / hit models | Typed outputs + diagnostics |
| `FTS_FIELD_WEIGHTS` | Initial weight constants |

---

### 6. Tests / verification steps

| Scenario | Expectation |
|----------|-------------|
| Normalization stability | same inputs → same normalized form; originals unchanged |
| Exact ID | resolves `stable_id` |
| Normalized title | unique title → exact; no false ID claim |
| Approved alias | unique alias → `approved_alias` |
| Alias collision | multiple concepts → ambiguous, not unique identity |
| Title weight | title match ranks above overview-only match |
| Alias weight | alias match ranks above overview-only match |
| Overview / domain lexical | non-exact queries still retrieve |
| Module title / body | module hit includes parent concept + location |
| Sync update | changed note updates FTS content |
| Sync delete / invalid | FTS rows gone; not searchable |
| Query escaping | odd punctuation does not break MATCH |

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
| FTS treated as identity | Keep deterministic path separate; never auto-claim unique identity from BM25 |
| Aggressive stemming breaks tech terms | `unicode61`, no porter; document choice |
| Flat B03 `document_text` cannot weight fields | Enrich materialization to fielded columns |
| FTS drifts from projections | Same-transaction upsert/delete with projection lifecycle |
| Overbuilding B07 search contract early | Lexical-only models now; hybrid/RRF later |
| Empty module bodies | Still index title/type/focus; body optional |
| User query FTS injection / syntax errors | Escape tokens; fall back gracefully |

**Assumptions**
- B03 sync/projection is stable and remains the writer of search documents
- Invalid/duplicate notes already lack searchable projections (B03) — FTS must follow that
- Initial weights are good enough for a baseline; evaluation harness may retune later
- Full hybrid `ConceptSearchService` waits for B05–B07

---

### 8. Questions or decisions needed before implementation

| # | Decision | Recommendation |
|---|----------|----------------|
| 1 | Schema version | **Bump to 3** for FTS virtual tables + any search-doc shape change |
| 2 | FTS content strategy | **Explicit sync from materialized docs inside projection transactions** (clearer than triggers alone) |
| 3 | Tokenizer | **`unicode61` without porter stemming** |
| 4 | Search API shape in B04 | **Lexical-specific models + thin facade**; defer full `ConceptSearchQuery`/`ConceptSearchResult` to B07 |
| 5 | Alias collision behavior | **Return all matches as ambiguous**; do not pick a winner |
| 6 | Module body text | **Use focus/empty for now** unless a small Scaffold Modules section extractor is cheap; avoid parser rewrite |
| 7 | CLI | **Library API only** (align with B03 / B13 later) |
| 8 | Filters (domain/type/status) | **Support simple post-filters in B04 if cheap**; full filter surface can wait for B07 |

### Plan Review Notes

Decisions recorded (2026-07-30):

1. Schema version → **bump to 3** (approved)
2. FTS content strategy → **explicit sync in projection transactions** (approved)
3. Tokenizer → **`unicode61` without porter stemming** (approved — FTS tokenization is independent of Python `normalize_for_lookup`; stemming stays off so technical titles are not rewritten)
4. Search API shape → **lexical-specific models + thin facade**; full contract deferred to B07 (approved)
5. Alias collisions → **ambiguous, no winner** (approved)
6. Module body → **focus/empty for now** (approved)
7. CLI → **library API only** (approved)
8. Filters → **simple post-filters only if cheap**; fuller filters later (approved)

### Approved to Implement?

- [x] Yes
    
- [ ] No, revise plan first
    

---

## Implemented search APIs (Steps 5–7)

These are the public lexical-search entrypoints shipped in B04. Comments below walk
through **deterministic identity** vs **weighted FTS** so the two tiers stay mentally
separate: Tier 0 never claims identity from BM25 ranks, and Tier 1a never skips
normalization/lookup when an exact ID/title/alias exists.

### Step 5 — Deterministic identity lookup

```python
def resolve_concept_identity(engine: Engine, query_text: str) -> IdentityResolution:
    """Tier 0: resolve a query to zero, one, or many concepts — without FTS.

    This path answers “do we already know exactly which concept this string
    refers to?” It uses equality on stored identity columns, not relevance
    ranking. BM25 is intentionally not consulted here so a fuzzy lexical hit
    can never be mistaken for a stable identity.

    Resolution order (first successful step wins; later steps are skipped):

    1. Exact ``concept_id``
       - Compare ``query_text.strip()`` to ``concepts.concept_id``.
       - No normalization beyond strip: IDs are opaque stable keys.
       - Unique hit → ``ExactMatchType.STABLE_ID``.

    2. Normalized canonical title
       - Compute ``normalized_query = normalize_for_lookup(query_text)``.
       - Matching-only transforms (display strings in the vault are unchanged):
         Unicode NFKC, casefold, trim/collapse whitespace, ``_``/``-`` → space,
         light surrounding punctuation stripped. No stemming.
       - Look up ``concepts.normalized_title == normalized_query``.
       - One row → ``CANONICAL_TITLE`` unique identity.
       - Multiple rows → same match type on each, ``is_ambiguous=True``
         (do not pick a winner).

    3. Approved alias equality
       - Only if title lookup found nothing.
       - Look up ``concept_aliases.normalized_alias == normalized_query``.
       - Deduplicate by ``concept_id`` (a concept may list the same alias twice).
       - One concept → ``APPROVED_ALIAS`` (includes the stored display ``alias``).
       - Multiple concepts sharing the normalized alias → ambiguous collision;
         return **all** matches; never auto-select one.

    Empty / whitespace-only queries after normalization yield no matches
    (unless step 1 hit an exact ID).

    Return shape (``IdentityResolution``):
    - ``query`` / ``normalized_query`` — original + matching form used for
      title/alias equality.
    - ``matches`` — zero or more ``IdentityMatch`` rows.
    - ``is_ambiguous`` — True when more than one concept shares the title/alias.
    - Helpers: ``is_unique``, ``unique_match`` (None unless exactly one match).
    """
```

### Step 6 — Weighted FTS search

```python
def search_concepts_fts(
    engine: Engine,
    query_text: str,
    *,
    limit: int = 20,
) -> list[LexicalConceptHit]:
    """Tier 1a (concepts): rank materialized FTS rows with weighted BM25.

    Preconditions / sync:
    - Rows live in FTS5 virtual table ``concept_fts`` (schema v3).
    - Columns: ``concept_id`` (UNINDEXED), ``title``, ``aliases``, ``domains``,
      ``overview``.
    - Projection upsert/delete (same SQLite transaction as concept projection)
      keeps FTS in lockstep with searchable concepts. Invalid/duplicate/removed
      notes have no FTS residue.

    Query construction (``build_fts_match_query``):
    - Split user text on non-word characters.
    - Quote each token and escape embedded ``"`` → ``""`` so punctuation cannot
      inject FTS operators.
    - AND tokens together. Empty token list → no MATCH; return ``[]``.

    Ranking:
    - ``bm25(concept_fts, title_w, aliases_w, domains_w, overview_w)``.
    - Initial weights (tunable constants): title > aliases > overview > domains.
    - SQLite BM25: **lower score is better**; results ``ORDER BY score``.
    - Tokenizer: ``unicode61`` **without** porter stemming (FTS-side only;
      independent of Python ``normalize_for_lookup``).

    Each hit includes:
    - ``concept_id``, ``canonical_title`` (from concept row when present),
    - ``rank`` (1-based), ``score`` (BM25),
    - ``matched_fields`` (diagnostic: which indexed fields contain query tokens),
    - ``overview_excerpt``, ``concept_type``, ``domains``.

    This API never asserts unique identity. A strong title hit is still only a
    ranked lexical candidate unless Tier 0 already resolved the query.
    """


def search_modules_fts(
    engine: Engine,
    query_text: str,
    *,
    limit: int = 20,
) -> list[LexicalModuleHit]:
    """Tier 1a (modules): same MATCH/escape/BM25 pattern over ``module_fts``.

    Columns: ``module_id`` / ``concept_id`` (UNINDEXED), ``title``, ``type``,
    ``focus``, ``body``. Body may be empty in B04 (focus/empty materialization);
    title/type/focus still index.

    Weights: module title > focus > type > body.

    Hits always carry parent ``concept_id`` (and ``parent_canonical_title`` when
    available) plus optional ``heading`` / ``anchor`` from the scaffold-module
    projection so callers can deep-link into a note without a second join pass.
    """
```

### Step 7 — Thin lexical facade

```python
def search_concepts_lexical(
    engine: Engine,
    query_text: str,
    *,
    concept_limit: int = 20,
    module_limit: int = 20,
    include_modules: bool = True,
) -> LexicalSearchResult:
    """Compose Tier 0 then Tier 1a. No hybrid fusion, vectors, or LLM (→ B07+).

    Control flow:

    1. ``identity = resolve_concept_identity(engine, query_text)``

    2. If ``identity.is_unique``:
       - ``resolution_state = exact_match``
       - Return immediately with empty ``concept_hits`` / ``module_hits``.
       - Exact ID/title/alias already answered the question; running FTS would
         only add noise and risk treating ranks as identity.

    3. If ``identity.is_ambiguous``:
       - ``resolution_state = ambiguous_results``
       - Keep all deterministic ``matches``; do not pick a winner.
       - Do not run FTS in this facade path (collision is an identity problem,
         not a ranking problem). Caller may still call ``search_*_fts`` separately
         if they want ranked context.

    4. Otherwise (no deterministic match):
       - Run ``search_concepts_fts(..., limit=concept_limit)``.
       - Optionally ``search_modules_fts(..., limit=module_limit)``.
       - If any hits → ``related_results``; else ``no_results``.

    ``LexicalSearchResult`` packages:
    - ``resolution_state`` — which branch above fired,
    - ``identity`` — always present (even when empty), for diagnostics,
    - ``concept_hits`` / ``module_hits`` — FTS ranks only on the related path,
    - ``warnings`` — e.g. alias/title collision explanation,
    - ``diagnostics`` — normalized query, match counts, FTS hit counts.

    B07 can wrap this facade (plus vectors/RRF) into the full
    ``ConceptSearchService`` contract without changing these lexical primitives.
    """
```

