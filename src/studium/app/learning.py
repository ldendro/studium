"""Backlog, retention, mastery, and personal-model application services."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import func, select

from studium.app.database import (
    app_transaction,
    backlog_items,
    mastery_snapshots,
    profile_observations,
    retention_cards,
    review_events,
    review_findings,
    review_sessions,
    row_dict,
)
from studium.app.learning_models import (
    BacklogItem,
    BacklogItemType,
    BacklogOrigin,
    BacklogStatus,
    MasteryRecord,
    MasteryState,
    ProfileCategory,
    ProfileObservation,
    ProfileObservationStatus,
    RetentionCard,
    RetentionCardState,
    RetentionEvaluation,
    RetentionReviewResult,
)
from studium.app.migrations import utc_now
from studium.app.search import concept_detail, graph_projection
from studium.app.workspace import WorkspaceContext
from studium.index.repositories import concepts, domains
from studium.index.schema import relationships as index_relationships
from studium.schemas import NoteVaultStatus, RelationshipType

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class BacklogService:
    def __init__(self, workspace: WorkspaceContext) -> None:
        self.workspace = workspace

    def create(
        self,
        *,
        title: str,
        item_type: BacklogItemType = BacklogItemType.NEW_CONCEPT,
        reason: str,
        origin: BacklogOrigin = BacklogOrigin.MANUAL,
        priority: int = 50,
        related_concept_id: str | None = None,
        required_by: list[str] | None = None,
        source_query: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BacklogItem:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Backlog title cannot be empty.")
        required = list(dict.fromkeys(required_by or []))
        existing = self._duplicate(clean_title, related_concept_id)
        if existing is not None:
            return existing
        scored_priority = min(
            100,
            max(
                0,
                priority
                + min(20, len(required) * 5)
                + self._personalization_boost(clean_title),
            ),
        )
        now = utc_now()
        identifier = f"backlog_{uuid4().hex}"
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                backlog_items.insert().values(
                    id=identifier,
                    title=clean_title,
                    item_type=item_type.value,
                    status=BacklogStatus.OPEN.value,
                    priority=scored_priority,
                    reason=reason.strip() or "Saved for later learning.",
                    origin=origin.value,
                    related_concept_id=related_concept_id,
                    required_by_json=json.dumps(required, sort_keys=True),
                    source_query=source_query,
                    metadata_json=json.dumps(metadata or {}, sort_keys=True),
                    created_at=now,
                    updated_at=now,
                    completed_at=None,
                )
            )
        return self.get(identifier)

    def create_many(self, candidates: list[dict[str, Any]]) -> list[BacklogItem]:
        result: list[BacklogItem] = []
        for candidate in candidates:
            title = str(candidate.get("title") or "").strip()
            if not title:
                continue
            result.append(
                self.create(
                    title=title,
                    item_type=_backlog_type(candidate.get("item_type")),
                    reason=str(candidate.get("reason") or "Recommended during Create."),
                    origin=_backlog_origin(candidate.get("origin") or "create"),
                    priority=int(candidate.get("priority") or 60),
                    related_concept_id=_optional_string(
                        candidate.get("related_concept_id")
                    ),
                    required_by=_string_list(candidate.get("required_by")),
                    metadata={"candidate": candidate},
                )
            )
        return result

    def list(
        self,
        *,
        status: BacklogStatus | None = None,
        origin: BacklogOrigin | None = None,
        item_type: BacklogItemType | None = None,
        query: str | None = None,
    ) -> list[BacklogItem]:
        statement = select(backlog_items).order_by(
            backlog_items.c.priority.desc(),
            backlog_items.c.updated_at.desc(),
        )
        if status:
            statement = statement.where(backlog_items.c.status == status.value)
        if origin:
            statement = statement.where(backlog_items.c.origin == origin.value)
        if item_type:
            statement = statement.where(backlog_items.c.item_type == item_type.value)
        if query:
            statement = statement.where(backlog_items.c.title.ilike(f"%{query}%"))
        with self.workspace.app_engine.connect() as connection:
            rows = connection.execute(statement).all()
        accepted = self._accepted_titles()
        result: list[BacklogItem] = []
        for row in rows:
            value = row_dict(row)
            candidate = accepted.get(_normalize(str(value["title"])))
            result.append(_decode_backlog(value, resolution_candidate=candidate))
        return result

    def get(self, item_id: str) -> BacklogItem:
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(backlog_items).where(backlog_items.c.id == item_id)
            ).first()
        if row is None:
            raise KeyError(item_id)
        candidate = self._accepted_titles().get(_normalize(str(row.title)))
        return _decode_backlog(row_dict(row), resolution_candidate=candidate)

    def update(
        self,
        item_id: str,
        *,
        status: BacklogStatus | None = None,
        priority: int | None = None,
        reason: str | None = None,
        title: str | None = None,
    ) -> BacklogItem:
        values: dict[str, Any] = {"updated_at": utc_now()}
        if status is not None:
            values["status"] = status.value
            values["completed_at"] = (
                utc_now()
                if status in {BacklogStatus.COMPLETED, BacklogStatus.DISMISSED}
                else None
            )
        if priority is not None:
            values["priority"] = min(100, max(0, priority))
        if reason is not None:
            values["reason"] = reason.strip()
        if title is not None:
            clean = title.strip()
            if not clean:
                raise ValueError("Backlog title cannot be empty.")
            values["title"] = clean
        with app_transaction(self.workspace.app_engine) as connection:
            result = connection.execute(
                backlog_items.update()
                .where(backlog_items.c.id == item_id)
                .values(**values)
            )
        if result.rowcount == 0:
            raise KeyError(item_id)
        return self.get(item_id)

    def derive_missing_relationships(self) -> list[BacklogItem]:
        with self.workspace.index_engine.connect() as connection:
            rows = connection.execute(
                select(index_relationships).where(
                    index_relationships.c.vault_status != "found"
                )
            ).mappings().all()
            concept_rows = concepts.list_concepts(connection)
        titles = {
            str(row["concept_id"]): str(row["canonical_title"]) for row in concept_rows
        }
        grouped: dict[str, list[str]] = defaultdict(list)
        relationship_types: dict[str, str] = {}
        for row in rows:
            title = str(row["target_title"]).strip()
            if not title:
                continue
            grouped[title].append(str(row["source_concept_id"]))
            relationship_types[title] = str(row["relationship_type"])
        created: list[BacklogItem] = []
        for title, required_ids in grouped.items():
            required_titles = [titles.get(item, item) for item in required_ids]
            relation = relationship_types[title]
            created.append(
                self.create(
                    title=title,
                    item_type=(
                        BacklogItemType.MISSING_PREREQUISITE
                        if relation == RelationshipType.DEPENDS_ON.value
                        else BacklogItemType.NEW_CONCEPT
                    ),
                    reason=(
                        f"Missing {relation.replace('_', ' ')} required by "
                        f"{', '.join(required_titles[:4])}."
                    ),
                    origin=BacklogOrigin.GRAPH,
                    priority=75,
                    required_by=required_ids,
                    metadata={
                        "relationship_type": relation,
                        "required_by_titles": required_titles,
                    },
                )
            )
        return created

    def promote(self, item_id: str) -> dict[str, Any]:
        item = self.update(item_id, status=BacklogStatus.IN_PROGRESS)
        context = item.reason
        if item.required_by:
            context += f" Required by: {', '.join(item.required_by)}."
        return {
            "backlog_id": item.id,
            "intent": item.title,
            "learning_goal": f"Resolve this {item.item_type.value.replace('_', ' ')}.",
            "user_context": context,
            "source_type": "backlog",
            "source_title": "Studium Backlog",
            "source_unit": item.id,
            "search_context": {
                "origin": item.origin.value,
                "priority": item.priority,
                "required_by": item.required_by,
            },
        }

    def confirm_resolution(self, item_id: str, concept_id: str | None = None) -> BacklogItem:
        item = self.get(item_id)
        candidate = item.resolution_candidate
        resolved_id = concept_id or (
            None if candidate is None else str(candidate["concept_id"])
        )
        if resolved_id is None:
            raise ValueError("No accepted concept matches this backlog item.")
        concept = self._accepted_concept(resolved_id)
        if concept is None:
            raise ValueError("Resolution must point to an accepted concept.")
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                backlog_items.update()
                .where(backlog_items.c.id == item_id)
                .values(
                    status=BacklogStatus.COMPLETED.value,
                    related_concept_id=resolved_id,
                    completed_at=utc_now(),
                    updated_at=utc_now(),
                )
            )
        return self.get(item_id)

    def _duplicate(
        self,
        title: str,
        related_concept_id: str | None,
    ) -> BacklogItem | None:
        candidates = self.list()
        normalized = _normalize(title)
        for item in candidates:
            if item.status in {BacklogStatus.COMPLETED, BacklogStatus.DISMISSED}:
                continue
            if _normalize(item.title) != normalized:
                continue
            if item.related_concept_id == related_concept_id:
                return item
        return None

    def _accepted_titles(self) -> dict[str, dict[str, Any]]:
        with self.workspace.index_engine.connect() as connection:
            rows = concepts.list_concepts(connection)
        return {
            _normalize(str(row["canonical_title"])): {
                "concept_id": str(row["concept_id"]),
                "title": str(row["canonical_title"]),
            }
            for row in rows
            if str(row["vault_status"]) == NoteVaultStatus.ACCEPTED.value
        }

    def _accepted_concept(self, concept_id: str) -> dict[str, Any] | None:
        with self.workspace.index_engine.connect() as connection:
            row = concepts.get_concept(connection, concept_id)
        if row is None or str(row["vault_status"]) != NoteVaultStatus.ACCEPTED.value:
            return None
        return row

    def _personalization_boost(self, title: str) -> int:
        title_tokens = set(_tokens(title))
        if not title_tokens:
            return 0
        statements = personalization_context(self.workspace)
        overlap = max(
            (
                len(title_tokens & set(_tokens(statement))) / len(title_tokens)
                for statement in statements
            ),
            default=0.0,
        )
        return round(overlap * 15)


class RetentionService:
    def __init__(self, workspace: WorkspaceContext) -> None:
        self.workspace = workspace

    def generate(self, concept_id: str | None = None) -> list[RetentionCard]:
        concept_rows = self._accepted_concepts(concept_id)
        created: list[RetentionCard] = []
        for concept in concept_rows:
            detail = concept_detail(self.workspace, str(concept["concept_id"]))
            modules = cast(list[dict[str, Any]], detail["modules"])
            specs = [
                {
                    "module_id": str(module["id"]),
                    "module_type": str(module["type"]),
                    "prompt": _retention_prompt(
                        str(detail["canonical_title"]),
                        str(module["type"]),
                        str(module["title"]),
                    ),
                    "expected": _expected_components(
                        str(module["type"]),
                        str(module.get("markdown") or ""),
                    ),
                }
                for module in modules
            ]
            if not specs:
                specs = [
                    {
                        "module_id": None,
                        "module_type": "concept_overview",
                        "prompt": (
                            f"Reconstruct {detail['canonical_title']} from memory: "
                            "state its problem, mechanism, assumptions, and boundary."
                        ),
                        "expected": [
                            "problem",
                            "mechanism",
                            "assumptions",
                            "boundary",
                        ],
                    }
                ]
            for spec in specs:
                created.append(
                    self._ensure_card(
                        concept_id=str(concept["concept_id"]),
                        module_id=cast(str | None, spec["module_id"]),
                        module_type=str(spec["module_type"]),
                        prompt=str(spec["prompt"]),
                        expected=cast(list[str], spec["expected"]),
                    )
                )
        return created

    def list_cards(
        self,
        *,
        queue: str | None = None,
        concept_id: str | None = None,
        limit: int = 100,
    ) -> list[RetentionCard]:
        statement = select(retention_cards).order_by(
            retention_cards.c.pinned.desc(),
            retention_cards.c.next_review_at,
        )
        if concept_id:
            statement = statement.where(retention_cards.c.concept_id == concept_id)
        with self.workspace.app_engine.connect() as connection:
            rows = connection.execute(statement.limit(max(1, min(limit, 500)))).all()
        cards = [self._decode_card(row_dict(row)) for row in rows]
        if queue:
            cards = [card for card in cards if card.queue == queue]
        return sorted(cards, key=lambda card: (-card.priority_score, card.next_review_at))

    def due(self, *, limit: int = 30) -> list[RetentionCard]:
        cards = self.list_cards(limit=max(limit * 3, 100))
        return [
            card for card in cards if card.queue in {"due", "overdue"}
        ][:limit]

    def get(self, card_id: str) -> RetentionCard:
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(retention_cards).where(retention_cards.c.id == card_id)
            ).first()
        if row is None:
            raise KeyError(card_id)
        return self._decode_card(row_dict(row))

    def update_card(
        self,
        card_id: str,
        *,
        pinned: bool | None = None,
        suspended: bool | None = None,
        prompt: str | None = None,
    ) -> RetentionCard:
        values: dict[str, Any] = {"updated_at": utc_now()}
        if pinned is not None:
            values["pinned"] = pinned
        if suspended is not None:
            values["state"] = (
                RetentionCardState.SUSPENDED.value
                if suspended
                else RetentionCardState.REVIEW.value
            )
        if prompt is not None:
            clean = prompt.strip()
            if not clean:
                raise ValueError("Retention prompt cannot be empty.")
            values["prompt"] = clean
            values["prompt_hash"] = _content_hash(clean)
        with app_transaction(self.workspace.app_engine) as connection:
            result = connection.execute(
                retention_cards.update()
                .where(retention_cards.c.id == card_id)
                .values(**values)
            )
        if result.rowcount == 0:
            raise KeyError(card_id)
        return self.get(card_id)

    def review(
        self,
        card_id: str,
        *,
        response: str,
        self_rating: int,
        confidence: int | None,
        latency_ms: int | None,
        hints_used: int = 0,
    ) -> RetentionReviewResult:
        if not 0 <= self_rating <= 5:
            raise ValueError("Self-rating must be between 0 and 5.")
        if confidence is not None and not 1 <= confidence <= 5:
            raise ValueError("Confidence must be between 1 and 5.")
        card = self.get(card_id)
        component_score, missed = _response_component_score(
            response,
            card.expected_components,
        )
        score = round(min(1.0, max(0.0, self_rating / 5 * 0.65 + component_score * 0.35)), 3)
        evaluation = _evaluation(self_rating, score)
        schedule = _schedule(card, evaluation)
        reviewed_at = datetime.now(UTC).replace(microsecond=0)
        next_at = reviewed_at + timedelta(days=schedule["interval_days"])
        event_id = f"event_{uuid4().hex}"
        next_state = (
            RetentionCardState.RELEARNING
            if evaluation == RetentionEvaluation.AGAIN
            else RetentionCardState.REVIEW
        )
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                retention_cards.update()
                .where(retention_cards.c.id == card_id)
                .values(
                    state=next_state.value,
                    interval_days=schedule["interval_days"],
                    ease_factor=schedule["ease_factor"],
                    repetitions=schedule["repetitions"],
                    lapses=schedule["lapses"],
                    difficulty=schedule["difficulty"],
                    stability=schedule["stability"],
                    last_reviewed_at=_iso(reviewed_at),
                    next_review_at=_iso(next_at),
                    updated_at=_iso(reviewed_at),
                )
            )
            connection.execute(
                review_events.insert().values(
                    id=event_id,
                    card_id=card_id,
                    concept_id=card.concept_id,
                    module_id=card.module_id,
                    response=response,
                    evaluation=evaluation.value,
                    score=score,
                    confidence=confidence,
                    latency_ms=latency_ms,
                    hints_used=max(0, hints_used),
                    evaluator="transparent_hybrid",
                    scheduled_interval_days=schedule["interval_days"],
                    created_at=_iso(reviewed_at),
                )
            )
        feedback = (
            ["Your response covered each expected component."]
            if not missed
            else [f"Revisit: {item}" for item in missed]
        )
        updated = self.get(card_id)
        MasteryService(self.workspace).recompute(card.concept_id)
        return RetentionReviewResult(
            event_id=event_id,
            card=updated,
            evaluation=evaluation,
            score=score,
            expected_components=card.expected_components,
            feedback=feedback,
            next_interval_days=schedule["interval_days"],
        )

    def stats(self) -> dict[str, Any]:
        cards = self.list_cards(limit=500)
        with self.workspace.app_engine.connect() as connection:
            event_rows = connection.execute(
                select(review_events).order_by(review_events.c.created_at.desc())
            ).all()
        events = [row_dict(row) for row in event_rows]
        average = (
            0.0
            if not events
            else sum(float(item["score"]) for item in events) / len(events)
        )
        streak_dates = {
            str(item["created_at"])[:10]
            for item in events
            if item.get("created_at") is not None
        }
        return {
            "due": sum(card.queue == "due" for card in cards),
            "overdue": sum(card.queue == "overdue" for card in cards),
            "upcoming": sum(card.queue == "upcoming" for card in cards),
            "total_cards": len(cards),
            "review_count": len(events),
            "average_score": round(average, 3),
            "study_days": len(streak_dates),
            "lapses": sum(card.lapses for card in cards),
        }

    def _ensure_card(
        self,
        *,
        concept_id: str,
        module_id: str | None,
        module_type: str,
        prompt: str,
        expected: list[str],
    ) -> RetentionCard:
        prompt_hash = _content_hash(prompt)
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(retention_cards)
                .where(retention_cards.c.concept_id == concept_id)
                .where(retention_cards.c.prompt_hash == prompt_hash)
            ).first()
        if row is not None:
            return self._decode_card(row_dict(row))
        now = utc_now()
        identifier = f"card_{uuid4().hex}"
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                retention_cards.insert().values(
                    id=identifier,
                    concept_id=concept_id,
                    module_id=module_id,
                    module_type=module_type,
                    prompt=prompt,
                    expected_components_json=json.dumps(expected, sort_keys=True),
                    prompt_hash=prompt_hash,
                    state=RetentionCardState.NEW.value,
                    interval_days=0,
                    ease_factor=2.5,
                    repetitions=0,
                    lapses=0,
                    difficulty=0.3,
                    stability=0.0,
                    last_reviewed_at=None,
                    next_review_at=now,
                    pinned=False,
                    created_at=now,
                    updated_at=now,
                )
            )
        return self.get(identifier)

    def _decode_card(self, row: dict[str, Any]) -> RetentionCard:
        concept = self._concept(row["concept_id"])
        next_at = _parse_time(str(row["next_review_at"]))
        now = datetime.now(UTC)
        state = RetentionCardState(str(row["state"]))
        if state == RetentionCardState.SUSPENDED:
            queue = "suspended"
        elif next_at <= now - timedelta(days=1):
            queue = "overdue"
        elif next_at <= now:
            queue = "due"
        else:
            queue = "upcoming"
        overdue_days = max(0.0, (now - next_at).total_seconds() / 86400)
        dependent_count, prerequisite_context = self._graph_context(str(row["concept_id"]))
        profile_boost = _profile_relevance(
            str(concept["canonical_title"]),
            personalization_context(self.workspace),
        )
        priority = (
            overdue_days * 4
            + dependent_count * 5
            + (12 if bool(row["pinned"]) else 0)
            + profile_boost * 10
            + max(0, int(row["lapses"])) * 2
        )
        return RetentionCard(
            id=str(row["id"]),
            concept_id=str(row["concept_id"]),
            concept_title=str(concept["canonical_title"]),
            module_id=None if row.get("module_id") is None else str(row["module_id"]),
            module_type=(
                None if row.get("module_type") is None else str(row["module_type"])
            ),
            prompt=str(row["prompt"]),
            expected_components=_json_strings(row["expected_components_json"]),
            state=state,
            interval_days=int(row["interval_days"]),
            ease_factor=float(row["ease_factor"]),
            repetitions=int(row["repetitions"]),
            lapses=int(row["lapses"]),
            difficulty=float(row["difficulty"]),
            stability=float(row["stability"]),
            last_reviewed_at=(
                None
                if row.get("last_reviewed_at") is None
                else str(row["last_reviewed_at"])
            ),
            next_review_at=str(row["next_review_at"]),
            pinned=bool(row["pinned"]),
            queue=queue,
            priority_score=round(priority, 2),
            prerequisite_context=prerequisite_context,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def _accepted_concepts(self, concept_id: str | None) -> list[dict[str, Any]]:
        with self.workspace.index_engine.connect() as connection:
            rows = concepts.list_concepts(connection)
        return [
            row
            for row in rows
            if str(row["vault_status"]) == NoteVaultStatus.ACCEPTED.value
            and (concept_id is None or str(row["concept_id"]) == concept_id)
        ]

    def _concept(self, concept_id: Any) -> dict[str, Any]:
        with self.workspace.index_engine.connect() as connection:
            row = concepts.get_concept(connection, str(concept_id))
        if row is None:
            return {
                "concept_id": str(concept_id),
                "canonical_title": str(concept_id),
            }
        return row

    def _graph_context(self, concept_id: str) -> tuple[int, list[str]]:
        with self.workspace.index_engine.connect() as connection:
            dependent_count = connection.execute(
                select(func.count())
                .select_from(index_relationships)
                .where(index_relationships.c.target_id == concept_id)
                .where(
                    index_relationships.c.relationship_type
                    == RelationshipType.DEPENDS_ON.value
                )
            ).scalar_one()
            prerequisite_rows = connection.execute(
                select(index_relationships.c.target_title)
                .where(index_relationships.c.source_concept_id == concept_id)
                .where(
                    index_relationships.c.relationship_type
                    == RelationshipType.DEPENDS_ON.value
                )
            ).all()
        return int(dependent_count), [str(row.target_title) for row in prerequisite_rows]


class MasteryService:
    def __init__(self, workspace: WorkspaceContext) -> None:
        self.workspace = workspace

    def recompute(self, concept_id: str | None = None) -> list[MasteryRecord]:
        with self.workspace.index_engine.connect() as connection:
            concept_rows = [
                row
                for row in concepts.list_concepts(connection)
                if str(row["vault_status"]) == NoteVaultStatus.ACCEPTED.value
                and (concept_id is None or str(row["concept_id"]) == concept_id)
            ]
        result: list[MasteryRecord] = []
        for concept in concept_rows:
            result.append(self._recompute_concept(concept))
        return result

    def summary(self) -> dict[str, Any]:
        records = self._latest_records()
        if not records:
            records = self.recompute()
        domain_scores: dict[str, list[float]] = defaultdict(list)
        for record in records:
            for domain in record.domains:
                domain_scores[domain].append(record.score)
        domains_payload = [
            {
                "domain": domain,
                "score": round(sum(scores) / len(scores), 3),
                "state": _mastery_state(sum(scores) / len(scores)).value,
                "concept_count": len(scores),
            }
            for domain, scores in sorted(domain_scores.items())
        ]
        state_counts = Counter(record.state.value for record in records)
        return {
            "concepts": [record.model_dump(mode="json") for record in records],
            "domains": domains_payload,
            "state_counts": dict(state_counts),
            "average_score": (
                0.0
                if not records
                else round(sum(item.score for item in records) / len(records), 3)
            ),
            "updated_at": max((item.updated_at for item in records), default=None),
        }

    def concept(self, concept_id: str) -> dict[str, Any]:
        records = [
            item
            for item in self._latest_records(include_modules=True)
            if item.concept_id == concept_id
        ]
        if not records:
            self.recompute(concept_id)
            records = [
                item
                for item in self._latest_records(include_modules=True)
                if item.concept_id == concept_id
            ]
        concept_record = next((item for item in records if item.module_id is None), None)
        if concept_record is None:
            raise KeyError(concept_id)
        return {
            "concept": concept_record.model_dump(mode="json"),
            "modules": [
                item.model_dump(mode="json")
                for item in records
                if item.module_id is not None
            ],
        }

    def graph(self) -> dict[str, Any]:
        projection = graph_projection(self.workspace, include_drafts=False)
        latest = {item.concept_id: item for item in self._latest_records()}
        due_counts = Counter(
            card.concept_id
            for card in RetentionService(self.workspace).list_cards(limit=500)
            if card.queue in {"due", "overdue"}
        )
        for node in cast(list[dict[str, Any]], projection["nodes"]):
            record = latest.get(str(node["id"]))
            node["mastery_score"] = None if record is None else record.score
            node["mastery_state"] = (
                MasteryState.UNASSESSED.value if record is None else record.state.value
            )
            node["retention_due_count"] = due_counts[str(node["id"])]
        projection["legend"] = {
            **cast(dict[str, str], projection["legend"]),
            "mastery_strong": "Strong",
            "mastery_developing": "Developing",
            "mastery_fragile": "Fragile",
        }
        return projection

    def _recompute_concept(self, concept: dict[str, Any]) -> MasteryRecord:
        concept_id = str(concept["concept_id"])
        detail = concept_detail(self.workspace, concept_id)
        modules = cast(list[dict[str, Any]], detail["modules"])
        with self.workspace.app_engine.connect() as connection:
            events = [
                row_dict(row)
                for row in connection.execute(
                    select(review_events).where(review_events.c.concept_id == concept_id)
                ).all()
            ]
            review_row = connection.execute(
                select(review_sessions)
                .where(review_sessions.c.concept_id == concept_id)
                .order_by(review_sessions.c.created_at.desc())
                .limit(1)
            ).first()
            open_findings = connection.execute(
                select(func.count())
                .select_from(review_findings)
                .where(review_findings.c.concept_id == concept_id)
                .where(review_findings.c.status.in_(["open", "rejected"]))
            ).scalar_one()

        module_scores: list[float] = []
        now = utc_now()
        for module in modules:
            module_id = str(module["id"])
            module_events = [
                event for event in events if str(event.get("module_id")) == module_id
            ]
            retention_score = _average_scores(module_events)
            completion = 1.0 if str(module["status"]) == "completed" else 0.35
            evidence_weight = min(1.0, len(module_events) / 3)
            module_score = round(
                min(
                    1.0,
                    retention_score * 0.7
                    + completion * 0.2
                    + evidence_weight * 0.1,
                ),
                3,
            )
            module_scores.append(module_score)
            signals = {
                "retention": {
                    "average_score": retention_score,
                    "reviews": len(module_events),
                },
                "module": {
                    "status": str(module["status"]),
                    "type": str(module["type"]),
                },
            }
            self._insert_snapshot(
                concept_id,
                module_id,
                module_score,
                _mastery_state(module_score),
                signals,
                now,
            )

        retention_score = _average_scores(events)
        review_signal = (
            0.0
            if review_row is None
            else {
                "approved": 1.0,
                "approved_with_suggestions": 0.75,
                "needs_revision": 0.35,
            }.get(str(review_row.readiness), 0.5)
        )
        module_score = (
            sum(module_scores) / len(module_scores)
            if module_scores
            else (0.3 if detail["vault_status"] == "accepted" else 0.0)
        )
        retention_weight = 0.55 if events else 0.15
        module_weight = 0.25 if events else 0.55
        review_weight = 1.0 - retention_weight - module_weight
        score = round(
            retention_score * retention_weight
            + module_score * module_weight
            + review_signal * review_weight,
            3,
        )
        signals = {
            "retention": {
                "average_score": retention_score,
                "reviews": len(events),
                "lapse_rate": (
                    0.0
                    if not events
                    else sum(str(event["evaluation"]) == "again" for event in events)
                    / len(events)
                ),
            },
            "modules": {
                "average_score": round(module_score, 3),
                "count": len(modules),
                "completed": sum(
                    str(module["status"]) == "completed" for module in modules
                ),
            },
            "agent_review": {
                "readiness": None if review_row is None else str(review_row.readiness),
                "open_findings": int(open_findings),
            },
            "weights": {
                "retention": retention_weight,
                "modules": module_weight,
                "agent_review": review_weight,
            },
        }
        state = _mastery_state(score)
        self._insert_snapshot(concept_id, None, score, state, signals, now)
        domains_for_concept = self._domains(concept_id)
        return MasteryRecord(
            concept_id=concept_id,
            concept_title=str(concept["canonical_title"]),
            score=score,
            state=state,
            signals=signals,
            domains=domains_for_concept,
            recommendations=_mastery_recommendations(
                str(concept["canonical_title"]),
                score,
                retention_score,
                int(open_findings),
            ),
            updated_at=now,
        )

    def _insert_snapshot(
        self,
        concept_id: str,
        module_id: str | None,
        score: float,
        state: MasteryState,
        signals: dict[str, Any],
        created_at: str,
    ) -> None:
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                mastery_snapshots.insert().values(
                    id=f"mastery_{uuid4().hex}",
                    concept_id=concept_id,
                    module_id=module_id,
                    score=score,
                    state=state.value,
                    signals_json=json.dumps(signals, sort_keys=True),
                    created_at=created_at,
                )
            )

    def _latest_records(self, *, include_modules: bool = False) -> list[MasteryRecord]:
        with self.workspace.app_engine.connect() as connection:
            rows = connection.execute(
                select(mastery_snapshots).order_by(mastery_snapshots.c.created_at.desc())
            ).all()
        latest: dict[tuple[str, str | None], dict[str, Any]] = {}
        history: dict[tuple[str, str | None], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            item = row_dict(row)
            key = (
                str(item["concept_id"]),
                None if item.get("module_id") is None else str(item["module_id"]),
            )
            history[key].append(
                {
                    "score": float(item["score"]),
                    "state": str(item["state"]),
                    "created_at": str(item["created_at"]),
                }
            )
            latest.setdefault(key, item)
        with self.workspace.index_engine.connect() as connection:
            concept_rows = {
                str(row["concept_id"]): row for row in concepts.list_concepts(connection)
            }
        records: list[MasteryRecord] = []
        concept_scores = {
            concept_id: float(item["score"])
            for (concept_id, module_id), item in latest.items()
            if module_id is None
        }
        weak_map = self._weak_prerequisites(concept_scores)
        for key, item in latest.items():
            concept_id, module_id = key
            if module_id is not None and not include_modules:
                continue
            concept = concept_rows.get(concept_id)
            if concept is None:
                continue
            module_title = None
            if module_id is not None:
                detail = concept_detail(self.workspace, concept_id)
                module_title = next(
                    (
                        str(module["title"])
                        for module in cast(list[dict[str, Any]], detail["modules"])
                        if str(module["id"]) == module_id
                    ),
                    module_id,
                )
            score = float(item["score"])
            signals = _json_object(item["signals_json"])
            records.append(
                MasteryRecord(
                    concept_id=concept_id,
                    concept_title=str(concept["canonical_title"]),
                    module_id=module_id,
                    module_title=module_title,
                    score=score,
                    state=MasteryState(str(item["state"])),
                    signals=signals,
                    trend=history[key][:12],
                    domains=self._domains(concept_id),
                    weak_prerequisites=weak_map.get(concept_id, []),
                    recommendations=_mastery_recommendations(
                        str(concept["canonical_title"]),
                        score,
                        float(
                            cast(dict[str, Any], signals.get("retention") or {}).get(
                                "average_score", 0.0
                            )
                        ),
                        int(
                            cast(dict[str, Any], signals.get("agent_review") or {}).get(
                                "open_findings", 0
                            )
                        ),
                    ),
                    updated_at=str(item["created_at"]),
                )
            )
        return sorted(records, key=lambda item: (item.score, item.concept_title))

    def _weak_prerequisites(
        self,
        scores: dict[str, float],
    ) -> dict[str, list[dict[str, Any]]]:
        with self.workspace.index_engine.connect() as connection:
            rows = connection.execute(
                select(index_relationships)
                .where(
                    index_relationships.c.relationship_type
                    == RelationshipType.DEPENDS_ON.value
                )
                .where(index_relationships.c.target_id.is_not(None))
            ).mappings().all()
        result: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            source = str(row["source_concept_id"])
            target = str(row["target_id"])
            target_score = scores.get(target, 0.0)
            source_score = scores.get(source, 0.0)
            if target_score < 0.55 and source_score >= target_score:
                result[source].append(
                    {
                        "concept_id": target,
                        "title": str(row["target_title"]),
                        "score": target_score,
                        "reason": "Prerequisite evidence is weaker than the dependent concept.",
                    }
                )
        return result

    def _domains(self, concept_id: str) -> list[str]:
        with self.workspace.index_engine.connect() as connection:
            rows = domains.list_domains_for_concept(connection, concept_id)
        return [str(row["domain"]) for row in rows]


class ProfileService:
    def __init__(self, workspace: WorkspaceContext) -> None:
        self.workspace = workspace

    def list(
        self,
        *,
        status: ProfileObservationStatus | None = None,
    ) -> list[ProfileObservation]:
        statement = select(profile_observations).order_by(
            profile_observations.c.pinned.desc(),
            profile_observations.c.updated_at.desc(),
        )
        if status:
            statement = statement.where(profile_observations.c.status == status.value)
        with self.workspace.app_engine.connect() as connection:
            rows = connection.execute(statement).all()
        return [_decode_observation(row_dict(row)) for row in rows]

    def create(
        self,
        *,
        category: ProfileCategory,
        statement: str,
        evidence: list[dict[str, Any]] | None = None,
        confidence: float = 1.0,
        status: ProfileObservationStatus = ProfileObservationStatus.ACCEPTED,
        pinned: bool = False,
        source: str = "manual",
    ) -> ProfileObservation:
        clean = statement.strip()
        if not clean:
            raise ValueError("Profile statement cannot be empty.")
        existing = next(
            (
                item
                for item in self.list()
                if item.category == category
                and _normalize(item.statement) == _normalize(clean)
                and item.status != ProfileObservationStatus.REJECTED
            ),
            None,
        )
        if existing is not None:
            return existing
        now = utc_now()
        identifier = f"observation_{uuid4().hex}"
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                profile_observations.insert().values(
                    id=identifier,
                    category=category.value,
                    statement=clean,
                    evidence_json=json.dumps(evidence or [], sort_keys=True),
                    confidence=min(1.0, max(0.0, confidence)),
                    status=status.value,
                    pinned=pinned,
                    source=source,
                    created_at=now,
                    updated_at=now,
                )
            )
        self.write_soul()
        return self.get(identifier)

    def get(self, observation_id: str) -> ProfileObservation:
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(profile_observations).where(
                    profile_observations.c.id == observation_id
                )
            ).first()
        if row is None:
            raise KeyError(observation_id)
        return _decode_observation(row_dict(row))

    def update(
        self,
        observation_id: str,
        *,
        statement: str | None = None,
        category: ProfileCategory | None = None,
        confidence: float | None = None,
        status: ProfileObservationStatus | None = None,
        pinned: bool | None = None,
    ) -> ProfileObservation:
        values: dict[str, Any] = {"updated_at": utc_now()}
        if statement is not None:
            clean = statement.strip()
            if not clean:
                raise ValueError("Profile statement cannot be empty.")
            values["statement"] = clean
        if category is not None:
            values["category"] = category.value
        if confidence is not None:
            values["confidence"] = min(1.0, max(0.0, confidence))
        if status is not None:
            values["status"] = status.value
        if pinned is not None:
            values["pinned"] = pinned
        with app_transaction(self.workspace.app_engine) as connection:
            result = connection.execute(
                profile_observations.update()
                .where(profile_observations.c.id == observation_id)
                .values(**values)
            )
        if result.rowcount == 0:
            raise KeyError(observation_id)
        self.write_soul()
        return self.get(observation_id)

    def infer(self) -> list[ProfileObservation]:
        proposals: list[ProfileObservation] = []
        with self.workspace.app_engine.connect() as connection:
            event_rows = [
                row_dict(row)
                for row in connection.execute(select(review_events)).all()
            ]
        by_concept: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in event_rows:
            by_concept[str(event["concept_id"])].append(event)
        for concept_id, events in by_concept.items():
            if len(events) < 2:
                continue
            average = _average_scores(events)
            title = _concept_title(self.workspace, concept_id)
            if average < 0.58:
                proposals.append(
                    self.create(
                        category=ProfileCategory.GAP,
                        statement=f"Recall for {title} is currently fragile.",
                        evidence=[
                            {
                                "type": "retention_event",
                                "id": str(event["id"]),
                                "score": float(event["score"]),
                            }
                            for event in events[-5:]
                        ],
                        confidence=min(0.95, 0.55 + len(events) * 0.06),
                        status=ProfileObservationStatus.PROPOSED,
                        source="retention",
                    )
                )
            elif average >= 0.82:
                proposals.append(
                    self.create(
                        category=ProfileCategory.STRENGTH,
                        statement=f"Repeated recall indicates strength in {title}.",
                        evidence=[
                            {
                                "type": "retention_event",
                                "id": str(event["id"]),
                                "score": float(event["score"]),
                            }
                            for event in events[-5:]
                        ],
                        confidence=min(0.95, 0.55 + len(events) * 0.06),
                        status=ProfileObservationStatus.PROPOSED,
                        source="retention",
                    )
                )
        open_backlog = BacklogService(self.workspace).list(status=BacklogStatus.OPEN)
        if len(open_backlog) >= 3:
            top = sorted(open_backlog, key=lambda item: item.priority, reverse=True)[:3]
            proposals.append(
                self.create(
                    category=ProfileCategory.TOPIC_PRIORITY,
                    statement=(
                        "Current learning priorities include "
                        + ", ".join(item.title for item in top)
                        + "."
                    ),
                    evidence=[
                        {"type": "backlog_item", "id": item.id, "priority": item.priority}
                        for item in top
                    ],
                    confidence=0.72,
                    status=ProfileObservationStatus.PROPOSED,
                    source="backlog",
                )
            )
        self.write_soul()
        return proposals

    def soul_markdown(self) -> str:
        active = [
            item
            for item in self.list()
            if item.status == ProfileObservationStatus.ACCEPTED or item.pinned
        ]
        grouped: dict[ProfileCategory, list[ProfileObservation]] = defaultdict(list)
        for item in active:
            grouped[item.category].append(item)
        headings = {
            ProfileCategory.GOAL: "Goals",
            ProfileCategory.ACTIVE_CONTEXT: "Active Context",
            ProfileCategory.LEARNING_PREFERENCE: "Learning Preferences",
            ProfileCategory.STRENGTH: "Observed Strengths",
            ProfileCategory.GAP: "Observed Gaps",
            ProfileCategory.TOPIC_PRIORITY: "Topic Priorities",
        }
        lines = [
            "# Studium Learning Profile",
            "<!-- studium-profile-version: 1 -->",
            "",
            (
                "This local document contains only observations you accepted or pinned. "
                "Each item keeps its structured provenance in Studium app data."
            ),
        ]
        for category in ProfileCategory:
            lines.extend(["", f"## {headings[category]}", ""])
            values = grouped.get(category, [])
            if not values:
                lines.append("_No accepted observations._")
                continue
            for item in values:
                pin = " 📌" if item.pinned else ""
                lines.append(
                    f"- {item.statement}{pin} "
                    f"<!-- {item.id}; confidence={item.confidence:.2f}; source={item.source} -->"
                )
        lines.extend(["", f"_Generated locally at {utc_now()}._", ""])
        return "\n".join(lines)

    def write_soul(self) -> dict[str, Any]:
        path = self.workspace.config.workspace_dir / "soul.md"
        markdown = self.soul_markdown()
        path.write_text(markdown, encoding="utf-8")
        return {"path": str(path), "markdown": markdown}


def personalization_context(workspace: WorkspaceContext) -> list[str]:
    with workspace.app_engine.connect() as connection:
        rows = connection.execute(
            select(profile_observations)
            .where(
                profile_observations.c.status
                == ProfileObservationStatus.ACCEPTED.value
            )
            .order_by(
                profile_observations.c.pinned.desc(),
                profile_observations.c.confidence.desc(),
            )
            .limit(20)
        ).all()
    return [str(row.statement) for row in rows]


def _decode_backlog(
    row: dict[str, Any],
    *,
    resolution_candidate: dict[str, Any] | None,
) -> BacklogItem:
    return BacklogItem(
        id=str(row["id"]),
        title=str(row["title"]),
        item_type=BacklogItemType(str(row["item_type"])),
        status=BacklogStatus(str(row["status"])),
        priority=int(row["priority"]),
        reason=str(row["reason"]),
        origin=BacklogOrigin(str(row["origin"])),
        related_concept_id=(
            None
            if row.get("related_concept_id") is None
            else str(row["related_concept_id"])
        ),
        required_by=_json_strings(row.get("required_by_json")),
        source_query=(
            None if row.get("source_query") is None else str(row["source_query"])
        ),
        metadata=_json_object(row.get("metadata_json")),
        resolution_candidate=resolution_candidate,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        completed_at=(
            None if row.get("completed_at") is None else str(row["completed_at"])
        ),
    )


def _decode_observation(row: dict[str, Any]) -> ProfileObservation:
    return ProfileObservation(
        id=str(row["id"]),
        category=ProfileCategory(str(row["category"])),
        statement=str(row["statement"]),
        evidence=_json_dicts(row.get("evidence_json")),
        confidence=float(row["confidence"]),
        status=ProfileObservationStatus(str(row["status"])),
        pinned=bool(row["pinned"]),
        source=str(row["source"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _backlog_type(value: Any) -> BacklogItemType:
    try:
        return BacklogItemType(str(value or BacklogItemType.NEW_CONCEPT.value))
    except ValueError:
        return BacklogItemType.NEW_CONCEPT


def _backlog_origin(value: Any) -> BacklogOrigin:
    try:
        return BacklogOrigin(str(value or BacklogOrigin.MANUAL.value))
    except ValueError:
        return BacklogOrigin.MANUAL


def _retention_prompt(title: str, module_type: str, module_title: str) -> str:
    prompts = {
        "conceptual_explanation": (
            f"Without notes, explain {title} through the “{module_title}” module. "
            "Name the problem, mechanism, assumptions, and boundary."
        ),
        "worked_example": (
            f"Reconstruct the worked example for {title}. State the setup, each "
            "transformation, a verification check, and the interpretation."
        ),
        "code_implementation": (
            f"Describe or write the implementation contract for {title}: inputs, "
            "outputs, invariant, algorithm, and one boundary test."
        ),
        "derivation": (
            f"Rebuild the derivation in “{module_title}” from its starting assumptions "
            "and justify each transformation."
        ),
        "comparison": (
            f"Compare {title} with its closest alternative by mechanism, assumptions, "
            "strength, failure mode, and decision rule."
        ),
        "misconception_debugging": (
            f"State a plausible misconception about {title}, expose it with a "
            "counterexample, and give the corrected model."
        ),
    }
    return prompts.get(
        module_type,
        f"Reconstruct the “{module_title}” module for {title} and explain how you verified it.",
    )


def _expected_components(module_type: str, markdown: str) -> list[str]:
    defaults = {
        "conceptual_explanation": ["problem", "mechanism", "assumptions", "boundary"],
        "worked_example": ["setup", "transformation", "check", "interpretation"],
        "code_implementation": ["input", "output", "invariant", "test"],
        "derivation": ["assumptions", "transformation", "rule", "interpretation"],
        "comparison": ["mechanism", "assumptions", "strength", "failure mode"],
        "application": ["goal", "signal", "decision", "limitation"],
        "misconception_debugging": ["mistake", "counterexample", "correction"],
    }
    values = list(defaults.get(module_type, ["claim", "reasoning", "verification"]))
    headings = [
        match.group(1).strip().casefold()
        for match in re.finditer(r"^####\s+(.+)$", markdown, re.MULTILINE)
    ]
    for heading in headings:
        if heading not in values and len(values) < 6:
            values.append(heading)
    return values


def _response_component_score(
    response: str,
    components: list[str],
) -> tuple[float, list[str]]:
    response_tokens = set(_tokens(response))
    if not components:
        return (1.0 if response_tokens else 0.0), []
    covered: list[str] = []
    for component in components:
        tokens = set(_tokens(component))
        if tokens and (tokens & response_tokens):
            covered.append(component)
    missed = [item for item in components if item not in covered]
    return len(covered) / len(components), missed


def _evaluation(self_rating: int, score: float) -> RetentionEvaluation:
    if self_rating <= 1 or score < 0.3:
        return RetentionEvaluation.AGAIN
    if self_rating == 2 or score < 0.52:
        return RetentionEvaluation.HARD
    if self_rating >= 5 and score >= 0.82:
        return RetentionEvaluation.EASY
    return RetentionEvaluation.GOOD


def _schedule(
    card: RetentionCard,
    evaluation: RetentionEvaluation,
) -> dict[str, Any]:
    quality = {
        RetentionEvaluation.AGAIN: 1,
        RetentionEvaluation.HARD: 3,
        RetentionEvaluation.GOOD: 4,
        RetentionEvaluation.EASY: 5,
    }[evaluation]
    ease = max(
        1.3,
        card.ease_factor
        + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )
    if evaluation == RetentionEvaluation.AGAIN:
        interval = 1
        repetitions = 0
        lapses = card.lapses + 1
    else:
        repetitions = card.repetitions + 1
        lapses = card.lapses
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 6
        else:
            modifier = {
                RetentionEvaluation.HARD: 0.8,
                RetentionEvaluation.GOOD: 1.0,
                RetentionEvaluation.EASY: 1.3,
            }[evaluation]
            interval = max(1, round(max(1, card.interval_days) * ease * modifier))
    difficulty = min(1.0, max(0.05, card.difficulty + (3 - quality) * 0.06))
    stability = max(0.1, card.stability * 0.85 + interval * (1.0 - difficulty))
    return {
        "interval_days": interval,
        "ease_factor": round(ease, 3),
        "repetitions": repetitions,
        "lapses": lapses,
        "difficulty": round(difficulty, 3),
        "stability": round(stability, 3),
    }


def _mastery_state(score: float) -> MasteryState:
    if score < 0.12:
        return MasteryState.UNASSESSED
    if score < 0.45:
        return MasteryState.FRAGILE
    if score < 0.75:
        return MasteryState.DEVELOPING
    return MasteryState.STRONG


def _mastery_recommendations(
    title: str,
    score: float,
    retention_score: float,
    open_findings: int,
) -> list[str]:
    values: list[str] = []
    if retention_score < 0.55:
        values.append(f"Run a focused recall session for {title}.")
    if open_findings:
        values.append(f"Resolve {open_findings} review finding(s) before expanding {title}.")
    if score < 0.45:
        values.append("Reconstruct one weak module before reading the full note.")
    elif score >= 0.75:
        values.append("Use transfer practice to test this strength in a new context.")
    return values


def _average_scores(events: list[dict[str, Any]]) -> float:
    if not events:
        return 0.0
    return round(sum(float(event["score"]) for event in events) / len(events), 3)


def _profile_relevance(title: str, statements: list[str]) -> float:
    title_tokens = set(_tokens(title))
    if not title_tokens:
        return 0.0
    return max(
        (
            len(title_tokens & set(_tokens(statement))) / len(title_tokens)
            for statement in statements
        ),
        default=0.0,
    )


def _concept_title(workspace: WorkspaceContext, concept_id: str) -> str:
    with workspace.index_engine.connect() as connection:
        row = concepts.get_concept(connection, concept_id)
    return concept_id if row is None else str(row["canonical_title"])


def _normalize(value: str) -> str:
    return " ".join(_tokens(value))


def _tokens(value: str) -> list[str]:
    return _TOKEN_RE.findall(value.casefold())


def _content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _json_strings(value: Any) -> list[str]:
    loaded = _json_value(value, [])
    if not isinstance(loaded, list):
        return []
    return [str(item) for item in cast(list[Any], loaded)]


def _json_dicts(value: Any) -> list[dict[str, Any]]:
    loaded = _json_value(value, [])
    if not isinstance(loaded, list):
        return []
    return [
        cast(dict[str, Any], item)
        for item in cast(list[Any], loaded)
        if isinstance(item, dict)
    ]


def _json_object(value: Any) -> dict[str, Any]:
    loaded = _json_value(value, {})
    return cast(dict[str, Any], loaded) if isinstance(loaded, dict) else {}


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    try:
        return json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return default


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in cast(list[Any], value)]


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

