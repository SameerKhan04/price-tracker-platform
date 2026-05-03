import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def check_and_fire_alerts(product_id: int, new_price: float) -> int:
    from app.extensions import db
    from app.models.notification import Notification
    from app.models.user_product import UserProduct

    price = Decimal(str(new_price))
    triggered = 0

    trackers = UserProduct.query.filter_by(product_id=product_id).all()

    for tracker in trackers:
        if tracker.target_price is None:
            continue
        if price <= tracker.target_price:
            existing = Notification.query.filter_by(
                user_id=tracker.user_id,
                product_id=product_id,
                is_read=False,
            ).first()
            if existing:
                continue

            notif = Notification(
                user_id=tracker.user_id,
                product_id=product_id,
                message=(
                    f"Price dropped to ${new_price:.2f} — "
                    f"at or below your target of ${float(tracker.target_price):.2f}"
                ),
            )
            db.session.add(notif)
            triggered += 1
            logger.info(
                f"Alert fired: user {tracker.user_id}, product {product_id}, "
                f"price {new_price} <= target {tracker.target_price}"
            )

    if triggered:
        db.session.commit()

    return triggered