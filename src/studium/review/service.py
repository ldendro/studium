"""Deterministic and provider-assisted review with explicit acceptance gates."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from studium.app.database import (
    app_transaction,
    note_versions,
    review_findings,
    review_sessions,
    row_dict,
    source_contributions,
)
from studium.app.learning import personalization_context
from studium.app.migrations import utc_now
from studium.app.workspace import WorkspaceContext
from studium.index.repositories import concepts
from studium.llm.runner import run_reasoning_task
from studium.llm.tasks import TaskConfig, TaskDefinition
from studium.parsing import parse_concept_note
from studium.review.models import (
    AcceptanceGate,
    FindingCategory,
    FindingSeverity,
    FindingStatus,
    PatchPreview,
    ReviewAnchor,
    ReviewFinding,
    ReviewReadiness,
    ReviewSession,
    ReviewSessionStatus,
    ReviewSummary,
)
from studium.schemas import (
    ConceptType,
    NoteStatus,
    NoteVaultStatus,
    RelationshipStatus,
    RelationshipType,
    RelationshipVaultStatus,
    ReviewStatus,
    ScaffoldModuleType,
    ValidationOperation,
    ValidationSeverity,
)
from studium.validation import parse_and_validate
from studium.writes import (
    WriteProposalBlockedError,
    build_metadata_update_proposal,
    build_update_note_proposal,
    proposal_can_be_committed,
)

_PLACEHOLDER = re.compile(
    r"\bTODO\b|NotImplementedError|_(?:Write|Fill|Name|Explain|State|Complete|Record|"
    r"Apply|Compute|Check|Define|Use|What)[^_\n]*_"
)
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)

_ESSENTIAL_MODULES: dict[ConceptType, tuple[ScaffoldModuleType, ...]] = {
    ConceptType.ALGORITHM: (
        ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
        ScaffoldModuleType.WORKED_EXAMPLE,
    ),
    ConceptType.MATHEMATICAL_CONCEPT: (
        ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
        ScaffoldModuleType.WORKED_EXAMPLE,
    ),
    ConceptType.THEORY_CONCEPT: (
        ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
        ScaffoldModuleType.WORKED_EXAMPLE,
    ),
    ConceptType.PROGRAMMING_CONCEPT: (
        ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
        ScaffoldModuleType.CODE_IMPLEMENTATION,
    ),
    ConceptType.SYSTEM_DESIGN_CONCEPT: (
        ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
        ScaffoldModuleType.CODE_IMPLEMENTATION,
    ),
    ConceptType.TOOLING_CONCEPT: (
        ScaffoldModuleType.CONCEPTUAL_EXPLANATION,
        ScaffoldModuleType.CODE_IMPLEMENTATION,
    ),
    ConceptType.GENERAL_CONCEPT: (ScaffoldModuleType.CONCEPTUAL_EXPLANATION,),
    ConceptType.PROCESS_CONCEPT: (ScaffoldModuleType.CONCEPTUAL_EXPLANATION,),
}


class _AgentFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Literal["critical", "recommended", "optional"]
    category: Literal["conceptual", "relationship", "source_grounding"]
    message: str
    quoted_text: str | None = None
    proposed_patch: str | None = None


def _empty_agent_findings() -> list[_AgentFinding]:
    return []


class _AgentReviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[_AgentFinding] = Field(default_factory=_empty_agent_findings)


_AGENT_REVIEW_TASK = TaskDefinition(
    task_id="concept_note_review",
    version="1",
    system_prompt=(
        "Review a Studium learning note for conceptual accuracy, coherent relationships, "
        "and fidelity to cited source context. Be conservative: report only actionable "
        "issues grounded in quoted note text. Never invent citations or vault concepts."
    ),
    user_template=(
        "Concept metadata (JSON):\n{metadata_json}\n\n"
        "Markdown note:\n{markdown}\n\n"
        "Return at most four findings as _AgentReviewOutput JSON."
    ),
    output_schema=_AgentReviewOutput,
    config=TaskConfig(temperature=0.0, max_tokens=1000, timeout_seconds=45.0),
)


class ReviewService:
    """Persisted review reports and the only promotion path for draft notes."""

    def __init__(self, workspace: WorkspaceContext) -> None:
        self.workspace = workspace

    def list_queue(self) -> list[dict[str, Any]]:
        with self.workspace.index_engine.connect() as connection:
            indexed = [
                row
                for row in concepts.list_concepts(connection)
                if str(row["vault_status"]) == NoteVaultStatus.DRAFT.value
            ]
        return [self._queue_item(row) for row in indexed]

    def submit(self, concept_id: str) -> ReviewSession:
        concept = self._concept(concept_id)
        file_path = str(concept["file_path"])
        raw = self.workspace.vault.read_markdown(file_path)
        parsed = parse_concept_note(raw)
        if parsed.metadata is None:
            raise ValueError("The draft cannot be reviewed because its metadata is invalid.")
        if parsed.metadata.vault_status == NoteVaultStatus.ARCHIVED:
            raise ValueError("Archived notes cannot be submitted for review.")

        review_id = f"review_{uuid4().hex}"
        created_at = utc_now()
        findings = self._deterministic_findings(review_id, concept_id, raw)
        review_context = parsed.metadata.model_dump(mode="json")
        review_context["accepted_learning_profile"] = personalization_context(
            self.workspace
        )
        agent_findings, agent_mode = self._provider_findings(
            review_id,
            concept_id,
            raw,
            review_context,
        )
        findings.extend(agent_findings)
        readiness = _readiness(findings)

        next_review_status = (
            ReviewStatus.CHANGES_REQUESTED
            if readiness == ReviewReadiness.NEEDS_REVISION
            else ReviewStatus.IN_REVIEW
        )
        next_metadata = parsed.metadata.model_copy(
            update={
                "status": NoteStatus.IN_REVIEW,
                "review_status": next_review_status,
                "vault_status": NoteVaultStatus.DRAFT,
                "updated_at": datetime.now(UTC).replace(microsecond=0),
            }
        )
        proposal = build_metadata_update_proposal(
            self.workspace.vault,
            file_path,
            next_metadata,
            body=parsed.body,
        )
        if not proposal_can_be_committed(proposal):
            raise WriteProposalBlockedError("Review status update failed note validation.")
        self.workspace.commit(proposal)
        reviewed_markdown = proposal.after_content
        summary = _summary(
            findings,
            content_hash=_content_hash(reviewed_markdown),
            agent_mode=agent_mode,
        )
        completed_at = utc_now()

        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                review_sessions.insert().values(
                    id=review_id,
                    concept_id=concept_id,
                    file_path=file_path,
                    status=ReviewSessionStatus.COMPLETED.value,
                    readiness=readiness.value,
                    summary_json=summary.model_dump_json(),
                    created_at=created_at,
                    completed_at=completed_at,
                )
            )
            if findings:
                connection.execute(
                    review_findings.insert(),
                    [_finding_row(item) for item in findings],
                )
        return self.get_session(review_id)

    def list_sessions(self, concept_id: str | None = None) -> list[ReviewSession]:
        statement = select(review_sessions).order_by(review_sessions.c.created_at.desc())
        if concept_id:
            statement = statement.where(review_sessions.c.concept_id == concept_id)
        with self.workspace.app_engine.connect() as connection:
            rows = connection.execute(statement).all()
        return [self._session_from_row(row_dict(row), include_findings=False) for row in rows]

    def latest(self, concept_id: str) -> ReviewSession:
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(review_sessions)
                .where(review_sessions.c.concept_id == concept_id)
                .order_by(review_sessions.c.created_at.desc())
                .limit(1)
            ).first()
        if row is None:
            raise KeyError(concept_id)
        return self._session_from_row(row_dict(row), include_findings=True)

    def get_session(self, review_id: str) -> ReviewSession:
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(review_sessions).where(review_sessions.c.id == review_id)
            ).first()
        if row is None:
            raise KeyError(review_id)
        return self._session_from_row(row_dict(row), include_findings=True)

    def preview_patch(self, finding_id: str, replacement: str | None = None) -> PatchPreview:
        finding = self._finding(finding_id)
        before, after, target_path, selected = self._patched_markdown(finding, replacement)
        proposal = build_update_note_proposal(
            self.workspace.vault,
            target_path,
            after,
            before_content=before,
        )
        return PatchPreview(
            finding_id=finding_id,
            target_path=target_path,
            replacement=selected,
            diff=_diff(target_path, before, after),
            can_commit=proposal_can_be_committed(proposal),
            warnings=[item.model_dump(mode="json") for item in proposal.warnings],
            critical_errors=[
                item.model_dump(mode="json") for item in proposal.critical_errors
            ],
        )

    def decide_finding(
        self,
        finding_id: str,
        *,
        action: str,
        replacement: str | None = None,
        decision_note: str | None = None,
    ) -> dict[str, Any]:
        finding = self._finding(finding_id)
        if action in {"accept", "edit"}:
            before, after, target_path, selected = self._patched_markdown(
                finding,
                replacement,
            )
            proposal = build_update_note_proposal(
                self.workspace.vault,
                target_path,
                after,
                before_content=before,
            )
            if not proposal_can_be_committed(proposal):
                raise WriteProposalBlockedError("The proposed patch failed note validation.")
            result = self.workspace.commit(proposal)
            self._set_finding_status(
                finding_id,
                FindingStatus.APPLIED,
                decision_note=decision_note or f"Applied replacement: {selected[:120]}",
            )
            self._refresh_session(
                finding.review_id,
                content_hash=_content_hash(after),
            )
            return {
                "finding": self._finding(finding_id).model_dump(mode="json"),
                "markdown": after,
                "index_revision": result.index_revision,
            }
        if action == "reject":
            self._set_finding_status(
                finding_id,
                FindingStatus.REJECTED,
                decision_note=decision_note,
            )
        elif action == "resolve":
            self._set_finding_status(
                finding_id,
                FindingStatus.RESOLVED,
                decision_note=decision_note,
            )
        elif action == "reopen":
            self._set_finding_status(
                finding_id,
                FindingStatus.OPEN,
                decision_note=decision_note,
            )
        else:
            raise ValueError("Action must be accept, edit, reject, resolve, or reopen.")
        self._refresh_session(finding.review_id)
        return {"finding": self._finding(finding_id).model_dump(mode="json")}

    def acceptance_gate(self, concept_id: str) -> AcceptanceGate:
        try:
            session = self.latest(concept_id)
        except KeyError:
            return AcceptanceGate(
                concept_id=concept_id,
                can_accept=False,
                blockers=["Complete at least one review before accepting this note."],
            )
        concept = self._concept(concept_id)
        raw = self.workspace.vault.read_markdown(str(concept["file_path"]))
        blockers = list(session.summary.blockers)
        if session.status != ReviewSessionStatus.COMPLETED:
            blockers.append("The latest review has not completed.")
        if _content_hash(raw) != session.summary.content_hash:
            blockers.append("The note changed after review. Run review again.")
        recommendations = [
            finding.message
            for finding in session.findings
            if finding.severity == FindingSeverity.RECOMMENDED
            and finding.status in {FindingStatus.OPEN, FindingStatus.REJECTED}
        ]
        next_metadata, body = self._accepted_metadata(raw)
        proposal = build_metadata_update_proposal(
            self.workspace.vault,
            str(concept["file_path"]),
            next_metadata,
            body=body,
        )
        if not proposal_can_be_committed(proposal):
            blockers.extend(issue.message for issue in proposal.critical_errors)
        return AcceptanceGate(
            concept_id=concept_id,
            review_id=session.id,
            readiness=session.readiness,
            can_accept=not blockers,
            requires_acknowledgement=bool(recommendations),
            blockers=list(dict.fromkeys(blockers)),
            recommendations=recommendations,
            preview_diff=_diff(str(concept["file_path"]), raw, proposal.after_content),
        )

    def accept(
        self,
        concept_id: str,
        *,
        acknowledge_recommended: bool = False,
    ) -> dict[str, Any]:
        gate = self.acceptance_gate(concept_id)
        if not gate.can_accept:
            raise ValueError("Acceptance blocked: " + " ".join(gate.blockers))
        if gate.requires_acknowledgement and not acknowledge_recommended:
            raise ValueError("Acknowledge the remaining recommended findings before acceptance.")

        concept = self._concept(concept_id)
        file_path = str(concept["file_path"])
        before = self.workspace.vault.read_markdown(file_path)
        metadata, body = self._accepted_metadata(before)
        proposal = build_metadata_update_proposal(
            self.workspace.vault,
            file_path,
            metadata,
            body=body,
        )
        if not proposal_can_be_committed(proposal):
            raise WriteProposalBlockedError("Acceptance metadata failed note validation.")
        result = self.workspace.commit(proposal)
        version = self._next_version(concept_id)
        now = utc_now()
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                note_versions.insert().values(
                    id=f"version_{uuid4().hex}",
                    concept_id=concept_id,
                    file_path=file_path,
                    version=version,
                    content_hash=_content_hash(proposal.after_content),
                    markdown=proposal.after_content,
                    reason="accepted_update" if version > 1 else "initial_acceptance",
                    created_at=now,
                )
            )
        return {
            "concept_id": concept_id,
            "target_path": file_path,
            "vault_status": NoteVaultStatus.ACCEPTED.value,
            "review_status": ReviewStatus.APPROVED.value,
            "index_revision": result.index_revision,
            "version": version,
        }

    def versions(self, concept_id: str) -> list[dict[str, Any]]:
        with self.workspace.app_engine.connect() as connection:
            rows = connection.execute(
                select(note_versions)
                .where(note_versions.c.concept_id == concept_id)
                .order_by(note_versions.c.version.desc())
            ).all()
        return [row_dict(row) for row in rows]

    def _deterministic_findings(
        self,
        review_id: str,
        concept_id: str,
        markdown: str,
    ) -> list[ReviewFinding]:
        parsed, validation = parse_and_validate(
            markdown,
            operation=ValidationOperation.UPDATE,
        )
        now = utc_now()
        findings: list[ReviewFinding] = []
        for issue in [*validation.critical_errors, *validation.warnings]:
            severity = (
                FindingSeverity.CRITICAL
                if issue.severity == ValidationSeverity.CRITICAL
                else FindingSeverity.RECOMMENDED
            )
            findings.append(
                _new_finding(
                    review_id,
                    concept_id,
                    FindingCategory.PREFLIGHT,
                    severity,
                    issue.message,
                    now=now,
                )
            )
        if parsed.metadata is None:
            return findings

        by_type = {module.type: module for module in parsed.metadata.scaffold_modules}
        essential = _ESSENTIAL_MODULES[parsed.metadata.concept_type]
        for module_type in essential:
            module = by_type.get(module_type)
            if module is None:
                findings.append(
                    _new_finding(
                        review_id,
                        concept_id,
                        FindingCategory.COVERAGE,
                        FindingSeverity.CRITICAL,
                        f"Add the essential {module_type.value.replace('_', ' ')} module.",
                        now=now,
                    )
                )
                continue
            content = _module_markdown(parsed.body, module.title)
            if len(_plain_words(content)) < 25:
                findings.append(
                    _new_finding(
                        review_id,
                        concept_id,
                        FindingCategory.COVERAGE,
                        FindingSeverity.CRITICAL,
                        f"Complete the essential module “{module.title}” before acceptance.",
                        module_id=module.id,
                        anchor=_anchor_for_text(markdown, f"### {module.title}", module.id),
                        now=now,
                    )
                )

        for module in parsed.metadata.scaffold_modules:
            content = _module_markdown(parsed.body, module.title)
            match = _PLACEHOLDER.search(content)
            if match is None:
                continue
            quoted = match.group(0)
            severity = (
                FindingSeverity.CRITICAL
                if module.type in essential
                else FindingSeverity.RECOMMENDED
            )
            findings.append(
                _new_finding(
                    review_id,
                    concept_id,
                    FindingCategory.CONCEPTUAL,
                    severity,
                    f"Replace the unresolved scaffold prompt in “{module.title}” with your answer.",
                    module_id=module.id,
                    anchor=_anchor_for_text(markdown, quoted, module.id),
                    quoted_text=quoted,
                    proposed_patch=(
                        "Explain the mechanism in your own words and verify it with a "
                        "concrete, checkable example."
                    ),
                    now=now,
                )
            )

        overview = _section_markdown(parsed.body, "Concept Overview")
        overview_placeholder = _PLACEHOLDER.search(overview)
        if overview_placeholder is not None:
            quoted = overview_placeholder.group(0)
            findings.append(
                _new_finding(
                    review_id,
                    concept_id,
                    FindingCategory.CONCEPTUAL,
                    FindingSeverity.RECOMMENDED,
                    "Replace the remaining Concept Overview prompt with a concise claim.",
                    anchor=_anchor_for_text(markdown, quoted),
                    quoted_text=quoted,
                    proposed_patch="State the core mechanism and the problem it solves.",
                    now=now,
                )
            )

        for relationship in parsed.metadata.relationships:
            if (
                relationship.relationship_type == RelationshipType.DEPENDS_ON
                and relationship.vault_status != RelationshipVaultStatus.FOUND
            ):
                findings.append(
                    _new_finding(
                        review_id,
                        concept_id,
                        FindingCategory.RELATIONSHIP,
                        FindingSeverity.CRITICAL,
                        f"Resolve prerequisite “{relationship.target_title}” before acceptance.",
                        now=now,
                    )
                )
            elif relationship.target_id is None:
                findings.append(
                    _new_finding(
                        review_id,
                        concept_id,
                        FindingCategory.RELATIONSHIP,
                        FindingSeverity.RECOMMENDED,
                        f"Reconcile the unresolved relationship to “{relationship.target_title}”.",
                        now=now,
                    )
                )

        attached_ids = {
            encounter.content_id
            for encounter in parsed.metadata.learning_encounters
            if encounter.content_attached and encounter.content_id
        }
        if attached_ids and not self._has_source_evidence(concept_id, attached_ids):
            findings.append(
                _new_finding(
                    review_id,
                    concept_id,
                    FindingCategory.SOURCE_GROUNDING,
                    FindingSeverity.RECOMMENDED,
                    "Attached source content has not yet been compared with this note.",
                    now=now,
                )
            )
        return _deduplicate_findings(findings)

    def _provider_findings(
        self,
        review_id: str,
        concept_id: str,
        markdown: str,
        metadata: dict[str, Any],
    ) -> tuple[list[ReviewFinding], str]:
        provider = self.workspace.llm_provider
        settings = self.workspace.provider_settings
        local_endpoint = settings.llm_base_url.startswith(
            ("http://127.0.0.1", "http://localhost")
        )
        if provider is None or (not settings.remote_data_allowed and not local_endpoint):
            return [], "deterministic"
        result = run_reasoning_task(
            provider,
            _AGENT_REVIEW_TASK,
            {
                "metadata_json": json.dumps(metadata, sort_keys=True),
                "markdown": markdown[:24000],
            },
        )
        if not result.ok or result.data is None:
            return [], "deterministic_provider_unavailable"
        output = _AgentReviewOutput.model_validate(result.data)
        now = utc_now()
        findings: list[ReviewFinding] = []
        for item in output.findings[:4]:
            candidate = item.quoted_text
            quoted = candidate if candidate is not None and candidate in markdown else None
            findings.append(
                _new_finding(
                    review_id,
                    concept_id,
                    FindingCategory(item.category),
                    FindingSeverity(item.severity),
                    item.message,
                    anchor=None if quoted is None else _anchor_for_text(markdown, quoted),
                    quoted_text=quoted,
                    proposed_patch=item.proposed_patch if quoted else None,
                    now=now,
                )
            )
        return findings, f"provider:{provider.model_id()}"

    def _has_source_evidence(self, concept_id: str, source_ids: set[str]) -> bool:
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(source_contributions.c.id)
                .where(source_contributions.c.concept_id == concept_id)
                .where(source_contributions.c.source_id.in_(source_ids))
                .limit(1)
            ).first()
        return row is not None

    def _concept(self, concept_id: str) -> dict[str, Any]:
        with self.workspace.index_engine.connect() as connection:
            concept = concepts.get_concept(connection, concept_id)
        if concept is None:
            raise KeyError(concept_id)
        return concept

    def _queue_item(self, concept: dict[str, Any]) -> dict[str, Any]:
        concept_id = str(concept["concept_id"])
        latest: ReviewSession | None
        try:
            latest = self.latest(concept_id)
        except KeyError:
            latest = None
        return {
            "concept_id": concept_id,
            "canonical_title": str(concept["canonical_title"]),
            "file_path": str(concept["file_path"]),
            "concept_type": str(concept["concept_type"]),
            "status": str(concept["status"]),
            "review_status": str(concept["review_status"]),
            "vault_status": str(concept["vault_status"]),
            "updated_at": concept.get("note_updated_at"),
            "latest_review": (
                None
                if latest is None
                else {
                    "id": latest.id,
                    "status": latest.status.value,
                    "readiness": latest.readiness.value,
                    "completed_at": latest.completed_at,
                }
            ),
            "open_critical_count": (
                0 if latest is None else latest.summary.open_critical_count
            ),
        }

    def _finding(self, finding_id: str) -> ReviewFinding:
        with self.workspace.app_engine.connect() as connection:
            row = connection.execute(
                select(review_findings).where(review_findings.c.id == finding_id)
            ).first()
        if row is None:
            raise KeyError(finding_id)
        return _decode_finding(row_dict(row))

    def _patched_markdown(
        self,
        finding: ReviewFinding,
        replacement: str | None,
    ) -> tuple[str, str, str, str]:
        selected = replacement if replacement is not None else finding.proposed_patch
        if selected is None or not selected.strip():
            raise ValueError("This finding does not include an applicable patch.")
        concept = self._concept(finding.concept_id)
        target_path = str(concept["file_path"])
        before = self.workspace.vault.read_markdown(target_path)
        quoted = finding.quoted_text
        if quoted and quoted in before:
            after = before.replace(quoted, selected.strip(), 1)
        elif finding.anchor and finding.anchor.start_offset is not None:
            start = finding.anchor.start_offset
            end = finding.anchor.end_offset or start
            if start > len(before) or end > len(before) or end < start:
                raise ValueError("The anchored patch is stale. Run review again.")
            after = f"{before[:start]}{selected.strip()}{before[end:]}"
        else:
            raise ValueError("The anchored text changed. Run review again.")
        return before, after, target_path, selected.strip()

    def _set_finding_status(
        self,
        finding_id: str,
        status: FindingStatus,
        *,
        decision_note: str | None,
    ) -> None:
        resolved = (
            utc_now()
            if status in {FindingStatus.RESOLVED, FindingStatus.APPLIED}
            else None
        )
        with app_transaction(self.workspace.app_engine) as connection:
            result = connection.execute(
                review_findings.update()
                .where(review_findings.c.id == finding_id)
                .values(
                    status=status.value,
                    decision_note=decision_note,
                    resolved_at=resolved,
                )
            )
        if result.rowcount == 0:
            raise KeyError(finding_id)

    def _refresh_session(
        self,
        review_id: str,
        *,
        content_hash: str | None = None,
    ) -> None:
        session = self.get_session(review_id)
        summary = _summary(
            session.findings,
            content_hash=content_hash or session.summary.content_hash,
            agent_mode=session.summary.agent_mode,
        )
        readiness = _readiness(session.findings)
        with app_transaction(self.workspace.app_engine) as connection:
            connection.execute(
                review_sessions.update()
                .where(review_sessions.c.id == review_id)
                .values(
                    readiness=readiness.value,
                    summary_json=summary.model_dump_json(),
                )
            )

    def _session_from_row(
        self,
        row: dict[str, Any],
        *,
        include_findings: bool,
    ) -> ReviewSession:
        findings: list[ReviewFinding] = []
        if include_findings:
            with self.workspace.app_engine.connect() as connection:
                finding_rows = connection.execute(
                    select(review_findings)
                    .where(review_findings.c.review_id == str(row["id"]))
                    .order_by(
                        review_findings.c.severity,
                        review_findings.c.created_at,
                    )
                ).all()
            findings = [_decode_finding(row_dict(item)) for item in finding_rows]
        return ReviewSession(
            id=str(row["id"]),
            concept_id=str(row["concept_id"]),
            file_path=str(row["file_path"]),
            status=ReviewSessionStatus(str(row["status"])),
            readiness=ReviewReadiness(str(row["readiness"])),
            summary=ReviewSummary.model_validate_json(str(row["summary_json"] or "{}")),
            created_at=str(row["created_at"]),
            completed_at=(
                None if row.get("completed_at") is None else str(row["completed_at"])
            ),
            findings=findings,
        )

    def _accepted_metadata(self, markdown: str) -> tuple[Any, str]:
        parsed = parse_concept_note(markdown)
        if parsed.metadata is None:
            raise ValueError("The note can no longer be parsed.")
        relationships = [
            relationship.model_copy(
                update={
                    "status": (
                        RelationshipStatus.USER_CONFIRMED
                        if relationship.target_id
                        else relationship.status
                    )
                }
            )
            for relationship in parsed.metadata.relationships
        ]
        metadata = parsed.metadata.model_copy(
            update={
                "status": NoteStatus.COMPLETED,
                "review_status": ReviewStatus.APPROVED,
                "vault_status": NoteVaultStatus.ACCEPTED,
                "relationships": relationships,
                "updated_at": datetime.now(UTC).replace(microsecond=0),
            }
        )
        return metadata, parsed.body

    def _next_version(self, concept_id: str) -> int:
        with self.workspace.app_engine.connect() as connection:
            current = connection.execute(
                select(func.max(note_versions.c.version)).where(
                    note_versions.c.concept_id == concept_id
                )
            ).scalar_one_or_none()
        return 1 if current is None else int(current) + 1


def _new_finding(
    review_id: str,
    concept_id: str,
    category: FindingCategory,
    severity: FindingSeverity,
    message: str,
    *,
    module_id: str | None = None,
    anchor: ReviewAnchor | None = None,
    quoted_text: str | None = None,
    proposed_patch: str | None = None,
    now: str,
) -> ReviewFinding:
    return ReviewFinding(
        id=f"finding_{uuid4().hex}",
        review_id=review_id,
        concept_id=concept_id,
        module_id=module_id,
        category=category,
        severity=severity,
        message=message,
        anchor=anchor,
        quoted_text=quoted_text,
        proposed_patch=proposed_patch,
        created_at=now,
    )


def _finding_row(finding: ReviewFinding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "review_id": finding.review_id,
        "concept_id": finding.concept_id,
        "module_id": finding.module_id,
        "category": finding.category.value,
        "severity": finding.severity.value,
        "message": finding.message,
        "anchor_json": None if finding.anchor is None else finding.anchor.model_dump_json(),
        "quoted_text": finding.quoted_text,
        "proposed_patch": finding.proposed_patch,
        "status": finding.status.value,
        "decision_note": finding.decision_note,
        "created_at": finding.created_at,
        "resolved_at": finding.resolved_at,
    }


def _decode_finding(row: dict[str, Any]) -> ReviewFinding:
    raw_anchor = row.get("anchor_json")
    return ReviewFinding(
        id=str(row["id"]),
        review_id=str(row["review_id"]),
        concept_id=str(row["concept_id"]),
        module_id=None if row.get("module_id") is None else str(row["module_id"]),
        category=FindingCategory(str(row["category"])),
        severity=FindingSeverity(str(row["severity"])),
        message=str(row["message"]),
        anchor=(
            None
            if raw_anchor is None
            else ReviewAnchor.model_validate_json(str(raw_anchor))
        ),
        quoted_text=(
            None if row.get("quoted_text") is None else str(row["quoted_text"])
        ),
        proposed_patch=(
            None if row.get("proposed_patch") is None else str(row["proposed_patch"])
        ),
        status=FindingStatus(str(row["status"])),
        decision_note=(
            None if row.get("decision_note") is None else str(row["decision_note"])
        ),
        created_at=str(row["created_at"]),
        resolved_at=(
            None if row.get("resolved_at") is None else str(row["resolved_at"])
        ),
    )


def _readiness(findings: Iterable[ReviewFinding]) -> ReviewReadiness:
    active = {
        FindingStatus.OPEN,
        FindingStatus.REJECTED,
    }
    values = list(findings)
    if any(
        finding.severity == FindingSeverity.CRITICAL and finding.status in active
        for finding in values
    ):
        return ReviewReadiness.NEEDS_REVISION
    if any(
        finding.severity == FindingSeverity.RECOMMENDED and finding.status in active
        for finding in values
    ):
        return ReviewReadiness.APPROVED_WITH_SUGGESTIONS
    return ReviewReadiness.APPROVED


def _summary(
    findings: list[ReviewFinding],
    *,
    content_hash: str,
    agent_mode: str,
) -> ReviewSummary:
    active = {FindingStatus.OPEN, FindingStatus.REJECTED}
    open_critical = [
        item
        for item in findings
        if item.severity == FindingSeverity.CRITICAL and item.status in active
    ]
    open_recommended = [
        item
        for item in findings
        if item.severity == FindingSeverity.RECOMMENDED and item.status in active
    ]
    missing = [
        item.message
        for item in open_critical
        if item.category == FindingCategory.COVERAGE
    ]
    blockers = [item.message for item in open_critical]
    return ReviewSummary(
        critical_count=sum(
            item.severity == FindingSeverity.CRITICAL for item in findings
        ),
        recommended_count=sum(
            item.severity == FindingSeverity.RECOMMENDED for item in findings
        ),
        optional_count=sum(
            item.severity == FindingSeverity.OPTIONAL for item in findings
        ),
        open_critical_count=len(open_critical),
        open_recommended_count=len(open_recommended),
        missing_essential_modules=missing,
        content_hash=content_hash,
        agent_mode=agent_mode,
        can_accept=not open_critical,
        blockers=blockers,
    )


def _module_markdown(body: str, title: str) -> str:
    matches = list(_HEADING.finditer(body))
    for index, match in enumerate(matches):
        if match.group(2).strip().casefold() != title.strip().casefold():
            continue
        level = len(match.group(1))
        end = len(body)
        for candidate in matches[index + 1 :]:
            if len(candidate.group(1)) <= level:
                end = candidate.start()
                break
        return body[match.end() : end].strip()
    return ""


def _section_markdown(body: str, title: str) -> str:
    return _module_markdown(body, title)


def _plain_words(markdown: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", re.sub(r"[`*_#>|-]", " ", markdown))


def _anchor_for_text(
    markdown: str,
    text: str,
    module_id: str | None = None,
) -> ReviewAnchor | None:
    start = markdown.find(text)
    if start < 0:
        return None
    end = start + len(text)
    line = markdown.count("\n", 0, start) + 1
    return ReviewAnchor(
        target_type="module_body" if module_id else "section",
        module_id=module_id,
        start_offset=start,
        end_offset=end,
        line_start=line,
        line_end=line + text.count("\n"),
    )


def _content_hash(markdown: str) -> str:
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


def _diff(target_path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{target_path}",
            tofile=f"b/{target_path}",
            n=3,
        )
    )


def _deduplicate_findings(findings: list[ReviewFinding]) -> list[ReviewFinding]:
    result: list[ReviewFinding] = []
    seen: set[tuple[str, str, str | None]] = set()
    for finding in findings:
        key = (finding.category.value, finding.message, finding.module_id)
        if key in seen:
            continue
        seen.add(key)
        result.append(finding)
    return result

