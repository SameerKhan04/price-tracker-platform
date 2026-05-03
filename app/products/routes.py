"""
products/routes.py
------------------
Routes for adding, viewing, and removing tracked products.
"""

import logging

from app.models.product import Product
from app.models.user_product import UserProduct
from app.products import products_bp
from app.services.price_service import get_price_history
from app.services.product_service import add_product, remove_product
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

logger = logging.getLogger(__name__)


@products_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        alert_price_raw = request.form.get("alert_price", "").strip()

        alert_price = None
        if alert_price_raw:
            try:
                alert_price = float(alert_price_raw)
                if alert_price <= 0:
                    raise ValueError
            except ValueError:
                flash("Alert price must be a positive number.", "error")
                return render_template("products/add.html", url=url)

        user_product, error = add_product(
            user_id=current_user.id,
            url=url,
            alert_price=alert_price,
        )

        if error:
            flash(error, "error")
            return render_template("products/add.html", url=url)

        flash("Product added! We're fetching the price now — check back in a moment.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("products/add.html")


@products_bp.route("/<int:product_id>")
@login_required
def detail(product_id):
    # Ensure the current user is actually tracking this product
    user_product = UserProduct.query.filter_by(
        user_id=current_user.id,
        product_id=product_id,
    ).first_or_404()

    product = user_product.product
    history = get_price_history(product_id)

    # Format data for Chart.js
    chart_labels = [h.scraped_at.strftime("%d %b %H:%M") for h in history]
    chart_prices = [float(h.price) for h in history]

    return render_template(
        "products/detail.html",
        product=product,
        user_product=user_product,
        chart_labels=chart_labels,
        chart_prices=chart_prices,
    )


@products_bp.route("/<int:product_id>/remove", methods=["POST"])
@login_required
def remove(product_id):
    success, error = remove_product(
        user_id=current_user.id,
        product_id=product_id,
    )
    if error:
        flash(error, "error")
    else:
        flash("Product removed from your watchlist.", "info")
    return redirect(url_for("dashboard.index"))

@products_bp.route("/<int:product_id>/alert", methods=["POST"])
@login_required
def update_alert(product_id):
    user_product = UserProduct.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first_or_404()

    alert_price_raw = request.form.get("alert_price", "").strip()
    if alert_price_raw:
        try:
            val = float(alert_price_raw)
            if val <= 0:
                raise ValueError
            user_product.alert_price = val
            from app.extensions import db
            db.session.commit()
            flash("Alert price saved.", "success")
        except ValueError:
            flash("Alert price must be a positive number.", "error")
    else:
        flash("Please enter a price.", "error")

    return redirect(url_for("products.detail", product_id=product_id))


@products_bp.route("/<int:product_id>/alert/clear", methods=["GET"])
@login_required
def clear_alert(product_id):
    user_product = UserProduct.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first_or_404()
    from app.extensions import db
    user_product.alert_price = None
    db.session.commit()
    flash("Alert cleared.", "info")
    return redirect(url_for("products.detail", product_id=product_id))