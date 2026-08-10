"""Provider-agnostic local LLM infrastructure and reasoning tasks."""

from studium.llm.deterministic import DeterministicLLMProvider
from studium.llm.openai_compat import OpenAICompatibleProvider
from studium.llm.protocol import LLMProvider, ProviderHealth, StructuredGenerationResult
from studium.llm.reasoning import (
    ALL_REASONING_TASKS,
    ConceptIdentityDecision,
    reason_identity,
    reason_new_concept,
)
from studium.llm.runner import extract_json_object, run_reasoning_task
from studium.llm.tasks import TaskConfig, TaskDefinition, render_user_prompt

# Selected default for OpenAI-compatible local servers (B10 selection note).
DEFAULT_REASONING_MODEL = "llama3.2:3b"
DEFAULT_LLM_BASE_URL = "http://127.0.0.1:11434/v1"

__all__ = [
    "ALL_REASONING_TASKS",
    "DEFAULT_LLM_BASE_URL",
    "DEFAULT_REASONING_MODEL",
    "ConceptIdentityDecision",
    "DeterministicLLMProvider",
    "LLMProvider",
    "OpenAICompatibleProvider",
    "ProviderHealth",
    "StructuredGenerationResult",
    "TaskConfig",
    "TaskDefinition",
    "extract_json_object",
    "reason_identity",
    "reason_new_concept",
    "render_user_prompt",
    "run_reasoning_task",
]
