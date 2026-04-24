"""
wsgi.py
-------
Entry point for Gunicorn (production web server).

Gunicorn is started with: gunicorn "wsgi:app"
It imports this file and looks for the variable named 'app'.

Why not just use Flask's built-in dev server in production?
Flask's dev server is single-threaded and not designed for real traffic.
Gunicorn spawns multiple worker processes that can handle concurrent requests.
"""

import os
from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))
