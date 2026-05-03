"""
services/price_service.py
--------------------------
Handles storing price snapshots and detecting price drops.
"""

import logging
from datetime import UTC, datetime

from app.extensions import db
from app.models.price_history import PriceHistory
from app.models.product import Product

logger = logging.getLogger(__name__)


def record_price(product_id: int, price: float) -> PriceHistory:
    """
    Save a new price snapshot for a product.
    Always appends — price history is never modified or deleted.
    Also updates the product's current_price and last_scraped timestamp.
    Returns the new PriceHistory row.
    """
    product = db.session.get(Product, product_id)
    if not product:
        raise ValueError(f"Product {product_id} not found")

    old_price = product.current_price

    # Write the new price snapshot
    snapshot = PriceHistory(product_id=product_id, price=price)
    db.session.add(snapshot)

    # Update denormalised current_price on the Product for fast dashboard queries
    product.current_price = price
    product.last_scraped = datetime.now(UTC)

    db.session.commit()
    logger.info(f"Price recorded for product {product_id}: {old_price} → {price}")

    # Check for price drops and notify tracking users
    if old_price is not None and price < old_price:
        _notify_price_drop(product, old_price, price)

    return snapshot


def _notify_price_drop(product: Product, old_price: float, new_price: float):
    """
    Create in-app notifications for all users tracking this product
    whose alert_price threshold has been crossed.
    """
    from app.models.user_product import UserProduct
    from app.services.notification_service import create_notification

    trackers = UserProduct.query.filter_by(product_id=product.id).all()

    for tracker in trackers:
        # Notify if: no alert_price set (notify on any drop)
        # OR new price is at or below their alert threshold
        if tracker.alert_price is None or new_price <= tracker.alert_price:
            message = (
                f"Price drop on {product.title or product.url}! "
                f"${old_price:.2f} → ${new_price:.2f}"
            )
            create_notification(
                user_id=tracker.user_id,
                product_id=product.id,
                message=message,
            )


def get_price_history(product_id: int, limit: int = 90) -> list:
    """
    Return the last `limit` price snapshots for a product,
    oldest first (so charts display left-to-right chronologically).
    """
    return (
        PriceHistory.query
        .filter_by(product_id=product_id)
        .order_by(PriceHistory.scraped_at.asc())
        .limit(limit)
        .all()
    )