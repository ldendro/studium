"""Local embedding generation pipeline (P2-B05)."""

from studium.index.embeddings.enumerate import enumerate_embedding_work
from studium.index.embeddings.fake import FakeEmbeddingProvider
from studium.index.embeddings.pipeline import (
    EmbeddingProcessReport,
    embed_query,
    process_embedding_work,
)
from studium.index.embeddings.protocol import EmbeddingModelMetadata, EmbeddingProvider
from studium.index.embeddings.sentence_transformers_provider import (
    SentenceTransformersEmbeddingProvider,
)
from studium.index.embeddings.serialize import pack_vector, unpack_vector
from studium.index.embeddings.sync_embed import (
    SyncAndEmbedReport,
    merge_embedding_work,
    sync_and_embed,
)

__all__ = [
    "EmbeddingModelMetadata",
    "EmbeddingProcessReport",
    "EmbeddingProvider",
    "FakeEmbeddingProvider",
    "SentenceTransformersEmbeddingProvider",
    "SyncAndEmbedReport",
    "embed_query",
    "enumerate_embedding_work",
    "merge_embedding_work",
    "pack_vector",
    "process_embedding_work",
    "sync_and_embed",
    "unpack_vector",
]
