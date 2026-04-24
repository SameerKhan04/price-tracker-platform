"""
config.py
---------
Configuration classes for different environments.

How it works:
- BaseConfig holds settings shared across ALL environments.
- DevelopmentConfig, TestingConfig, ProductionConfig override only what differs.
- The create_app() factory selects the right class using the FLASK_ENV variable.

Why use classes instead of a flat config file?
Because you can swap the entire config in one line during testing — no monkey-patching,
no risk of test settings leaking into production.
"""

import os


class BaseConfig:
    """Settings shared by every environment."""

    # Flask uses this to sign session cookies. Must be secret in production.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    # SQLAlchemy — disable modification tracking (it's a performance drain)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Scraper behaviour
    SCRAPER_TIMEOUT = int(os.environ.get("SCRAPER_TIMEOUT", 10))
    SCRAPER_DELAY = float(os.environ.get("SCRAPER_DELAY", 2))

    # Celery — use Redis as both the message broker and result backend
    CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Admin
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")


class DevelopmentConfig(BaseConfig):
    """Local development — verbose errors, local database."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://pricetracker:password@localhost:5432/pricetracker"
    )
    # Show SQL queries in the terminal during development (helpful for learning)
    SQLALCHEMY_ECHO = True


class TestingConfig(BaseConfig):
    """Test suite — uses SQLite in memory so tests never touch a real database."""

    TESTING = True
    # SQLite in-memory database: fast, isolated, destroyed after each test run
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False

    # Disable CSRF protection in tests so we can POST forms freely
    WTF_CSRF_ENABLED = False

    # Don't actually queue Celery tasks during tests — run them synchronously
    CELERY_TASK_ALWAYS_EAGER = True


class ProductionConfig(BaseConfig):
    """Production — strict settings, no debug output."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Hard fail if SECRET_KEY wasn't set properly in production
    @classmethod
    def validate(cls):
        if not os.environ.get("SECRET_KEY"):
            raise ValueError("SECRET_KEY environment variable must be set in production")


# Lookup table used by create_app() to select config by name
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
