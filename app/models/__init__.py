"""
models/__init__.py
------------------
Imports all models so that Flask-Migrate (Alembic) can detect every table
when it scans the app. If a model isn't imported here, it won't appear in
generated migrations.
"""

from app.models.user import User
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.watchlist import UserProduct
from app.models.notification import Notification
from app.models.scrape_job import ScrapeJob

__all__ = [
    "User",
    "Product",
    "PriceHistory",
    "UserProduct",
    "Notification",
    "ScrapeJob",
]
