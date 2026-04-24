import os


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCRAPER_TIMEOUT = int(os.environ.get("SCRAPER_TIMEOUT", 10))
    SCRAPER_DELAY = float(os.environ.get("SCRAPER_DELAY", 2))
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")

    # Celery 5 uses lowercase keys — the old CELERY_ prefix is no longer supported
    broker_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    result_backend = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://pricetracker:password@localhost:5432/pricetracker"
    )
    SQLALCHEMY_ECHO = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False
    task_always_eager = True  # Celery 5 lowercase


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    @classmethod
    def validate(cls):
        if not os.environ.get("SECRET_KEY"):
            raise ValueError("SECRET_KEY environment variable must be set in production")


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
