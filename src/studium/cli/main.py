"""Studium CLI entrypoint."""

from __future__ import annotations

import argparse
import sys

from studium.cli.create_concept import cmd_create_concept
from studium.cli.graph import (
    cmd_graph_candidates,
    cmd_graph_evaluate_recommendations,
    cmd_graph_evaluate_retrieval,
    cmd_graph_find,
    cmd_graph_inspect,
    cmd_graph_modules,
    cmd_graph_propose,
    cmd_graph_rebuild,
    cmd_graph_relationships,
    cmd_graph_status,
    cmd_graph_sync,
)
from studium.cli.serve import cmd_serve
from studium.cli.validate_note import cmd_validate_note
from studium.cli.validate_vault import cmd_validate_vault


def _add_common_graph_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--vault", required=True, help="Path to the vault root directory")
    parser.add_argument(
        "--app-data",
        default=None,
        help="Optional application data directory for the derived index",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Include technical diagnostics when available",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser with Phase 1 and Phase 2 commands."""
    parser = argparse.ArgumentParser(
        prog="studium",
        description="Studium vault storage and concept-intelligence CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser(
        "create-concept",
        help="Create a concept note in a test vault via a write proposal",
    )
    create.add_argument("title", help="Canonical title for the new concept note")
    create.add_argument("--vault", required=True, help="Path to the vault root directory")
    create.add_argument(
        "--path",
        default=None,
        help="Optional vault-relative target path (default: concepts/<slug>.md)",
    )
    create.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the write proposal without committing",
    )
    create.set_defaults(func=cmd_create_concept)

    validate_note = subparsers.add_parser(
        "validate-note",
        help="Validate a single Markdown concept note",
    )
    validate_note.add_argument("path", help="Vault-relative or absolute note path")
    validate_note.add_argument("--vault", required=True, help="Path to the vault root directory")
    validate_note.set_defaults(func=cmd_validate_note)

    validate_vault = subparsers.add_parser(
        "validate-vault",
        help="Validate all Markdown notes in a vault directory",
    )
    validate_vault.add_argument("vault_dir", help="Path to the vault root directory")
    validate_vault.set_defaults(func=cmd_validate_vault)

    graph = subparsers.add_parser("graph", help="Phase 2 concept index and intelligence")
    graph_sub = graph.add_subparsers(dest="graph_command", required=True)

    sync = graph_sub.add_parser("sync", help="Incrementally sync vault into the concept index")
    _add_common_graph_flags(sync)
    sync.set_defaults(func=cmd_graph_sync)

    rebuild = graph_sub.add_parser("rebuild", help="Rebuild the concept index from the vault")
    _add_common_graph_flags(rebuild)
    rebuild.set_defaults(func=cmd_graph_rebuild)

    status = graph_sub.add_parser("status", help="Show index and model configuration status")
    _add_common_graph_flags(status)
    status.set_defaults(func=cmd_graph_status)

    find = graph_sub.add_parser("find", help="Hybrid concept search")
    _add_common_graph_flags(find)
    find.add_argument("query", help="Search text")
    find.set_defaults(func=cmd_graph_find)

    candidates = graph_sub.add_parser("candidates", help="Show ranked search candidates")
    _add_common_graph_flags(candidates)
    candidates.add_argument("query", help="Search text")
    candidates.set_defaults(func=cmd_graph_candidates)

    inspect = graph_sub.add_parser("inspect", help="Inspect one-hop graph neighborhood")
    _add_common_graph_flags(inspect)
    inspect.add_argument("concept_id", help="Concept ID")
    inspect.set_defaults(func=cmd_graph_inspect)

    modules = graph_sub.add_parser("modules", help="Search scaffold modules")
    _add_common_graph_flags(modules)
    modules.add_argument("query", help="Search text")
    modules.set_defaults(func=cmd_graph_modules)

    relationships = graph_sub.add_parser("relationships", help="Show relationships for a concept")
    _add_common_graph_flags(relationships)
    relationships.add_argument("concept_id", help="Concept ID")
    relationships.set_defaults(func=cmd_graph_relationships)

    propose = graph_sub.add_parser("propose", help="Assemble a concept recommendation")
    _add_common_graph_flags(propose)
    propose.add_argument("query", help="User query / concept intent")
    propose.add_argument("--source-type", default=None)
    propose.add_argument("--source-title", default=None)
    propose.add_argument("--unit", default=None)
    propose.add_argument("--module", action="store_true", help="Prefer scaffold-module intent")
    propose.set_defaults(func=cmd_graph_propose)

    eval_ret = graph_sub.add_parser("evaluate-retrieval", help="Run retrieval evaluation cases")
    _add_common_graph_flags(eval_ret)
    eval_ret.add_argument("--cases", default=None, help="Optional cases directory or YAML file")
    eval_ret.set_defaults(func=cmd_graph_evaluate_retrieval)

    eval_rec = graph_sub.add_parser(
        "evaluate-recommendations",
        help="Run recommendation evaluation cases",
    )
    _add_common_graph_flags(eval_rec)
    eval_rec.add_argument("--cases", default=None, help="Optional cases directory or YAML file")
    eval_rec.set_defaults(func=cmd_graph_evaluate_recommendations)

    serve = subparsers.add_parser("serve", help="Run the local Studium application")
    serve.add_argument("--vault", default=None, help="Vault to open on startup")
    serve.add_argument("--app-data", default=None, help="Optional application-data directory")
    serve.add_argument("--frontend", default=None, help="Optional built frontend directory")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument(
        "--open-browser",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Open Studium in the default browser",
    )
    serve.add_argument(
        "--log-level",
        choices=("critical", "error", "warning", "info", "debug", "trace"),
        default="info",
    )
    serve.set_defaults(func=cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to a CLI command handler."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
