from flask import render_template
from flask_login import login_required
from app.products import products_bp


@products_bp.route("/add")
@login_required
def add():
    # Stub — full implementation in Phase 3
    return render_template("products/add.html")
