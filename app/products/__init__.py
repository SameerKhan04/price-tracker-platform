from flask import Blueprint

products_bp = Blueprint("products", __name__, template_folder="templates")

from app.products import routes  # noqa: E402, F401
