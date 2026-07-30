"""Tests for matching normalization."""

from __future__ import annotations

from studium.index.normalize import (
    dedupe_aliases_by_normalized,
    normalize_for_lookup,
    normalize_title,
)


def test_normalize_for_lookup_casefold_whitespace_and_hyphens() -> None:
    assert normalize_for_lookup("  Stochastic   Gradient-Descent ") == (
        "stochastic gradient descent"
    )
    assert normalize_for_lookup("semi_supervised") == "semi supervised"


def test_normalize_for_lookup_strips_light_surrounding_punctuation() -> None:
    assert normalize_for_lookup('"SGD"') == "sgd"
    assert normalize_for_lookup("(SGD)") == "sgd"


def test_normalize_for_lookup_folds_latin_diacritics_like_fts() -> None:
    assert normalize_for_lookup("Café") == normalize_for_lookup("cafe")
    assert normalize_for_lookup("naïve") == "naive"


def test_normalize_for_lookup_preserves_indic_virama() -> None:
    # Must not collapse कर्म → करम (virama is not a Latin COMBINING mark).
    assert normalize_for_lookup("कर्म") == "कर्म"


def test_normalize_title_delegates_to_lookup_normalizer() -> None:
    assert normalize_title("A-B_C") == normalize_for_lookup("A-B_C")


def test_dedupe_aliases_by_normalized_keeps_first_display_form() -> None:
    assert dedupe_aliases_by_normalized(["foo-bar", "foo_bar", "Other"]) == [
        "foo-bar",
        "Other",
    ]
    assert dedupe_aliases_by_normalized(["foo_bar", "foo-bar"]) == ["foo_bar"]
