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
from studium.evaluate.models import (
    EvaluationCase,
    RecommendationCaseResult,
    RetrievalCaseResult,
)


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


def test_incomplete_recommendation_coverage_fails_evaluation() -> None:
    cases = load_evaluation_cases()[:2]
    retrieval = [
        RetrievalCaseResult(
            case_id=case.case_id,
            hit=True,
            reciprocal_rank=1.0,
            ranked_ids=list(case.required_candidate_ids),
            resolution_state="exact_match",
            search_status="complete",
        )
        for case in cases
    ]
    recommendations = [
        RecommendationCaseResult(
            case_id=cases[0].case_id,
            action="use_existing_concept",
            action_ok=True,
            structured_ok=True,
        )
    ]

    report = generate_evaluation_report(
        cases=cases,
        retrieval=retrieval,
        recommendations=recommendations,
    )

    assert report.action_accuracy == 1.0
    assert report.structured_validity == 1.0
    assert report.thresholds_met is False


def test_recall_threshold_allows_one_missed_positive_case() -> None:
    cases = [
        EvaluationCase(
            case_id=f"case-{index}",
            query=f"query {index}",
            required_candidate_ids=[f"concept-{index}"],
            expected_resolution_states=["related_results"],
        )
        for index in range(10)
    ]
    retrieval = [
        RetrievalCaseResult(
            case_id=case.case_id,
            hit=index < 9,
            reciprocal_rank=1.0 if index < 9 else 0.0,
            ranked_ids=list(case.required_candidate_ids) if index < 9 else [],
            resolution_state="related_results",
            search_status="complete",
        )
        for index, case in enumerate(cases)
    ]

    report = generate_evaluation_report(cases=cases, retrieval=retrieval, recommendations=[])

    assert report.recall_at_5 == 0.9
    assert report.thresholds_met is True


def test_related_prohibited_identity_does_not_fail_retrieval_gate() -> None:
    case = EvaluationCase(
        case_id="distinct-related",
        query="related but distinct",
        prohibited_identity_ids=["related-concept"],
        expected_resolution_states=["related_results"],
    )
    retrieval = [
        RetrievalCaseResult(
            case_id=case.case_id,
            hit=True,
            reciprocal_rank=0.0,
            ranked_ids=["related-concept"],
            exact_match_ids=[],
            resolution_state="related_results",
            search_status="complete",
        )
    ]

    report = generate_evaluation_report(cases=[case], retrieval=retrieval, recommendations=[])

    assert report.thresholds_met is True
