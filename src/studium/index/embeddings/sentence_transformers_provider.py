"""Optional local sentence-transformers embedding provider."""

from __future__ import annotations

from typing import Any, cast

from studium.index.embeddings.protocol import EmbeddingModelMetadata


class SentenceTransformersEmbeddingProvider:
    """Local MiniLM-class provider via the optional ``embeddings`` extra.

    Requires ``sentence-transformers`` (and its torch dependency). Constructing
    this class without the optional extra raises ``ImportError`` with install
    guidance.
    """

    def __init__(
        self,
        model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
        *,
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
        model = cast(Any, SentenceTransformer(model_id, **kwargs))
        self._model: Any = model
        dim = int(model.get_sentence_embedding_dimension())
        self._metadata = EmbeddingModelMetadata(
            model_id=model_id,
            model_revision=None,
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
