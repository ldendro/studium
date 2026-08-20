"""Hybrid concept search: Tier 0 identity + Tier 1 weighted RRF fusion."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from sqlalchemy.engine import Engine

from studium.index.config import (
    DEFAULT_RRF_CONSTANT,
    DEFAULT_RRF_WEIGHTS,
)
from studium.index.embeddings.pipeline import embed_query
from studium.index.embeddings.protocol import EmbeddingProvider
from studium.index.repositories import aliases, concepts, domains
from studium.index.schema_manager import get_index_revision
from studium.index.search.fts import search_concepts_fts, search_modules_fts
from studium.index.search.lookup import resolve_concept_identity
from studium.index.search.models import (
    ChannelContribution,
    ConceptSearchQuery,
    ConceptSearchResult,
    HybridModuleHit,
    IdentityMatch,
    RankedConceptCandidate,
    RankedModuleMatch,
    ResolutionState,
    SearchChannel,
    SearchEvidenceItem,
    SearchStatus,
)
from studium.index.search.rrf import fuse_ranked_lists, ranks_from_ordered_ids
from studium.index.vector.facade import (
    search_concept_identity_vectors,
    search_concept_semantic_vectors,
    search_module_semantic_vectors,
)
from studium.index.vector.models import ModelSpaceFilter, VectorConceptHit, VectorModuleHit
from studium.index.vector.protocol import VectorSearchBackend


@dataclass(frozen=True, slots=True)
class HybridSearchOptions:
    """Optional backends and fusion knobs for ``search_concepts``."""

    embedding_provider: EmbeddingProvider | None = None
    model_filter: ModelSpaceFilter | None = None
    query_identity_vector: list[float] | None = None
    query_semantic_vector: list[float] | None = None
    vector_backend: VectorSearchBackend | None = None
    rrf_constant: float = DEFAULT_RRF_CONSTANT
    rrf_weights: dict[str, float] | None = None


def search_concepts(
    engine: Engine,
    query: ConceptSearchQuery | str,
    *,
    options: HybridSearchOptions | None = None,
) -> ConceptSearchResult:
    """Run Tier 0 exact lookup, else Tier 1 hybrid FTS + vector fusion.

    Does not invoke LLM reasoning. Callers supply embedding vectors or a provider
    for vector channels; without either, Tier 1 falls back to FTS-only (partial).
    """
    opts = options or HybridSearchOptions()
    search_query = (
        query if isinstance(query, ConceptSearchQuery) else ConceptSearchQuery(text=query)
    )
    revision = get_index_revision(engine)
    identity = resolve_concept_identity(engine, search_query.text)
    warnings: list[str] = []
    diagnostics: dict[str, Any] = {
        "path": "tier0",
        "normalized_query": identity.normalized_query,
        "deterministic_match_count": len(identity.matches),
    }

    if identity.matches and _has_filters(search_query):
        filtered_matches: list[IdentityMatch] = []
        for match in identity.matches:
            candidate = _load_ranked_exact(engine, match)
            if candidate is not None and _passes_filters(candidate, search_query):
                filtered_matches.append(match)
        identity = identity.model_copy(
            update={"matches": filtered_matches, "is_ambiguous": len(filtered_matches) > 1}
        )

    if identity.is_unique:
        match = identity.unique_match
        assert match is not None
        candidate = _load_ranked_exact(engine, match)
        if candidate is not None and not _passes_filters(candidate, search_query):
            warnings.append("Exact identity match excluded by query filters.")
            diagnostics["exact_match_filtered"] = True
        else:
            evidence = [
                SearchEvidenceItem(
                    evidence_type="exact_identity",
                    summary=f"Exact {match.match_type.value} match",
                    concept_id=match.concept_id,
                    details={"match_type": match.match_type.value},
                )
            ]
            return ConceptSearchResult(
                query=search_query,
                index_revision=revision,
                search_status=SearchStatus.COMPLETE,
                resolution_state=ResolutionState.EXACT_MATCH,
                exact_matches=[match],
                ranked_concepts=[candidate] if candidate is not None else [],
                module_hits=[],
                evidence=evidence,
                warnings=warnings,
                diagnostics=diagnostics if search_query.include_diagnostics else {},
            )

    if identity.is_ambiguous:
        warnings.append(
            "Multiple concepts share this normalized title or approved alias; "
            "identity is ambiguous."
        )
        return ConceptSearchResult(
            query=search_query,
            index_revision=revision,
            search_status=SearchStatus.COMPLETE,
            resolution_state=ResolutionState.AMBIGUOUS_RESULTS,
            exact_matches=list(identity.matches),
            ranked_concepts=[],
            module_hits=[],
            evidence=[],
            warnings=warnings,
            diagnostics=diagnostics if search_query.include_diagnostics else {},
        )

    return _tier1_hybrid(
        engine,
        search_query,
        revision=revision,
        warnings=warnings,
        diagnostics=diagnostics,
        options=opts,
    )


def _tier1_hybrid(
    engine: Engine,
    search_query: ConceptSearchQuery,
    *,
    revision: int,
    warnings: list[str],
    diagnostics: dict[str, Any],
    options: HybridSearchOptions,
) -> ConceptSearchResult:
    diagnostics["path"] = "tier1"
    limits = search_query.limits
    channel_limit = limits.channel
    weights = dict(options.rrf_weights or DEFAULT_RRF_WEIGHTS)
    status = SearchStatus.COMPLETE
    channel_errors: list[str] = []

    fts_concepts = search_concepts_fts(engine, search_query.text, limit=channel_limit)
    fts_modules = (
        search_modules_fts(engine, search_query.text, limit=channel_limit)
        if search_query.include_modules
        else []
    )

    identity_hits: list[VectorConceptHit] = []
    semantic_hits: list[VectorConceptHit] = []
    module_vector_hits: list[VectorModuleHit] = []

    try:
        identity_vec, semantic_vec, model_filter, vector_ready = _resolve_query_vectors(
            search_query.text, options
        )
    except Exception as exc:
        identity_vec = semantic_vec = None
        model_filter = None
        vector_ready = False
        channel_errors.append(f"query_embedding_failed: {exc}")
        warnings.append("Query embedding failed; using FTS-only results.")
    if not vector_ready:
        status = SearchStatus.PARTIAL
        warnings.append(
            "Vector channels skipped: provide embedding_provider or query vectors "
            "with model_filter."
        )
        diagnostics["vector_channels"] = "skipped"
    else:
        assert model_filter is not None
        assert identity_vec is not None
        assert semantic_vec is not None
        with ThreadPoolExecutor(max_workers=3) as pool:
            fut_id = pool.submit(
                search_concept_identity_vectors,
                engine,
                identity_vec,
                model_filter,
                limit=channel_limit,
                backend=options.vector_backend,
            )
            fut_sem = pool.submit(
                search_concept_semantic_vectors,
                engine,
                semantic_vec,
                model_filter,
                limit=channel_limit,
                backend=options.vector_backend,
            )
            fut_mod = None
            if search_query.include_modules:
                fut_mod = pool.submit(
                    search_module_semantic_vectors,
                    engine,
                    semantic_vec,
                    model_filter,
                    limit=channel_limit,
                    backend=options.vector_backend,
                )
            try:
                identity_hits = fut_id.result()
            except Exception as exc:
                channel_errors.append(f"identity_vector_failed: {exc}")
            try:
                semantic_hits = fut_sem.result()
            except Exception as exc:
                channel_errors.append(f"semantic_vector_failed: {exc}")
            if fut_mod is not None:
                try:
                    module_vector_hits = fut_mod.result()
                except Exception as exc:
                    channel_errors.append(f"module_vector_failed: {exc}")
        if channel_errors:
            status = SearchStatus.PARTIAL
            warnings.append("One or more vector channels failed; using available channels.")
            diagnostics["vector_channels"] = "partial"
        else:
            diagnostics["vector_channels"] = "ok"

    if channel_errors:
        diagnostics["channel_errors"] = channel_errors

    # Concept-level ranks (lexical and vector module hits contribute parent ids).
    lexical_concept_ranks = ranks_from_ordered_ids([hit.concept_id for hit in fts_concepts])
    for hit in fts_modules:
        current_rank = lexical_concept_ranks.get(hit.concept_id)
        if current_rank is None or hit.rank < current_rank:
            lexical_concept_ranks[hit.concept_id] = hit.rank
    channel_ranks: dict[str, dict[str, int]] = {
        SearchChannel.FTS.value: lexical_concept_ranks,
        SearchChannel.IDENTITY_VECTOR.value: ranks_from_ordered_ids(
            [hit.concept_id for hit in identity_hits]
        ),
        SearchChannel.SEMANTIC_VECTOR.value: ranks_from_ordered_ids(
            [hit.concept_id for hit in semantic_hits]
        ),
        SearchChannel.MODULE_VECTOR.value: ranks_from_ordered_ids(
            [hit.concept_id for hit in module_vector_hits]
        ),
    }
    fused = fuse_ranked_lists(
        channel_ranks,
        channel_weights=weights,
        constant=options.rrf_constant,
    )

    fts_score = {hit.concept_id: hit.score for hit in fts_concepts}
    fts_fields = {hit.concept_id: list(hit.matched_fields) for hit in fts_concepts}
    fts_excerpt = {hit.concept_id: hit.overview_excerpt for hit in fts_concepts}
    id_score = {hit.concept_id: hit.score for hit in identity_hits}
    id_rank = {hit.concept_id: hit.rank for hit in identity_hits}
    sem_score = {hit.concept_id: hit.score for hit in semantic_hits}
    sem_rank = {hit.concept_id: hit.rank for hit in semantic_hits}
    mod_parent_rank: dict[str, int] = {}
    mod_parent_score: dict[str, float] = {}
    for hit in module_vector_hits:
        mod_parent_rank.setdefault(hit.concept_id, hit.rank)
        mod_parent_score.setdefault(hit.concept_id, hit.score)

    # Module fusion (lexical + vector)
    module_channel_ranks: dict[str, dict[str, int]] = {
        SearchChannel.FTS.value: ranks_from_ordered_ids([m.module_id for m in fts_modules]),
        SearchChannel.MODULE_VECTOR.value: ranks_from_ordered_ids(
            [m.module_id for m in module_vector_hits]
        ),
    }
    module_weights = {
        SearchChannel.FTS.value: weights.get(SearchChannel.FTS.value, 1.0),
        SearchChannel.MODULE_VECTOR.value: weights.get(SearchChannel.MODULE_VECTOR.value, 1.0),
    }
    fused_modules = fuse_ranked_lists(
        module_channel_ranks,
        channel_weights=module_weights,
        constant=options.rrf_constant,
    )

    fts_mod_by_id = {m.module_id: m for m in fts_modules}
    vec_mod_by_id = {m.module_id: m for m in module_vector_hits}

    hybrid_modules: list[HybridModuleHit] = []
    modules_by_parent: dict[str, list[RankedModuleMatch]] = {}
    parent_filter_cache: dict[str, bool] = {}
    for module_id, fused_score in fused_modules:
        if len(hybrid_modules) >= limits.modules:
            break
        fts_m = fts_mod_by_id.get(module_id)
        vec_m = vec_mod_by_id.get(module_id)
        concept_id = (
            fts_m.concept_id
            if fts_m is not None
            else (vec_m.concept_id if vec_m is not None else "")
        )
        if _has_filters(search_query):
            if concept_id not in parent_filter_cache:
                parent = _enrich_concept(
                    engine,
                    concept_id,
                    fused_rank=0,
                    fused_score=0.0,
                    channels=[],
                    matched_fields=[],
                    overview_excerpt=None,
                    matching_modules=[],
                )
                parent_filter_cache[concept_id] = bool(
                    parent is not None and _passes_filters(parent, search_query)
                )
            if not parent_filter_cache[concept_id]:
                continue
        title = (
            fts_m.title
            if fts_m is not None
            else (vec_m.module_title if vec_m is not None else module_id)
        )
        channels: list[ChannelContribution] = []
        if fts_m is not None:
            channels.append(
                ChannelContribution(channel=SearchChannel.FTS, rank=fts_m.rank, score=fts_m.score)
            )
        if vec_m is not None:
            channels.append(
                ChannelContribution(
                    channel=SearchChannel.MODULE_VECTOR,
                    rank=vec_m.rank,
                    score=vec_m.score,
                )
            )
        parent_title = (
            fts_m.parent_canonical_title
            if fts_m is not None
            else (vec_m.parent_canonical_title if vec_m is not None else None)
        )
        heading = (
            fts_m.heading if fts_m is not None else (vec_m.heading if vec_m is not None else None)
        )
        anchor = (
            fts_m.anchor if fts_m is not None else (vec_m.anchor if vec_m is not None else None)
        )
        module_type = fts_m.module_type if fts_m is not None else None
        segment_id = vec_m.segment_id if vec_m is not None else ""
        hybrid = HybridModuleHit(
            module_id=module_id,
            concept_id=concept_id,
            parent_canonical_title=parent_title,
            title=title,
            module_type=module_type,
            segment_id=segment_id,
            heading=heading,
            anchor=anchor,
            channels=channels,
            fused_rank=len(hybrid_modules) + 1,
            fused_score=fused_score,
        )
        hybrid_modules.append(hybrid)
        if concept_id:
            modules_by_parent.setdefault(concept_id, []).append(
                RankedModuleMatch(
                    module_id=module_id,
                    title=title,
                    module_type=module_type,
                    segment_id=segment_id,
                    heading=heading,
                    anchor=anchor,
                    channels=channels,
                    fused_score=fused_score,
                )
            )

    ranked_concepts: list[RankedConceptCandidate] = []
    evidence: list[SearchEvidenceItem] = []
    for fused_rank, (concept_id, fused_score) in enumerate(fused, start=1):
        if len(ranked_concepts) >= limits.concepts:
            break
        candidate = _enrich_concept(
            engine,
            concept_id,
            fused_rank=fused_rank,
            fused_score=fused_score,
            channels=_concept_channels(
                concept_id,
                channel_ranks,
                fts_score=fts_score,
                id_score=id_score,
                id_rank=id_rank,
                sem_score=sem_score,
                sem_rank=sem_rank,
                mod_parent_rank=mod_parent_rank,
                mod_parent_score=mod_parent_score,
            ),
            matched_fields=fts_fields.get(concept_id, []),
            overview_excerpt=fts_excerpt.get(concept_id),
            matching_modules=modules_by_parent.get(concept_id, []),
        )
        if candidate is None:
            continue
        if not _passes_filters(candidate, search_query):
            continue
        ranked_concepts.append(candidate)
        evidence.append(
            SearchEvidenceItem(
                evidence_type="hybrid_fusion",
                summary=f"Fused rank {fused_rank}",
                concept_id=concept_id,
                details={
                    "fused_score": fused_score,
                    "channels": [c.channel.value for c in candidate.channels],
                },
            )
        )

    # Re-number fused_rank after filter drops
    for index, candidate in enumerate(ranked_concepts, start=1):
        candidate.fused_rank = index

    if not ranked_concepts and not hybrid_modules:
        state = ResolutionState.NO_RESULTS
    else:
        state = ResolutionState.RELATED_RESULTS

    if (
        not fts_concepts
        and not identity_hits
        and not semantic_hits
        and not module_vector_hits
        and status == SearchStatus.COMPLETE
    ):
        status = SearchStatus.FALLBACK

    diagnostics.update(
        {
            "fts_concept_count": len(fts_concepts),
            "fts_module_count": len(fts_modules),
            "identity_vector_count": len(identity_hits),
            "semantic_vector_count": len(semantic_hits),
            "module_vector_count": len(module_vector_hits),
            "rrf_constant": options.rrf_constant,
            "rrf_weights": weights,
            "ranked_concept_count": len(ranked_concepts),
        }
    )

    return ConceptSearchResult(
        query=search_query,
        index_revision=revision,
        search_status=status,
        resolution_state=state,
        exact_matches=[],
        ranked_concepts=ranked_concepts,
        module_hits=hybrid_modules if search_query.include_modules else [],
        evidence=evidence,
        warnings=warnings,
        diagnostics=diagnostics if search_query.include_diagnostics else {},
    )


def _resolve_query_vectors(
    text: str,
    options: HybridSearchOptions,
) -> tuple[list[float] | None, list[float] | None, ModelSpaceFilter | None, bool]:
    if options.model_filter is None:
        return None, None, None, False
    identity = options.query_identity_vector
    semantic = options.query_semantic_vector
    if identity is None or semantic is None:
        if options.embedding_provider is None:
            return None, None, None, False
        metadata = options.embedding_provider.model_metadata()
        model_filter = options.model_filter
        expected = (
            model_filter.model_id,
            model_filter.model_revision,
            model_filter.dimension,
            model_filter.normalizes_embeddings,
        )
        actual = (
            metadata.model_id,
            metadata.model_revision,
            metadata.dimension,
            metadata.normalizes_embeddings,
        )
        if actual != expected:
            raise ValueError(
                "Embedding provider metadata does not match the selected model space: "
                f"expected {expected!r}, got {actual!r}"
            )
        vector = embed_query(options.embedding_provider, text)
        identity = identity if identity is not None else vector
        semantic = semantic if semantic is not None else vector
    return identity, semantic, options.model_filter, True


def _concept_channels(
    concept_id: str,
    channel_ranks: dict[str, dict[str, int]],
    *,
    fts_score: dict[str, float],
    id_score: dict[str, float],
    id_rank: dict[str, int],
    sem_score: dict[str, float],
    sem_rank: dict[str, int],
    mod_parent_rank: dict[str, int],
    mod_parent_score: dict[str, float],
) -> list[ChannelContribution]:
    channels: list[ChannelContribution] = []
    fts_r = channel_ranks[SearchChannel.FTS.value].get(concept_id)
    if fts_r is not None:
        channels.append(
            ChannelContribution(
                channel=SearchChannel.FTS, rank=fts_r, score=fts_score.get(concept_id)
            )
        )
    if concept_id in id_rank:
        channels.append(
            ChannelContribution(
                channel=SearchChannel.IDENTITY_VECTOR,
                rank=id_rank[concept_id],
                score=id_score.get(concept_id),
            )
        )
    if concept_id in sem_rank:
        channels.append(
            ChannelContribution(
                channel=SearchChannel.SEMANTIC_VECTOR,
                rank=sem_rank[concept_id],
                score=sem_score.get(concept_id),
            )
        )
    if concept_id in mod_parent_rank:
        channels.append(
            ChannelContribution(
                channel=SearchChannel.MODULE_VECTOR,
                rank=mod_parent_rank[concept_id],
                score=mod_parent_score.get(concept_id),
            )
        )
    return channels


def _passes_filters(candidate: RankedConceptCandidate, query: ConceptSearchQuery) -> bool:
    filters = query.filters
    if filters.domains and not any(d in filters.domains for d in candidate.domains):
        return False
    if filters.concept_types and (
        candidate.concept_type is None or candidate.concept_type not in filters.concept_types
    ):
        return False
    if filters.vault_statuses and (
        candidate.vault_status is None or candidate.vault_status not in filters.vault_statuses
    ):
        return False
    review_ok = not filters.review_statuses or (
        candidate.review_status is not None and candidate.review_status in filters.review_statuses
    )
    return review_ok


def _has_filters(query: ConceptSearchQuery) -> bool:
    filters = query.filters
    return bool(
        filters.domains
        or filters.concept_types
        or filters.vault_statuses
        or filters.review_statuses
    )


def _load_ranked_exact(engine: Engine, match: IdentityMatch) -> RankedConceptCandidate | None:
    return _enrich_concept(
        engine,
        match.concept_id,
        fused_rank=1,
        fused_score=1.0,
        channels=[],
        matched_fields=[match.match_type.value],
        overview_excerpt=None,
        matching_modules=[],
    )


def _enrich_concept(
    engine: Engine,
    concept_id: str,
    *,
    fused_rank: int,
    fused_score: float,
    channels: list[ChannelContribution],
    matched_fields: list[str],
    overview_excerpt: str | None,
    matching_modules: list[RankedModuleMatch],
) -> RankedConceptCandidate | None:
    with engine.connect() as connection:
        concept = concepts.get_concept(connection, concept_id)
        if concept is None:
            return None
        alias_rows = aliases.list_aliases_for_concept(connection, concept_id)
        domain_rows = domains.list_domains_for_concept(connection, concept_id)
    return RankedConceptCandidate(
        concept_id=concept_id,
        canonical_title=str(concept["canonical_title"]),
        aliases=[str(row["alias"]) for row in alias_rows],
        concept_type=None if concept.get("concept_type") is None else str(concept["concept_type"]),
        domains=[str(row["domain"]) for row in domain_rows],
        overview_excerpt=overview_excerpt,
        status=None if concept.get("status") is None else str(concept["status"]),
        vault_status=(
            None if concept.get("vault_status") is None else str(concept["vault_status"])
        ),
        review_status=(
            None if concept.get("review_status") is None else str(concept["review_status"])
        ),
        channels=channels,
        matched_fields=matched_fields,
        fused_rank=fused_rank,
        fused_score=fused_score,
        matching_modules=matching_modules,
        evidence=[],
    )
