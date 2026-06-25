"""
Gunicorn production configuration.

Usage:
    gunicorn -c gunicorn.conf.py wsgi:app

Tunable via environment variables so the same config file works
unchanged across staging/production without edits.
"""
from __future__ import annotations

import multiprocessing
import os

bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '5000')}"

# CPU-bound embedding inference benefits from a small, fixed worker count
# rather than the (2 * cores + 1) rule of thumb used for I/O-bound apps —
# each worker loads its own copy of the embedding model into memory, so
# too many workers exhausts RAM rather than improving throughput.
workers = int(os.getenv("GUNICORN_WORKERS", min(4, multiprocessing.cpu_count())))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
worker_class = "gthread"

timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Restart workers periodically to bound any slow memory growth from the
# embedding model / tokenizer caches over long-running processes.
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))

# Load the application once in the master process before forking workers.
# Combined with the eager `_init_services` call in `create_app`, this means
# the (expensive) embedding model is loaded once and shared copy-on-write
# across forked workers instead of being re-loaded per worker.
preload_app = True

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = (
    '%(h)s "%(r)s" %(s)s %(b)s %(L)ss "%(a)s"'
)


def on_starting(server):
    server.log.info("HireSense AI starting with %s workers", workers)


def worker_exit(server, worker):
    server.log.info("Worker %s exited", worker.pid)
