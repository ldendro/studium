"""Versioned reasoning task definitions and prompts."""

from __future__ import annotations

from studium.llm.reasoning.schemas import (
    AliasProposalDecision,
    ClarificationDecision,
    ConceptIdentityDecision,
    NewConceptAnalysis,
    RelationshipAndPrerequisiteAnalysis,
    ScaffoldModuleIntentDecision,
    SourceEncounterAmbiguityDecision,
)
from studium.llm.tasks import TaskConfig, TaskDefinition

IDENTITY_TASK = TaskDefinition(
    task_id="concept_identity",
    version="1",
    system_prompt=(
        "You decide whether a query refers to an existing concept candidate, "
        "a distinct related concept, or lacks enough information."
    ),
    user_template=(
        "Query: {query}\n"
        "Candidates (JSON):\n{candidates_json}\n"
        "Return ConceptIdentityDecision JSON."
    ),
    output_schema=ConceptIdentityDecision,
    config=TaskConfig(temperature=0.0, max_tokens=512),
)

NEW_CONCEPT_TASK = TaskDefinition(
    task_id="new_concept_analysis",
    version="1",
    system_prompt=(
        "Analyze a likely new concept: suggest type, domains, graph positions, "
        "and missing prerequisites. Do not invent vault IDs that were not provided."
    ),
    user_template=(
        "Query: {query}\nContext (JSON):\n{context_json}\nReturn NewConceptAnalysis JSON."
    ),
    output_schema=NewConceptAnalysis,
)

MODULE_INTENT_TASK = TaskDefinition(
    task_id="module_intent",
    version="1",
    system_prompt=(
        "Decide whether scaffold-module intent should attach to an existing concept, "
        "create with a new concept, is redundant, or is unclear."
    ),
    user_template=(
        "Query: {query}\n"
        "Candidates (JSON):\n{candidates_json}\n"
        "Return ScaffoldModuleIntentDecision JSON."
    ),
    output_schema=ScaffoldModuleIntentDecision,
)

RELATIONSHIP_TASK = TaskDefinition(
    task_id="relationship_prerequisite",
    version="1",
    system_prompt=(
        "Propose relationship types, learning roles, directions, and missing prerequisites "
        "for a concept relative to narrowed candidates."
    ),
    user_template=(
        "Query: {query}\n"
        "Context (JSON):\n{context_json}\n"
        "Return RelationshipAndPrerequisiteAnalysis JSON."
    ),
    output_schema=RelationshipAndPrerequisiteAnalysis,
)

SOURCE_AMBIGUITY_TASK = TaskDefinition(
    task_id="source_ambiguity",
    version="1",
    system_prompt="Resolve ambiguous learning-encounter comparisons using metadata only.",
    user_template=(
        "Candidate source (JSON): {candidate_json}\n"
        "Existing encounters (JSON): {existing_json}\n"
        "Prior matcher outcome: {prior_outcome}\n"
        "Return SourceEncounterAmbiguityDecision JSON."
    ),
    output_schema=SourceEncounterAmbiguityDecision,
)

ALIAS_PROPOSAL_TASK = TaskDefinition(
    task_id="alias_proposal",
    version="1",
    system_prompt=(
        "Propose an alias for a target concept, or reject poor aliases. "
        "Note collisions if present in context."
    ),
    user_template=(
        "Proposed alias: {alias}\n"
        "Target concept: {target_concept_id} ({target_title})\n"
        "Collision context (JSON): {collision_json}\n"
        "Return AliasProposalDecision JSON."
    ),
    output_schema=AliasProposalDecision,
)

CLARIFICATION_TASK = TaskDefinition(
    task_id="clarification",
    version="1",
    system_prompt=(
        "Decide whether the user input is vague and needs clarification before "
        "creating a low-quality concept."
    ),
    user_template=(
        "Query: {query}\nSearch resolution: {resolution_state}\nReturn ClarificationDecision JSON."
    ),
    output_schema=ClarificationDecision,
)

ALL_REASONING_TASKS: tuple[TaskDefinition, ...] = (
    IDENTITY_TASK,
    NEW_CONCEPT_TASK,
    MODULE_INTENT_TASK,
    RELATIONSHIP_TASK,
    SOURCE_AMBIGUITY_TASK,
    ALIAS_PROPOSAL_TASK,
    CLARIFICATION_TASK,
)

TASKS_BY_ID: dict[str, TaskDefinition] = {task.task_id: task for task in ALL_REASONING_TASKS}
