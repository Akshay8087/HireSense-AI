"""
Embedding service.

Wraps a Sentence-Transformers model (BERT-family encoder) to turn raw
text into dense vector embeddings used for semantic similarity. The
model is loaded once per process (expensive) and reused for every
request; embeddings for repeated text are cached on disk so re-scoring
the same resume against multiple jobs doesn't re-run the encoder.
"""
from __future__ import annotations

import hashlib
import threading

import numpy as np

from app.core.exceptions import EmbeddingError

_model = None
_model_lock = threading.Lock()
_model_name: str | None = None


def get_model(model_name: str, device: str = "cpu"):
    """Lazily load and cache the Sentence-Transformers model (singleton)."""
    global _model, _model_name
    if _model is not None and _model_name == model_name:
        return _model

    with _model_lock:
        if _model is not None and _model_name == model_name:
            return _model
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(model_name, device=device)
            _model_name = model_name
        except Exception as exc:
            raise EmbeddingError(f"Failed to load embedding model '{model_name}': {exc}") from exc

    return _model


def _hash_text(text: str, model_name: str) -> str:
    h = hashlib.sha256()
    h.update(model_name.encode("utf-8"))
    h.update(b"::")
    h.update(text.encode("utf-8"))
    return h.hexdigest()


class EmbeddingService:
    """
    High-level interface for turning text into embeddings, with an
    optional disk cache (via diskcache) to avoid recomputation.
    """

    def __init__(self, model_name: str, device: str = "cpu", cache=None):
        self.model_name = model_name
        self.device = device
        self.cache = cache  # diskcache.Cache instance or None
        self._model = get_model(model_name, device)

    def embed(self, text: str) -> np.ndarray:
        """Embed a single piece of text, returning a 1D float32 vector."""
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text.")

        if self.cache is not None:
            key = _hash_text(text, self.model_name)
            cached = self.cache.get(key)
            if cached is not None:
                return np.array(cached, dtype=np.float32)

        try:
            vector = self._model.encode(
                text, convert_to_numpy=True, normalize_embeddings=True
            ).astype(np.float32)
        except Exception as exc:
            raise EmbeddingError(f"Embedding failed: {exc}") from exc

        if self.cache is not None:
            self.cache.set(key, vector.tolist())

        return vector

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts at once (much faster than looping `embed`)."""
        texts = [t for t in texts if t and t.strip()]
        if not texts:
            raise EmbeddingError("Cannot embed an empty batch.")
        try:
            vectors = self._model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=32,
                show_progress_bar=False,
            ).astype(np.float32)
        except Exception as exc:
            raise EmbeddingError(f"Batch embedding failed: {exc}") from exc
        return vectors

    @staticmethod
    def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Cosine similarity between two already-normalized vectors.
        Since vectors from `embed`/`embed_batch` are L2-normalized,
        this reduces to a plain dot product, but we guard against
        unnormalized inputs for safety/reuse.
        """
        denom = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
        if denom == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / denom)
