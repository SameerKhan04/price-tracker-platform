import logging
from celery_worker import celery

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3)
def scrape_product(self, product_id: int):
    """Stub — implemented in Phase 3."""
    logger.info(f"scrape_product stub called for product_id={product_id}")

@celery.task
def refresh_all_products():
    """Stub — implemented in Phase 3."""
    logger.info("refresh_all_products stub called")
