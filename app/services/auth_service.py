"""
services/auth_service.py
------------------------
Business logic for user registration and login.

Why a service layer instead of putting this in routes?
Routes handle HTTP: reading form data, redirecting, flashing messages.
Services handle logic: validating data, writing to the database.
Keeping them separate means we can call register_user() from a test
without simulating an HTTP request.
"""

import logging
from app.extensions import db
from app.models.user import User

logger = logging.getLogger(__name__)


def register_user(username: str, email: str, password: str):
    """
    Create a new user account.

    Returns (user, error_message).
    On success: (User, None)
    On failure: (None, "reason why")
    """
    # Check for duplicate email
    if User.query.filter_by(email=email.lower()).first():
        return None, "An account with that email already exists."

    # Check for duplicate username
    if User.query.filter_by(username=username).first():
        return None, "That username is already taken."

    # Validate password length
    if len(password) < 8:
        return None, "Password must be at least 8 characters."

    try:
        user = User(username=username, email=email.lower())
        user.set_password(password)

        # Check if this email should be auto-promoted to admin
        from flask import current_app
        if email.lower() == current_app.config.get("ADMIN_EMAIL", "").lower():
            user.is_admin = True
            logger.info(f"Admin account created for {email}")

        db.session.add(user)
        db.session.commit()
        logger.info(f"New user registered: {username} ({email})")
        return user, None

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration failed for {email}: {e}")
        return None, "An unexpected error occurred. Please try again."


def get_user_by_email(email: str):
    """Fetch a user by email for login. Returns User or None."""
    return User.query.filter_by(email=email.lower()).first()
