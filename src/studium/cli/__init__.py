"""Minimal CLI (branch P1-B8).

Thin command surface (create-concept, validate-note, validate-vault) that
calls storage-layer functions.
"""

from studium.cli.main import main

__all__ = ["main"]
