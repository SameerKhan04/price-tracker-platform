"""
models/user.py
--------------
The User model represents a registered account.

How passwords work:
- We NEVER store the plain-text password.
- bcrypt.hashpw() runs the password through a one-way hashing algorithm.
- On login, bcrypt.checkpw() hashes the attempt and compares — the original
  password is never reconstructed.

Flask-Login integration:
- The four methods (is_authenticated, is_active, is_anonymous, get_id) are
  required by Flask-Login. UserMixin provides default implementations so we
  don't have to write them ourselves.
"""

import bcrypt
from flask_login import UserMixin
from datetime import datetime, timezone

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships — lets us do user.tracked_products, user.notifications etc.
    tracked_products = db.relationship(
        "UserProduct", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, plain_text: str) -> None:
        """Hash and store a password. Never call this with an already-hashed value."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(
            plain_text.encode("utf-8"), salt
        ).decode("utf-8")

    def check_password(self, plain_text: str) -> bool:
        """Return True if plain_text matches the stored hash."""
        return bcrypt.checkpw(
            plain_text.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    @property
    def unread_notification_count(self) -> int:
        """Convenience property used in the nav badge."""
        return Notification.query.filter_by(
            user_id=self.id, is_read=False
        ).count()

    def __repr__(self) -> str:
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id: str):
    """
    Flask-Login calls this on every request to reload the user from the session.
    It receives the user_id we stored in the session cookie and returns the User object.
    """
    return db.session.get(User, int(user_id))
