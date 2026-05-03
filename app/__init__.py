"""
app/__init__.py
---------------
Application factory for the Price Tracker Flask app.

Why use a factory function instead of a global `app = Flask(__name__)`?
- Lets you create multiple app instances with different configs (e.g. one for
  tests, one for the actual server) without any global state conflicts.
- Blueprints are registered here, keeping each feature self-contained.
- Extensions (db, login_manager, etc.) are initialised here without being
  tied to a specific app instance at import time.
"""

import logging
import os

from app.config import config_map
from flask import Flask, render_template


def create_app(config_name: str = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'testing', 'production'.
                     Defaults to the FLASK_ENV environment variable,
                     or 'development' if that's not set either.

    Returns:
        A fully configured Flask app instance.
    """
    app = Flask(__name__)

    # ── 1. Load config ────────────────────────────────────────────────────────
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    config_class = config_map.get(config_name, config_map["development"])
    app.config.from_object(config_class)

    # ── 2. Set up logging ─────────────────────────────────────────────────────
    # Outputs: [LEVEL] timestamp — message
    # Simple format that's easy to read in Docker logs
    logging.basicConfig(
        level=logging.DEBUG if app.config.get("DEBUG") else logging.INFO,
        format="[%(levelname)s] %(asctime)s — %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    app.logger.info(f"Starting Price Tracker in '{config_name}' mode")

    # ── 3. Initialise extensions ──────────────────────────────────────────────
    from app.extensions import db, login_manager, migrate

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # ── 4. Register blueprints ────────────────────────────────────────────────
    # Each blueprint is a self-contained feature module.
    # url_prefix means all routes inside auth/ start with /auth, etc.
    from app.admin import admin_bp
    from app.auth import auth_bp
    from app.dashboard import dashboard_bp
    from app.products import products_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ── 5. Register a simple health check route ───────────────────────────────
    # Used by Docker and monitoring tools to verify the app is alive.
    @app.route("/health")
    def health():
        from flask import jsonify
        return jsonify({"status": "ok", "env": config_name}), 200

    # ── 6. Import models so Flask-Migrate can detect them ─────────────────────
    # Alembic needs to see the models at app creation time to generate migrations.
    from app.models import (notification, price_history, product,  # noqa: F401
                            scrape_job, user, user_product)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
