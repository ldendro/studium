## 1. Goal

This branch exists to amend the phase 1 storage schema for phase 2 relationship and source metadata. We introduce indexing, validation, querying, and reasoning over a finalized metadata model, so we must update the model consisting of adding relationship fields (learning_role, confidence, status), defining the learning_role enum, confidence values, relationship status as it pertains to the recommendation object, and other minor tweaks.  

---

## 3. Concepts I Need to Understand

List concepts I should understand before or during implementation.

- `[[Concept Name]]`
    
- `[[Concept Name]]`
    

Questions I should be able to answer:

---

## 4. Cursor Implementation Planning Prompt

Use this prompt to ask Cursor for a detailed implementation plan **before any code is generated**.

Cursor should not implement yet. The goal of this step is to produce a clear plan that I can review, question, and approve.

```text
We are planning the implementation for a single branch of Studium.

Do not implement code yet.

Project context:
Studium is an AI-assisted learning system built around Markdown/Obsidian-compatible notes, concept graphs, scaffold generation, source-aware RAG, local/source library processing, and agent-based note review.

Phase:
2

Branch:
Schema V2 Amendments

Branch goal:
Change the schema_version of the metadata to 2 after adding reqiored relationship fields (learning role, confidence, status) and successfully updating phase 1 pydnatic models, serializer behavior, and test fixtures/golden markdowns. 

Expected outcome:
The current setup works with the updated schema version, all previous and new tests addressing the new fields pass. 

Relevant context:
Within the Phase 2 - Concept Graph Core, the files 2 - Final Phase Roadmap, 3 - Technical Plan, and 4 - Branch Plan. Disregard 1 - Initial Phase Roadmap

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

Treat this as a **storage-schema bump**, not a migration feature. There are no durable Phase 1 user vaults; bump `schema_version` to `2` everywhere new notes are modeled, serialized, parsed, validated, and fixture-tested.

**In scope**
1. Extend `RelationshipMetadata` with required `learning_role`, `confidence`, and `status`.
2. Add enums for those three fields (values from Technical Plan §5.2–5.3).
3. Add optional typed `external_id` on `SourceMetadata` (`type` + `value`, both non-empty when present).
4. Change `ConceptNoteMetadata.schema_version` from `Literal[1] = 1` → `Literal[2] = 2`.
5. Update canonical YAML field ordering so serializers emit the new keys in a stable order.
6. Update all Phase 1 fixtures, test helpers, and golden Markdown so the suite is fully schema-v2.
7. Keep relationship **body projection** unchanged (wikilinks only); new fields live in YAML only.

**Out of scope for B01**
- SQLite index / repositories (B02+)
- Recommendation objects, rejected/deferred recommendation history
- Runtime migration of old v1 notes
- Graph queries, LLM tasks, confidence aggregation for recommendations

**Design principles**
- Prefer Pydantic + `StrEnum` for validation; avoid inventing a separate migration layer.
- Name relationship status enum distinctly (`RelationshipStatus`) so it does not collide with note `status` (`NoteStatus`).
- Confidence remains `low|medium|high` only — never `confirmed` (confirmation is status).
- Rejected / deferred are **not** relationship statuses.

---

### 2. Files likely to be created or modified

| Path | Action | Role |
|------|--------|------|
| `src/studium/schemas/enums.py` | **Modify** | Add `LearningRole`, `RelationshipConfidence`, `RelationshipStatus` |
| `src/studium/schemas/relationship.py` | **Modify** | Require new relationship fields |
| `src/studium/schemas/source.py` | **Modify** | Add optional nested `external_id` |
| `src/studium/schemas/concept_note.py` | **Modify** | `schema_version: Literal[2] = 2` |
| `src/studium/schemas/canonical.py` | **Modify** | Extend `RELATIONSHIP_FIELD_ORDER`, `SOURCE_FIELD_ORDER` |
| `src/studium/schemas/__init__.py` | **Modify** | Export new enums / nested model |
| `tests/schemas/test_relationship.py` | **Modify** | Cover new required fields + invalid enums |
| `tests/schemas/test_concept_note.py` | **Modify** | Expect schema v2 |
| `tests/schemas/helpers.py` | **Modify** | Default `schema_version: 2`; relationship helpers |
| `tests/schemas/test_learning_encounter.py` / source tests | **Modify / Create** | `external_id` validation |
| `tests/serialization/helpers.py` | **Modify** | schema v2 + complete relationship shape |
| `tests/serialization/test_*.py` | **Modify** | Golden YAML expectations |
| `tests/parsing/helpers.py` | **Modify** | Frontmatter templates → v2 |
| `tests/fixtures/parsing/*.md` | **Modify** | `schema_version: 2`; relationship fields where present |
| `tests/fixtures/test_vault/concepts/*.md` | **Modify** | Same |
| `tests/writes/**`, `tests/validation/**`, `tests/cli/**` | **Modify as needed** | Any hardcoded v1 / incomplete relationships |
| Schema / Phase docs (if present in repo) | **Modify lightly** | Reflect v2 shape; Branch Plan success criteria already list this |

**No new packages** expected. Optional small nested model file only if preferred over defining `ExternalId` inline in `source.py` — recommend **inline nested model in `source.py`** (or tiny `ExternalIdentifier` class in the same file).

---

### 3. Step-by-step implementation sequence

#### Step 1 — Enums
Add to `enums.py`:

```text
LearningRole:
  mathematical_prerequisite
  conceptual_prerequisite
  implementation_prerequisite
  foundational_theory
  broader_parent_concept
  specialized_child_concept
  alternative_variant
  comparison_target
  supporting_concept
  application_context

RelationshipConfidence:
  low
  medium
  high

RelationshipStatus:
  agent_suggested
  user_confirmed
```

#### Step 2 — Relationship model
Update `RelationshipMetadata`:

```text
relationship_type   (existing, required)
target_id           (optional)
target_title        (required, min_length=1)
vault_status        (existing, required)
learning_role       (LearningRole, required)
confidence          (RelationshipConfidence, required)
status              (RelationshipStatus, required)
```

Field order for YAML (update `RELATIONSHIP_FIELD_ORDER`):

```text
relationship_type, target_id, target_title, vault_status,
learning_role, confidence, status
```

(Matches Technical Plan example: type → ids/title → vault_status → learning_role → confidence → status.)

#### Step 3 — Source `external_id`
Add nested model, e.g.:

```text
ExternalId:
  type: str (min_length=1)
  value: str (min_length=1)
```

On `SourceMetadata`: `external_id: ExternalId | None = None`

Update `SOURCE_FIELD_ORDER` to append `external_id` after `link`.

Validation: if `external_id` is present, both fields non-empty (enforced by nested model). Empty string type/value → ValidationError. Omit / `null` when absent.

#### Step 4 — Schema version bump
- `ConceptNoteMetadata.schema_version: Literal[2] = 2`
- Default in all test helpers / fixtures → `2`
- No dual-version accept path in B01 (v1 notes fail schema validation by design; no migration)

#### Step 5 — Serialization / parsing
- Serializer already dumps via `model_dump` + canonical key orders; updating orders + models is enough for YAML round-trip.
- Body relationship projection (`serialization/relationships.py`) unchanged — still only wikilinks by type.
- Create-from-title path creates empty `relationships: []`, so no create-path defaulting of learning_role needed unless fixtures construct relationships.

#### Step 6 — Fixtures and goldens
For every committed Markdown fixture and string template:
1. Set `schema_version: 2`.
2. Where a relationship entry exists (e.g. `concept_with_missing_relationship_target.md`), add required fields, e.g.:

```yaml
learning_role: mathematical_prerequisite
confidence: high
status: agent_suggested
```

3. Optionally add one fixture/source example with `external_id` for parse/serialize coverage (can be a unit test dict instead of a vault fixture).

#### Step 7 — Tests + verify
- Expand relationship / source schema tests.
- Fix any broken Phase 1 tests from the version bump.
- Run `uv run ruff check .`, `uv run pyright`, `uv run pytest`.

---

### 4. Data model or schema changes

| Topic | Change |
|-------|--------|
| `schema_version` | `1` → `2` (Literal + default) |
| `RelationshipMetadata` | +`learning_role`, +`confidence`, +`status` (all required) |
| New enums | `LearningRole`, `RelationshipConfidence`, `RelationshipStatus` |
| `SourceMetadata` | + optional `external_id: {type, value}` |
| Canonical orders | Relationship + source field tuples |
| Index / SQLite | **None** (later branches) |
| Recommendation models | **None** (later branches) |

**Naming note:** YAML key remains `status` on relationships (per roadmap). Python field is also `status`, typed as `RelationshipStatus`. Note-level `status` remains `NoteStatus`. No rename of the YAML key.

---

### 5. Important functions / classes / modules

| Symbol | Role |
|--------|------|
| `LearningRole` | Enum of learning purposes for targets |
| `RelationshipConfidence` | `low` / `medium` / `high` |
| `RelationshipStatus` | `agent_suggested` / `user_confirmed` |
| `RelationshipMetadata` | Durable relationship shape (v2) |
| `ExternalId` (nested) | Typed optional source identifier |
| `SourceMetadata.external_id` | Optional attachment point |
| `ConceptNoteMetadata.schema_version` | Fixed at 2 |
| `RELATIONSHIP_FIELD_ORDER` / `SOURCE_FIELD_ORDER` | Stable YAML emission |
| `serialize_metadata_to_yaml` | Unchanged API; picks up new fields via dump + order |

No new CLI commands. No new validation-operation modes.

---

### 6. Tests / verification steps

**Schema unit tests**
- Valid relationship with all v2 fields.
- Missing `learning_role` / `confidence` / `status` → `ValidationError`.
- Invalid enum values → `ValidationError`.
- Empty `learning_role` / empty strings rejected.
- `target_id` still optional for `missing` / `unresolved`.
- `external_id` omitted OK; present with type+value OK; empty type or value fails.
- `ConceptNoteMetadata` accepts `schema_version: 2`; rejects `1` (and other ints).

**Serialization / parsing**
- Round-trip metadata with relationships includes new keys in canonical order.
- Golden / fixture Markdown with relationships parses under PARSE.
- Vault fixture `concept_with_missing_relationship_target` still validates (warnings/criticals unchanged aside from schema bump).

**Regression**
- Full Phase 1 suite: schemas, parsing, serialization, validation, writes, CLI.
- `validate-vault` on `tests/fixtures/test_vault` still exits `1` due to intentional invalid YAML fixture (not due to missing relationship fields).

**Commands**
```bash
uv run ruff check .
uv run pyright
uv run pytest
```

---

### 7. Risks, edge cases, or assumptions

| Risk | Mitigation |
|------|------------|
| Field name `status` ambiguity (note vs relationship) | Distinct Python enums; document in tests |
| Incomplete fixture updates leave flaky suite | Grep for `schema_version: 1` and bare relationship blocks before finish |
| Serializer omits new keys if order tuples not updated | Update `RELATIONSHIP_FIELD_ORDER` / `SOURCE_FIELD_ORDER` in same PR |
| Temptation to accept both v1 and v2 | Explicitly reject dual-version; no migration in B01 |
| Putting `rejected`/`deferred` in relationship status | Do not add; recommendation history is later |
| `external_id.type` as free string vs enum | Follow Technical Plan: flexible string types (`doi`, `isbn`, …), not a closed enum yet |
| Learning role vs relationship type duplication | No cross-field consistency checks in B01; roles are independent enums |

**Assumptions**
- Technical Plan §5.2–5.4 is the source of truth for enum values.
- Create-concept continues to emit empty relationships; defaults for new fields only matter when constructing relationship objects in tests/fixtures.
- Phase 1 docs that historically say `schema_version: 1` do not all need rewriting; update living schema references if/where the repo keeps them, and rely on Phase 2 docs + code as current truth.
- No architecture change beyond storage models.

---

### 8. Questions or decisions needed before implementation

| # | Decision | Recommendation |
|---|----------|----------------|
| 1 | Exact `LearningRole` values | **Use Technical Plan §5.3 list as-is** (10 values). |
| 2 | Relationship confidence values | **`low` / `medium` / `high` only** — no `confirmed`. |
| 3 | Persistent relationship statuses | **`agent_suggested` / `user_confirmed` only**. |
| 4 | Accept schema v1 notes? | **No** — `Literal[2]` only; update all fixtures. |
| 5 | `external_id.type` closed enum? | **No for B01** — non-empty free string. |
| 6 | Default values when constructing relationships in tests | Prefer **explicit** values in helpers (e.g. `supporting_concept` + `high` + `agent_suggested`) rather than model defaults, so requiredness stays honest. Optional model defaults only if you want create-time convenience later — recommend **no defaults** on the three required fields. |
| 7 | YAML key for relationship status | Keep **`status`** (roadmap); Python type `RelationshipStatus`. |
| 8 | Docs update scope | Update branch doc + any active schema reference used by the team; do not rewrite archived Phase 1 history unless you want consistency. |

### Plan Review Notes

Decisions 1–7 approved as recommended (2026-07-28). Decision 8 left as light docs: branch plan marked approved; no Phase 1 history rewrite.

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