"""Load YAML evaluation cases and compute retrieval/recommendation metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml
from sqlalchemy.engine import Engine

from studium.evaluate.models import (
    EvaluationCase,
    EvaluationReport,
    RecommendationCaseResult,
    RetrievalCaseResult,
)
from studium.index.search.hybrid import HybridSearchOptions, search_concepts
from studium.index.search.models import ConceptSearchQuery, ResolutionState
from studium.llm.protocol import LLMProvider
from studium.recommend.models import RecommendationFailure
from studium.recommend.service import recommend

# Approved Phase 2 thresholds (Technical Plan provisional values confirmed for harness).
APPROVED_THRESHOLDS: dict[str, float] = {
    "exact_lookup_accuracy": 1.0,
    "recall_at_5": 0.90,
    "structured_validity": 1.0,
    "action_accuracy": 0.85,
}


def default_cases_dir() -> Path:
    packaged = Path(__file__).resolve().parent / "cases"
    if packaged.exists():
        return packaged
    return Path(__file__).resolve().parents[3] / "evals" / "phase2" / "cases"


def load_evaluation_cases(path: Path | None = None) -> list[EvaluationCase]:
    root = default_cases_dir() if path is None else path
    if not root.exists():
        raise FileNotFoundError(f"Evaluation cases path does not exist: {root}")
    files = [root] if root.is_file() else sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml"))
    cases: list[EvaluationCase] = []
    for file in files:
        payload = yaml.safe_load(file.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            for item in cast(list[Any], payload):
                cases.append(EvaluationCase.model_validate(item))
        else:
            cases.append(EvaluationCase.model_validate(payload))
    return cases


def recall_at_k(ranked_ids: list[str], required: list[str], *, k: int = 5) -> float:
    if not required:
        return 0.0
    top = set(ranked_ids[:k])
    hits = sum(1 for concept_id in required if concept_id in top)
    return hits / len(required)


def mean_reciprocal_rank(ranked_ids: list[str], required: list[str]) -> float:
    if not required:
        return 0.0
    best = 0.0
    for concept_id in required:
        try:
            rank = ranked_ids.index(concept_id) + 1
        except ValueError:
            continue
        best = max(best, 1.0 / rank)
    return best


def run_retrieval_evaluation(
    engine: Engine,
    cases: list[EvaluationCase],
    *,
    options: HybridSearchOptions | None = None,
) -> list[RetrievalCaseResult]:
    results: list[RetrievalCaseResult] = []
    for case in cases:
        search = search_concepts(
            engine,
            ConceptSearchQuery(text=case.query, include_diagnostics=False),
            options=options,
        )
        ranked_ids = [c.concept_id for c in search.ranked_concepts]
        if search.exact_matches:
            ranked_ids = [m.concept_id for m in search.exact_matches] + ranked_ids
        required = case.required_candidate_ids
        prohibited = set(case.prohibited_identity_ids)
        if not required and not prohibited:
            raise ValueError(f"Retrieval case {case.case_id!r} has no retrieval labels")
        prohibited_found = bool(prohibited.intersection(ranked_ids))
        hit = (
            not required or recall_at_k(ranked_ids, required, k=5) >= 1.0
        ) and not prohibited_found
        results.append(
            RetrievalCaseResult(
                case_id=case.case_id,
                hit=hit,
                reciprocal_rank=mean_reciprocal_rank(ranked_ids, required),
                ranked_ids=ranked_ids[:10],
                resolution_state=search.resolution_state.value,
                search_status=search.search_status.value,
            )
        )
    return results


def run_recommendation_evaluation(
    engine: Engine,
    cases: list[EvaluationCase],
    *,
    provider: LLMProvider | None = None,
    options: HybridSearchOptions | None = None,
) -> list[RecommendationCaseResult]:
    results: list[RecommendationCaseResult] = []
    for case in cases:
        search = search_concepts(
            engine,
            ConceptSearchQuery(text=case.query),
            options=options,
        )
        outcome = recommend(engine, search=search, provider=provider)
        if isinstance(outcome, RecommendationFailure):
            results.append(
                RecommendationCaseResult(
                    case_id=case.case_id,
                    action=None,
                    action_ok=False,
                    structured_ok=False,
                    failure_code=outcome.error_code,
                )
            )
            continue
        action = outcome.action
        action_ok = not case.acceptable_actions or action in case.acceptable_actions
        results.append(
            RecommendationCaseResult(
                case_id=case.case_id,
                action=action,
                action_ok=action_ok,
                structured_ok=True,
            )
        )
    return results


def generate_evaluation_report(
    *,
    cases: list[EvaluationCase],
    retrieval: list[RetrievalCaseResult],
    recommendations: list[RecommendationCaseResult],
    config: dict[str, Any] | None = None,
) -> EvaluationReport:
    n = max(1, len(cases))
    recall = sum(1.0 if r.hit else 0.0 for r in retrieval) / max(1, len(retrieval))
    mrr = sum(r.reciprocal_rank for r in retrieval) / max(1, len(retrieval))
    exact_cases = [
        case
        for case in cases
        if ResolutionState.EXACT_MATCH.value in case.expected_resolution_states
    ]
    exact_ok = 0
    for case in exact_cases:
        match = next((r for r in retrieval if r.case_id == case.case_id), None)
        if match and match.resolution_state == ResolutionState.EXACT_MATCH.value:
            exact_ok += 1
    exact_acc = 1.0 if not exact_cases else exact_ok / len(exact_cases)
    action_acc = (
        sum(1.0 if r.action_ok else 0.0 for r in recommendations) / len(recommendations)
        if recommendations
        else 0.0
    )
    structured = (
        sum(1.0 if r.structured_ok else 0.0 for r in recommendations) / len(recommendations)
        if recommendations
        else 0.0
    )
    thresholds = dict(APPROVED_THRESHOLDS)
    retrieval_met = (
        exact_acc >= thresholds["exact_lookup_accuracy"] and recall >= thresholds["recall_at_5"]
    )
    recommendation_met = (
        structured >= thresholds["structured_validity"]
        and action_acc >= thresholds["action_accuracy"]
    )
    met = retrieval_met and (not recommendations or recommendation_met)
    return EvaluationReport(
        case_count=n,
        recall_at_5=recall,
        mrr=mrr,
        exact_lookup_accuracy=exact_acc,
        action_accuracy=action_acc,
        structured_validity=structured,
        retrieval_results=retrieval,
        recommendation_results=recommendations,
        config=config or {},
        thresholds=thresholds,
        thresholds_met=met,
    )


def report_to_markdown(report: EvaluationReport) -> str:
    lines = [
        "# Phase 2 Evaluation Report",
        "",
        f"- cases: {report.case_count}",
        f"- Recall@5: {report.recall_at_5:.3f}",
        f"- MRR: {report.mrr:.3f}",
        f"- exact lookup accuracy: {report.exact_lookup_accuracy:.3f}",
        f"- action accuracy: {report.action_accuracy:.3f}",
        f"- structured validity: {report.structured_validity:.3f}",
        f"- thresholds met: {report.thresholds_met}",
        "",
        "## Thresholds",
    ]
    for key, value in report.thresholds.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"
