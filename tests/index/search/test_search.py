"""Deterministic lookup and weighted FTS search tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Engine, text

from studium.index import (
    ExactMatchType,
    ResolutionState,
    begin_connection,
    resolve_concept_identity,
    search_concepts_fts,
    search_concepts_lexical,
    search_modules_fts,
    sync_vault,
)
from studium.index.config import IndexConfig
from studium.index.repositories import fts
from studium.index.search.weights import CONCEPT_FTS_WEIGHTS, MODULE_FTS_WEIGHTS
from studium.vault import Vault
from tests.index.sync.helpers import write_concept_note


@pytest.fixture
def vault(vault_root: Path) -> Vault:
    return Vault(vault_root)


def _sync_two_concepts(
    vault: Vault,
    vault_root: Path,
    engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/sgd.md",
        id="concept_sgd_aaaaaa",
        canonical_title="Stochastic Gradient Descent",
        overview="An iterative optimizer for machine learning models.",
    )
    # Inject alias via rewriting the file after helper write is awkward;
    # use a second note and patch aliases through a custom write.
    content = (vault_root / "concepts/sgd.md").read_text(encoding="utf-8")
    content = content.replace("aliases: []", "aliases:\n  - SGD")
    (vault_root / "concepts/sgd.md").write_text(content, encoding="utf-8")

    write_concept_note(
        vault_root,
        "concepts/gd.md",
        id="concept_gd_bbbbbb",
        canonical_title="Gradient Descent",
        overview="Batch gradient updates for convex objectives.",
    )
    sync_vault(vault, engine, index_config)


def test_exact_id_and_title_and_alias_lookup(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    _sync_two_concepts(vault, vault_root, initialized_engine, index_config)

    by_id = resolve_concept_identity(initialized_engine, "concept_sgd_aaaaaa")
    assert by_id.is_unique
    assert by_id.unique_match is not None
    assert by_id.unique_match.match_type == ExactMatchType.STABLE_ID

    by_title = resolve_concept_identity(initialized_engine, "stochastic gradient-descent")
    assert by_title.is_unique
    assert by_title.unique_match is not None
    assert by_title.unique_match.match_type == ExactMatchType.CANONICAL_TITLE

    by_alias = resolve_concept_identity(initialized_engine, "SGD")
    assert by_alias.is_unique
    assert by_alias.unique_match is not None
    assert by_alias.unique_match.match_type == ExactMatchType.APPROVED_ALIAS


def test_alias_collision_is_ambiguous(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root, "concepts/a.md", id="concept_a_aaaaaa", canonical_title="Alpha One"
    )
    write_concept_note(
        vault_root, "concepts/b.md", id="concept_b_bbbbbb", canonical_title="Alpha Two"
    )
    for relative in ("concepts/a.md", "concepts/b.md"):
        path = vault_root / relative
        text_value = path.read_text(encoding="utf-8")
        path.write_text(
            text_value.replace("aliases: []", "aliases:\n  - SharedAlias"),
            encoding="utf-8",
        )
    sync_vault(vault, initialized_engine, index_config)

    resolution = resolve_concept_identity(initialized_engine, "SharedAlias")
    assert resolution.is_ambiguous
    assert len(resolution.matches) == 2
    result = search_concepts_lexical(initialized_engine, "SharedAlias")
    assert result.resolution_state == ResolutionState.AMBIGUOUS_RESULTS


def test_title_outweighs_overview_only_match(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/title.md",
        id="concept_title_aaa",
        canonical_title="Backpropagation",
        overview="Unrelated filler about oranges.",
    )
    write_concept_note(
        vault_root,
        "concepts/overview.md",
        id="concept_overview_bbb",
        canonical_title="Neural Networks",
        overview="Uses backpropagation when training deep models.",
    )
    sync_vault(vault, initialized_engine, index_config)

    hits = search_concepts_fts(initialized_engine, "backpropagation", limit=5)
    assert hits
    assert hits[0].concept_id == "concept_title_aaa"
    assert hits[0].rank == 1


def test_module_fts_includes_parent_concept(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/mod.md",
        id="concept_mod_cccccc",
        canonical_title="Expectation Maximization",
        modules_yaml=(
            "scaffold_modules:\n"
            "  - id: module_em_e_step\n"
            "    type: derivation\n"
            "    title: E-Step Derivation\n"
            "    status: scaffolded\n"
            "    origin:\n"
            "    focus: soft assignment update\n"
        ),
    )
    sync_vault(vault, initialized_engine, index_config)
    hits = search_modules_fts(initialized_engine, "E-Step", limit=5)
    assert hits
    assert hits[0].concept_id == "concept_mod_cccccc"
    assert hits[0].parent_canonical_title == "Expectation Maximization"


def test_fts_removed_when_concept_invalidated(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/x.md",
        id="concept_x_dddddd",
        canonical_title="UniqueZebraTerm",
        overview="UniqueZebraTerm overview text.",
    )
    sync_vault(vault, initialized_engine, index_config)
    assert search_concepts_fts(initialized_engine, "UniqueZebraTerm")

    (vault_root / "concepts/x.md").write_text("broken\n", encoding="utf-8")
    sync_vault(vault, initialized_engine, index_config)
    assert search_concepts_fts(initialized_engine, "UniqueZebraTerm") == []
    with begin_connection(initialized_engine) as connection:
        rows = connection.execute(
            text("SELECT concept_id FROM concept_fts WHERE concept_id = :cid"),
            {"cid": "concept_x_dddddd"},
        ).all()
        assert rows == []


def test_lexical_facade_exact_then_related(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    _sync_two_concepts(vault, vault_root, initialized_engine, index_config)
    exact = search_concepts_lexical(initialized_engine, "concept_sgd_aaaaaa")
    assert exact.resolution_state == ResolutionState.EXACT_MATCH

    related = search_concepts_lexical(initialized_engine, "optimizer machine learning")
    assert related.resolution_state == ResolutionState.RELATED_RESULTS
    assert related.concept_hits


def test_alias_hyphen_underscore_variants_do_not_break_sync(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/variants.md",
        id="concept_var_eeeeee",
        canonical_title="Variant Concept",
    )
    path = vault_root / "concepts/variants.md"
    text_value = path.read_text(encoding="utf-8")
    path.write_text(
        text_value.replace("aliases: []", "aliases:\n  - foo-bar\n  - foo_bar"),
        encoding="utf-8",
    )
    report = sync_vault(vault, initialized_engine, index_config)
    assert not report.errors

    resolution = resolve_concept_identity(initialized_engine, "foo-bar")
    assert resolution.is_unique
    assert resolution.unique_match is not None
    assert resolution.unique_match.concept_id == "concept_var_eeeeee"

    with begin_connection(initialized_engine) as connection:
        aliases_text = connection.execute(
            text("SELECT aliases FROM concept_fts WHERE concept_id = :cid"),
            {"cid": "concept_var_eeeeee"},
        ).scalar_one()
    # Only the first display form is indexed (no duplicate token inflation).
    assert aliases_text == "foo-bar"


def test_fts_tie_break_is_stable_by_concept_id(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    # Same overview-only term → equal BM25; secondary ORDER BY concept_id.
    write_concept_note(
        vault_root,
        "concepts/z.md",
        id="concept_z_zzzzzz",
        canonical_title="Concept Z",
        overview="sharedtiebreakterm appears once.",
    )
    write_concept_note(
        vault_root,
        "concepts/a.md",
        id="concept_a_aaaaaa",
        canonical_title="Concept A",
        overview="sharedtiebreakterm appears once.",
    )
    sync_vault(vault, initialized_engine, index_config)

    query = "sharedtiebreakterm"
    first = [hit.concept_id for hit in search_concepts_fts(initialized_engine, query)]
    # Unrelated metadata-style re-sync should not reshuffle ties.
    sync_vault(vault, initialized_engine, index_config)
    second = [hit.concept_id for hit in search_concepts_fts(initialized_engine, query)]
    assert first == second == ["concept_a_aaaaaa", "concept_z_zzzzzz"]


def test_bm25_weight_tuples_include_unindexed_placeholders() -> None:
    assert CONCEPT_FTS_WEIGHTS[0] == 0.0
    assert CONCEPT_FTS_WEIGHTS[1:] == (10.0, 8.0, 2.0, 4.0)
    assert MODULE_FTS_WEIGHTS[:2] == (0.0, 0.0)
    assert MODULE_FTS_WEIGHTS[2:] == (8.0, 2.0, 3.0, 1.0)


def test_fts_tables_created_on_initialize(initialized_engine: Engine) -> None:
    with begin_connection(initialized_engine) as connection:
        fts.create_fts_tables(connection)  # idempotent
        names = {
            row[0]
            for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
        assert "concept_fts" in names
        assert "module_fts" in names
