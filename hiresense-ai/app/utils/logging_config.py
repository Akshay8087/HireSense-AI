"""
Structured logging setup using structlog.

Production logs are emitted as single-line JSON so they can be shipped
straight into log aggregators (CloudWatch, ELK, Datadog, etc.) without
a separate parsing step. Development logs render as human-readable
colored console output.
"""
from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "hiresense"):
    return structlog.get_logger(name)


def bind_request_context(**kwargs) -> None:
    """Bind key/value pairs (e.g. request_id) onto every subsequent log
    line emitted during the current request, via structlog's contextvars
    support. Cleared automatically per-request by clear_request_context().
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_request_context() -> None:
    structlog.contextvars.clear_contextvars()
