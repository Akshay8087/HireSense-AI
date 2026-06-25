"""
Integration tests for the Flask API.

Since `_init_services` deliberately skips heavyweight singleton
construction when `TESTING=True` (see app/__init__.py), these tests
wire the same lightweight, session-scoped fixtures (built once for the
whole test session) directly onto `app.extensions` before issuing
requests — exercising the exact same blueprint code paths as
production without re-loading the embedding model per test.
"""
from __future__ import annotations

import io

import pytest

from app.services.matching_engine import MatchingEngine
from app.services.suggestion_service import SuggestionService


@pytest.fixture()
def wired_client(app, embedding_service, test_faiss_index):
    app.extensions["embedding_service"] = embedding_service
    app.extensions["faiss_service"] = test_faiss_index
    app.extensions["matching_engine"] = MatchingEngine(embedding_service)
    app.extensions["suggestion_service"] = SuggestionService(api_key=None)
    return app.test_client()


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_ready_endpoint_without_services_is_not_ready(client):
    res = client.get("/api/ready")
    assert res.status_code == 503
    assert res.get_json()["status"] == "not_ready"


def test_ready_endpoint_with_services_is_ready(wired_client):
    res = wired_client.get("/api/ready")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ready"


def test_match_endpoint_with_pasted_text(wired_client, sample_resume_text, sample_job_text):
    res = wired_client.post(
        "/api/match",
        data={"resume_text": sample_resume_text, "job_text": sample_job_text},
    )
    assert res.status_code == 200
    payload = res.get_json()

    assert "match_score" in payload
    assert 0 <= payload["match_score"] <= 100
    assert "job_fit_category" in payload
    assert "suggestions" in payload
    assert payload["suggestions"]["source"] == "fallback"


def test_match_endpoint_with_file_upload(wired_client, sample_job_text, sample_resume_text):
    data = {
        "resume_file": (io.BytesIO(sample_resume_text.encode("utf-8")), "resume.txt"),
        "job_text": sample_job_text,
    }
    res = wired_client.post("/api/match", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    payload = res.get_json()
    assert "match_score" in payload


def test_match_endpoint_missing_job_text_returns_400(wired_client, sample_resume_text):
    res = wired_client.post("/api/match", data={"resume_text": sample_resume_text})
    assert res.status_code == 400
    assert res.get_json()["error"] == "empty_input"


def test_match_endpoint_empty_resume_returns_400(wired_client, sample_job_text):
    res = wired_client.post("/api/match", data={"resume_text": "", "job_text": sample_job_text})
    assert res.status_code == 400


def test_match_endpoint_rejects_unsupported_file_type(wired_client, sample_job_text):
    data = {
        "resume_file": (io.BytesIO(b"not a real exe but pretend"), "resume.exe"),
        "job_text": sample_job_text,
    }
    res = wired_client.post("/api/match", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    assert res.get_json()["error"] == "invalid_file"


def test_similar_resumes_endpoint(wired_client):
    res = wired_client.post(
        "/api/similar-resumes",
        json={"text": "Python developer with Flask and machine learning experience.", "top_k": 3},
    )
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["count"] == 3
    assert len(payload["results"]) == 3


def test_similar_resumes_endpoint_requires_text(wired_client):
    res = wired_client.post("/api/similar-resumes", json={"text": ""})
    assert res.status_code == 400


def test_extract_text_endpoint(wired_client, sample_resume_text):
    data = {"resume_file": (io.BytesIO(sample_resume_text.encode("utf-8")), "resume.txt")}
    res = wired_client.post("/api/extract-text", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    payload = res.get_json()
    assert "Python" in payload["extracted_text"]
    assert payload["char_count"] > 0


def test_match_endpoint_is_rate_limited(app, embedding_service, test_faiss_index, sample_resume_text, sample_job_text):
    """
    Regression test: /match must enforce its own (stricter) rate limit,
    separate from the global default. This previously silently no-op'd
    because the limiter was applied to the view function *after* route
    registration instead of via the decorator at definition time.
    """
    app.config["RATE_LIMIT_MATCH"] = "2 per minute"
    app.extensions["embedding_service"] = embedding_service
    app.extensions["faiss_service"] = test_faiss_index
    app.extensions["matching_engine"] = MatchingEngine(embedding_service)
    app.extensions["suggestion_service"] = SuggestionService(api_key=None)
    client = app.test_client()

    statuses = []
    for _ in range(4):
        res = client.post(
            "/api/match",
            data={"resume_text": sample_resume_text, "job_text": sample_job_text},
        )
        statuses.append(res.status_code)

    assert statuses[:2] == [200, 200]
    assert 429 in statuses[2:]


def test_version_endpoint_reports_gemini_disabled_without_key(wired_client):
    res = wired_client.get("/api/version")
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["gemini_enabled"] is False
    assert "name" in payload and "version" in payload


def test_error_response_includes_request_id(wired_client, sample_resume_text):
    res = wired_client.post("/api/match", data={"resume_text": sample_resume_text, "job_text": ""})
    assert res.status_code == 400
    payload = res.get_json()
    assert "request_id" in payload


def test_response_has_security_headers(client):
    res = client.get("/api/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "X-Request-ID" in res.headers


def test_index_page_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"HireSense" in res.data
