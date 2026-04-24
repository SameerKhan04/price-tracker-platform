"""
services/notification_service.py
---------------------------------
Create and manage in-app notifications.
"""

import logging

from app.extensions import db
from app.models.notification import Notification

logger = logging.getLogger(__name__)


def create_notification(user_id: int, product_id: int, message: str) -> Notification:
    """Create a new unread notification for a user."""
    notification = Notification(
        user_id=user_id,
        product_id=product_id,
        message=message,
    )
    db.session.add(notification)
    db.session.commit()
    logger.info(f"Notification created for user {user_id}: {message}")
    return notification


def get_user_notifications(user_id: int, unread_only: bool = False) -> list:
    """Return notifications for a user, newest first."""
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc()).limit(50).all()


def mark_all_read(user_id: int):
    """Mark all of a user's notifications as read."""
    Notification.query.filter_by(user_id=user_id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()