"""Phase 2 evaluation harness."""

from studium.evaluate.harness import (
    APPROVED_THRESHOLDS,
    default_cases_dir,
    generate_evaluation_report,
    load_evaluation_cases,
    mean_reciprocal_rank,
    recall_at_k,
    report_to_markdown,
    run_recommendation_evaluation,
    run_retrieval_evaluation,
)
from studium.evaluate.models import EvaluationCase, EvaluationReport

__all__ = [
    "APPROVED_THRESHOLDS",
    "EvaluationCase",
    "EvaluationReport",
    "default_cases_dir",
    "generate_evaluation_report",
    "load_evaluation_cases",
    "mean_reciprocal_rank",
    "recall_at_k",
    "report_to_markdown",
    "run_recommendation_evaluation",
    "run_retrieval_evaluation",
]
