"""Tests for LearningEncounter and SourceMetadata."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from studium.schemas import (
    ContributionStatus,
    EncounterRole,
    LearningEncounter,
    SourceMetadata,
    SourceType,
    default_studium_learning_encounter,
)


def test_default_studium_encounter_is_valid() -> None:
    encounter = default_studium_learning_encounter()

    assert encounter.source.type == SourceType.STUDIUM
    assert encounter.source.title == "Studium"
    assert encounter.role == EncounterRole.PRIMARY
    assert encounter.contribution_status == ContributionStatus.PENDING
    assert encounter.content_attached is False
    assert encounter.content_id is None


def test_missing_source_title_raises() -> None:
    with pytest.raises(ValidationError):
        SourceMetadata(type=SourceType.BOOK, title="")


def test_invalid_source_type_raises() -> None:
    with pytest.raises(ValidationError):
        SourceMetadata.model_validate({"type": "magazine", "title": "Example"})


def test_content_id_none_allowed() -> None:
    encounter = LearningEncounter(
        source=SourceMetadata(type=SourceType.BOOK, title="Deep Learning"),
        role=EncounterRole.ADDITIONAL,
        contribution_status=ContributionStatus.PENDING,
        content_attached=False,
        content_id=None,
    )

    assert encounter.content_id is None


def test_optional_source_fields_default_to_none() -> None:
    source = SourceMetadata(type=SourceType.STUDIUM, title="Studium")

    assert source.unit_type is None
    assert source.unit is None
    assert source.section is None
    assert source.link is None
