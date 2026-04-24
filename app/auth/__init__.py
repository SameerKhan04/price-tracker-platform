from flask import Blueprint

auth_bp = Blueprint("auth", __name__, template_folder="templates")

# Routes are imported at the bottom to avoid circular imports.
# This is the standard Flask blueprint pattern.
from app.auth import routes  # noqa: E402, F401
