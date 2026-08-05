"""SQLAlchemy Core table definitions for the derived concept index."""

from __future__ import annotations

from sqlalchemy import (
    BLOB,
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

index_metadata = Table(
    "index_metadata",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("schema_version", Integer, nullable=False),
    Column("vault_path", Text, nullable=False),
    Column("vault_identifier", String(64), nullable=False),
    Column("index_revision", Integer, nullable=False, server_default="0"),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
    Column("last_rebuild_at", Text, nullable=True),
)

indexed_files = Table(
    "indexed_files",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("file_path", Text, nullable=False, unique=True),
    Column("concept_id", Text, nullable=True),
    Column("note_schema_version", Integer, nullable=True),
    Column("file_hash", String(128), nullable=True),
    Column("projection_hash", String(128), nullable=True),
    Column("mtime_ns", Integer, nullable=True),
    Column("index_state", String(64), nullable=False),
    Column("last_success_revision", Integer, nullable=True),
    Column("invalid_since_revision", Integer, nullable=True),
    Column("validation_errors_json", Text, nullable=True),
    Column("indexed_at", Text, nullable=True),
)

concepts = Table(
    "concepts",
    metadata,
    Column("concept_id", Text, primary_key=True),
    Column("canonical_title", Text, nullable=False),
    Column("normalized_title", Text, nullable=False),
    Column("concept_type", String(64), nullable=False),
    Column("status", String(64), nullable=False),
    Column("review_status", String(64), nullable=False),
    Column("vault_status", String(64), nullable=False),
    Column("file_path", Text, nullable=False),
    Column("h1_title", Text, nullable=True),
    Column("overview_markdown", Text, nullable=True),
    Column("overview_plaintext", Text, nullable=True),
    Column("identity_input_hash", String(128), nullable=True),
    Column("semantic_input_hash", String(128), nullable=True),
    Column("note_schema_version", Integer, nullable=False),
    Column("validity_state", String(64), nullable=False),
    Column("indexed_revision", Integer, nullable=False),
    Column("note_created_at", Text, nullable=True),
    Column("note_updated_at", Text, nullable=True),
)

concept_aliases = Table(
    "concept_aliases",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "concept_id",
        Text,
        ForeignKey("concepts.concept_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("alias", Text, nullable=False),
    Column("normalized_alias", Text, nullable=False),
    UniqueConstraint("concept_id", "normalized_alias", name="uq_concept_aliases"),
)

concept_domains = Table(
    "concept_domains",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "concept_id",
        Text,
        ForeignKey("concepts.concept_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("domain", Text, nullable=False),
    UniqueConstraint("concept_id", "domain", name="uq_concept_domains"),
)

learning_encounters = Table(
    "learning_encounters",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "concept_id",
        Text,
        ForeignKey("concepts.concept_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("source_type", String(64), nullable=False),
    Column("source_title", Text, nullable=False),
    Column("unit_type", Text, nullable=True),
    Column("unit", Text, nullable=True),
    Column("section", Text, nullable=True),
    Column("link", Text, nullable=True),
    Column("external_id_type", Text, nullable=True),
    Column("external_id_value", Text, nullable=True),
    Column("role", String(64), nullable=False),
    Column("contribution_status", String(64), nullable=False),
    Column("content_attached", Boolean, nullable=False),
    Column("content_id", Text, nullable=True),
    Column("fingerprint", Text, nullable=True),
)

relationships = Table(
    "relationships",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "source_concept_id",
        Text,
        ForeignKey("concepts.concept_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("relationship_type", String(64), nullable=False),
    Column("target_id", Text, nullable=True),
    Column("target_title", Text, nullable=False),
    Column("vault_status", String(64), nullable=False),
    Column("learning_role", String(64), nullable=False),
    Column("confidence", String(64), nullable=False),
    Column("status", String(64), nullable=False),
)

scaffold_modules = Table(
    "scaffold_modules",
    metadata,
    Column("module_id", Text, primary_key=True),
    Column(
        "concept_id",
        Text,
        ForeignKey("concepts.concept_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("type", String(64), nullable=False),
    Column("title", Text, nullable=False),
    Column("normalized_title", Text, nullable=False),
    Column("status", String(64), nullable=False),
    Column("origin", String(64), nullable=True),
    Column("focus", Text, nullable=True),
    Column("heading", Text, nullable=True),
    Column("anchor", Text, nullable=True),
    Column("segment_count", Integer, nullable=False, server_default="1"),
    Column("module_input_hash", String(128), nullable=True),
    Column("indexed_revision", Integer, nullable=False),
)

concept_search_documents = Table(
    "concept_search_documents",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "concept_id",
        Text,
        ForeignKey("concepts.concept_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    Column("document_text", Text, nullable=False),
    Column("field_weights_json", Text, nullable=True),
    Column("indexed_revision", Integer, nullable=False),
)

module_search_documents = Table(
    "module_search_documents",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "module_id",
        Text,
        ForeignKey("scaffold_modules.module_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    Column(
        "concept_id",
        Text,
        ForeignKey("concepts.concept_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("document_text", Text, nullable=False),
    Column("indexed_revision", Integer, nullable=False),
)

embeddings = Table(
    "embeddings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("owner_type", String(64), nullable=False),
    Column("owner_id", Text, nullable=False),
    Column(
        "parent_concept_id",
        Text,
        ForeignKey("concepts.concept_id", ondelete="CASCADE"),
        nullable=True,
    ),
    Column("segment_id", Text, nullable=False, server_default=""),
    Column("embedding_type", String(64), nullable=False),
    Column("vector", BLOB, nullable=False),
    Column("dimension", Integer, nullable=False),
    Column("model_id", Text, nullable=False),
    Column("model_revision", Text, nullable=True),
    Column("input_hash", String(128), nullable=False),
    Column("created_at", Text, nullable=False),
    Column("indexed_revision", Integer, nullable=False),
    UniqueConstraint(
        "owner_type",
        "owner_id",
        "embedding_type",
        "segment_id",
        name="uq_embeddings_owner_type_segment",
    ),
)

invalid_index_records = Table(
    "invalid_index_records",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("file_path", Text, nullable=False),
    Column("concept_id", Text, nullable=True),
    Column("reason_code", String(64), nullable=False),
    Column("message", Text, nullable=False),
    Column("details_json", Text, nullable=True),
    Column("since_revision", Integer, nullable=True),
    Column("recorded_at", Text, nullable=False),
)

Index("ix_concepts_normalized_title", concepts.c.normalized_title)
Index("ix_concept_aliases_normalized_alias", concept_aliases.c.normalized_alias)
Index("ix_relationships_source_concept_id", relationships.c.source_concept_id)
Index("ix_relationships_target_id", relationships.c.target_id)
Index("ix_scaffold_modules_concept_id", scaffold_modules.c.concept_id)
Index("ix_indexed_files_concept_id", indexed_files.c.concept_id)
Index("ix_embeddings_owner", embeddings.c.owner_type, embeddings.c.owner_id)
Index("ix_embeddings_input_hash", embeddings.c.input_hash)
Index("ix_invalid_index_records_file_path", invalid_index_records.c.file_path)
