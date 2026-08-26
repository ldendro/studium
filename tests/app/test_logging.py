"""Content-safe logging tests."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from studium.app.logging import ContentSafeJsonFormatter, configure_content_safe_logging


def test_formatter_redacts_prompt_and_markdown_fields() -> None:
    formatter = ContentSafeJsonFormatter()
    record = logging.LogRecord(
        name="studium.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="provider_call",
        args=(),
        exc_info=None,
    )
    record.prompt = "Explain stochastic gradient descent in full."
    record.markdown = "# Secret note"
    record.job_id = "job_abc"
    payload = json.loads(formatter.format(record))
    assert payload["event"] == "provider_call"
    assert payload["prompt"] == "[redacted]"
    assert payload["markdown"] == "[redacted]"
    assert payload["job_id"] == "job_abc"
    assert "Explain stochastic" not in formatter.format(record)


def test_configure_logging_writes_jsonl(tmp_path: Path) -> None:
    log_path = configure_content_safe_logging(app_data_dir=tmp_path, level="info")
    logger = logging.getLogger("studium")
    logger.info("workspace_opened", extra={"vault_id": "abc123", "query": "hidden search"})
    raw = log_path.read_text(encoding="utf-8").strip().splitlines()[-1]
    payload = json.loads(raw)
    assert payload["event"] == "workspace_opened"
    assert payload["vault_id"] == "abc123"
    assert payload["query"] == "[redacted]"
