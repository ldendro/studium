"""End-to-end synchronization behavior tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError

from studium.index import (
    SyncStatus,
    begin_connection,
    get_index_revision,
    rebuild_vault_index,
    sync_vault,
)
from studium.index.config import IndexConfig
from studium.index.repositories import concepts, indexed_files, invalid_records, projections
from studium.vault import Vault
from tests.index.sync.helpers import write_concept_note, write_invalid_note


@pytest.fixture
def vault(vault_root: Path) -> Vault:
    return Vault(vault_root)


def test_empty_vault_sync_is_no_changes(
    vault: Vault, initialized_engine: Engine, index_config: IndexConfig
) -> None:
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.status == SyncStatus.NO_CHANGES
    assert report.revision_before == report.revision_after == 0
    assert report.counts.scanned == 0


def test_first_valid_concept_creates_projection(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/sgd.md",
        id="concept_sgd_a1b2c3",
        canonical_title="Stochastic Gradient Descent",
        overview="Gradient-based optimizer.",
    )
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.status == SyncStatus.SUCCESS
    assert report.revision_after == 1
    assert report.counts.created == 1
    assert any(item.embedding_type == "concept_identity" for item in report.embedding_work)
    assert any(item.embedding_type == "concept_semantic" for item in report.embedding_work)

    with begin_connection(initialized_engine) as connection:
        row = concepts.get_concept(connection, "concept_sgd_a1b2c3")
        assert row is not None
        assert row["canonical_title"] == "Stochastic Gradient Descent"
        assert "optimizer" in (row["overview_plaintext"] or "")
        indexed = indexed_files.get_indexed_file(connection, "concepts/sgd.md")
        assert indexed is not None
        assert indexed["index_state"] == "valid"


def test_unchanged_resync_is_no_changes(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(vault_root, "concepts/a.md", id="concept_a_aaaaaa")
    first = sync_vault(vault, initialized_engine, index_config)
    second = sync_vault(vault, initialized_engine, index_config)
    assert first.status == SyncStatus.SUCCESS
    assert second.status == SyncStatus.NO_CHANGES
    assert second.revision_after == first.revision_after
    assert second.counts.unchanged == 1
    assert second.embedding_work == []


def test_metadata_change_updates_and_selective_embedding_work(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(
        vault_root,
        "concepts/a.md",
        id="concept_a_aaaaaa",
        canonical_title="Alpha",
        overview="First overview",
    )
    sync_vault(vault, initialized_engine, index_config)
    write_concept_note(
        vault_root,
        "concepts/a.md",
        id="concept_a_aaaaaa",
        canonical_title="Alpha",
        overview="Second overview only",
    )
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.status == SyncStatus.SUCCESS
    assert report.counts.updated == 1
    types = {item.embedding_type for item in report.embedding_work}
    assert types == {"concept_semantic"}


def test_file_move_updates_path_not_delete_create(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(vault_root, "concepts/old.md", id="concept_move_001")
    sync_vault(vault, initialized_engine, index_config)
    old = vault_root / "concepts/old.md"
    new = vault_root / "concepts/new.md"
    new.write_text(old.read_text(encoding="utf-8"), encoding="utf-8")
    old.unlink()

    report = sync_vault(vault, initialized_engine, index_config)
    assert report.counts.moved == 1
    assert report.counts.created == 0
    assert report.counts.removed == 0
    with begin_connection(initialized_engine) as connection:
        row = concepts.get_concept(connection, "concept_move_001")
        assert row is not None
        assert row["file_path"] == "concepts/new.md"
        assert indexed_files.get_indexed_file(connection, "concepts/old.md") is None
        assert indexed_files.get_indexed_file(connection, "concepts/new.md") is not None


def test_delete_removes_projection(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(vault_root, "concepts/a.md", id="concept_del_001")
    sync_vault(vault, initialized_engine, index_config)
    (vault_root / "concepts/a.md").unlink()
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.counts.removed == 1
    with begin_connection(initialized_engine) as connection:
        assert concepts.get_concept(connection, "concept_del_001") is None
        assert indexed_files.get_indexed_file(connection, "concepts/a.md") is None


def test_invalid_new_note_has_no_searchable_concept(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_invalid_note(vault_root, "concepts/bad.md", "not a concept note\n")
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.status == SyncStatus.PARTIAL_SUCCESS
    assert report.counts.invalid == 1
    with begin_connection(initialized_engine) as connection:
        assert concepts.list_concepts(connection) == []
        indexed = indexed_files.get_indexed_file(connection, "concepts/bad.md")
        assert indexed is not None
        assert indexed["index_state"] == "invalid"
        assert invalid_records.list_invalid_records(connection)


def test_valid_then_invalid_removes_searchable_projection(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(vault_root, "concepts/a.md", id="concept_vi_001")
    sync_vault(vault, initialized_engine, index_config)
    write_invalid_note(vault_root, "concepts/a.md", "---\nid: concept_vi_001\n---\n# Broken\n")
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.counts.invalid == 1
    with begin_connection(initialized_engine) as connection:
        assert concepts.get_concept(connection, "concept_vi_001") is None
        indexed = indexed_files.get_indexed_file(connection, "concepts/a.md")
        assert indexed is not None
        assert indexed["index_state"] == "invalid"


def test_invalid_then_valid_restores_projection(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_invalid_note(vault_root, "concepts/a.md", "broken")
    sync_vault(vault, initialized_engine, index_config)
    write_concept_note(vault_root, "concepts/a.md", id="concept_iv_001")
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.status == SyncStatus.SUCCESS
    assert report.counts.created == 1 or report.counts.updated == 1
    with begin_connection(initialized_engine) as connection:
        assert concepts.get_concept(connection, "concept_iv_001") is not None
        indexed = indexed_files.get_indexed_file(connection, "concepts/a.md")
        assert indexed is not None
        assert indexed["index_state"] == "valid"


def test_duplicate_ids_exclude_all(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(vault_root, "concepts/a.md", id="concept_dup_001", canonical_title="A")
    write_concept_note(vault_root, "concepts/b.md", id="concept_dup_001", canonical_title="B")
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.status == SyncStatus.PARTIAL_SUCCESS
    assert report.counts.duplicate_conflicts == 2
    with begin_connection(initialized_engine) as connection:
        assert concepts.get_concept(connection, "concept_dup_001") is None
        left = indexed_files.get_indexed_file(connection, "concepts/a.md")
        right = indexed_files.get_indexed_file(connection, "concepts/b.md")
        assert left is not None and right is not None
        assert left["index_state"] == "duplicate_id_conflict"
        assert right["index_state"] == "duplicate_id_conflict"


def test_partial_success_keeps_unrelated_valid_notes(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(vault_root, "concepts/good.md", id="concept_good_001")
    write_invalid_note(vault_root, "concepts/bad.md", "nope")
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.status == SyncStatus.PARTIAL_SUCCESS
    assert report.counts.created == 1
    assert report.counts.invalid == 1
    with begin_connection(initialized_engine) as connection:
        assert concepts.get_concept(connection, "concept_good_001") is not None


def test_full_rebuild_matches_incremental(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(vault_root, "concepts/a.md", id="concept_rb_001", overview="One")
    sync_vault(vault, initialized_engine, index_config)
    engine, report = rebuild_vault_index(vault, index_config, existing_engine=initialized_engine)
    assert report.status == SyncStatus.SUCCESS
    assert get_index_revision(engine) == 1
    with begin_connection(engine) as connection:
        row = concepts.get_concept(connection, "concept_rb_001")
        assert row is not None
        assert row["overview_plaintext"] == "One"


def test_atomic_rollback_leaves_no_partial_children(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_concept_note(vault_root, "concepts/a.md", id="concept_atom_001")

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("statement", {}, Exception("forced"))

    monkeypatch.setattr(projections, "upsert_concept_projection", _boom)
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.errors
    assert report.counts.created == 0
    assert report.counts.updated == 0
    assert report.counts.moved == 0
    assert report.counts.invalid == 1
    with begin_connection(initialized_engine) as connection:
        assert concepts.get_concept(connection, "concept_atom_001") is None


def test_revision_unchanged_on_pure_no_changes(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(vault_root, "concepts/a.md", id="concept_rev_001")
    sync_vault(vault, initialized_engine, index_config)
    before = get_index_revision(initialized_engine)
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.status == SyncStatus.NO_CHANGES
    assert get_index_revision(initialized_engine) == before


def test_concept_id_change_removes_previous_projection(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_concept_note(vault_root, "concepts/a.md", id="concept_old_aaaaaa", canonical_title="Old")
    sync_vault(vault, initialized_engine, index_config)
    write_concept_note(vault_root, "concepts/a.md", id="concept_new_bbbbbb", canonical_title="New")
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.counts.updated == 1
    with begin_connection(initialized_engine) as connection:
        assert concepts.get_concept(connection, "concept_old_aaaaaa") is None
        new_row = concepts.get_concept(connection, "concept_new_bbbbbb")
        assert new_row is not None
        assert new_row["file_path"] == "concepts/a.md"
        indexed = indexed_files.get_indexed_file(connection, "concepts/a.md")
        assert indexed is not None
        assert indexed["concept_id"] == "concept_new_bbbbbb"


def test_unchanged_invalid_file_does_not_bump_revision(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_invalid_note(vault_root, "concepts/bad.md", "not a concept note\n")
    first = sync_vault(vault, initialized_engine, index_config)
    assert first.status == SyncStatus.PARTIAL_SUCCESS
    assert first.revision_after == 1
    with begin_connection(initialized_engine) as connection:
        before_records = invalid_records.list_invalid_records(connection)
        before_indexed = indexed_files.get_indexed_file(connection, "concepts/bad.md")
    assert before_indexed is not None
    before_invalid_since = before_indexed["invalid_since_revision"]

    second = sync_vault(vault, initialized_engine, index_config)
    assert second.status == SyncStatus.NO_CHANGES
    assert second.revision_after == first.revision_after
    assert second.counts.invalid == 0
    assert second.counts.unchanged == 1
    with begin_connection(initialized_engine) as connection:
        after_records = invalid_records.list_invalid_records(connection)
        after_indexed = indexed_files.get_indexed_file(connection, "concepts/bad.md")
    assert after_indexed is not None
    assert after_indexed["invalid_since_revision"] == before_invalid_since
    assert len(after_records) == len(before_records)


def test_delete_invalid_file_clears_invalid_records(
    vault: Vault,
    vault_root: Path,
    initialized_engine: Engine,
    index_config: IndexConfig,
) -> None:
    write_invalid_note(vault_root, "concepts/bad.md", "broken note")
    sync_vault(vault, initialized_engine, index_config)
    with begin_connection(initialized_engine) as connection:
        assert invalid_records.list_invalid_records(connection)

    (vault_root / "concepts/bad.md").unlink()
    report = sync_vault(vault, initialized_engine, index_config)
    assert report.counts.removed == 1
    with begin_connection(initialized_engine) as connection:
        assert indexed_files.get_indexed_file(connection, "concepts/bad.md") is None
        assert invalid_records.list_invalid_records(connection) == []
