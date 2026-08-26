"""Tests for the local serve command port handling."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false

from __future__ import annotations

import socket
import subprocess
import sys
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path

import pytest

from studium.cli.main import build_parser
from studium.cli.serve import (
    cmd_serve,
    ensure_port,
    listening_pids,
    port_busy_message,
    port_is_free,
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _hold_port(port: int) -> subprocess.Popen[str]:
    script = (
        "import socket, sys, time\n"
        "port = int(sys.argv[1])\n"
        "sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
        "sock.bind(('127.0.0.1', port))\n"
        "sock.listen(1)\n"
        "print('ready', flush=True)\n"
        "time.sleep(60)\n"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    line = process.stdout.readline()
    assert "ready" in line
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and port_is_free("127.0.0.1", port):
        time.sleep(0.05)
    assert not port_is_free("127.0.0.1", port)
    return process


def test_serve_help_mentions_replace() -> None:
    parser = build_parser()
    serve_parser: ArgumentParser | None = None
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict) and "serve" in choices:
            candidate = choices["serve"]
            if isinstance(candidate, ArgumentParser):
                serve_parser = candidate
            break
    assert serve_parser is not None
    assert "--replace" in serve_parser.format_help()


def test_port_busy_message_includes_kill_command() -> None:
    message = port_busy_message("127.0.0.1", 8765)
    assert "already in use" in message
    assert "lsof -nP -t -iTCP:8765 -sTCP:LISTEN" in message
    assert "make app" in message


def test_ensure_port_reports_busy_without_replace() -> None:
    port = _free_port()
    holder = _hold_port(port)
    try:
        assert ensure_port("127.0.0.1", port, replace=False) is False
        assert holder.poll() is None
    finally:
        holder.kill()
        holder.wait(timeout=5)


def test_ensure_port_replace_stops_existing_listener() -> None:
    port = _free_port()
    holder = _hold_port(port)
    try:
        assert ensure_port("127.0.0.1", port, replace=True) is True
        assert port_is_free("127.0.0.1", port)
        holder.wait(timeout=5)
    finally:
        if holder.poll() is None:
            holder.kill()
            holder.wait(timeout=5)


def test_cmd_serve_returns_busy_before_starting(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    port = _free_port()
    holder = _hold_port(port)
    try:
        code = cmd_serve(
            Namespace(
                vault=None,
                app_data=str(tmp_path / "app-data"),
                frontend=None,
                host="127.0.0.1",
                port=port,
                replace=False,
                open_browser=False,
                log_level="error",
            )
        )
        captured = capsys.readouterr()
        assert code == 1
        assert "already in use" in captured.out
        assert "Studium is running" not in captured.out
    finally:
        holder.kill()
        holder.wait(timeout=5)


def test_listening_pids_includes_holder() -> None:
    port = _free_port()
    holder = _hold_port(port)
    try:
        pids = listening_pids(port)
        assert holder.pid in pids
    finally:
        holder.kill()
        holder.wait(timeout=5)
