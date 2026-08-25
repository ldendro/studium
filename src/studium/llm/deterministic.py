"""Deterministic LLM provider for unit tests and CI."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from studium.llm.protocol import ProviderHealth


class DeterministicLLMProvider:
    """Returns scripted JSON responses keyed by substrings in the user prompt."""

    def __init__(
        self,
        *,
        model_id: str = "deterministic-test",
        responses: dict[str, dict[str, Any]] | None = None,
        default_response: dict[str, Any] | None = None,
        healthy: bool = True,
        handler: Callable[[str, str], dict[str, Any]] | None = None,
    ) -> None:
        self._model_id = model_id
        self._responses = dict(responses or {})
        self._default = default_response or {}
        self._healthy = healthy
        self._handler = handler
        self.calls: list[tuple[str, str]] = []

    def model_id(self) -> str:
        return self._model_id

    def check_health(self) -> ProviderHealth:
        return ProviderHealth(
            healthy=self._healthy,
            ready=self._healthy,
            model_id=self._model_id,
            message="ok" if self._healthy else "provider unavailable",
        )

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: float,
    ) -> str:
        _ = temperature, max_tokens, timeout_seconds
        self.calls.append((system_prompt, user_prompt))
        if not self._healthy:
            msg = "Deterministic provider is unhealthy"
            raise RuntimeError(msg)
        if self._handler is not None:
            payload = self._handler(system_prompt, user_prompt)
            return json.dumps(payload)
        for needle, payload in self._responses.items():
            if needle in user_prompt:
                return json.dumps(payload)
        return json.dumps(self._default)
