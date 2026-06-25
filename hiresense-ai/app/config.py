"""
Centralized configuration for HireSense AI.

All runtime settings are sourced from environment variables (with sane
defaults) so the same code base runs unmodified across local dev, CI,
and production (Docker / cloud) without touching source files.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present (no-op in containers where env vars are injected directly)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [v.strip().lower() for v in value.split(",") if v.strip()]


class Config:
    """Base configuration shared by all environments."""

    # --- App metadata ---
    APP_NAME: str = "HireSense AI"
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

    # --- Flask ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    DEBUG: bool = _bool(os.getenv("DEBUG"), default=False)
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))

    # --- CORS ---
    # Comma-separated list of allowed origins for /api/*, e.g.
    # "https://app.example.com,https://admin.example.com". Defaults to "*"
    # for local development convenience — lock this down in production.
    CORS_ALLOWED_ORIGINS: list[str] | str = _list(
        os.getenv("CORS_ALLOWED_ORIGINS"), default=["*"]
    )

    # --- Paths ---
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"

    # --- Gemini ---
    _raw_gemini_key = os.getenv("GEMINI_API_KEY") or ""
    _GEMINI_PLACEHOLDER = "PASTE_YOUR_GEMINI_API_KEY_HERE"
    GEMINI_API_KEY: str | None = (
        _raw_gemini_key if _raw_gemini_key and _raw_gemini_key != _GEMINI_PLACEHOLDER else None
    )
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # --- Embeddings ---
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")

    # --- FAISS ---
    FAISS_INDEX_PATH: Path = BASE_DIR / os.getenv(
        "FAISS_INDEX_PATH", "data/faiss_index/resumes.index"
    )
    FAISS_METADATA_PATH: Path = BASE_DIR / os.getenv(
        "FAISS_METADATA_PATH", "data/faiss_index/metadata.json"
    )
    FAISS_INDEX_TYPE: str = os.getenv("FAISS_INDEX_TYPE", "flat")

    RESUME_CORPUS_PATH: Path = BASE_DIR / os.getenv(
        "RESUME_CORPUS_PATH", "data/sample_resumes.csv"
    )

    # --- Uploads ---
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    MAX_CONTENT_LENGTH: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS: list[str] = _list(
        os.getenv("ALLOWED_EXTENSIONS"), default=["pdf", "docx", "txt"]
    )

    # --- Rate limiting ---
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "60 per minute")
    RATE_LIMIT_MATCH: str = os.getenv("RATE_LIMIT_MATCH", "10 per minute")

    # --- Caching ---
    CACHE_DIR: Path = BASE_DIR / os.getenv("CACHE_DIR", ".cache")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create any directories the app needs at startup."""
        cls.FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_for_production(cls) -> list[str]:
        """
        Return a list of human-readable problems that should block
        startup in production. Called by ProductionConfig but exposed
        on the base class so it can also be used in deploy-time checks
        (e.g. a CI step that runs `python -c "...validate_for_production()"`).
        """
        problems = []
        if cls.SECRET_KEY in {"dev-secret-key-change-me", "", None}:
            problems.append(
                "SECRET_KEY is unset or using the insecure default. "
                "Set a long random value via the SECRET_KEY env var."
            )
        if cls.GEMINI_API_KEY is None:
            # Not fatal — the app degrades gracefully to rule-based
            # suggestions — but worth surfacing loudly so it's a choice,
            # not an oversight.
            problems.append(
                "GEMINI_API_KEY is unset (or still the placeholder value). "
                "The app will run using rule-based suggestions only."
            )
        return problems


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    GEMINI_API_KEY = None  # force fallback suggestion engine in tests
    RESUME_CORPUS_PATH = Config.BASE_DIR / "tests" / "fixtures" / "tiny_resumes.csv"
    FAISS_INDEX_PATH = Config.BASE_DIR / "tests" / "fixtures" / "test.index"
    FAISS_METADATA_PATH = Config.BASE_DIR / "tests" / "fixtures" / "test_meta.json"


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config() -> type[Config]:
    env = os.getenv("FLASK_ENV", "production").lower()
    return CONFIG_MAP.get(env, ProductionConfig)
