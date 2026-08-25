"""Create the deterministic vault used by the bundled positive evaluation cases."""

from __future__ import annotations

import sys
from pathlib import Path

DOMAINS = ("math", "systems", "biology", "history", "ml")


def _note(index: int) -> str:
    domain = DOMAINS[(index - 1) % 5]
    title = f"Exact Title {index}" if index <= 5 else f"{domain.title()} Sample Topic {index}"
    overview = (
        f"Deterministic fixture for Phase 2 evaluation case p2-{index:03d}."
        if index <= 5
        else f"A sample learning query about {domain}, fixture number {index}."
    )
    return f"""---
id: concept_eval_{index:03d}
schema_version: 2
note_type: concept
concept_type: general_concept
concept_domains:
  - {domain}
canonical_title: {title}
aliases: []
status: scaffolded
review_status: not_submitted
vault_status: draft
learning_encounters:
  - source:
      type: studium
      title: Studium Phase 2 Evaluation Fixture
    role: primary
    contribution_status: pending
    content_attached: false
    content_id:
scaffold_modules: []
relationships: []
created_at: 2026-08-20T00:00:00Z
updated_at: 2026-08-20T00:00:00Z
---
# {title}

## Concept Overview

{overview}

## Prerequisites

## Module Index

## Scaffold Modules

## Related Concepts

## Open Questions / Gaps
"""


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: seed_vault.py VAULT_PATH")
    concepts = Path(sys.argv[1]).expanduser().resolve() / "concepts"
    concepts.mkdir(parents=True, exist_ok=True)
    for index in range(1, 16):
        (concepts / f"concept_eval_{index:03d}.md").write_text(_note(index), encoding="utf-8")


if __name__ == "__main__":
    main()
