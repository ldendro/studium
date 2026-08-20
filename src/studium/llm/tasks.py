"""Versioned reasoning task assets and configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict


class TaskConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = 0.0
    max_tokens: int = 1024
    timeout_seconds: float = 60.0
    repair_enabled: bool = True
    repair_timeout_seconds: float = 30.0


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    """Versioned task asset: prompt + config + schema id."""

    task_id: str
    version: str
    system_prompt: str
    user_template: str
    output_schema: type[BaseModel]
    config: TaskConfig = field(default_factory=TaskConfig)

    @property
    def qualified_id(self) -> str:
        return f"{self.task_id}_v{self.version}"


def render_user_prompt(template: str, values: dict[str, Any]) -> str:
    """Simple ``{key}`` substitution for task user prompts."""
    return re.sub(
        r"\{([^{}]+)\}",
        lambda match: str(values.get(match.group(1), match.group(0))),
        template,
    )
