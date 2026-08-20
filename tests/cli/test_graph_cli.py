"""CLI tests for Phase 2 graph commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from studium.cli import graph
from studium.cli.main import main
from studium.index import FakeEmbeddingProvider
from studium.index.errors import IndexNotInitializedError
from studium.llm import DeterministicLLMProvider
from tests.index.sync.helpers import write_concept_note


def test_payload_exit_code_fails_for_embedding_errors() -> None:
    assert (
        graph._payload_exit_code(  # pyright: ignore[reportPrivateUsage]
            {"sync": {"status": "success"}, "embeddings": {"failed": 1}}
        )
        == 1
    )


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


def test_graph_read_rejects_unsynced_vault(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    app = tmp_path / "app"
    vault.mkdir()
    app.mkdir()

    with pytest.raises(IndexNotInitializedError):
        main(
            [
                "graph",
                "find",
                "Missing",
                "--vault",
                str(vault),
                "--app-data",
                str(app),
                "--json",
            ]
        )


def test_graph_rebuild_regenerates_embeddings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    vault = tmp_path / "vault"
    app = tmp_path / "app"
    vault.mkdir()
    app.mkdir()
    write_concept_note(
        vault,
        "concepts/a.md",
        id="concept_rebuild_aaaaaa",
        canonical_title="Rebuild Concept",
    )
    monkeypatch.setattr(
        graph,
        "SentenceTransformersEmbeddingProvider",
        lambda: FakeEmbeddingProvider(),
    )

    assert (
        main(
            [
                "graph",
                "rebuild",
                "--vault",
                str(vault),
                "--app-data",
                str(app),
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["embeddings"]["written"] >= 2


def test_graph_modules_bypasses_exact_concept_identity(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    vault = tmp_path / "vault"
    app = tmp_path / "app"
    vault.mkdir()
    app.mkdir()
    write_concept_note(
        vault,
        "concepts/a.md",
        id="concept_modules_aaaaaa",
        canonical_title="Exact Module Term",
        modules_yaml=(
            "scaffold_modules:\n"
            "  - id: module_exact_aaaaaa\n"
            "    type: derivation\n"
            "    title: Exact Module Term\n"
            "    status: scaffolded\n"
            "    origin:\n"
            "    focus: exact module lookup\n"
        ),
    )
    assert main(["graph", "sync", "--vault", str(vault), "--app-data", str(app)]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "graph",
                "modules",
                "Exact Module Term",
                "--vault",
                str(vault),
                "--app-data",
                str(app),
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["module_hits"][0]["module_id"] == "module_exact_aaaaaa"


def test_graph_propose_uses_healthy_reasoning_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    vault = tmp_path / "vault"
    app = tmp_path / "app"
    vault.mkdir()
    app.mkdir()
    assert main(["graph", "sync", "--vault", str(vault), "--app-data", str(app)]) == 0
    capsys.readouterr()

    def _reasoning_response(system_prompt: str, _user_prompt: str) -> dict[str, Any]:
        if "whether a query refers to an existing concept" in system_prompt:
            return {
                "classification": "insufficient_information",
                "selected_concept_id": None,
                "confidence": "low",
                "rationale": "No verified identity candidate.",
                "evidence": ["test_provider"],
            }
        if "clarification" in system_prompt.lower():
            return {
                "needs_clarification": False,
                "ambiguity_type": "none",
                "candidate_interpretations": [],
                "clarification_message": "No clarification required.",
                "confidence": "medium",
                "evidence": ["test_provider"],
            }
        return {
            "suggested_concept_type": "general_concept",
            "suggested_domains": [],
            "scope_summary": "Test provider suggestion.",
            "graph_positions": [],
            "prerequisite_titles": [],
            "confidence": "medium",
            "rationale": "No existing concept was verified.",
            "evidence": ["test_provider"],
        }

    provider = DeterministicLLMProvider(handler=_reasoning_response)

    def _provider(**_kwargs: Any) -> DeterministicLLMProvider:
        return provider

    monkeypatch.setattr(graph, "OpenAICompatibleProvider", _provider)
    assert (
        main(
            [
                "graph",
                "propose",
                "Novel Topic",
                "--vault",
                str(vault),
                "--app-data",
                str(app),
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["reasoning_mode"] == "llm"


def test_graph_recommendation_evaluation_classifies_retrieved_fixture_candidate(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    vault = tmp_path / "vault"
    app = tmp_path / "app"
    cases = tmp_path / "case.yaml"
    vault.mkdir()
    app.mkdir()
    write_concept_note(
        vault,
        "concepts/six.md",
        id="custom_gradient_descent",
        canonical_title="Gradient Descent Optimization",
        overview="Gradient descent optimization method",
    )
    note_path = vault / "concepts/six.md"
    note_path.write_text(
        note_path.read_text(encoding="utf-8").replace(
            "concept_domains: []", "concept_domains:\n  - math"
        ),
        encoding="utf-8",
    )
    cases.write_text(
        """case_id: p2-006
query: Gradient descent optimization method
domain: math
acceptable_actions:
  - use_existing_concept
required_candidate_ids:
  - custom_gradient_descent
prohibited_identity_ids: []
expected_resolution_states:
  - related_results
""",
        encoding="utf-8",
    )
    assert main(["graph", "sync", "--vault", str(vault), "--app-data", str(app)]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "graph",
                "evaluate-recommendations",
                "--vault",
                str(vault),
                "--app-data",
                str(app),
                "--cases",
                str(cases),
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["recommendation_results"][0]["action"] == "use_existing_concept"
    assert payload["thresholds_met"] is True
