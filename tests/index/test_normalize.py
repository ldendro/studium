"""Tests for matching normalization."""

from __future__ import annotations

from studium.index.normalize import normalize_for_lookup, normalize_title


def test_normalize_for_lookup_casefold_whitespace_and_hyphens() -> None:
    assert normalize_for_lookup("  Stochastic   Gradient-Descent ") == (
        "stochastic gradient descent"
    )
    assert normalize_for_lookup("semi_supervised") == "semi supervised"


def test_normalize_for_lookup_strips_light_surrounding_punctuation() -> None:
    assert normalize_for_lookup('"SGD"') == "sgd"
    assert normalize_for_lookup("(SGD)") == "sgd"


def test_normalize_title_delegates_to_lookup_normalizer() -> None:
    assert normalize_title("A-B_C") == normalize_for_lookup("A-B_C")
