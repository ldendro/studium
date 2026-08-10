"""Structured generation with validation and a single repair attempt."""

from __future__ import annotations

import json
import re
from typing import Any, cast

from pydantic import ValidationError

from studium.llm.protocol import LLMProvider, StructuredGenerationResult
from studium.llm.tasks import TaskDefinition, render_user_prompt

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from model text (raw or fenced)."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        loaded: object = json.loads(stripped)
        if isinstance(loaded, dict):
            return cast(dict[str, Any], loaded)
    except json.JSONDecodeError:
        pass
    match = _JSON_OBJECT_RE.search(text)
    if match is None:
        msg = "No JSON object found in model output"
        raise ValueError(msg)
    loaded = json.loads(match.group(0))
    if not isinstance(loaded, dict):
        msg = "JSON payload is not an object"
        raise ValueError(msg)
    return cast(dict[str, Any], loaded)


def run_reasoning_task(
    provider: LLMProvider,
    task: TaskDefinition,
    prompt_values: dict[str, Any],
) -> StructuredGenerationResult:
    """Generate, validate, and optionally repair structured task output once."""
    health = provider.check_health()
    if not health.healthy or not health.ready:
        return StructuredGenerationResult(
            ok=False,
            error_code="provider_unavailable",
            message=health.message or "Provider is not healthy",
            diagnostics={"privacy": "prompt_omitted"},
        )

    user_prompt = render_user_prompt(task.user_template, prompt_values)
    system_prompt = (
        f"{task.system_prompt}\n\n"
        "Respond with a single JSON object matching the required schema. "
        "Do not include markdown commentary."
    )
    diagnostics: dict[str, Any] = {
        "task_id": task.qualified_id,
        "model_id": provider.model_id(),
        "privacy": "prompt_omitted",
    }

    try:
        raw = provider.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=task.config.temperature,
            max_tokens=task.config.max_tokens,
            timeout_seconds=task.config.timeout_seconds,
        )
    except Exception as exc:
        return StructuredGenerationResult(
            ok=False,
            error_code="generation_failed",
            message=str(exc),
            diagnostics=diagnostics,
        )

    validated = _validate(task, raw, diagnostics=diagnostics, repaired=False)
    if validated.ok:
        return validated
    if not task.config.repair_enabled:
        return validated

    repair_system = (
        f"{system_prompt}\n\n"
        "Your previous answer was invalid. Return corrected JSON only.\n"
        f"Validation error: {validated.message}"
    )
    try:
        repaired_raw = provider.generate_text(
            system_prompt=repair_system,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=task.config.max_tokens,
            timeout_seconds=task.config.repair_timeout_seconds,
        )
    except Exception as exc:
        return StructuredGenerationResult(
            ok=False,
            raw_text=raw,
            error_code="repair_failed",
            message=str(exc),
            diagnostics=diagnostics,
        )
    return _validate(task, repaired_raw, diagnostics=diagnostics, repaired=True)


def _validate(
    task: TaskDefinition,
    raw: str,
    *,
    diagnostics: dict[str, Any],
    repaired: bool,
) -> StructuredGenerationResult:
    try:
        payload = extract_json_object(raw)
        model = task.output_schema.model_validate(payload)
    except (ValueError, ValidationError, json.JSONDecodeError) as exc:
        return StructuredGenerationResult(
            ok=False,
            raw_text=raw,
            repaired=repaired,
            error_code="invalid_structured_output",
            message=str(exc),
            diagnostics=diagnostics,
        )
    return StructuredGenerationResult(
        ok=True,
        data=model.model_dump(mode="json"),
        raw_text=raw,
        repaired=repaired,
        diagnostics=diagnostics,
    )
