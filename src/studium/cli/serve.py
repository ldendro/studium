"""Run the local Studium application service."""

from __future__ import annotations

import argparse
import errno
import os
import signal
import socket
import subprocess
import threading
import time
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
    if frontend is None:
        default_frontend = Path.cwd() / "web" / "dist"
        if (default_frontend / "index.html").is_file():
            frontend = default_frontend.resolve()
    if vault is None:
        remembered = load_last_workspace(app_data)
        if remembered is not None:
            vault, remembered_app_data = remembered
            if app_data is None:
                app_data = remembered_app_data
    if not ensure_port(args.host, args.port, replace=bool(getattr(args, "replace", False))):
        return 1
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
    if frontend is not None and (frontend / "index.html").is_file():
        print(f"Frontend: {frontend}")
    else:
        print("Frontend: not built. Run `cd web && npm install && npm run build`.")
    print(f"Content-safe log: {log_path}")
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            access_log=False,
        )
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        if not port_is_free(args.host, args.port):
            print(port_busy_message(args.host, args.port), end="")
            return 1
        return code
    return 0


def port_is_free(host: str, port: int) -> bool:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                return False
            raise
    return True


def listening_pids(port: int) -> list[int]:
    try:
        completed = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return []
    pids: list[int] = []
    for token in completed.stdout.split():
        try:
            pid = int(token)
        except ValueError:
            continue
        if pid not in pids:
            pids.append(pid)
    return pids


def stop_listeners(port: int, *, timeout: float = 4.0) -> list[int]:
    pids = [pid for pid in listening_pids(port) if pid != os.getpid()]
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            continue
    deadline = time.monotonic() + timeout
    remaining = set(pids)
    while remaining and time.monotonic() < deadline:
        remaining &= set(listening_pids(port))
        if not remaining:
            break
        time.sleep(0.05)
    for pid in list(remaining):
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            continue
    return pids


def port_busy_message(host: str, port: int) -> str:
    pids = listening_pids(port)
    pid_text = f" Process id: {', '.join(str(pid) for pid in pids)}." if pids else ""
    return (
        f"Port {port} is already in use, so Studium could not start.{pid_text}\n"
        "An earlier Studium process is probably still running.\n"
        "In that terminal, press Ctrl+C. Then run `make app` again.\n"
        f"Or stop it directly: kill $(lsof -nP -t -iTCP:{port} -sTCP:LISTEN)\n"
        f"Then open http://{host}:{port}\n"
    )


def ensure_port(host: str, port: int, *, replace: bool) -> bool:
    if port_is_free(host, port):
        return True
    if replace:
        stopped = stop_listeners(port)
        if stopped:
            names = ", ".join(str(pid) for pid in stopped)
            print(f"Stopped existing process on port {port}: {names}")
        if port_is_free(host, port):
            return True
    print(port_busy_message(host, port), end="")
    return False
