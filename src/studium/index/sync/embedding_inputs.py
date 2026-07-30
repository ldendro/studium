"""Deterministic embedding input builders (Technical Plan §4.11)."""

from __future__ import annotations

from studium.schemas import ConceptNoteMetadata
from studium.schemas.scaffold_module import ScaffoldModuleMetadata


def build_identity_embedding_input(
    *,
    canonical_title: str,
    aliases: list[str],
) -> str:
    alias_text = ", ".join(aliases)
    return f"Title: {canonical_title}\nAliases: {alias_text}"


def build_semantic_embedding_input(
    *,
    canonical_title: str,
    aliases: list[str],
    concept_type: str,
    domains: list[str],
    overview_plaintext: str,
) -> str:
    alias_text = ", ".join(aliases)
    domain_text = ", ".join(domains)
    return (
        f"Title: {canonical_title}\n"
        f"Aliases: {alias_text}\n"
        f"Concept Type: {concept_type}\n"
        f"Domains: {domain_text}\n"
        f"Overview: {overview_plaintext}"
    )


def build_module_embedding_input(
    *,
    title: str,
    module_type: str,
    focus: str | None,
    body: str = "",
) -> str:
    focus_text = focus or ""
    return f"Module Title: {title}\nModule Type: {module_type}\nFocus: {focus_text}\nBody: {body}"


def identity_input_from_metadata(metadata: ConceptNoteMetadata) -> str:
    return build_identity_embedding_input(
        canonical_title=metadata.canonical_title,
        aliases=list(metadata.aliases),
    )


def semantic_input_from_metadata(
    metadata: ConceptNoteMetadata,
    *,
    overview_plaintext: str,
) -> str:
    return build_semantic_embedding_input(
        canonical_title=metadata.canonical_title,
        aliases=list(metadata.aliases),
        concept_type=str(metadata.concept_type),
        domains=list(metadata.concept_domains),
        overview_plaintext=overview_plaintext,
    )


def module_input_from_metadata(module: ScaffoldModuleMetadata, *, body: str = "") -> str:
    return build_module_embedding_input(
        title=module.title,
        module_type=str(module.type),
        focus=module.focus,
        body=body,
    )
