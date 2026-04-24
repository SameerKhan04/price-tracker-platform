"""
services/product_service.py
----------------------------
Business logic for tracking products.

Key decisions:
- Products are deduplicated by URL. If two users track the same URL,
  only one Product row exists. This avoids redundant scrape requests.
- UserProduct is the join table linking a user to a product.
- add_product() queues a Celery scrape task immediately so the user
  sees data as quickly as possible after adding a product.
"""

import logging
from urllib.parse import urlparse

from app.extensions import db
from app.models.product import Product
from app.models.user_product import UserProduct

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    """Basic URL validation — must have scheme and netloc."""
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


def add_product(user_id: int, url: str, alert_price: float = None):
    """
    Add a product to a user's watchlist.

    Returns (user_product, error_message).
    Handles three cases:
      1. Product URL is new → create Product, create UserProduct, queue scrape
      2. Product URL exists, user not tracking it → create UserProduct only
      3. User already tracking this URL → return error (duplicate)
    """
    url = url.strip()

    if not is_valid_url(url):
        return None, "Please enter a valid URL starting with http:// or https://"

    # Check if this user is already tracking this URL
    existing_product = Product.query.filter_by(url=url).first()
    if existing_product:
        already_tracking = UserProduct.query.filter_by(
            user_id=user_id,
            product_id=existing_product.id
        ).first()
        if already_tracking:
            return None, "You are already tracking this product."

    try:
        if not existing_product:
            # New product — create the record
            existing_product = Product(
                url=url,
                scrape_status="pending",
                source_site=urlparse(url).netloc.replace("www.", ""),
            )
            db.session.add(existing_product)
            db.session.flush()  # Get the ID without committing
            logger.info(f"New product created: {url}")

        user_product = UserProduct(
            user_id=user_id,
            product_id=existing_product.id,
            alert_price=alert_price,
        )
        db.session.add(user_product)
        db.session.commit()

        # Queue an immediate scrape task so the user gets data fast.
        # Import here to avoid circular imports at module load time.
        from app.tasks.scrape_tasks import scrape_product
        scrape_product.delay(existing_product.id)
        logger.info(f"Scrape task queued for product {existing_product.id}")

        return user_product, None

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add product {url} for user {user_id}: {e}")
        return None, "An unexpected error occurred. Please try again."


def remove_product(user_id: int, product_id: int):
    """
    Remove a product from a user's watchlist.
    Does NOT delete the Product itself — other users may still be tracking it.
    """
    user_product = UserProduct.query.filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()

    if not user_product:
        return False, "Product not found in your watchlist."

    try:
        db.session.delete(user_product)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to remove product {product_id} for user {user_id}: {e}")
        return False, "An unexpected error occurred."


def get_user_products(user_id: int) -> list:
    """
    Return all UserProduct rows for a user, with the related Product
    eagerly loaded to avoid N+1 queries.
    """
    return (
        UserProduct.query
        .filter_by(user_id=user_id)
        .join(UserProduct.product)
        .order_by(UserProduct.added_at.desc())
        .all()
    )