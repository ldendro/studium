"""Allow ``python -m studium.cli``."""

from __future__ import annotations

import sys

from studium.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
