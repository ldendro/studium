"""Evaluation harness unit tests."""

from __future__ import annotations

from studium.evaluate import (
    APPROVED_THRESHOLDS,
    load_evaluation_cases,
    mean_reciprocal_rank,
    recall_at_k,
    report_to_markdown,
)
from studium.evaluate.harness import generate_evaluation_report
from studium.evaluate.models import RecommendationCaseResult, RetrievalCaseResult


def test_load_cases() -> None:
    cases = load_evaluation_cases()
    assert len(cases) >= 40
    assert cases[0].case_id.startswith("p2-")


def test_metrics() -> None:
    assert recall_at_k(["a", "b", "c"], ["b"], k=5) == 1.0
    assert mean_reciprocal_rank(["a", "b"], ["b"]) == 0.5
    assert recall_at_k(["a"], []) == 0.0
    assert mean_reciprocal_rank(["a"], []) == 0.0


def test_report_markdown() -> None:
    report = generate_evaluation_report(
        cases=[],
        retrieval=[
            RetrievalCaseResult(
                case_id="x",
                hit=True,
                reciprocal_rank=1.0,
                ranked_ids=["a"],
                resolution_state="exact_match",
                search_status="complete",
            )
        ],
        recommendations=[
            RecommendationCaseResult(
                case_id="x",
                action="use_existing_concept",
                action_ok=True,
                structured_ok=True,
            )
        ],
    )
    text = report_to_markdown(report)
    assert "Recall@5" in text
    assert "exact_lookup_accuracy" in APPROVED_THRESHOLDS


def test_empty_case_set_fails_evaluation() -> None:
    report = generate_evaluation_report(
        cases=[],
        retrieval=[
            RetrievalCaseResult(
                case_id="x",
                hit=True,
                reciprocal_rank=1.0,
                ranked_ids=["a"],
                resolution_state="related_results",
                search_status="complete",
            )
        ],
        recommendations=[],
    )
    assert report.case_count == 0
    assert report.thresholds_met is False
