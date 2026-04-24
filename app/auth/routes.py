"""
auth/routes.py
--------------
Handles register, login, and logout HTTP flows.

How Flask-Login works here:
- login_user(user) stores the user's ID in a signed session cookie.
- On every subsequent request, Flask-Login calls load_user() (defined in
  models/user.py) to reload the User object from the database.
- logout_user() clears the session cookie.
- @login_required on other routes redirects to /auth/login if not logged in.
"""

import logging
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.services.auth_service import register_user, get_user_by_email

logger = logging.getLogger(__name__)

# Simple rate limiting for login: track attempts in memory.
# NOTE: This resets if the worker restarts. For production, use Flask-Limiter
# with Redis backend. Marked as a known limitation in the README.
# TODO (stretch): Replace with Flask-Limiter + Redis for persistent rate limiting
_login_attempts: dict = {}
MAX_LOGIN_ATTEMPTS = 10


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # If user is already logged in, send them to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Basic input validation
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("auth/register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")

        if "@" not in email:
            flash("Please enter a valid email address.", "error")
            return render_template("auth/register.html")

        user, error = register_user(username, email, password)

        if error:
            flash(error, "error")
            return render_template("auth/register.html")

        # Log them in immediately after registering
        login_user(user)
        flash(f"Welcome, {user.username}! Your account has been created.", "success")
        logger.info(f"User {user.username} registered and logged in")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        ip = request.remote_addr

        # Primitive rate limiting — blocks after MAX_LOGIN_ATTEMPTS from same IP
        attempts = _login_attempts.get(ip, 0)
        if attempts >= MAX_LOGIN_ATTEMPTS:
            flash("Too many login attempts. Please try again later.", "error")
            return render_template("auth/login.html")

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("auth/login.html")

        user = get_user_by_email(email)

        if user and user.check_password(password):
            # Successful login — reset attempt counter
            _login_attempts.pop(ip, None)
            login_user(user, remember=True)
            flash(f"Welcome back, {user.username}!", "success")
            logger.info(f"User {user.username} logged in from {ip}")

            # Redirect to the page they were trying to visit (if any)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        else:
            # Increment failed attempt counter
            _login_attempts[ip] = attempts + 1
            flash("Invalid email or password.", "error")
            logger.warning(f"Failed login attempt for {email} from {ip}")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logger.info(f"User {current_user.username} logged out")
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
