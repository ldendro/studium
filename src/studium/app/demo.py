"""Deterministic, coherent demonstration workspace for product evaluation."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from studium.app.learning import (
    BacklogService,
    MasteryService,
    ProfileService,
    RetentionService,
)
from studium.app.learning_models import (
    BacklogItemType,
    BacklogOrigin,
    ProfileCategory,
)
from studium.app.workspace import WorkspaceContext
from studium.review import ReviewService
from studium.schemas import (
    ConceptType,
    ContributionStatus,
    EncounterRole,
    LearningEncounter,
    LearningRole,
    NoteStatus,
    NoteVaultStatus,
    RelationshipConfidence,
    RelationshipMetadata,
    RelationshipStatus,
    RelationshipType,
    RelationshipVaultStatus,
    ReviewStatus,
    ScaffoldModuleMetadata,
    ScaffoldModuleOrigin,
    ScaffoldModuleStatus,
    ScaffoldModuleType,
    SourceMetadata,
    SourceType,
)
from studium.serialization import build_concept_note_metadata, serialize_concept_note
from studium.serialization.concept_id import generate_concept_id, slugify_title
from studium.sources import SourceService
from studium.writes import build_create_note_proposal


@dataclass(frozen=True, slots=True)
class DemoModule:
    identifier: str
    title: str
    module_type: ScaffoldModuleType
    content: str


@dataclass(frozen=True, slots=True)
class DemoConcept:
    title: str
    aliases: tuple[str, ...]
    concept_type: ConceptType
    domains: tuple[str, ...]
    overview: str
    modules: tuple[DemoModule, ...]
    relationships: tuple[tuple[RelationshipType, str, LearningRole], ...] = ()
    accepted: bool = True


def seed_demo_workspace(workspace: WorkspaceContext) -> dict[str, Any]:
    """Populate all primary workflows without bypassing safe note proposals."""

    source_service = SourceService(workspace)
    source, duplicate = source_service.stage_upload(
        filename="optimization-field-notes.md",
        mime_type="text/markdown",
        title="Optimization Field Notes",
        content=_DEMO_SOURCE.encode("utf-8"),
    )
    if not duplicate or str(source["status"]) != "ready":
        source_service.process(str(source["id"]), progress=_ignore_progress)

    created_concepts: list[str] = []
    for definition in _DEMO_CONCEPTS:
        concept_id = generate_concept_id(definition.title)
        relative_path = f"concepts/{slugify_title(definition.title).replace('_', '-')}.md"
        if workspace.vault.exists(relative_path):
            continue
        markdown = _concept_markdown(
            definition,
            source_id=str(source["id"]),
        )
        proposal = build_create_note_proposal(workspace.vault, relative_path, markdown)
        workspace.commit(proposal)
        created_concepts.append(concept_id)

    gradient_id = generate_concept_id("Gradient Descent")
    contribution = source_service.analyze_contribution(
        source_id=str(source["id"]),
        concept_id=gradient_id,
        focus="learning-rate stability and convergence",
    )
    source_service.decide_contribution(contribution.id, "accepted")

    backlog = BacklogService(workspace).create(
        title="Adaptive Learning Rates",
        item_type=BacklogItemType.CONCEPT_EXPANSION,
        reason="Compare fixed learning rates with adaptive schedules after mastering stability.",
        origin=BacklogOrigin.GRAPH,
        priority=78,
        related_concept_id=generate_concept_id("Learning Rate"),
        required_by=[gradient_id],
        source_query="adaptive optimizer learning-rate schedule",
    )
    profile = ProfileService(workspace)
    profile.create(
        category=ProfileCategory.LEARNING_PREFERENCE,
        statement="Prefer mechanism-first explanations followed by a small worked example.",
        evidence=[{"source": "demo_setup", "signal": "explicit preference"}],
        confidence=0.95,
        pinned=True,
    )
    profile.create(
        category=ProfileCategory.TOPIC_PRIORITY,
        statement="Prioritize optimization concepts and implementation failure modes.",
        evidence=[{"source": "demo_setup", "signal": "active learning goal"}],
        confidence=0.9,
    )

    retention = RetentionService(workspace)
    cards = retention.generate()
    if cards:
        first = cards[0]
        response = " ".join(first.expected_components) or (
            "Explain the mechanism, assumptions, boundary, and smallest checkable example."
        )
        retention.review(
            first.id,
            response=response,
            self_rating=4,
            confidence=4,
            latency_ms=42_000,
        )
    mastery = MasteryService(workspace).recompute()

    momentum_id = generate_concept_id("Momentum Optimization")
    review_session = None
    with suppress(KeyError, ValueError):
        review_session = ReviewService(workspace).submit(momentum_id)
    return {
        "seeded": True,
        "created_concepts": created_concepts,
        "source_id": str(source["id"]),
        "backlog_id": backlog.id,
        "retention_cards": len(cards),
        "mastery_records": len(mastery),
        "review_id": None if review_session is None else review_session.id,
    }


def _concept_markdown(definition: DemoConcept, *, source_id: str) -> str:
    identifiers = {
        title: generate_concept_id(title) for title in {item.title for item in _DEMO_CONCEPTS}
    }
    modules = [
        ScaffoldModuleMetadata(
            id=module.identifier,
            type=module.module_type,
            title=module.title,
            status=(
                ScaffoldModuleStatus.COMPLETED
                if definition.accepted
                else ScaffoldModuleStatus.IN_PROGRESS
            ),
            origin=ScaffoldModuleOrigin.MANUAL,
            focus=f"Reconstruct {definition.title} through {module.title.casefold()}.",
        )
        for module in definition.modules
    ]
    relationships = [
        RelationshipMetadata(
            relationship_type=relationship_type,
            target_title=target,
            target_id=identifiers[target],
            vault_status=RelationshipVaultStatus.FOUND,
            learning_role=learning_role,
            confidence=RelationshipConfidence.HIGH,
            status=RelationshipStatus.USER_CONFIRMED,
        )
        for relationship_type, target, learning_role in definition.relationships
    ]
    encounter = LearningEncounter(
        source=SourceMetadata(
            type=SourceType.ARTICLE,
            title="Optimization Field Notes",
            section=definition.title,
        ),
        role=EncounterRole.PRIMARY,
        contribution_status=ContributionStatus.SOURCE_ANALYZED,
        content_attached=True,
        content_id=source_id,
    )
    metadata = build_concept_note_metadata(
        definition.title,
        aliases=list(definition.aliases),
        concept_type=definition.concept_type,
        concept_domains=list(definition.domains),
        status=NoteStatus.COMPLETED if definition.accepted else NoteStatus.IN_PROGRESS,
        review_status=ReviewStatus.APPROVED if definition.accepted else ReviewStatus.NOT_SUBMITTED,
        vault_status=NoteVaultStatus.ACCEPTED if definition.accepted else NoteVaultStatus.DRAFT,
        learning_encounters=[encounter],
        scaffold_modules=modules,
        relationships=relationships,
    )
    module_index = "\n".join(
        f"- [x] [[#{module.title}|{module.title}]] - `{module.module_type.value}`"
        for module in definition.modules
    )
    module_body = "\n\n".join(
        f"### {module.title}\n\n{module.content}" for module in definition.modules
    )
    prerequisites = [
        f"- [[{target}]] - {role.value.replace('_', ' ')}"
        for relation, target, role in definition.relationships
        if relation == RelationshipType.DEPENDS_ON
    ]
    related = [
        f"- [[{target}]] - {relation.value.replace('_', ' ')}"
        for relation, target, _role in definition.relationships
        if relation != RelationshipType.DEPENDS_ON
    ]
    open_questions = (
        "No blocking gaps remain."
        if definition.accepted
        else "- [ ] Contrast momentum with an adaptive learning-rate method."
    )
    body = f"""# {definition.title}

