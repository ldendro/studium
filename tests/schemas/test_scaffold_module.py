"""Tests for ScaffoldModuleMetadata."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from studium.schemas import (
    ScaffoldModuleMetadata,
    ScaffoldModuleOrigin,
    ScaffoldModuleStatus,
    ScaffoldModuleType,
)


def test_valid_module_with_optional_fields() -> None:
    module = ScaffoldModuleMetadata(
        id="module_sgd_gradient_update_derivation_001",
        type=ScaffoldModuleType.DERIVATION,
        title="Gradient Update Formula Derivation",
        status=ScaffoldModuleStatus.SCAFFOLDED,
        origin=ScaffoldModuleOrigin.USER_REQUESTED,
        focus="gradient_update_formula",
    )

    assert module.origin == ScaffoldModuleOrigin.USER_REQUESTED
    assert module.focus == "gradient_update_formula"


def test_valid_module_without_optional_fields() -> None:
    module = ScaffoldModuleMetadata(
        id="module_minimal_001",
        type=ScaffoldModuleType.WORKED_EXAMPLE,
        title="Example",
        status=ScaffoldModuleStatus.SCAFFOLDED,
    )

    assert module.origin is None
    assert module.focus is None


@pytest.mark.parametrize("missing_field", ["id", "type", "title", "status"])
def test_missing_required_field_raises(missing_field: str) -> None:
    data = {
        "id": "module_test_001",
        "type": "derivation",
        "title": "Derivation",
        "status": "scaffolded",
    }
    del data[missing_field]

    with pytest.raises(ValidationError):
        ScaffoldModuleMetadata.model_validate(data)
