"""Learning encounter metadata."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from studium.schemas.enums import ContributionStatus, EncounterRole, SourceType
from studium.schemas.source import SourceMetadata


class LearningEncounter(BaseModel):
    """Context through which the user encountered or created a concept."""

    model_config = ConfigDict(extra="forbid")

    source: SourceMetadata
    role: EncounterRole
    contribution_status: ContributionStatus
    content_attached: bool
    content_id: str | None


def default_studium_learning_encounter() -> LearningEncounter:
    """Return the canonical Studium-origin learning encounter from the Technical Plan."""
    return LearningEncounter(
        source=SourceMetadata(type=SourceType.STUDIUM, title="Studium"),
        role=EncounterRole.PRIMARY,
        contribution_status=ContributionStatus.PENDING,
        content_attached=False,
        content_id=None,
    )