## Concept Overview

{definition.overview}

## Prerequisites

{chr(10).join(prerequisites) or "No additional prerequisite is required for this note."}

## Module Index

{module_index}

## Scaffold Modules

{module_body}

## Related Concepts

{chr(10).join(related) or "Connections are captured as the workspace develops."}

## Open Questions / Gaps

{open_questions}
"""
    return serialize_concept_note(metadata, body)


def _ignore_progress(_value: float, _message: str | None = None) -> None:
    return None


_DEMO_SOURCE = """# Optimization Field Notes

Gradient descent minimizes an objective by moving parameters opposite the local gradient.
The learning rate scales that step. A rate that is too large can overshoot a narrow valley,
while a very small rate makes useful progress needlessly slow.

## Momentum

Momentum accumulates an exponentially decayed velocity. It can damp oscillation across a
steep direction while preserving progress along a shallow direction. The velocity state and
decay coefficient are part of the algorithm, not merely implementation details.

## Diagnostic checks

For example, plot objective value and gradient norm together. A falling objective with a
persistently large gradient may indicate unstable steps; a flat objective and tiny updates
may indicate a learning rate that is too conservative.
"""


_DEMO_CONCEPTS = (
    DemoConcept(
        title="Derivatives",
        aliases=("Local Rate of Change",),
        concept_type=ConceptType.MATHEMATICAL_CONCEPT,
        domains=("calculus", "machine_learning"),
        overview=(
            "A derivative is a local linear model of how an output changes as an input changes. "
            "Its sign gives direction and its magnitude gives local sensitivity."
        ),
        modules=(
            DemoModule(
                "module_derivatives_reconstruction",
                "Conceptual Reconstruction",
                ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
                "Reconstruct the derivative as the limit of secant slopes, then explain why the "
                "result is only a local approximation.",
            ),
            DemoModule(
                "module_derivatives_example",
                "Worked Example",
                ScaffoldModuleType.WORKED_EXAMPLE,
                "For f(x)=x², expand f(x+h)-f(x), divide by h, and take h toward zero. Check the "
                "result at x=3 against a nearby finite difference.",
            ),
        ),
    ),
    DemoConcept(
        title="Learning Rate",
        aliases=("Step Size",),
        concept_type=ConceptType.MATHEMATICAL_CONCEPT,
        domains=("machine_learning", "optimization"),
        overview=(
            "The learning rate controls how far an optimizer moves along its chosen direction. "
            "It trades immediate progress against stability."
        ),
        modules=(
            DemoModule(
                "module_learning_rate_reconstruction",
                "Stability Mechanism",
                ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
                "Explain why curvature turns one globally fixed step size into different local "
                "stability limits across directions.",
            ),
            DemoModule(
                "module_learning_rate_debugging",
                "Misconception Debugging",
                ScaffoldModuleType.MISCONCEPTION_DEBUGGING,
                "A lower loss after one step does not prove stability. Check a trajectory, "
                "gradient norms, and sensitivity to a modest rate change.",
            ),
        ),
    ),
    DemoConcept(
        title="Gradient Descent",
        aliases=("Steepest Descent", "GD"),
        concept_type=ConceptType.ALGORITHM,
        domains=("machine_learning", "optimization"),
        overview=(
            "Gradient descent repeatedly follows the negative gradient because that direction "
            "gives the fastest local decrease under the Euclidean norm."
        ),
        modules=(
            DemoModule(
                "module_gradient_descent_reconstruction",
                "Mechanism From Memory",
                ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
                "State the objective, compute a gradient, choose a learning rate, update state, "
                "and explain the local assumption behind the direction.",
            ),
            DemoModule(
                "module_gradient_descent_example",
                "One-Dimensional Worked Example",
                ScaffoldModuleType.WORKED_EXAMPLE,
                "From x=4 on f(x)=x² with rate 0.1, x'=3.2. Verify that the objective falls "
                "and compare with a rate of 1.1.",
            ),
            DemoModule(
                "module_gradient_descent_implementation",
                "Implementation and Checks",
                ScaffoldModuleType.CODE_IMPLEMENTATION,
                "Track objective value, gradient norm, and finite values. Stop from an explicit "
                "criterion rather than assuming a fixed iteration count means convergence.",
            ),
        ),
        relationships=(
            (
                RelationshipType.DEPENDS_ON,
                "Derivatives",
                LearningRole.MATHEMATICAL_PREREQUISITE,
            ),
            (
                RelationshipType.RELATED_TO,
                "Learning Rate",
                LearningRole.SUPPORTING_CONCEPT,
            ),
        ),
    ),
    DemoConcept(
        title="Bias-Variance Tradeoff",
        aliases=("Bias Variance Decomposition",),
        concept_type=ConceptType.THEORY_CONCEPT,
        domains=("machine_learning", "statistics"),
        overview=(
            "Expected prediction error can be reasoned about through systematic bias, sensitivity "
            "to the sampled training set, and irreducible noise."
        ),
        modules=(
            DemoModule(
                "module_bias_variance_comparison",
                "Model Capacity Comparison",
                ScaffoldModuleType.COMPARISON,
                "Compare a rigid linear model and a high-capacity tree by mechanism, not by the "
                "slogan that one always underfits and the other always overfits.",
            ),
            DemoModule(
                "module_bias_variance_application",
                "Diagnostic Application",
                ScaffoldModuleType.APPLICATION,
                "Use training and validation learning curves to distinguish limited capacity from "
                "variance caused by sensitivity to the training sample.",
            ),
        ),
    ),
    DemoConcept(
        title="Momentum Optimization",
        aliases=("Momentum",),
        concept_type=ConceptType.ALGORITHM,
        domains=("machine_learning", "optimization"),
        overview=(
            "Momentum keeps a decayed velocity so repeated gradient directions accumulate while "
            "alternating directions partially cancel."
        ),
        modules=(
            DemoModule(
                "module_momentum_reconstruction",
                "Velocity Reconstruction",
                ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
                "Explain the velocity update and parameter update, then identify what the decay "
                "coefficient controls.",
            ),
        ),
        relationships=(
            (
                RelationshipType.DEPENDS_ON,
                "Gradient Descent",
                LearningRole.CONCEPTUAL_PREREQUISITE,
            ),
        ),
        accepted=False,
    ),
)
