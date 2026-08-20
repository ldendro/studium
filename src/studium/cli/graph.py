"""Phase 2 graph CLI command handlers (thin wrappers)."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
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
    ModelSpaceFilter,
    SentenceTransformersEmbeddingProvider,
    create_engine_for_config,
    ensure_compatible_index,
    get_index_revision,
    initialize_index,
    process_embedding_work,
    rebuild_vault_index,
    search_concepts,
    search_modules_fts,
    sync_and_embed,
    sync_vault,
)
from studium.index.errors import IndexNotInitializedError
from studium.index.graph import (
    get_one_hop_neighborhood,
    get_prerequisites,
)
from studium.index.repositories import embeddings as embeddings_repo
from studium.index.search.hybrid import HybridSearchOptions
from studium.index.search.models import ConceptSearchQuery
from studium.llm import (
    DEFAULT_LLM_BASE_URL,
    DEFAULT_REASONING_MODEL,
    DeterministicLLMProvider,
    LLMProvider,
    OpenAICompatibleProvider,
)
from studium.recommend import recommend
from studium.vault import Vault


def _config_from_args(args: argparse.Namespace) -> IndexConfig:
    app_data = getattr(args, "app_data", None)
    return IndexConfig(
        vault_root=Path(args.vault),
        app_data_dir=None if app_data is None else Path(app_data),
    )


def _engine(config: IndexConfig):
    Vault(config.resolved_vault_root)
    engine = create_engine_for_config(config)
    ensure_compatible_index(engine)
    return engine


def _sync_engine(config: IndexConfig):
    """Open an index for sync, initializing only a previously absent schema."""
    Vault(config.resolved_vault_root)
    engine = create_engine_for_config(config)
    try:
        ensure_compatible_index(engine)
    except IndexNotInitializedError:
        initialize_index(engine, config)
    return engine


def _reasoning_provider() -> LLMProvider | None:
    """Return the configured local provider only when it is ready."""
    try:
        provider = OpenAICompatibleProvider(
            base_url=DEFAULT_LLM_BASE_URL,
            model_id=DEFAULT_REASONING_MODEL,
        )
        health = provider.check_health()
    except Exception:
        return None
    return provider if health.healthy and health.ready else None


def _search_options(engine: Any) -> HybridSearchOptions:
    """Use the newest persisted embedding space when its local provider is available."""
    with engine.connect() as connection:
        spaces = embeddings_repo.list_model_spaces(connection)
    if not spaces:
        return HybridSearchOptions()
    space = spaces[0]
    revision = None if space["model_revision"] is None else str(space["model_revision"])
    try:
        provider = SentenceTransformersEmbeddingProvider(
            model_id=str(space["model_id"]),
            revision=revision,
            normalize_embeddings=bool(space["normalizes_embeddings"]),
        )
    except Exception:
        return HybridSearchOptions()
    model_filter = ModelSpaceFilter(
        model_id=str(space["model_id"]),
        model_revision=revision,
        dimension=int(space["dimension"]),
        normalizes_embeddings=bool(space["normalizes_embeddings"]),
    )
    return HybridSearchOptions(embedding_provider=provider, model_filter=model_filter)


def _emit(payload: Any, *, as_json: bool, diagnostics: dict[str, Any] | None = None) -> int:
    exit_code = _payload_exit_code(payload)
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
        return exit_code
    if hasattr(payload, "model_dump"):
        dumped = payload.model_dump(mode="json")
        print(json.dumps(dumped, indent=2, default=str))
    else:
        print(payload)
    if diagnostics:
        print("--- diagnostics ---")
        print(json.dumps(diagnostics, indent=2, default=str))
    return exit_code


def _payload_exit_code(payload: Any) -> int:
    data = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else payload
    if isinstance(data, dict):
        data = cast(dict[str, Any], data)
        if data.get("status") == "failed":
            return 1
        sync_data = data.get("sync")
        if isinstance(sync_data, dict):
            sync_data = cast(dict[str, Any], sync_data)
            if sync_data.get("status") == "failed":
                return 1
        if data.get("thresholds_met") is False:
            return 1
        if "failure_stage" in data and "error_code" in data:
            return 1
    return 0


def cmd_graph_sync(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _sync_engine(config)
    vault = Vault(config.resolved_vault_root)
    try:
        provider = SentenceTransformersEmbeddingProvider()
    except Exception as exc:
        report = sync_vault(vault, engine, config)
        payload: Any = {
            "sync": report.model_dump(mode="json"),
            "embeddings": {"status": "unavailable", "error": str(exc)},
        }
    else:
        combined = sync_and_embed(vault, engine, config, provider)
        payload = {
            "sync": combined.sync.model_dump(mode="json"),
            "embeddings": combined.embeddings.model_dump(mode="json"),
        }
    return _emit(
        payload,
        as_json=args.json,
        diagnostics={"index_revision": get_index_revision(engine)} if args.diagnostics else None,
    )


def cmd_graph_rebuild(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = create_engine_for_config(config)
    rebuilt_engine, report = rebuild_vault_index(
        Vault(config.resolved_vault_root),
        config,
        existing_engine=engine,
    )
    try:
        provider = SentenceTransformersEmbeddingProvider()
    except Exception as exc:
        payload: Any = {
            "sync": report.model_dump(mode="json"),
            "embeddings": {"status": "unavailable", "error": str(exc)},
        }
    else:
        embedding_report = process_embedding_work(
            rebuilt_engine,
            report.embedding_work,
            provider,
            indexed_revision=report.revision_after,
        )
        payload = {
            "sync": report.model_dump(mode="json"),
            "embeddings": embedding_report.model_dump(mode="json"),
        }
    return _emit(payload, as_json=args.json)


def cmd_graph_status(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    payload: dict[str, Any] = {
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
    result = search_concepts(
        engine,
        ConceptSearchQuery(text=args.query, include_diagnostics=args.diagnostics),
        options=_search_options(engine),
    )
    diagnostics = result.diagnostics if args.diagnostics else None
    return _emit(result, as_json=args.json, diagnostics=diagnostics)


def cmd_graph_candidates(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    result = search_concepts(
        engine,
        ConceptSearchQuery(text=args.query, include_diagnostics=args.diagnostics),
        options=_search_options(engine),
    )
    payload: dict[str, Any] = {
        "ranked_concepts": [c.model_dump(mode="json") for c in result.ranked_concepts],
        "module_hits": [m.model_dump(mode="json") for m in result.module_hits],
        "resolution_state": result.resolution_state.value,
    }
    if args.diagnostics:
        payload["diagnostics"] = result.diagnostics
    return _emit(payload, as_json=True)


def cmd_graph_inspect(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    neighborhood = get_one_hop_neighborhood(engine, args.concept_id)
    return _emit(neighborhood, as_json=args.json)


def cmd_graph_modules(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    module_hits = search_modules_fts(engine, args.query)
    return _emit(
        {"module_hits": [hit.model_dump(mode="json") for hit in module_hits]},
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
    search = search_concepts(engine, args.query, options=_search_options(engine))
    provider = _reasoning_provider()
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
    retrieval = run_retrieval_evaluation(engine, cases, options=_search_options(engine))
    report = generate_evaluation_report(
        cases=cases,
        retrieval=retrieval,
        recommendations=[],
        config={"command": "evaluate-retrieval"},
    )
    if args.json:
        return _emit(report, as_json=True)
    print(report_to_markdown(report))
    return _payload_exit_code(report)


def cmd_graph_evaluate_recommendations(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    engine = _engine(config)
    cases = load_evaluation_cases(None if args.cases is None else Path(args.cases))
    options = _search_options(engine)
    retrieval = run_retrieval_evaluation(engine, cases, options=options)
    provider = DeterministicLLMProvider(handler=_evaluation_reasoning_response)
    recommendations = run_recommendation_evaluation(
        engine,
        cases,
        provider_factory=lambda case: DeterministicLLMProvider(
            handler=_evaluation_reasoning_handler(set(case.required_candidate_ids))
        ),
        options=options,
    )
    report = generate_evaluation_report(
        cases=cases,
        retrieval=retrieval,
        recommendations=recommendations,
        config={"command": "evaluate-recommendations", "provider": provider.model_id()},
    )
    if args.json:
        return _emit(report, as_json=True)
    print(report_to_markdown(report))
    return _payload_exit_code(report)


def _evaluation_reasoning_response(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    return _evaluation_reasoning_handler(set())(system_prompt, user_prompt)


def _evaluation_reasoning_handler(
    required_candidate_ids: set[str],
) -> Callable[[str, str], dict[str, Any]]:
    def respond(system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return _evaluation_reasoning_response_for_case(
            system_prompt, user_prompt, required_candidate_ids=required_candidate_ids
        )

    return respond


def _evaluation_reasoning_response_for_case(
    system_prompt: str,
    user_prompt: str,
    *,
    required_candidate_ids: set[str],
) -> dict[str, Any]:
    if "whether a query refers to an existing concept" in system_prompt:
        marker = "Candidates (JSON):\n"
        candidate_text = user_prompt.partition(marker)[2]
        candidates: list[Any] = []
        if candidate_text:
            try:
                loaded, _end = json.JSONDecoder().raw_decode(candidate_text)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(loaded, list):
                    candidates = cast(list[Any], loaded)
        candidate_dicts = [
            cast(dict[str, Any], candidate)
            for candidate in candidates
            if isinstance(candidate, dict)
        ]
        selected = next(
            (
                candidate
                for candidate in candidate_dicts
                if candidate.get("concept_id") in required_candidate_ids
            ),
            None,
        )
        if selected is not None:
            return {
                "classification": "same_concept",
                "selected_concept_id": str(selected["concept_id"]),
                "confidence": "high",
                "rationale": "The retrieved fixture candidate matches the evaluation query.",
                "evidence": ["deterministic_evaluation_candidate"],
            }
        return {
            "classification": "insufficient_information",
            "selected_concept_id": None,
            "confidence": "low",
            "rationale": "No verified identity candidate.",
            "evidence": ["deterministic_evaluation"],
        }
    if "clarification" in system_prompt.lower():
        return {
            "needs_clarification": False,
            "ambiguity_type": "none",
            "candidate_interpretations": [],
            "clarification_message": "No clarification required.",
            "confidence": "medium",
            "evidence": ["deterministic_evaluation"],
        }
    return {
        "suggested_concept_type": "general_concept",
        "suggested_domains": [],
        "scope_summary": "Deterministic evaluation suggestion.",
        "graph_positions": [],
        "prerequisite_titles": [],
        "confidence": "medium",
        "rationale": "No existing concept was verified.",
        "evidence": ["deterministic_evaluation"],
    }
