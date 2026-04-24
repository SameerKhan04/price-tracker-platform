import logging
from celery_worker import celery

logger = logging.getLogger(__name__)

@celery.task
def send_price_drop_alert(user_id: int, product_id: int):
    """Stub — implemented in Phase 5."""
    logger.info(f"send_price_drop_alert stub: user={user_id} product={product_id}")
