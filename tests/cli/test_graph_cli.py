"""CLI tests for Phase 2 graph commands."""

from __future__ import annotations

from pathlib import Path

from studium.cli.main import main
from tests.index.sync.helpers import write_concept_note


def test_graph_status_and_sync(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    app = tmp_path / "app"
    vault.mkdir()
    app.mkdir()
    write_concept_note(
        vault,
        "concepts/a.md",
        id="concept_cli_aaaaaa",
        canonical_title="CLI Concept",
    )
    assert (
        main(
            [
                "graph",
                "sync",
                "--vault",
                str(vault),
                "--app-data",
                str(app),
                "--json",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "graph",
                "status",
                "--vault",
                str(vault),
                "--app-data",
                str(app),
                "--json",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "graph",
                "find",
                "CLI Concept",
                "--vault",
                str(vault),
                "--app-data",
                str(app),
                "--json",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "graph",
                "propose",
                "CLI Concept",
                "--vault",
                str(vault),
                "--app-data",
                str(app),
                "--json",
            ]
        )
        == 0
    )
