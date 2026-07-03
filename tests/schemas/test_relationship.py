"""Tests for RelationshipMetadata."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from studium.schemas import RelationshipMetadata, RelationshipType, RelationshipVaultStatus


def test_found_target_with_id() -> None:
    rel = RelationshipMetadata(
        relationship_type=RelationshipType.DEPENDS_ON,
        target_id="concept_chain_rule_x9y8z7",
        target_title="Chain Rule",
        vault_status=RelationshipVaultStatus.FOUND,
    )

    assert rel.target_id == "concept_chain_rule_x9y8z7"
    assert rel.vault_status == RelationshipVaultStatus.FOUND


def test_missing_target_without_id() -> None:
    rel = RelationshipMetadata(
        relationship_type=RelationshipType.DEPENDS_ON,
        target_title="Chain Rule",
        vault_status=RelationshipVaultStatus.MISSING,
    )

    assert rel.target_id is None


def test_unresolved_target_without_id() -> None:
    rel = RelationshipMetadata(
        relationship_type=RelationshipType.DEPENDS_ON,
        target_title="Chain Rule",
        vault_status=RelationshipVaultStatus.UNRESOLVED,
    )

    assert rel.target_id is None
    assert rel.vault_status == RelationshipVaultStatus.UNRESOLVED


def test_missing_target_title_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata(
            relationship_type=RelationshipType.RELATED_TO,
            target_title="",
            vault_status=RelationshipVaultStatus.MISSING,
        )


def test_missing_vault_status_raises() -> None:
    with pytest.raises(ValidationError):
        RelationshipMetadata.model_validate(
            {
                "relationship_type": "depends_on",
                "target_title": "Chain Rule",
            }
        )
