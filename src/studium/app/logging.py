"""Structured application logging that never records user content or secrets."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from studium.index.paths import resolve_application_data_dir

_RESERVED = set(logging.makeLogRecord({}).__dict__)
_SENSITIVE_FRAGMENTS = (
    "authorization",
    "body",
    "content",
    "markdown",
    "password",
    "prompt",
    "query",
    "quote",
    "response",
    "secret",
    "text",
    "token",
)


class ContentSafeJsonFormatter(logging.Formatter):
    """Emit machine-readable metadata while deliberately omitting content fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            if any(fragment in key.casefold() for fragment in _SENSITIVE_FRAGMENTS):
                payload[key] = "[redacted]"
                continue
            payload[key] = _safe_value(value)
        if record.exc_info is not None and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, sort_keys=True, ensure_ascii=True)


def configure_content_safe_logging(
    *,
    app_data_dir: Path | None = None,
    level: str = "info",
) -> Path:
    """Configure Studium's stderr and rotating JSONL logs."""

    log_dir = resolve_application_data_dir(app_data_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "studium.jsonl"
    formatter = ContentSafeJsonFormatter()
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger = logging.getLogger("studium")
    logger.handlers.clear()
    logger.addHandler(stream)
    logger.addHandler(file_handler)
    logger.setLevel(numeric_level)
    logger.propagate = False
    return log_path


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return value[:240]
    if isinstance(value, Path):
        return value.name
    if isinstance(value, dict):
        return {
            str(key): (
                "[redacted]"
                if any(fragment in str(key).casefold() for fragment in _SENSITIVE_FRAGMENTS)
                else _safe_value(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list | tuple | set):
        return [_safe_value(item) for item in value]
    return type(value).__name__
