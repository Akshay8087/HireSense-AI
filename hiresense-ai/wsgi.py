"""
WSGI entry point for production servers (gunicorn, uWSGI, etc.).

    gunicorn -c gunicorn.conf.py wsgi:app

For local development, use `python app.py` instead — it prints a
startup banner and is safe to run with the Flask dev server's
auto-reloader. This file intentionally stays minimal since process
managers import `app` directly and never execute `__main__`.
"""
from app import create_app

app = create_app()

