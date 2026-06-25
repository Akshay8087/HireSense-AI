"""Health, readiness, and version endpoints for load balancers / orchestrators."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """Liveness probe — returns 200 as long as the process is up."""
    return jsonify({"status": "ok"}), 200


@health_bp.route("/ready", methods=["GET"])
def ready():
    """
    Readiness probe — returns 200 only once heavyweight dependencies
    (embedding model, FAISS index) have successfully loaded.
    """
    embedding_service = current_app.extensions.get("embedding_service")
    faiss_service = current_app.extensions.get("faiss_service")

    checks = {
        "embedding_model_loaded": embedding_service is not None,
        "faiss_index_loaded": bool(faiss_service and faiss_service.is_ready()),
    }
    overall_ok = checks["embedding_model_loaded"]  # FAISS is optional for /match
    status_code = 200 if overall_ok else 503

    return jsonify({"status": "ready" if overall_ok else "not_ready", "checks": checks}), status_code


@health_bp.route("/version", methods=["GET"])
def version():
    """Build/version metadata — useful for confirming what's actually deployed."""
    config = current_app.config
    suggestion_service = current_app.extensions.get("suggestion_service")
    faiss_service = current_app.extensions.get("faiss_service")

    return jsonify({
        "name": config.get("APP_NAME", "HireSense AI"),
        "version": config.get("APP_VERSION", "unknown"),
        "embedding_model": config.get("EMBEDDING_MODEL"),
        "gemini_enabled": bool(suggestion_service and suggestion_service.api_key),
        "faiss_index_size": faiss_service.size if faiss_service else 0,
    }), 200
