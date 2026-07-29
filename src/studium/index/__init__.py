"""Derived SQLite concept index (Phase 2).

Provides path resolution, SQLAlchemy Core schema, schema-version handling,
and thin repositories. Vault synchronization is implemented in a later branch.
"""

from studium.index.config import DEFAULT_BUSY_TIMEOUT_MS, INDEX_SCHEMA_VERSION, IndexConfig
from studium.index.engine import begin_connection, create_index_engine, read_pragma
from studium.index.errors import (
    ConceptIndexError,
    IndexIntegrityError,
    IndexNotInitializedError,
    IndexSchemaMismatchError,
)
from studium.index.normalize import normalize_title
from studium.index.paths import derive_vault_identifier, index_db_path, resolve_application_data_dir
from studium.index.schema_manager import (
    create_engine_for_config,
    ensure_compatible_index,
    initialize_index,
    read_index_schema_version,
    rebuild_index,
)

__all__ = [
    "DEFAULT_BUSY_TIMEOUT_MS",
    "INDEX_SCHEMA_VERSION",
    "ConceptIndexError",
    "IndexConfig",
    "IndexIntegrityError",
    "IndexNotInitializedError",
    "IndexSchemaMismatchError",
    "begin_connection",
    "create_engine_for_config",
    "create_index_engine",
    "derive_vault_identifier",
    "ensure_compatible_index",
    "index_db_path",
    "initialize_index",
    "normalize_title",
    "read_index_schema_version",
    "read_pragma",
    "rebuild_index",
    "resolve_application_data_dir",
]
