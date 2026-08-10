"""Phase 2 graph CLI command handlers (thin wrappers)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from studium.evaluate import (
    generate_evaluation_report,
    load_evaluation_cases,
    report_to_markdown,
    run_recommendation_evaluation,
    run_retrieval_evaluation,
)
from studium.index import (
    IndexConfig,
    create_engine_for_config,
    ensure_compatible_index,
    get_index_revision,
    initialize_index,
    rebuild_vault_index,
    search_concepts,
    sync_vault,
)
from studium.index.errors import IndexNotInitializedError, IndexSchemaMismatchError
from studium.index.graph import (
    get_one_hop_neighborhood,
    get_prerequisites,
)
from studium.index.search.hybrid import HybridSearchOptions
from studium.llm import DEFAULT_LLM_BASE_URL, DEFAULT_REASONING_MODEL, DeterministicLLMProvider
from studium.recommend import recommend
from studium.vault import Vault


def _config_from_args(args: argparse.Namespace) -> IndexConfig:
    app_data = getattr(args, "app_data", None)
    return IndexConfig(
        vault_root=Path(args.vault),
        app_data_dir=None if app_data is None else Path(app_data),
    )


def _engine(config: IndexConfig):
    engine = create_engine_for_config(config)
    try:
        ensure_compatible_index(engine)
    except (IndexNotInitializedError, IndexSchemaMismatchError):
        initialize_index(engine, config)
    return engine


def _emit(payload: Any, *, as_json: bool, diagnostics: dict[str, Any] | None = None) -> int:
    data: Any
    if as_json:
        if isinstance(payload, dict):
            data = cast(dict[str, Any], payload)
        elif hasattr(payload, "model_dump"):
            data = payload.model_dump(mode="json")
        else:
            data = payload
        if diagnostics is not None:
            data = {"result": data, "diagnostics": diagnostics}
        print(json.dumps(data, indent=2, default=str))
        return 0
    if hasattr(payload, "model_dump"):
        dumped = payload.model_dump(mode="json")
        print(json.dumps(dumped, indent=2, default=str))
    else:
        print(payload)
    if diagnostics:
        print("--- diagnostics ---")
        print(json.dumps(diagnostics, indent=2, default=str))
    return 0


def cmd_graph_sync(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    report = sync_vault(Vault(config.resolved_vault_root), engine, config)
    return _emit(
        report,
        as_json=args.json,
        diagnostics={"index_revision": get_index_revision(engine)} if args.diagnostics else None,
    )


def cmd_graph_rebuild(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = create_engine_for_config(config)
    _engine_out, report = rebuild_vault_index(
        Vault(config.resolved_vault_root),
        config,
        existing_engine=engine,
    )
    return _emit(report, as_json=args.json)


def cmd_graph_status(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    payload = {
        "vault": str(config.resolved_vault_root),
        "database": str(config.database_path),
        "index_revision": get_index_revision(engine),
        "default_reasoning_model": DEFAULT_REASONING_MODEL,
        "default_llm_base_url": DEFAULT_LLM_BASE_URL,
    }
    return _emit(payload, as_json=args.json)


def cmd_graph_find(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    result = search_concepts(engine, args.query)
    diagnostics = result.diagnostics if args.diagnostics else None
    return _emit(result, as_json=args.json, diagnostics=diagnostics)


def cmd_graph_candidates(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    result = search_concepts(engine, args.query)
    payload = {
        "ranked_concepts": [c.model_dump(mode="json") for c in result.ranked_concepts],
        "module_hits": [m.model_dump(mode="json") for m in result.module_hits],
        "resolution_state": result.resolution_state.value,
    }
    return _emit(payload, as_json=True)


def cmd_graph_inspect(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    neighborhood = get_one_hop_neighborhood(engine, args.concept_id)
    return _emit(neighborhood, as_json=args.json)


def cmd_graph_modules(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    result = search_concepts(engine, args.query)
    return _emit(
        {"module_hits": [m.model_dump(mode="json") for m in result.module_hits]},
        as_json=args.json,
    )


def cmd_graph_relationships(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    prereqs = get_prerequisites(engine, args.concept_id)
    neighborhood = get_one_hop_neighborhood(engine, args.concept_id)
    payload = {
        "prerequisites": [p.model_dump(mode="json") for p in prereqs],
        "neighborhood": neighborhood.model_dump(mode="json"),
    }
    return _emit(payload, as_json=args.json)


def cmd_graph_propose(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    search = search_concepts(engine, args.query)
    provider = DeterministicLLMProvider() if args.deterministic else None
    outcome = recommend(
        engine,
        search=search,
        provider=provider,
        source_type=args.source_type,
        source_title=args.source_title,
        unit=args.unit,
        module_intent=args.module,
    )
    return _emit(outcome, as_json=args.json)


def cmd_graph_evaluate_retrieval(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    cases = load_evaluation_cases(None if args.cases is None else Path(args.cases))
    retrieval = run_retrieval_evaluation(engine, cases, options=HybridSearchOptions())
    report = generate_evaluation_report(
        cases=cases,
        retrieval=retrieval,
        recommendations=[],
        config={"command": "evaluate-retrieval"},
    )
    if args.json:
        return _emit(report, as_json=True)
    print(report_to_markdown(report))
    return 0


def cmd_graph_evaluate_recommendations(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    cases = load_evaluation_cases(None if args.cases is None else Path(args.cases))
    provider = DeterministicLLMProvider()
    retrieval = run_retrieval_evaluation(engine, cases)
    recommendations = run_recommendation_evaluation(engine, cases, provider=provider)
    report = generate_evaluation_report(
        cases=cases,
        retrieval=retrieval,
        recommendations=recommendations,
        config={"command": "evaluate-recommendations", "provider": "deterministic"},
    )
    if args.json:
        return _emit(report, as_json=True)
    print(report_to_markdown(report))
    return 0
