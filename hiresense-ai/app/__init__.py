"""
Application factory.

Using the factory pattern (rather than a module-level `app = Flask(...)`)
keeps the app testable: tests can create independent app instances with
a `TestingConfig`, and we avoid import-time side effects like loading
the ML model before configuration is finalized.
"""
from __future__ import annotations

from flask import Flask, g, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import get_config
from app.core.exceptions import HireSenseError
from app.utils.logging_config import configure_logging, get_logger
from app.utils.middleware import register_middleware

limiter = Limiter(key_func=get_remote_address)

logger = get_logger("hiresense.app")


def create_app(config_object=None) -> Flask:
    config_object = config_object or get_config()
    config_object.ensure_dirs()

    configure_logging(config_object.LOG_LEVEL, config_object.LOG_FORMAT)

    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(config_object)

    CORS(app, resources={r"/api/*": {"origins": config_object.CORS_ALLOWED_ORIGINS}})
    limiter.init_app(app)
    app.config["RATELIMIT_DEFAULT"] = config_object.RATE_LIMIT_DEFAULT

    register_middleware(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_pages(app)
    _init_services(app, config_object)

    if not config_object.DEBUG and not app.config.get("TESTING"):
        problems = config_object.validate_for_production()
        for problem in problems:
            logger.warning("production_config_warning", detail=problem)

    logger.info("app_started", debug=config_object.DEBUG, version=config_object.APP_VERSION)
    return app


def _register_blueprints(app: Flask) -> None:
    from app.api.health import health_bp
    from app.api.match import match_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(match_bp, url_prefix="/api")


def _register_pages(app: Flask) -> None:
    from flask import render_template

    @app.route("/")
    def index():
        return render_template("index.html")


def _register_error_handlers(app: Flask) -> None:
    def _with_request_id(payload: dict) -> dict:
        payload["request_id"] = g.get("request_id", "unknown")
        return payload

    @app.errorhandler(HireSenseError)
    def handle_app_error(err: HireSenseError):
        logger.warning("handled_error", error_code=err.error_code, message=err.message)
        return jsonify(_with_request_id(err.to_dict())), err.status_code

    @app.errorhandler(413)
    def handle_too_large(_err):
        payload = {"error": "file_too_large", "message": "Uploaded file exceeds the size limit."}
        return jsonify(_with_request_id(payload)), 413

    @app.errorhandler(404)
    def handle_not_found(_err):
        payload = {"error": "not_found", "message": "The requested resource was not found."}
        return jsonify(_with_request_id(payload)), 404

    @app.errorhandler(429)
    def handle_rate_limit(_err):
        payload = {"error": "rate_limit_exceeded", "message": "Too many requests. Please slow down."}
        return jsonify(_with_request_id(payload)), 429

    @app.errorhandler(500)
    def handle_internal_error(err):
        logger.error("unhandled_error", error=str(err))
        payload = {"error": "internal_error", "message": "An unexpected error occurred."}
        return jsonify(_with_request_id(payload)), 500


def _init_services(app: Flask, config_object) -> None:
    """
    Eagerly initialize heavyweight singletons (embedding model, FAISS
    index, cache) at startup rather than on first request, so the
    first real user request isn't penalized with multi-second model
    load latency and so a broken index/model fails fast at boot.
    """
    from app.services.embedding_service import EmbeddingService
    from app.services.faiss_index_service import FaissIndexService
    from app.services.matching_engine import MatchingEngine
    from app.services.suggestion_service import SuggestionService
    from app.utils.cache import build_cache

    if app.config.get("TESTING"):
        # Tests construct their own lightweight service instances per-test.
        return

    cache = build_cache(config_object.CACHE_DIR, config_object.CACHE_TTL_SECONDS)
    embedding_service = EmbeddingService(
        model_name=config_object.EMBEDDING_MODEL,
        device=config_object.EMBEDDING_DEVICE,
        cache=cache,
    )

    faiss_service = FaissIndexService(
        index_path=config_object.FAISS_INDEX_PATH,
        metadata_path=config_object.FAISS_METADATA_PATH,
    )
    try:
        faiss_service.load()
        logger.info("faiss_index_loaded", size=faiss_service.size)
    except Exception as exc:
        logger.warning("faiss_index_unavailable", reason=str(exc))

    suggestion_service = SuggestionService(
        api_key=config_object.GEMINI_API_KEY,
        model_name=config_object.GEMINI_MODEL,
    )

    app.extensions["embedding_service"] = embedding_service
    app.extensions["faiss_service"] = faiss_service
    app.extensions["matching_engine"] = MatchingEngine(embedding_service)
    app.extensions["suggestion_service"] = suggestion_service
