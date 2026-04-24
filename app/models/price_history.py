"""
models/price_history.py
-----------------------
An append-only log of every price recorded for a product.

Why append-only?
We never UPDATE a price_history row — we only INSERT new ones.
This gives us a full audit trail and makes the chart data reliable.
It also avoids write conflicts if two Celery workers somehow scraped
the same product simultaneously.

The index on (product_id, scraped_at) makes chart queries fast:
  SELECT * FROM price_history WHERE product_id = X ORDER BY scraped_at
"""

from datetime import datetime, timezone
from app.extensions import db


class PriceHistory(db.Model):
    __tablename__ = "price_history"

    # Composite index for fast per-product time-series queries
    __table_args__ = (
        db.Index("ix_price_history_product_time", "product_id", "scraped_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False
    )
    price = db.Column(db.Numeric(10, 2), nullable=False)
    scraped_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationship back to product
    product = db.relationship("Product", back_populates="price_history")

    def __repr__(self) -> str:
        return f"<PriceHistory product={self.product_id} price={self.price} at={self.scraped_at}>"
