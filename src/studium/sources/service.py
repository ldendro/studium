"""Durable source library, processing, retrieval, and note comparison."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert

from studium.app.database import (
    app_transaction,
    row_dict,
    source_chunks,
    source_contributions,
    sources,
)
from studium.app.migrations import utc_now
from studium.app.workspace import WorkspaceContext
from studium.index.repositories import concepts
from studium.sources.adapters import detect_kind, extract_units
from studium.sources.chunking import chunk_units
from studium.sources.models import (
    Citation,
    ContributionResult,
    RetrievalHit,
    SourceChunkModel,
    SourceStatus,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SAFE_FILENAME = re.compile(r"[^a-zA-Z0-9._-]+")


class SourceService:
    def __init__(self, workspace: WorkspaceContext) -> None:
        self.workspace = workspace

    def stage_upload(
        self,
        *,
        filename: str,
        content: bytes,
        mime_type: str | None,
        title: str | None = None,
    ) -> tuple[dict[str, Any], bool]:
        if not content:
            raise ValueError("The uploaded source is empty.")
        content_hash = hashlib.sha256(content).hexdigest()
        existing = self._source_by_hash(content_hash)
        if existing is not None:
            return existing, True

        safe_filename = _safe_filename(filename)
        kind = detect_kind(safe_filename, mime_type)
        source_id = f"source_{uuid4().hex}"
        asset_dir = self.workspace.config.source_assets_dir / source_id
        asset_dir.mkdir(parents=True, exist_ok=False)
        asset_path = asset_dir / safe_filename
        asset_path.write_bytes(content)
        now = utc_now()
        values = {
            "id": source_id,
            "title": (title or Path(filename).stem or filename).strip(),
            "source_type": kind.value,
            "status": SourceStatus.QUEUED.value,
            "original_filename": filename,
            "asset_path": str(asset_path),
            "mime_type": mime_type,
            "content_hash": content_hash,
            "size_bytes": len(content),
            "page_count": None,
            "metadata_json": "{}",
            "processing_error": None,
            "created_at": now,
            "updated_at": now,
        }
        try:
            with app_transaction(self.workspace.app_engine) as connection:
                connection.execute(sources.insert().values(**values))
        except Exception:
            shutil.rmtree(asset_dir, ignore_errors=True)
            raise
        return self.get(source_id), False

    def enqueue_processing(self, source_id: str) -> dict[str, Any]:
        source = self.get(source_id)
        job = self.workspace.jobs.submit(
            "source_processing",
            {"source_id": source_id, "filename": source.get("original_filename")},
            lambda progress: self.process(source_id, progress=progress),
        )
        return {"source": source, "job": job}

    def process(self, source_id: str, *, progress: Any) -> dict[str, Any]:
        source = self.get(source_id)
        path = Path(str(source["asset_path"]))
        try:
            self._set_status(source_id, SourceStatus.EXTRACTING)
            progress(0.08, "Extracting structured text")
            content = path.read_bytes()
            units, extracted_metadata = extract_units(
                content,
                filename=str(source["original_filename"]),
                kind=detect_kind(
                    str(source["original_filename"]),
                    None if source["mime_type"] is None else str(source["mime_type"]),
                ),
            )
            if not units or not any(unit.text.strip() for unit in units):
                raise ValueError("No readable text could be extracted from this source.")

            self._set_status(source_id, SourceStatus.CHUNKING)
            progress(0.35, "Chunking with provenance")
            chunks = chunk_units(source_id, units)
            if not chunks:
                raise ValueError("Text extraction succeeded but produced no searchable chunks.")

            self._set_status(source_id, SourceStatus.EMBEDDING)
            progress(0.58, f"Embedding {len(chunks)} chunks")
            vectors = self.workspace.embedding_provider.embed_documents(
                [chunk.text for chunk in chunks]
            )
            model = self.workspace.embedding_provider.model_metadata()
            if len(vectors) != len(chunks):
                raise RuntimeError("Embedding provider returned an unexpected vector count.")
            embedded = [
                chunk.model_copy(
                    update={
                        "embedding": vector,
                        "embedding_model": model.model_id,
                    }
                )
                for chunk, vector in zip(chunks, vectors, strict=True)
            ]
            progress(0.86, "Publishing source index")
            page_count = extracted_metadata.get("page_count")
            now = utc_now()
            with app_transaction(self.workspace.app_engine) as connection:
                connection.execute(
                    source_chunks.delete().where(source_chunks.c.source_id == source_id)
                )
                connection.execute(
                    source_chunks.insert(),
                    [_chunk_row(chunk, now) for chunk in embedded],
                )
                connection.execute(
                    sources.update()
                    .where(sources.c.id == source_id)
                    .values(
                        status=SourceStatus.READY.value,
                        page_count=page_count,
                        metadata_json=json.dumps(extracted_metadata, sort_keys=True),
                        processing_error=None,
                        updated_at=now,
                    )
                )
            return {
                "source_id": source_id,
                "status": SourceStatus.READY.value,
                "chunk_count": len(embedded),
                "page_count": page_count,
                "embedding_model": model.model_id,
            }
        except Exception as exc:
            with app_transaction(self.workspace.app_engine) as connection:
                connection.execute(
                    sources.update()
                    .where(sources.c.id == source_id)
                    .values(
                        status=SourceStatus.FAILED.value,
                        processing_error=f"{type(exc).__name__}: {exc}",
                        updated_at=utc_now(),
                    )
                )
            raise

    def list(
        self,
        *,
        status: str | None = None,
        query: str | None = None,
    ) -> list[dict[str, Any]]:
        statement = (
            select(
                sources,
                func.count(source_chunks.c.id).label("chunk_count"),
            )
            .outerjoin(source_chunks, sources.c.id == source_chunks.c.source_id)
            .group_by(sources.c.id)
            .order_by(sources.c.updated_at.desc())
        )
        if status:
            statement = statement.where(sources.c.status == status)
        if query:
            statement = statement.where(sources.c.title.ilike(f"%{query}%"))
        with self.workspace.app_engine.connect() as connection:
            rows = connection.execute(statement).all()
        return [_decode_source(row_dict(row)) for row in rows]

    def get(self, source_id: str, *, include_chunks: bool = False) -> dict[str, Any]:
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(select(sources).where(sources.c.id == source_id)).first()
            if row is None:
                raise KeyError(source_id)
            source = _decode_source(row_dict(row))
            count = connection.execute(
                select(func.count()).select_from(source_chunks).where(
                    source_chunks.c.source_id == source_id
                )
            ).scalar_one()
            source["chunk_count"] = int(count)
            if include_chunks:
                chunk_rows = connection.execute(
                    select(source_chunks)
                    .where(source_chunks.c.source_id == source_id)
                    .order_by(source_chunks.c.ordinal)
                ).all()
                source["chunks"] = [
                    _decode_chunk(row_dict(chunk), include_embedding=False)
                    for chunk in chunk_rows
                ]
        return source

    def delete(self, source_id: str) -> None:
        source = self.get(source_id)
        with app_transaction(self.workspace.app_engine) as connection:
            result = connection.execute(sources.delete().where(sources.c.id == source_id))
        if result.rowcount == 0:
            raise KeyError(source_id)
        asset_path = source.get("asset_path")
        if asset_path:
            shutil.rmtree(Path(str(asset_path)).parent, ignore_errors=True)

    def retrieve(
        self,
        query: str,
        *,
        source_id: str | None = None,
        concept_id: str | None = None,
        limit: int = 12,
    ) -> list[RetrievalHit]:
        conditioned = query.strip()
        if concept_id:
            concept = self._concept_context(concept_id)
            conditioned = f"{conditioned}\nConcept: {concept}".strip()
        vector = self.workspace.embedding_provider.embed_query(conditioned)
        query_tokens = set(_tokens(conditioned))
        statement = (
            select(source_chunks, sources.c.title.label("source_title"))
            .join(sources, sources.c.id == source_chunks.c.source_id)
            .where(sources.c.status == SourceStatus.READY.value)
        )
        if source_id:
            statement = statement.where(source_chunks.c.source_id == source_id)
        with self.workspace.app_engine.connect() as connection:
            rows = connection.execute(statement).all()
        hits: list[RetrievalHit] = []
        for row in rows:
            item = row_dict(row)
            chunk_vector = _json_vector(item.get("embedding_json"))
            semantic = _cosine(vector, chunk_vector) if chunk_vector else 0.0
            chunk_tokens = set(_tokens(str(item["text"])))
            lexical = (
                len(query_tokens & chunk_tokens) / max(1, len(query_tokens))
                if query_tokens
                else 0.0
            )
            score = 0.72 * max(0.0, semantic) + 0.28 * lexical
            citation = _citation(item)
            hits.append(
                RetrievalHit(
                    chunk_id=str(item["id"]),
                    source_id=str(item["source_id"]),
                    source_title=str(item["source_title"]),
                    text=str(item["text"]),
                    score=score,
                    semantic_score=semantic,
                    lexical_score=lexical,
                    citation=citation,
                )
            )
        hits.sort(key=lambda hit: (-hit.score, hit.chunk_id))
        return hits[: max(1, min(limit, 50))]

    def analyze_contribution(
        self,
        *,
        source_id: str,
        concept_id: str,
        focus: str = "",
    ) -> ContributionResult:
        source = self.get(source_id)
        context = self._concept_context(concept_id)
        hits = self.retrieve(
            f"{focus} {context}".strip(),
            source_id=source_id,
            concept_id=concept_id,
            limit=8,
        )
        if not hits:
            raise ValueError("No relevant source evidence was retrieved.")
        concept_tokens = set(_tokens(context))
        source_tokens = set(_tokens(" ".join(hit.text for hit in hits[:5])))
        overlap = len(concept_tokens & source_tokens) / max(1, len(source_tokens))
        source_text = " ".join(hit.text for hit in hits[:5]).casefold()
        if any(cue in source_text for cue in ("contrary to", "however", "does not imply", "fails when")):
            classification = "qualification_or_contradiction"
            module_type = "misconception_debugging"
        elif any(cue in source_text for cue in ("for example", "consider ", "suppose ", "case study")):
            classification = "worked_example"
            module_type = "worked_example"
        elif any(cue in source_text for cue in ("requires", "prerequisite", "before ", "assume ")):
            classification = "prerequisite_context"
            module_type = "conceptual_explanation"
        elif overlap < 0.16:
            classification = "novel_extension"
            module_type = "application"
        else:
            classification = "reinforcement"
            module_type = "conceptual_explanation"
        summary = _summary_for(classification, source, hits)
        proposed_module = {
            "type": module_type,
            "title": _module_title(classification, str(source["title"])),
            "focus": summary,
            "source_id": source_id,
            "citations": [
                hit.citation.model_dump(mode="json") for hit in hits[:4]
            ],
        }
        contribution_id = f"contribution_{uuid4().hex}"
        now = utc_now()
        result = ContributionResult(
            id=contribution_id,
            source_id=source_id,
            concept_id=concept_id,
            classification=classification,
            summary=summary,
            evidence=[hit.citation for hit in hits[:4]],
            proposed_module=proposed_module,
        )
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                source_contributions.insert().values(
                    id=contribution_id,
                    source_id=source_id,
                    concept_id=concept_id,
                    classification=classification,
                    summary=summary,
                    evidence_json=json.dumps(
                        [item.model_dump(mode="json") for item in result.evidence],
                        sort_keys=True,
                    ),
                    proposed_module_json=json.dumps(proposed_module, sort_keys=True),
                    status="proposed",
                    created_at=now,
                    updated_at=now,
                )
            )
        return result

    def list_contributions(
        self,
        *,
        source_id: str | None = None,
        concept_id: str | None = None,
    ) -> list[dict[str, Any]]:
        statement = select(source_contributions).order_by(
            source_contributions.c.created_at.desc()
        )
        if source_id:
            statement = statement.where(source_contributions.c.source_id == source_id)
        if concept_id:
            statement = statement.where(
                source_contributions.c.concept_id == concept_id
            )
        with self.workspace.app_engine.connect() as connection:
            rows = connection.execute(statement).all()
        return [_decode_contribution(row_dict(row)) for row in rows]

    def decide_contribution(self, contribution_id: str, status: str) -> dict[str, Any]:
        if status not in {"proposed", "accepted", "rejected"}:
            raise ValueError("Contribution status must be proposed, accepted, or rejected.")
        with app_transaction(self.workspace.app_engine) as connection:
            result = connection.execute(
                source_contributions.update()
                .where(source_contributions.c.id == contribution_id)
                .values(status=status, updated_at=utc_now())
            )
        if result.rowcount == 0:
            raise KeyError(contribution_id)
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(source_contributions).where(
                    source_contributions.c.id == contribution_id
                )
            ).first()
        assert row is not None
        return _decode_contribution(row_dict(row))

    def _set_status(self, source_id: str, status: SourceStatus) -> None:
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                sources.update()
                .where(sources.c.id == source_id)
                .values(status=status.value, updated_at=utc_now())
            )

    def _source_by_hash(self, content_hash: str) -> dict[str, Any] | None:
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(sources).where(sources.c.content_hash == content_hash)
            ).first()
        return None if row is None else _decode_source(row_dict(row))

    def _concept_context(self, concept_id: str) -> str:
        with self.workspace.index_engine.connect() as connection:
            row = concepts.get_concept(connection, concept_id)
        if row is None:
            raise KeyError(concept_id)
        return " ".join(
            value
            for value in (
                str(row["canonical_title"]),
                "" if row.get("overview_plaintext") is None else str(row["overview_plaintext"]),
            )
            if value
        )


def _chunk_row(chunk: SourceChunkModel, created_at: str) -> dict[str, Any]:
    return {
        "id": chunk.id,
        "source_id": chunk.source_id,
        "ordinal": chunk.ordinal,
        "text": chunk.text,
        "section": chunk.section,
        "page": chunk.page,
        "timestamp_start": chunk.timestamp_start,
        "timestamp_end": chunk.timestamp_end,
        "char_start": chunk.char_start,
        "char_end": chunk.char_end,
        "token_count": chunk.token_count,
        "embedding_json": (
            None if chunk.embedding is None else json.dumps(chunk.embedding)
        ),
        "embedding_model": chunk.embedding_model,
        "created_at": created_at,
    }


def _decode_source(row: dict[str, Any]) -> dict[str, Any]:
    value = dict(row)
    raw = value.pop("metadata_json", "{}")
    value["metadata"] = json.loads(str(raw or "{}"))
    return value


def _decode_chunk(row: dict[str, Any], *, include_embedding: bool) -> dict[str, Any]:
    value = dict(row)
    raw = value.pop("embedding_json", None)
    if include_embedding:
        value["embedding"] = _json_vector(raw)
    return value


def _decode_contribution(row: dict[str, Any]) -> dict[str, Any]:
    value = dict(row)
    value["evidence"] = json.loads(str(value.pop("evidence_json") or "[]"))
    raw_module = value.pop("proposed_module_json", None)
    value["proposed_module"] = (
        None if raw_module is None else json.loads(str(raw_module))
    )
    return value


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "source.txt"
    safe = _SAFE_FILENAME.sub("-", name).strip(".-")
    return safe[:180] or "source.txt"


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.casefold())


def _json_vector(value: Any) -> list[float]:
    if value is None:
        return []
    try:
        loaded = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    if not isinstance(loaded, list):
        return []
    return [float(item) for item in cast(list[Any], loaded)]


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    denominator = left_norm * right_norm
    return 0.0 if denominator == 0.0 else numerator / denominator


def _citation(item: dict[str, Any]) -> Citation:
    if item.get("page") is not None:
        locator = f"p. {item['page']}"
    elif item.get("timestamp_start") is not None:
        locator = _format_time(float(item["timestamp_start"]))
    elif item.get("section"):
        locator = f"§ {item['section']}"
    else:
        locator = f"chunk {int(item['ordinal']) + 1}"
    text = str(item["text"]).strip()
    quote = text if len(text) <= 360 else f"{text[:357].rstrip()}…"
    return Citation(
        source_id=str(item["source_id"]),
        source_title=str(item["source_title"]),
        chunk_id=str(item["id"]),
        locator=locator,
        quote=quote,
        section=None if item.get("section") is None else str(item["section"]),
        page=None if item.get("page") is None else int(item["page"]),
        timestamp_start=(
            None
            if item.get("timestamp_start") is None
            else float(item["timestamp_start"])
        ),
        timestamp_end=(
            None
            if item.get("timestamp_end") is None
            else float(item["timestamp_end"])
        ),
    )


def _format_time(seconds: float) -> str:
    minutes, remainder = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return (
        f"{hours:d}:{minutes:02d}:{remainder:02d}"
        if hours
        else f"{minutes:d}:{remainder:02d}"
    )


def _summary_for(
    classification: str,
    source: dict[str, Any],
    hits: list[RetrievalHit],
) -> str:
    first = hits[0].text.strip().replace("\n", " ")
    sentence = re.split(r"(?<=[.!?])\s+", first, maxsplit=1)[0]
    if len(sentence) > 260:
        sentence = f"{sentence[:257].rstrip()}…"
    labels = {
        "qualification_or_contradiction": "qualifies or challenges the current explanation",
        "worked_example": "adds a concrete worked example",
        "prerequisite_context": "makes prerequisite assumptions explicit",
        "novel_extension": "adds material not represented in the current note",
        "reinforcement": "reinforces the current concept with source-grounded detail",
    }
    return f"{source['title']} {labels[classification]}: {sentence}"


def _module_title(classification: str, source_title: str) -> str:
    names = {
        "qualification_or_contradiction": "Source Qualification and Misconception Check",
        "worked_example": "Source-Grounded Worked Example",
        "prerequisite_context": "Prerequisite Assumptions",
        "novel_extension": f"Extension from {source_title}",
        "reinforcement": "Source-Grounded Reconstruction",
    }
    return names[classification]
