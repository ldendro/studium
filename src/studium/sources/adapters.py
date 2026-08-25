"""Format adapters that preserve source provenance during extraction."""

from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any, cast

from bs4 import BeautifulSoup
from pypdf import PdfReader

from studium.sources.models import ExtractedUnit, SourceKind

_TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3})\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3})"
)
_MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def detect_kind(filename: str, mime_type: str | None = None) -> SourceKind:
    suffix = Path(filename).suffix.casefold()
    mime = (mime_type or "").casefold()
    if suffix == ".pdf" or mime == "application/pdf":
        return SourceKind.PDF
    if suffix in {".md", ".markdown"} or "markdown" in mime:
        return SourceKind.MARKDOWN
    if suffix in {".html", ".htm"} or "html" in mime:
        return SourceKind.HTML
    if suffix in {".srt", ".vtt"} or "vtt" in mime or "subrip" in mime:
        return SourceKind.TRANSCRIPT
    if suffix == ".json" and ("transcript" in filename.casefold() or "json" in mime):
        return SourceKind.TRANSCRIPT
    return SourceKind.TEXT


def extract_units(
    content: bytes,
    *,
    filename: str,
    kind: SourceKind,
) -> tuple[list[ExtractedUnit], dict[str, Any]]:
    if kind == SourceKind.PDF:
        return _extract_pdf(content)
    text = _decode(content)
    if kind == SourceKind.MARKDOWN:
        return _extract_markdown(text), {}
    if kind == SourceKind.HTML:
        return _extract_html(text), {}
    if kind == SourceKind.TRANSCRIPT:
        return _extract_transcript(text, filename=filename), {}
    return [ExtractedUnit(text=text)], {}


def _extract_pdf(content: bytes) -> tuple[list[ExtractedUnit], dict[str, Any]]:
    reader = PdfReader(BytesIO(content))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError("The PDF is encrypted and could not be opened.") from exc
    units: list[ExtractedUnit] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text(extraction_mode="layout") or page.extract_text() or ""
        text = _normalize_text(text)
        if text:
            units.append(ExtractedUnit(text=text, page=page_number))
    document_info = reader.metadata
    metadata: dict[str, Any] = {}
    if document_info is not None:
        for field in ("title", "author", "subject", "creator", "producer"):
            value = getattr(document_info, field, None)
            if value is not None:
                metadata[field] = str(value)
    metadata["page_count"] = len(reader.pages)
    return units, metadata


def _extract_markdown(text: str) -> list[ExtractedUnit]:
    units: list[ExtractedUnit] = []
    section = "Document"
    buffer: list[str] = []
    in_fence = False

    def flush() -> None:
        nonlocal buffer
        value = "\n".join(buffer).strip()
        if value:
            units.append(ExtractedUnit(text=value, section=section))
        buffer = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
        heading = None if in_fence else _MARKDOWN_HEADING.match(stripped)
        if heading:
            flush()
            section = heading.group(2).strip()
            buffer.append(line)
        else:
            buffer.append(line)
    flush()
    return units


def _extract_html(text: str) -> list[ExtractedUnit]:
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    units: list[ExtractedUnit] = []
    section = "Document"
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        value = _normalize_text("\n".join(buffer))
        if value:
            units.append(ExtractedUnit(text=value, section=section))
        buffer = []

    body = soup.body or soup
    for node in body.find_all(["h1", "h2", "h3", "p", "li", "pre", "blockquote"]):
        value = node.get_text(" ", strip=True)
        if not value:
            continue
        if node.name in {"h1", "h2", "h3"}:
            flush()
            section = value
        else:
            buffer.append(value)
    flush()
    return units or [ExtractedUnit(text=_normalize_text(body.get_text("\n", strip=True)))]


def _extract_transcript(text: str, *, filename: str) -> list[ExtractedUnit]:
    if Path(filename).suffix.casefold() == ".json":
        units = _extract_json_transcript(text)
        if units:
            return units
    units: list[ExtractedUnit] = []
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n"))
    for block in blocks:
        match = _TIMESTAMP_RE.search(block)
        if match is None:
            continue
        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
            and not line.strip().isdigit()
            and "-->" not in line
            and not line.startswith(("WEBVTT", "NOTE"))
        ]
        value = _normalize_text(" ".join(lines))
        if value:
            units.append(
                ExtractedUnit(
                    text=value,
                    timestamp_start=_parse_timestamp(match.group("start")),
                    timestamp_end=_parse_timestamp(match.group("end")),
                )
            )
    if units:
        return units
    return [ExtractedUnit(text=_normalize_text(text))]


def _extract_json_transcript(text: str) -> list[ExtractedUnit]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    values: Any
    if isinstance(payload, dict):
        typed = cast(dict[str, Any], payload)
        values = typed.get("segments") or typed.get("transcript") or typed.get("items")
    else:
        values = payload
    if not isinstance(values, list):
        return []
    units: list[ExtractedUnit] = []
    for value in cast(list[Any], values):
        if isinstance(value, str):
            units.append(ExtractedUnit(text=value))
            continue
        if not isinstance(value, dict):
            continue
        item = cast(dict[str, Any], value)
        content = item.get("text") or item.get("content") or item.get("utterance")
        if not content:
            continue
        units.append(
            ExtractedUnit(
                text=str(content),
                section=None if item.get("speaker") is None else str(item["speaker"]),
                timestamp_start=_optional_float(item.get("start") or item.get("start_time")),
                timestamp_end=_optional_float(item.get("end") or item.get("end_time")),
            )
        )
    return units


def _decode(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _normalize_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _parse_timestamp(value: str) -> float:
    normalized = value.replace(",", ".")
    parts = normalized.split(":")
    seconds = float(parts[-1])
    minutes = float(parts[-2])
    hours = float(parts[-3]) if len(parts) == 3 else 0.0
    return hours * 3600 + minutes * 60 + seconds


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
