"""
models/product.py
-----------------
A Product represents a single URL being tracked.

Key design decision — products are shared across users:
If Alice and Bob both track the same URL, there is ONE Product row.
Both of their UserProduct rows point to it. This means we only scrape
that URL once per refresh cycle instead of twice.

scrape_status values:
- 'pending'  — just added, not yet scraped
- 'ok'       — last scrape succeeded
- 'error'    — last scrape failed (see latest ScrapeJob for reason)
"""

from datetime import datetime, timezone
from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, unique=True, nullable=False)
    title = db.Column(db.String(500))
    image_url = db.Column(db.Text)
    source_site = db.Column(db.String(100))   # e.g. "amazon.com.au"
    current_price = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(10), default="AUD")
    last_scraped = db.Column(db.DateTime)
    scrape_status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    price_history = db.relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan",
        order_by="PriceHistory.scraped_at"
    )
    tracked_by = db.relationship(
        "UserProduct", back_populates="product", cascade="all, delete-orphan"
    )
    scrape_jobs = db.relationship(
        "ScrapeJob", back_populates="product", cascade="all, delete-orphan",
        order_by="ScrapeJob.attempted_at.desc()"
    )
    notifications = db.relationship(
        "Notification", back_populates="product", cascade="all, delete-orphan"
    )

    @property
    def latest_price(self):
        """Return the most recent PriceHistory entry, or None."""
        if self.price_history:
            return self.price_history[-1]
        return None

    @property
    def price_history_for_chart(self) -> list:
        """
        Returns price history as a list of dicts for Chart.js.
        Format: [{"date": "2024-01-01", "price": 49.99}, ...]
        """
        return [
            {
                "date": entry.scraped_at.strftime("%Y-%m-%d %H:%M"),
                "price": float(entry.price),
            }
            for entry in self.price_history
        ]

    def __repr__(self) -> str:
        return f"<Product {self.source_site} — {self.title[:40] if self.title else 'untitled'}>"
