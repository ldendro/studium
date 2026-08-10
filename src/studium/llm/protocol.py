"""Provider-agnostic structured LLM generation protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class ProviderHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    healthy: bool
    ready: bool
    model_id: str | None = None
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class StructuredGenerationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    data: dict[str, Any] | None = None
    raw_text: str | None = None
    repaired: bool = False
    error_code: str | None = None
    message: str | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    def model_id(self) -> str:
        """Active model identifier."""
        ...

    def check_health(self) -> ProviderHealth:
        """Health and readiness for structured generation."""
        ...

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: float,
    ) -> str:
        """Return model text (may include JSON). Raises on hard failure."""
        ...
