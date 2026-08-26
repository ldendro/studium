"""Retention scheduler, mastery labels, and learning-loop services."""

from __future__ import annotations

from studium.app.learning import (
    BacklogService,
    ProfileService,
    _evaluation,
    _mastery_state,
    _schedule,
)
from studium.app.learning_models import (
    BacklogItemType,
    BacklogOrigin,
    MasteryState,
    ProfileCategory,
    RetentionCard,
    RetentionCardState,
    RetentionEvaluation,
)
from studium.app.workspace import WorkspaceContext


def _card(**overrides: object) -> RetentionCard:
    values: dict[str, object] = {
        "id": "card_test",
        "concept_id": "concept_example",
        "concept_title": "Example",
        "module_id": "module_example",
        "module_type": "conceptual_explanation",
        "prompt": "Explain the mechanism.",
        "expected_components": ["mechanism", "assumption"],
        "state": RetentionCardState.LEARNING,
        "interval_days": 6,
        "ease_factor": 2.5,
        "repetitions": 2,
        "lapses": 0,
        "difficulty": 0.3,
        "stability": 4.0,
        "last_reviewed_at": None,
        "next_review_at": "2026-08-26T00:00:00Z",
        "pinned": False,
        "created_at": "2026-08-26T00:00:00Z",
        "updated_at": "2026-08-26T00:00:00Z",
    }
    values.update(overrides)
    return RetentionCard.model_validate(values)


def test_evaluation_thresholds() -> None:
    assert _evaluation(1, 0.9) == RetentionEvaluation.AGAIN
    assert _evaluation(3, 0.2) == RetentionEvaluation.AGAIN
    assert _evaluation(2, 0.7) == RetentionEvaluation.HARD
    assert _evaluation(5, 0.9) == RetentionEvaluation.EASY
    assert _evaluation(4, 0.7) == RetentionEvaluation.GOOD


def test_schedule_lapse_and_interval_growth() -> None:
    again = _schedule(_card(), RetentionEvaluation.AGAIN)
    assert again["interval_days"] == 1
    assert again["repetitions"] == 0
    assert again["lapses"] == 1
    easy = _schedule(_card(repetitions=2, interval_days=6), RetentionEvaluation.EASY)
    assert easy["repetitions"] == 3
    assert easy["interval_days"] >= 6


def test_mastery_states() -> None:
    assert _mastery_state(0.05) == MasteryState.UNASSESSED
    assert _mastery_state(0.3) == MasteryState.FRAGILE
    assert _mastery_state(0.6) == MasteryState.DEVELOPING
    assert _mastery_state(0.9) == MasteryState.STRONG


def test_backlog_and_profile_round_trip(workspace: WorkspaceContext) -> None:
    item = BacklogService(workspace).create(
        title="Natural Gradients",
        item_type=BacklogItemType.NEW_CONCEPT,
        reason="Follow-up after mastering first-order methods.",
        origin=BacklogOrigin.MANUAL,
        priority=70,
    )
    listed = BacklogService(workspace).list()
    assert listed[0].id == item.id
    observation = ProfileService(workspace).create(
        category=ProfileCategory.GOAL,
        statement="Build durable optimization intuition.",
        evidence=[{"source": "test"}],
        pinned=True,
    )
    soul = ProfileService(workspace).write_soul()
    assert observation.statement in soul["markdown"]
    assert (workspace.config.workspace_dir / "soul.md").is_file()
