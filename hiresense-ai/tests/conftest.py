"""Shared pytest fixtures for the HireSense AI test suite."""
from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app
from app.config import TestingConfig
from app.services.embedding_service import EmbeddingService
from app.services.faiss_index_service import FaissIndexService
from app.services.matching_engine import MatchingEngine
from app.services.suggestion_service import SuggestionService

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def embedding_service() -> EmbeddingService:
    """
    Real (but small) Sentence-Transformers model loaded once per test
    session — loading the model is the slow part, so we pay that cost
    exactly once across the whole suite.
    """
    return EmbeddingService(model_name=TestingConfig.EMBEDDING_MODEL, device="cpu", cache=None)


@pytest.fixture(scope="session")
def matching_engine(embedding_service) -> MatchingEngine:
    return MatchingEngine(embedding_service)


@pytest.fixture()
def suggestion_service_fallback() -> SuggestionService:
    """Suggestion service with no API key, forcing the rule-based fallback path."""
    return SuggestionService(api_key=None)


@pytest.fixture()
def sample_resume_text() -> str:
    return (FIXTURES_DIR / "sample_resume.txt").read_text()


@pytest.fixture()
def sample_job_text() -> str:
    return (FIXTURES_DIR / "sample_job.txt").read_text()


@pytest.fixture(scope="session")
def test_faiss_index(embedding_service) -> FaissIndexService:
    """Build a tiny in-memory FAISS index from the 5-row test fixture CSV."""
    import pandas as pd

    df = pd.read_csv(FIXTURES_DIR / "tiny_resumes.csv")
    embeddings = embedding_service.embed_batch(df["resume_text"].tolist())
    metadata = [
        {"id": str(row["ID"]), "category": row["Category"], "snippet": row["resume_text"][:100]}
        for _, row in df.iterrows()
    ]

    service = FaissIndexService(
        index_path=FIXTURES_DIR / "test.index", metadata_path=FIXTURES_DIR / "test_meta.json"
    )
    service.build(embeddings, metadata)
    return service


@pytest.fixture()
def app():
    """Flask app instance configured for testing (no heavyweight singletons)."""
    flask_app = create_app(TestingConfig)
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()
