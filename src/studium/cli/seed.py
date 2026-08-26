"""Seed a deterministic demonstration workspace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from studium.app.demo import seed_demo_workspace
from studium.app.workspace import WorkspaceContext


def cmd_seed_demo(args: argparse.Namespace) -> int:
    vault = Path(args.vault).expanduser().resolve()
    vault.mkdir(parents=True, exist_ok=True)
    (vault / "concepts").mkdir(exist_ok=True)
    app_data = Path(args.app_data).expanduser().resolve() if args.app_data else None
    workspace = WorkspaceContext(vault, app_data_dir=app_data, sync_on_open=True)
    try:
        result = seed_demo_workspace(workspace)
        result["vault_path"] = str(workspace.vault.root)
        result["app_data_dir"] = str(workspace.config.resolved_app_data_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        workspace.close()
    return 0
