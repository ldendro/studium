"""Rebuild embedding work from current index projections."""

from __future__ import annotations

from sqlalchemy import Engine

from studium.index.repositories import aliases as aliases_repo
from studium.index.repositories import concepts as concepts_repo
from studium.index.repositories import domains as domains_repo
from studium.index.repositories import scaffold_modules as scaffold_modules_repo
from studium.index.sync.embedding_inputs import (
    build_identity_embedding_input,
    build_module_embedding_input,
    build_semantic_embedding_input,
)
from studium.index.sync.hashes import hash_text
from studium.index.sync.models import EmbeddingWorkRequest


def enumerate_embedding_work(engine: Engine) -> list[EmbeddingWorkRequest]:
    """Build work for every current concept/module projection in the index.

    Used for retry, model-change, and missing-row repair when ``sync_vault``
    emits an empty ``embedding_work`` list because vault files are unchanged.
    Input texts are reconstructed from indexed columns (matching B03 builders;
    module body is empty until body extraction is stored in the index).
    """
    work: list[EmbeddingWorkRequest] = []
    with engine.connect() as connection:
        for concept in concepts_repo.list_concepts(connection):
            concept_id = str(concept["concept_id"])
            aliases = [
                str(row["alias"])
                for row in aliases_repo.list_aliases_for_concept(connection, concept_id)
            ]
            domains = [
                str(row["domain"])
                for row in domains_repo.list_domains_for_concept(connection, concept_id)
            ]
            title = str(concept["canonical_title"])
            overview = concept.get("overview_plaintext")
            overview_text = "" if overview is None else str(overview)

            identity_text = build_identity_embedding_input(canonical_title=title, aliases=aliases)
            work.append(
                EmbeddingWorkRequest(
                    owner_type="concept",
                    owner_id=concept_id,
                    embedding_type="concept_identity",
                    input_hash=hash_text(identity_text),
                    input_text=identity_text,
                    parent_concept_id=concept_id,
                )
            )

            semantic_text = build_semantic_embedding_input(
                canonical_title=title,
                aliases=aliases,
                concept_type=str(concept["concept_type"]),
                domains=domains,
                overview_plaintext=overview_text,
            )
            work.append(
                EmbeddingWorkRequest(
                    owner_type="concept",
                    owner_id=concept_id,
                    embedding_type="concept_semantic",
                    input_hash=hash_text(semantic_text),
                    input_text=semantic_text,
                    parent_concept_id=concept_id,
                )
            )

            for module in scaffold_modules_repo.list_modules_for_concept(connection, concept_id):
                module_id = str(module["module_id"])
                focus = module.get("focus")
                module_text = build_module_embedding_input(
                    title=str(module["title"]),
                    module_type=str(module["type"]),
                    focus=None if focus is None else str(focus),
                    body="",
                )
                work.append(
                    EmbeddingWorkRequest(
                        owner_type="scaffold_module",
                        owner_id=module_id,
                        embedding_type="module_semantic",
                        input_hash=hash_text(module_text),
                        input_text=module_text,
                        parent_concept_id=concept_id,
                        segment_id=f"{module_id}:0",
                    )
                )
    return work
