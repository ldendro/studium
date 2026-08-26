"""Run the local Studium application service."""

from __future__ import annotations

import argparse
import threading
import webbrowser
from pathlib import Path

import uvicorn

from studium.api import create_app
from studium.app.config import load_last_workspace
from studium.app.logging import configure_content_safe_logging


def cmd_serve(args: argparse.Namespace) -> int:
    vault = Path(args.vault).expanduser().resolve() if args.vault else None
    app_data = Path(args.app_data).expanduser().resolve() if args.app_data else None
    frontend = Path(args.frontend).expanduser().resolve() if args.frontend else None
    if vault is None:
        remembered = load_last_workspace(app_data)
        if remembered is not None:
            vault, remembered_app_data = remembered
            if app_data is None:
                app_data = remembered_app_data
    log_path = configure_content_safe_logging(
        app_data_dir=app_data,
        level=args.log_level,
    )
    app = create_app(vault_root=vault, app_data_dir=app_data, frontend_dir=frontend)
    url = f"http://{args.host}:{args.port}"
    if args.open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    print(f"Studium is running at {url}")
    if vault is not None:
        print(f"Vault: {vault}")
    print(f"Content-safe log: {log_path}")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        access_log=False,
    )
    return 0
