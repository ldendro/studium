"""OpenAI-compatible local HTTP server adapter."""

from __future__ import annotations

import json
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from studium.llm.protocol import ProviderHealth


class OpenAICompatibleProvider:
    """Minimal chat-completions client for Ollama / LM Studio / llama.cpp server."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434/v1",
        model_id: str = "llama3.2:3b",
        api_key: str = "ollama",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_id = model_id
        self._api_key = api_key

    def model_id(self) -> str:
        return self._model_id

    def check_health(self) -> ProviderHealth:
        try:
            payload = cast(
                dict[str, Any],
                self._request("GET", "/models", body=None, timeout_seconds=5.0),
            )
            data = payload.get("data")
            models = cast(list[Any], data) if isinstance(data, list) else []
            model_objects = [
                cast(dict[str, Any], item) for item in models if isinstance(item, dict)
            ]
            model_ids = {str(item["id"]) for item in model_objects if item.get("id") is not None}
            ready = self._model_id in model_ids
            return ProviderHealth(
                healthy=True,
                ready=ready,
                model_id=self._model_id,
                message="reachable" if ready else f"Model {self._model_id!r} is not available",
                details={"model_count": len(models), "model_ids": sorted(model_ids)},
            )
        except Exception as exc:
            return ProviderHealth(
                healthy=False,
                ready=False,
                model_id=self._model_id,
                message=str(exc),
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
        body = {
            "model": self._model_id,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        payload = cast(
            dict[str, Any],
            self._request(
                "POST",
                "/chat/completions",
                body=body,
                timeout_seconds=timeout_seconds,
            ),
        )
        try:
            choices = cast(list[Any], payload["choices"])
            message = cast(dict[str, Any], choices[0]["message"])
            return str(message["content"])
        except (KeyError, IndexError, TypeError) as exc:
            msg = f"Unexpected chat completion shape: {exc}"
            raise RuntimeError(msg) from exc

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None,
        timeout_seconds: float,
    ) -> Any:
        url = f"{self._base_url}{path}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            msg = f"HTTP {exc.code}: {detail}"
            raise RuntimeError(msg) from exc
        except URLError as exc:
            msg = f"Provider unreachable: {exc.reason}"
            raise RuntimeError(msg) from exc
        if not raw:
            return {}
        return json.loads(raw)
