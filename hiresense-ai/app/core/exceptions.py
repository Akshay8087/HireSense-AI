"""
Custom exception hierarchy.

Using typed exceptions (rather than raising bare ValueError/Exception
everywhere) lets the API layer map failures to the correct HTTP status
codes and gives operators an unambiguous error `code` to alert on.
"""
from __future__ import annotations


class HireSenseError(Exception):
    """Base class for all application-specific errors."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        payload = {"error": self.error_code, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


class InvalidFileError(HireSenseError):
    status_code = 400
    error_code = "invalid_file"


class FileTooLargeError(HireSenseError):
    status_code = 413
    error_code = "file_too_large"


class TextExtractionError(HireSenseError):
    status_code = 422
    error_code = "text_extraction_failed"


class EmptyInputError(HireSenseError):
    status_code = 400
    error_code = "empty_input"


class EmbeddingError(HireSenseError):
    status_code = 500
    error_code = "embedding_failed"


class IndexNotReadyError(HireSenseError):
    status_code = 503
    error_code = "index_not_ready"


class SuggestionServiceError(HireSenseError):
    status_code = 502
    error_code = "suggestion_service_failed"


class RateLimitExceededError(HireSenseError):
    status_code = 429
    error_code = "rate_limit_exceeded"
