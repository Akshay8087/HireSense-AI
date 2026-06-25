"""
Resume <-> Job matching API.

POST /api/match
    Accepts a resume (file upload OR raw text) and a job description
    (raw text), returns match score, missing skills, recommended
    keywords, resume improvement suggestions, and job fit category.

POST /api/extract-text
    Utility endpoint: extracts and returns plain text from an uploaded
    resume file, without running any matching. Useful for letting the
    frontend show "here's what we read from your file" before scoring.

GET /api/similar-resumes
    Given resume text, returns the most similar resumes from the
    bundled FAISS-indexed corpus (demonstrates the FAISS-backed
    semantic search capability independent of job matching).
"""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.core.exceptions import EmptyInputError, IndexNotReadyError
from app.services.document_parser import extract_text
from app.services.skill_extractor import analyze_skill_gap
from app.utils.logging_config import get_logger
from app.utils.validation import validate_text_input, validate_upload

match_bp = Blueprint("match", __name__)
logger = get_logger("hiresense.api.match")


def _match_rate_limit() -> str:
    """
    Evaluated per-request (not at import time) so it always reflects
    the current app's config — required for Flask-Limiter's dynamic
    limit strings, and so tests/different environments can override
    RATE_LIMIT_MATCH without re-importing this module.
    """
    return current_app.config.get("RATE_LIMIT_MATCH", "10 per minute")


def _get_limiter():
    # Imported lazily (not at module level) to avoid a circular import:
    # app/__init__.py imports this module while registering blueprints,
    # so `from app import limiter` at the top of this file would try to
    # import a partially-initialized `app` package.
    from app import limiter
    return limiter


def _get_resume_text_from_request() -> str:
    """
    Resolve resume text from either an uploaded file (`resume_file`)
    or a raw text field (`resume_text`), preferring the file if both
    are present.
    """
    if "resume_file" in request.files and request.files["resume_file"].filename:
        config = current_app.config
        file_bytes = validate_upload(
            request.files["resume_file"],
            allowed_extensions=config["ALLOWED_EXTENSIONS"],
            max_size_bytes=config["MAX_CONTENT_LENGTH"],
        )
        return extract_text(file_bytes, request.files["resume_file"].filename)

    resume_text = request.form.get("resume_text")
    if not resume_text and request.is_json:
        resume_text = (request.get_json(silent=True) or {}).get("resume_text")
    return validate_text_input(resume_text, field_name="resume_text", min_length=50)


@match_bp.route("/extract-text", methods=["POST"])
def extract_text_endpoint():
    config = current_app.config
    file_bytes = validate_upload(
        request.files.get("resume_file"),
        allowed_extensions=config["ALLOWED_EXTENSIONS"],
        max_size_bytes=config["MAX_CONTENT_LENGTH"],
    )
    text = extract_text(file_bytes, request.files["resume_file"].filename)
    return jsonify({"extracted_text": text, "char_count": len(text)}), 200


@match_bp.route("/match", methods=["POST"])
@_get_limiter().limit(_match_rate_limit)
def match():
    job_text = request.form.get("job_text") or (request.get_json(silent=True) or {}).get("job_text")
    job_text = validate_text_input(job_text, field_name="job_text", min_length=30)

    resume_text = _get_resume_text_from_request()

    matching_engine = current_app.extensions["matching_engine"]
    suggestion_service = current_app.extensions["suggestion_service"]

    result = matching_engine.score(resume_text, job_text)

    gap = analyze_skill_gap(resume_text, job_text)
    suggestions = suggestion_service.generate(
        resume_text=resume_text,
        job_text=job_text,
        gap=gap,
        match_score=result.match_score,
    )

    logger.info(
        "match_scored",
        match_score=result.match_score,
        job_fit_category=result.job_fit_category,
        suggestion_source=suggestions.source,
    )

    response = result.to_dict()
    response["suggestions"] = suggestions.to_dict()
    response["resume_char_count"] = len(resume_text)
    response["job_char_count"] = len(job_text)
    return jsonify(response), 200


@match_bp.route("/similar-resumes", methods=["POST"])
def similar_resumes():
    payload = request.get_json(silent=True) or {}
    text = validate_text_input(
        payload.get("text") or request.form.get("text"),
        field_name="text",
        min_length=30,
    )
    top_k = int(payload.get("top_k", request.form.get("top_k", 5)))
    top_k = max(1, min(top_k, 20))

    embedding_service = current_app.extensions["embedding_service"]
    faiss_service = current_app.extensions["faiss_service"]

    if not faiss_service.is_ready():
        raise IndexNotReadyError(
            "The resume similarity index has not been built yet. "
            "Run scripts/build_index.py first."
        )

    query_vector = embedding_service.embed(text)
    results = faiss_service.search(query_vector, top_k=top_k)
    return jsonify({"results": results, "count": len(results)}), 200
