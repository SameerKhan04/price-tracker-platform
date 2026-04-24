"""
extensions.py
-------------
Extension instances are created here WITHOUT being tied to a specific Flask app.

Why separate from __init__.py?
If db = SQLAlchemy() were defined inside create_app(), then every file that
needs `db` would have to import from inside the factory, causing circular imports.
Instead, we create the objects here and call db.init_app(app) in create_app().

This is the standard Flask pattern for any project beyond a single file.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Database ORM — use this everywhere you need to query or write to the DB
db = SQLAlchemy()

# Handles user sessions: login_required decorator, current_user proxy, etc.
login_manager = LoginManager()

# Tells Flask-Login which route to redirect to when @login_required fails
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

# Handles database migrations (alembic under the hood)
migrate = Migrate()
