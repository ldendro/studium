"""Source and encounter fingerprinting and comparison."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.engine import Engine

from studium.index.graph.models import (
    EncounterComparison,
    EncounterOutcome,
    SourceIdentity,
)
from studium.index.repositories import learning_encounters as encounters_repo


def _norm_text(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def _norm_url(value: str | None) -> str:
    if value is None:
        return ""
    raw = value.strip()
    parts = urlsplit(raw)
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, parts.fragment)
    )


def normalize_source_identity(
    *,
    source_type: str,
    source_title: str,
    unit_type: str | None = None,
    unit: str | None = None,
    section: str | None = None,
    link: str | None = None,
    external_id_type: str | None = None,
    external_id_value: str | None = None,
) -> SourceIdentity:
    """Normalize source identity fields for deterministic fingerprinting."""
    return SourceIdentity(
        source_type=_norm_text(source_type),
        source_title=_norm_text(source_title),
        unit_type=_norm_text(unit_type) or None,
        unit=_norm_text(unit) or None,
        section=_norm_text(section) or None,
        link=_norm_url(link) or None,
        external_id_type=_norm_text(external_id_type) or None,
        external_id_value=external_id_value.strip() if external_id_value else None,
    )


def _fingerprint_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_source_fingerprint(identity: SourceIdentity) -> str:
    """Fingerprint for source identity (external id, link, or type+title)."""
    if identity.external_id_type and identity.external_id_value:
        payload = {
            "kind": "external_id",
            "type": identity.external_id_type,
            "value": identity.external_id_value,
        }
    elif identity.link:
        payload = {
            "kind": "link",
            "source_type": identity.source_type,
            "source_title": identity.source_title,
            "link": identity.link,
        }
    else:
        payload = {
            "kind": "title",
            "source_type": identity.source_type,
            "source_title": identity.source_title,
        }
    return _fingerprint_payload(payload)


def build_encounter_fingerprint(identity: SourceIdentity) -> str:
    """Fingerprint for a full learning encounter (source + unit + section)."""
    return _fingerprint_payload(
        {
            "source": build_source_fingerprint(identity),
            "unit_type": identity.unit_type or "",
            "unit": identity.unit or "",
            "section": identity.section or "",
        }
    )


def identity_from_row(row: dict[str, Any]) -> SourceIdentity:
    return normalize_source_identity(
        source_type=str(row.get("source_type") or ""),
        source_title=str(row.get("source_title") or ""),
        unit_type=None if row.get("unit_type") is None else str(row["unit_type"]),
        unit=None if row.get("unit") is None else str(row["unit"]),
        section=None if row.get("section") is None else str(row["section"]),
        link=None if row.get("link") is None else str(row["link"]),
        external_id_type=(
            None if row.get("external_id_type") is None else str(row["external_id_type"])
        ),
        external_id_value=(
            None if row.get("external_id_value") is None else str(row["external_id_value"])
        ),
    )


def compare_against_rows(
    existing: list[dict[str, Any]],
    *,
    candidate: SourceIdentity,
) -> EncounterComparison:
    source_fp = build_source_fingerprint(candidate)
    encounter_fp = build_encounter_fingerprint(candidate)
    if not existing:
        return EncounterComparison(
            outcome=EncounterOutcome.DIFFERENT_SOURCE,
            source_fingerprint=source_fp,
            encounter_fingerprint=encounter_fp,
            evidence={"reason": "no_existing_encounters"},
        )

    exact_matches: list[dict[str, Any]] = []
    same_source: list[dict[str, Any]] = []
    for row in existing:
        identity = identity_from_row(row)
        row_encounter_fp = build_encounter_fingerprint(identity)
        row_source_only = build_source_fingerprint(identity)
        stored = row.get("fingerprint")
        if row_encounter_fp == encounter_fp or (stored is not None and str(stored) == encounter_fp):
            exact_matches.append(row)
        elif row_source_only == source_fp or _same_source_by_fallback(identity, candidate):
            same_source.append(row)

    if len(exact_matches) == 1:
        row = exact_matches[0]
        return EncounterComparison(
            outcome=EncounterOutcome.EXACT_SAME_ENCOUNTER,
            source_fingerprint=source_fp,
            encounter_fingerprint=encounter_fp,
            matched_encounter_id=int(row["id"]),
            matched_concept_id=str(row["concept_id"]),
            evidence={"match": "encounter_fingerprint"},
        )
    if len(exact_matches) > 1:
        return EncounterComparison(
            outcome=EncounterOutcome.AMBIGUOUS,
            source_fingerprint=source_fp,
            encounter_fingerprint=encounter_fp,
            evidence={"exact_match_count": len(exact_matches)},
        )
    if not same_source:
        return EncounterComparison(
            outcome=EncounterOutcome.DIFFERENT_SOURCE,
            source_fingerprint=source_fp,
            encounter_fingerprint=encounter_fp,
            evidence={"reason": "no_same_source"},
        )
    compatible = [
        row for row in same_source if _fields_compatible(identity_from_row(row), candidate)
    ]
    candidates = compatible or (same_source if len(same_source) == 1 else [])
    if len(candidates) != 1:
        return EncounterComparison(
            outcome=EncounterOutcome.AMBIGUOUS,
            source_fingerprint=source_fp,
            encounter_fingerprint=encounter_fp,
            evidence={
                "same_source_count": len(same_source),
                "compatible_count": len(compatible),
            },
        )

    row = candidates[0]
    existing_identity = identity_from_row(row)
    if _is_enrichment(existing_identity, candidate):
        return EncounterComparison(
            outcome=EncounterOutcome.SAME_SOURCE_ENRICH_EXISTING,
            source_fingerprint=source_fp,
            encounter_fingerprint=encounter_fp,
            matched_encounter_id=int(row["id"]),
            matched_concept_id=str(row["concept_id"]),
            evidence={"enrichment": True},
        )
    if _unit_differs(existing_identity, candidate):
        return EncounterComparison(
            outcome=EncounterOutcome.SAME_SOURCE_NEW_UNIT,
            source_fingerprint=source_fp,
            encounter_fingerprint=encounter_fp,
            matched_encounter_id=int(row["id"]),
            matched_concept_id=str(row["concept_id"]),
            evidence={"new_unit": candidate.unit},
        )
    return EncounterComparison(
        outcome=EncounterOutcome.AMBIGUOUS,
        source_fingerprint=source_fp,
        encounter_fingerprint=encounter_fp,
        matched_encounter_id=int(row["id"]),
        matched_concept_id=str(row["concept_id"]),
        evidence={"reason": "same_source_unclear_delta"},
    )


def compare_learning_encounter(
    engine: Engine,
    *,
    concept_id: str,
    candidate: SourceIdentity,
) -> EncounterComparison:
    """Compare a candidate encounter against indexed encounters for ``concept_id``."""
    with engine.connect() as connection:
        existing = encounters_repo.list_encounters_for_concept(connection, concept_id)
    return compare_against_rows(existing, candidate=candidate)


def _is_enrichment(existing: SourceIdentity, candidate: SourceIdentity) -> bool:
    compatible = _fields_compatible(existing, candidate)
    unit_enrich = not existing.unit and bool(candidate.unit)
    section_enrich = not existing.section and bool(candidate.section)
    return compatible and (unit_enrich or section_enrich)


def _fields_compatible(existing: SourceIdentity, candidate: SourceIdentity) -> bool:
    return all(
        not old or not new or old == new
        for old, new in (
            (existing.unit_type, candidate.unit_type),
            (existing.unit, candidate.unit),
            (existing.section, candidate.section),
        )
    )


def _same_source_by_fallback(existing: SourceIdentity, candidate: SourceIdentity) -> bool:
    same_title = (
        existing.source_type == candidate.source_type
        and existing.source_title == candidate.source_title
    )
    if not same_title:
        return False
    existing_external = (existing.external_id_type, existing.external_id_value)
    candidate_external = (candidate.external_id_type, candidate.external_id_value)
    if all(existing_external) and all(candidate_external):
        return existing_external == candidate_external
    return True


def _unit_differs(existing: SourceIdentity, candidate: SourceIdentity) -> bool:
    if existing.unit and candidate.unit and existing.unit != candidate.unit:
        return True
    return bool(
        existing.unit_type and candidate.unit_type and existing.unit_type != candidate.unit_type
    )
