"""Tests for concept ID generation."""

from __future__ import annotations

from studium.serialization import generate_concept_id, slugify_title


def test_slugify_title_normalizes_text() -> None:
    assert slugify_title("Stochastic Gradient Descent") == "stochastic_gradient_descent"


def test_slugify_title_ascii_folds_and_strips() -> None:
    assert slugify_title("Café & Derivatives!!!") == "cafe_derivatives"


def test_slugify_title_fallback_for_empty_result() -> None:
    assert slugify_title("🙂") == "concept"


def test_generate_concept_id_format() -> None:
    concept_id = generate_concept_id("Stochastic Gradient Descent")

    assert concept_id.startswith("concept_stochastic_gradient_descent_")
    assert len(concept_id.split("_")[-1]) == 6


def test_generate_concept_id_is_deterministic() -> None:
    title = "Stochastic Gradient Descent"
    assert generate_concept_id(title) == generate_concept_id(title)
