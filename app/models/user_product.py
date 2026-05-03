"""
models/watchlist.py
-------------------
UserProduct is the join table between users and products.

Why a full model instead of a simple association table?
Because we need to store extra data on the relationship itself:
- added_at: when did THIS user start tracking this product?
- alert_price: what price threshold should trigger an alert for THIS user?

A plain db.Table() association can't hold extra columns — a full Model can.

The UNIQUE constraint on (user_id, product_id) prevents a user from
accidentally adding the same product twice.
"""

from datetime import datetime, timezone

from app.extensions import db


class UserProduct(db.Model):
    __tablename__ = "user_products"

    __table_args__ = (
        # Prevent duplicate tracking entries per user
        db.UniqueConstraint("user_id", "product_id", name="uq_user_product"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Optional: alert when price drops below this value.
    # NULL means "no alert threshold set".
    alert_price = db.Column(db.Numeric(10, 2), nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="tracked_products")
    product = db.relationship("Product", back_populates="tracked_by")

    def __repr__(self) -> str:
        return f"<UserProduct user={self.user_id} product={self.product_id}>"
