"""Unit tests for app.services.embedding_service (uses a real small model)."""
import numpy as np
import pytest

from app.core.exceptions import EmbeddingError
from app.services.embedding_service import EmbeddingService


def test_embed_returns_normalized_vector(embedding_service: EmbeddingService):
    vec = embedding_service.embed("Python developer with Flask experience.")
    assert isinstance(vec, np.ndarray)
    assert vec.ndim == 1
    # normalize_embeddings=True means the L2 norm should be ~1.0
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-3


def test_embed_empty_text_raises(embedding_service: EmbeddingService):
    with pytest.raises(EmbeddingError):
        embedding_service.embed("")
    with pytest.raises(EmbeddingError):
        embedding_service.embed("   ")


def test_embed_batch_returns_matrix(embedding_service: EmbeddingService):
    texts = ["Python developer", "Registered nurse", "Sales executive"]
    matrix = embedding_service.embed_batch(texts)
    assert matrix.shape[0] == 3
    assert matrix.shape[1] > 0


def test_similar_texts_have_higher_cosine_similarity(embedding_service: EmbeddingService):
    a = embedding_service.embed("Python backend engineer with Flask and Docker experience.")
    b = embedding_service.embed("Backend developer skilled in Python, Flask, and containerization.")
    c = embedding_service.embed("Registered nurse with ICU patient care experience.")

    sim_related = EmbeddingService.cosine_similarity(a, b)
    sim_unrelated = EmbeddingService.cosine_similarity(a, c)

    assert sim_related > sim_unrelated


def test_cosine_similarity_handles_zero_vector():
    zero = np.zeros(5, dtype=np.float32)
    other = np.ones(5, dtype=np.float32)
    assert EmbeddingService.cosine_similarity(zero, other) == 0.0
