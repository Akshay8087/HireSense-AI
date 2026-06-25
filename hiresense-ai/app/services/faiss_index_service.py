"""
FAISS vector index service.

Maintains a FAISS index over resume embeddings plus a parallel JSON
metadata store (id -> {category, snippet, source}) so that nearest-
neighbor search results can be mapped back to human-readable resume
records. The index is persisted to disk and rebuilt from the resume
corpus via `scripts/build_index.py`.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.core.exceptions import IndexNotReadyError


class FaissIndexService:
    def __init__(self, index_path: Path, metadata_path: Path, dimension: int | None = None):
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.dimension = dimension
        self._index = None
        self._metadata: list[dict] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def build(self, embeddings: np.ndarray, metadata: list[dict]) -> None:
        """Build a fresh index from scratch (used by the build script)."""
        import faiss

        if embeddings.shape[0] != len(metadata):
            raise ValueError("Embeddings and metadata must be the same length.")

        self.dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(self.dimension)  # inner product == cosine, since normalized
        index.add(embeddings.astype(np.float32))

        self._index = index
        self._metadata = metadata

    def save(self) -> None:
        import faiss

        if self._index is None:
            raise IndexNotReadyError("No index to save; call build() first.")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self.index_path))
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False)

    def load(self) -> None:
        import faiss

        if not self.index_path.exists() or not self.metadata_path.exists():
            raise IndexNotReadyError(
                f"FAISS index not found at {self.index_path}. "
                "Run scripts/build_index.py to create it."
            )
        self._index = faiss.read_index(str(self.index_path))
        self.dimension = self._index.d
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

    def is_ready(self) -> bool:
        return self._index is not None and self._index.ntotal > 0

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[dict]:
        if not self.is_ready():
            raise IndexNotReadyError("FAISS index is not loaded or is empty.")

        query = query_vector.astype(np.float32).reshape(1, -1)
        top_k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            record = dict(self._metadata[idx])
            record["similarity_score"] = round(float(score), 4)
            results.append(record)
        return results

    @property
    def size(self) -> int:
        return self._index.ntotal if self._index is not None else 0
