"""Tests for RelationshipMetadata."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from studium.schemas import (
    LearningRole,
    RelationshipConfidence,
    RelationshipMetadata,
    RelationshipStatus,
    RelationshipType,
    RelationshipVaultStatus,
)


def test_found_target_with_id() -> None:
    rel = RelationshipMetadata(
        relationship_type=RelationshipType.DEPENDS_ON,
        target_id="concept_chain_rule_x9y8z7",
        target_title="Chain Rule",
        vault_status=RelationshipVaultStatus.FOUND,
        learning_role=LearningRole.MATHEMATICAL_PREREQUISITE,
        confidence=RelationshipConfidence.HIGH,
        status=RelationshipStatus.USER_CONFIRMED,
    )

    assert rel.target_id == "concept_chain_rule_x9y8z7"
    assert rel.vault_status == RelationshipVaultStatus.FOUND
    assert rel.learning_role == LearningRole.MATHEMATICAL_PREREQUISITE
    assert rel.confidence == RelationshipConfidence.HIGH
    assert rel.status == RelationshipStatus.USER_CONFIRMED


def test_missing_target_without_id() -> None:
    rel = RelationshipMetadata(
        relationship_type=RelationshipType.DEPENDS_ON,
        target_title="Chain Rule",
        vault_status=RelationshipVaultStatus.MISSING,
        learning_role=LearningRole.MATHEMATICAL_PREREQUISITE,
        confidence=RelationshipConfidence.HIGH,
        status=RelationshipStatus.AGENT_SUGGESTED,
    )

    assert rel.target_id is None


def test_unresolved_target_without_id() -> None:
    rel = RelationshipMetadata(
        relationship_type=RelationshipType.DEPENDS_ON,
        target_title="Chain Rule",
        vault_status=RelationshipVaultStatus.UNRESOLVED,
        learning_role=LearningRole.MATHEMATICAL_PREREQUISITE,
        confidence=RelationshipConfidence.HIGH,
        status=RelationshipStatus.AGENT_SUGGESTED,
    )

    assert rel.target_id is None
    assert rel.vault_status == RelationshipVaultStatus.UNRESOLVED


def test_missing_target_title_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata(
            relationship_type=RelationshipType.RELATED_TO,
            target_title="",
            vault_status=RelationshipVaultStatus.MISSING,
            learning_role=LearningRole.SUPPORTING_CONCEPT,
            confidence=RelationshipConfidence.MEDIUM,
            status=RelationshipStatus.AGENT_SUGGESTED,
        )


def test_missing_vault_status_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata.model_validate(
            {
                "relationship_type": "depends_on",
                "target_title": "Chain Rule",
                "learning_role": "mathematical_prerequisite",
                "confidence": "high",
                "status": "agent_suggested",
            }
        )


def test_missing_learning_role_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata.model_validate(
            {
                "relationship_type": "depends_on",
                "target_title": "Chain Rule",
                "vault_status": "missing",
                "confidence": "high",
                "status": "agent_suggested",
            }
        )


def test_missing_confidence_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata.model_validate(
            {
                "relationship_type": "depends_on",
                "target_title": "Chain Rule",
                "vault_status": "missing",
                "learning_role": "mathematical_prerequisite",
                "status": "agent_suggested",
            }
        )


def test_missing_relationship_status_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata.model_validate(
            {
                "relationship_type": "depends_on",
                "target_title": "Chain Rule",
                "vault_status": "missing",
                "learning_role": "mathematical_prerequisite",
                "confidence": "high",
            }
        )


def test_invalid_learning_role_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata.model_validate(
            {
                "relationship_type": "depends_on",
                "target_title": "Chain Rule",
                "vault_status": "missing",
                "learning_role": "not_a_role",
                "confidence": "high",
                "status": "agent_suggested",
            }
        )


def test_invalid_confidence_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata.model_validate(
            {
                "relationship_type": "depends_on",
                "target_title": "Chain Rule",
                "vault_status": "missing",
                "learning_role": "mathematical_prerequisite",
                "confidence": "confirmed",
                "status": "agent_suggested",
            }
        )


def test_invalid_relationship_status_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata.model_validate(
            {
                "relationship_type": "depends_on",
                "target_title": "Chain Rule",
                "vault_status": "missing",
                "learning_role": "mathematical_prerequisite",
                "confidence": "high",
                "status": "rejected",
            }
        )
