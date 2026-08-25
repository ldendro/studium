## 1. Goal

Implement one-hop graph queries over indexed relationships (including derived inverses) and structured learning-encounter comparison via source/encounter fingerprints — without multi-hop traversal or source-content analysis.

---

## 2. Branch Context

### Main System Area

- Relationship / prerequisite / parent-child / variant lookup
- Source encounter recognition and enrichment detection
- Compact graph context for later reasoning

### Branch Dependencies

- P2-B02 / P2-B03 (relationships + learning_encounters tables and sync projection)

### Risks / Things to Watch

- Inverses must be derived, never duplicated in SQLite
- Fingerprints must be stable and metadata-only
- Previously `fingerprint` was always `None` at projection time

---

## 3. Concepts I Need to Understand

- `[[Derived inverse relationships]]` — e.g. `depends_on` ↔ `prerequisite_for`
- `[[Source fingerprint vs encounter fingerprint]]` — source identity vs unit/section-aware encounter
- `[[Encounter outcomes]]` — exact / enrich / new unit / different / ambiguous

Questions I should be able to answer:

- Why must inverses not be persisted?
- When is enrichment preferred over “new unit”?
- Why is typed external ID the highest-priority source identity signal?

---

## 4. Cursor Implementation Planning Prompt

_(See Branch Plan B08 and Technical Plan §§4.16–4.17.)_

---

## 5. Cursor Implementation Plan

### Summary of approach

1. Package `studium.index.graph`
2. Graph APIs: direct, grouped, prerequisites, parent/child/variant, one-hop, derive inverse
3. Encounter APIs: normalize, fingerprints, `compare_learning_encounter` (five outcomes)
4. Wire encounter fingerprints into sync `project.py`
5. Repository helper `list_relationships_for_target`

### Files created / modified

| Path | Role |
|------|------|
| `src/studium/index/graph/` | models, inverses, queries, encounters |
| `src/studium/index/repositories/relationships.py` | `list_relationships_for_target` |
| `src/studium/index/sync/project.py` | persist encounter fingerprints |
| `tests/index/graph/test_graph.py` | inverses + outcome coverage |

### Approved to Implement?

- [x] Yes (implemented 2026-08-10)

---

## 6. Implementation Notes

### Shipped

- Inverse map covers depends_on/prerequisite_for, parent/child, and symmetric related/contrast/variant
- Encounter fingerprints hashed from normalized metadata; stored on sync
- Outcomes: `exact_same_encounter`, `same_source_enrich_existing`, `same_source_new_unit`, `different_source`, `ambiguous`
- Schema: **no bump** (fingerprint column already existed)

### Out of scope

- Multi-hop graph reasoning
- Source content contribution inference
- Recommendation payloads that consume encounters (B11)

---
