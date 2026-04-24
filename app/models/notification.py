"""
models/notification.py
----------------------
In-app notifications for price drop alerts.

How it works:
1. Celery scrapes a product and finds the price dropped below alert_price.
2. NotificationService creates a Notification row for every user tracking
   that product with an alert_price set.
3. The nav bar reads user.unread_notification_count on every page load.
4. The notifications page marks them all as is_read = True.

# TODO (stretch): Replace this with real email via SendGrid or Mailgun.
#   The NotificationService is already the right place to add that call.
"""

from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False
    )
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship("User", back_populates="notifications")
    product = db.relationship("Product", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification user={self.user_id} read={self.is_read}>"
