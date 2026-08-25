"""Provenance-aware source chunking."""

from __future__ import annotations

import re

from studium.sources.models import ExtractedUnit, SourceChunkModel

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def chunk_units(
    source_id: str,
    units: list[ExtractedUnit],
    *,
    target_chars: int = 1100,
    overlap_chars: int = 140,
) -> list[SourceChunkModel]:
    chunks: list[SourceChunkModel] = []
    document_offset = 0
    for unit in units:
        pieces = _split_unit(unit.text, target_chars=target_chars, overlap_chars=overlap_chars)
        search_from = 0
        for piece in pieces:
            local_start = unit.text.find(piece, search_from)
            if local_start < 0:
                local_start = search_from
            local_end = min(len(unit.text), local_start + len(piece))
            chunks.append(
                SourceChunkModel(
                    id=f"{source_id}:chunk:{len(chunks):05d}",
                    source_id=source_id,
                    ordinal=len(chunks),
                    text=piece,
                    section=unit.section,
                    page=unit.page,
                    timestamp_start=unit.timestamp_start,
                    timestamp_end=unit.timestamp_end,
                    char_start=document_offset + local_start,
                    char_end=document_offset + local_end,
                    token_count=len(re.findall(r"\w+", piece)),
                )
            )
            search_from = max(0, local_end - overlap_chars)
        document_offset += len(unit.text) + 1
    return chunks


def _split_unit(text: str, *, target_chars: int, overlap_chars: int) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []
    if len(normalized) <= target_chars:
        return [normalized]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    segments: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= target_chars:
            segments.append(paragraph)
        else:
            segments.extend(
                sentence.strip()
                for sentence in _SENTENCE_BOUNDARY.split(paragraph)
                if sentence.strip()
            )

    chunks: list[str] = []
    current = ""
    for segment in segments:
        if current and len(current) + len(segment) + 2 > target_chars:
            chunks.append(current.strip())
            overlap = _tail_at_boundary(current, overlap_chars)
            current = f"{overlap}\n\n{segment}".strip() if overlap else segment
        else:
            current = f"{current}\n\n{segment}".strip()
        while len(current) > target_chars * 1.35:
            cut = _best_cut(current, target_chars)
            chunks.append(current[:cut].strip())
            overlap = _tail_at_boundary(current[:cut], overlap_chars)
            current = f"{overlap} {current[cut:]}".strip()
    if current:
        chunks.append(current.strip())
    return chunks


def _best_cut(text: str, target: int) -> int:
    floor = max(1, int(target * 0.7))
    for marker in ("\n", ". ", "; ", ", ", " "):
        position = text.rfind(marker, floor, target + 1)
        if position > 0:
            return position + len(marker)
    return target


def _tail_at_boundary(text: str, length: int) -> str:
    if length <= 0 or len(text) <= length:
        return text
    tail = text[-length:]
    boundary = min(
        (position for position in (tail.find(". "), tail.find("\n"), tail.find(" ")) if position >= 0),
        default=-1,
    )
    return tail[boundary + 1 :].strip() if boundary >= 0 else tail
