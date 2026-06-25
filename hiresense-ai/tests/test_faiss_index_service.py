"""Unit tests for app.services.faiss_index_service."""
import pytest

from app.core.exceptions import IndexNotReadyError
from app.services.faiss_index_service import FaissIndexService


def test_index_is_ready_after_build(test_faiss_index: FaissIndexService):
    assert test_faiss_index.is_ready()
    assert test_faiss_index.size == 5


def test_search_returns_results_with_scores(test_faiss_index, embedding_service):
    query_vec = embedding_service.embed(
        "Software engineer skilled in Python, Flask, and machine learning."
    )
    results = test_faiss_index.search(query_vec, top_k=3)

    assert len(results) == 3
    for r in results:
        assert "similarity_score" in r
        assert "category" in r
        assert "snippet" in r
    # Results should be sorted by descending similarity.
    scores = [r["similarity_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_finds_most_relevant_category_first(test_faiss_index, embedding_service):
    query_vec = embedding_service.embed(
        "Nurse with ICU patient care and EHR documentation experience."
    )
    results = test_faiss_index.search(query_vec, top_k=1)
    assert results[0]["category"] == "HEALTHCARE"


def test_search_on_unloaded_index_raises():
    empty_service = FaissIndexService(index_path="/tmp/nope.index", metadata_path="/tmp/nope.json")
    import numpy as np
    with pytest.raises(IndexNotReadyError):
        empty_service.search(np.zeros(384, dtype="float32"), top_k=3)


def test_save_and_load_roundtrip(test_faiss_index, tmp_path):
    index_path = tmp_path / "roundtrip.index"
    meta_path = tmp_path / "roundtrip_meta.json"

    test_faiss_index.index_path = index_path
    test_faiss_index.metadata_path = meta_path
    test_faiss_index.save()

    reloaded = FaissIndexService(index_path=index_path, metadata_path=meta_path)
    reloaded.load()

    assert reloaded.is_ready()
    assert reloaded.size == test_faiss_index.size
