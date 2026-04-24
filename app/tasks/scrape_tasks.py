"""
tasks/scrape_tasks.py
---------------------
Celery tasks for scraping product prices.

scrape_product:
  - Called immediately when a user adds a product
  - Called by refresh_all_products on schedule
  - Uses exponential backoff retry on failure (3 attempts)
  - Logs every attempt to scrape_jobs table for the admin panel

refresh_all_products:
  - Triggered by Celery Beat every hour
  - Queues one scrape_product task per active product
  - This means scrapes are parallelised across Celery workers
"""

import logging
import time
from datetime import datetime

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from celery_worker import \
    celery  # noqa: F401 — ensures the app's Celery instance is active

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute base delay; Celery doubles it each retry
    name="app.tasks.scrape_tasks.scrape_product",
)
def scrape_product(self, product_id: int):
    """
    Scrape a product URL and record the price.

    bind=True gives us `self` so we can call self.retry().
    max_retries=3 with exponential backoff means attempts at:
      T+0s, T+60s, T+120s, T+240s before giving up.
    """
    from app.extensions import db
    from app.models.product import Product
    from app.models.scrape_job import ScrapeJob
    from app.scraper.factory import get_scraper
    from app.services.price_service import record_price

    started_at = datetime.utcnow()

    # Look up the product
    product = Product.query.get(product_id)
    if not product:
        logger.error(f"scrape_product: product {product_id} not found, skipping")
        return

    logger.info(f"Scraping product {product_id}: {product.url}")

    # Be respectful — add a small delay before each request
    # In production this should use a per-domain rate limiter
    from flask import current_app
    delay = current_app.config.get("SCRAPER_DELAY", 2)
    time.sleep(delay)

    scraper = get_scraper(product.url)

    try:
        timeout = current_app.config.get("SCRAPER_TIMEOUT", 10)
        result = scraper.scrape(product.url, timeout=timeout)
        duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)

        if result.success and result.price:
            # Update product metadata on first successful scrape
            if not product.title and result.title:
                product.title = result.title
            if not product.image_url and result.image_url:
                product.image_url = result.image_url
            product.source_site = result.source_site
            db.session.commit()

            # Store price and trigger notifications if price dropped
            record_price(product_id, result.price)

            # Log successful job
            job = ScrapeJob(
                product_id=product_id,
                status="success",
                duration_ms=duration_ms,
            )
            db.session.add(job)
            db.session.commit()
            logger.info(f"Product {product_id} scraped successfully: £{result.price}")

        else:
            # Scrape returned but couldn't extract price
            product.scrape_status = "error"
            db.session.commit()

            job = ScrapeJob(
                product_id=product_id,
                status="failed",
                error_message=result.error or "Price not found",
                duration_ms=duration_ms,
            )
            db.session.add(job)
            db.session.commit()
            logger.warning(f"Product {product_id} scrape failed: {result.error}")

            # Retry if we haven't exceeded max retries
            raise self.retry(exc=Exception(result.error or "Price extraction failed"))

    except MaxRetriesExceededError:
        logger.error(f"Product {product_id} exceeded max retries, giving up")
        product.scrape_status = "error"
        db.session.commit()

    except Exception as exc:
        duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        logger.error(f"Unexpected error scraping product {product_id}: {exc}")

        # Log the failure
        try:
            job = ScrapeJob(
                product_id=product_id,
                status="failed",
                error_message=str(exc)[:500],
                duration_ms=duration_ms,
            )
            db.session.add(job)
            product.scrape_status = "error"
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        except MaxRetriesExceededError:
            logger.error(f"Product {product_id} max retries exceeded")


@shared_task(name="app.tasks.scrape_tasks.refresh_all_products")
def refresh_all_products():
    """
    Queue a scrape task for every product that has been successfully
    scraped before OR is still pending.
    Called by Celery Beat every hour.
    """
    from app.models.product import Product

    products = Product.query.filter(
        Product.scrape_status.in_(["ok", "pending"])
    ).all()

    count = 0
    for product in products:
        scrape_product.delay(product.id)
        count += 1

    logger.info(f"refresh_all_products: queued {count} scrape tasks")
    return count