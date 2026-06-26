"""Smoke test verifying the package imports and tooling runs."""

import studium


def test_package_has_version() -> None:
    assert isinstance(studium.__version__, str)
    assert studium.__version__ == "0.1.0"
