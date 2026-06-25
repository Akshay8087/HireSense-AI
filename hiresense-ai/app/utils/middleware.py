"""
Request-scoped middleware.

Adds three production essentials that are easy to skip in a demo build
but matter the moment this runs behind a load balancer or gets used by
more than one person at a time:

1. **Request ID propagation** — every request gets a UUID (reused from
   the `X-Request-ID` header if the caller/proxy already set one) that
   is attached to every log line emitted while handling that request,
   and echoed back in the response header. This is what lets you grep
   one user's request across logs from multiple gunicorn workers.
2. **Security headers** — baseline hardening (clickjacking, MIME
   sniffing, referrer leakage) applied to every response.
3. **Access logging + timing** — one structured log line per request
   with status code and duration, independent of gunicorn's own access
   log, so the application's own logs are self-contained.
"""
from __future__ import annotations

import time
import uuid

from flask import Flask, g, request

from app.utils.logging_config import bind_request_context, clear_request_context, get_logger

logger = get_logger("hiresense.access")

REQUEST_ID_HEADER = "X-Request-ID"


def register_middleware(app: Flask) -> None:
    @app.before_request
    def _start_request_context():
        g.request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        g.request_start_time = time.monotonic()
        bind_request_context(request_id=g.request_id, path=request.path, method=request.method)

    @app.after_request
    def _finalize_response(response):
        # --- Request ID echo ---
        response.headers[REQUEST_ID_HEADER] = getattr(g, "request_id", "unknown")

        # --- Baseline security headers ---
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"  # superseded by CSP; explicitly disabled
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
            "font-src fonts.gstatic.com; "
            "script-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self';",
        )
        if not app.config.get("DEBUG"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # --- Structured access log line ---
        duration_ms = round((time.monotonic() - getattr(g, "request_start_time", time.monotonic())) * 1000, 2)
        if request.path != "/api/health":  # keep liveness-probe noise out of logs
            logger.info(
                "request_completed",
                status=response.status_code,
                duration_ms=duration_ms,
                remote_addr=request.headers.get("X-Forwarded-For", request.remote_addr),
            )
        clear_request_context()
        return response
