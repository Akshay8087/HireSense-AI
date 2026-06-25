"""
HireSense AI — application entry point.

This is the file most people reach for first (`python app.py`), so it's
kept as a thin, readable launcher. It builds on the same application
factory used by `wsgi.py` (the production gunicorn target) and by the
test suite — there is exactly one code path that constructs the Flask
app, so dev, test, and prod never drift from each other.

Local development:
    python app.py

Production (do NOT use this file in production):
    gunicorn -c gunicorn.conf.py wsgi:app
"""
from __future__ import annotations

import sys

from app import create_app
from app.config import get_config

config = get_config()
app = create_app(config)


def _print_startup_banner() -> None:
    banner = f"""
  _    _ _          _____                       _____
 | |  | (_)        / ____|                     /  _  \\   _____
 | |__| |_ _ __ ___| (___   ___ _ __  ___  ___ | | | |  |_   _|
 |  __  | | '__/ _ \\\\___ \\ / _ \\ '_ \\/ __|/ _ \\| | | |    | |
 | |  | | | | |  __/____) |  __/ | | \\__ \\  __/| |_| |    | |
 |_|  |_|_|_|  \\___|_____/ \\___|_| |_|___/\\___|\\_____/    |_|

 Resume Ranking & Job Match System
 ----------------------------------
 Environment : {('development' if config.DEBUG else 'production')}
 Host        : {config.HOST}:{config.PORT}
 Embedding   : {config.EMBEDDING_MODEL} ({config.EMBEDDING_DEVICE})
 Gemini      : {'configured' if config.GEMINI_API_KEY else 'NOT SET — using rule-based suggestion fallback'}
 FAISS index : {config.FAISS_INDEX_PATH}
"""
    print(banner, file=sys.stderr)


if __name__ == "__main__":
    _print_startup_banner()

    if not config.DEBUG:
        print(
            "WARNING: This is the Flask development server. "
            "Do not use it in production — run via gunicorn instead:\n"
            "    gunicorn -c gunicorn.conf.py wsgi:app\n",
            file=sys.stderr,
        )

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
