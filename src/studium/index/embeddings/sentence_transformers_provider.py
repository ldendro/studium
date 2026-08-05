"""Optional local sentence-transformers embedding provider."""

from __future__ import annotations

import re
from typing import Any, cast

from studium.index.embeddings.protocol import EmbeddingModelMetadata

_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)


class SentenceTransformersEmbeddingProvider:
    """Local MiniLM-class provider via the optional ``embeddings`` extra.

    Requires ``sentence-transformers`` (and its torch dependency). Constructing
    this class without the optional extra raises ``ImportError`` with install
    guidance.

    ``model_revision`` in metadata is always a resolved Hub commit SHA when
    discovery succeeds — never a mutable ref such as ``main``.
    """

    def __init__(
        self,
        model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
        *,
        revision: str | None = None,
        device: str | None = None,
        normalize_embeddings: bool = True,
        batch_size: int = 32,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
        except ImportError as exc:
            msg = (
                "sentence-transformers is required for SentenceTransformersEmbeddingProvider. "
                "Install with: uv sync --extra embeddings"
            )
            raise ImportError(msg) from exc

        self._model_id = model_id
        self._normalize = normalize_embeddings
        self._batch_size = batch_size
        kwargs: dict[str, Any] = {}
        if device is not None:
            kwargs["device"] = device
        if revision is not None:
            kwargs["revision"] = revision
        model = cast(Any, SentenceTransformer(model_id, **kwargs))
        self._model: Any = model
        dim = int(model.get_sentence_embedding_dimension())
        self._metadata = EmbeddingModelMetadata(
            model_id=model_id,
            model_revision=resolve_model_revision(model_id, revision=revision),
            dimension=dim,
            normalizes_embeddings=normalize_embeddings,
            max_input_chars=None,
            batch_size_hint=batch_size,
        )

    def model_metadata(self) -> EmbeddingModelMetadata:
        return self._metadata

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=self._normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [list(map(float, row)) for row in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def is_commit_sha(revision: str) -> bool:
    """Return True when ``revision`` looks like a git/Hub commit SHA."""
    return bool(_COMMIT_SHA_RE.fullmatch(revision.strip()))


def resolve_model_revision(model_id: str, *, revision: str | None = None) -> str | None:
    """Resolve a Hub revision ref to a commit SHA.

    Mutable refs (``main``, branch names, tags) are resolved via
    ``huggingface_hub.model_info``. Already-SHA values are returned as-is when
    discovery is unavailable. Unresolved mutable refs return ``None`` so they
    are not persisted as stable model identity.
    """
    discovered = discover_model_revision(model_id, revision=revision)
    if discovered is not None:
        return discovered
    if revision is not None and is_commit_sha(revision):
        return revision.strip().lower()
    return None


def discover_model_revision(model_id: str, *, revision: str | None = None) -> str | None:
    """Look up the Hub commit SHA for ``model_id`` at ``revision`` (default tip)."""
    try:
        from huggingface_hub import model_info  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        if revision is None:
            info = cast(Any, model_info(model_id))
        else:
            info = cast(Any, model_info(model_id, revision=revision))
    except Exception:
        return None
    sha = getattr(info, "sha", None)
    return None if sha is None else str(sha)
