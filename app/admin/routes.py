"""
admin/routes.py
---------------
Admin panel — restricted to users with is_admin = True.
"""

import logging

from app.admin import admin_bp
from app.extensions import db
from app.models.product import Product
from app.models.scrape_job import ScrapeJob
from app.models.user import User
from app.models.user_product import UserProduct
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

logger = logging.getLogger(__name__)


def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("You don't have permission to access the admin panel.", "error")
            return redirect(url_for("dashboard.index"))
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route("/")
@admin_required
def index():
    total_users = User.query.count()
    total_products = Product.query.count()
    ok_products = Product.query.filter_by(scrape_status="ok").count()
    error_products = Product.query.filter_by(scrape_status="error").count()
    pending_products = Product.query.filter_by(scrape_status="pending").count()
    total_jobs = ScrapeJob.query.count()
    failed_jobs = ScrapeJob.query.filter_by(status="failed").count()
    recent_jobs = ScrapeJob.query.order_by(ScrapeJob.attempted_at.desc()).limit(10).all()

    return render_template(
        "admin/index.html",
        total_users=total_users,
        total_products=total_products,
        ok_products=ok_products,
        error_products=error_products,
        pending_products=pending_products,
        total_jobs=total_jobs,
        failed_jobs=failed_jobs,
        recent_jobs=recent_jobs,
    )


@admin_bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def toggle_admin(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("You can't change your own admin status.", "error")
        return redirect(url_for("admin.users"))
    user.is_admin = not user.is_admin
    db.session.commit()
    status = "granted" if user.is_admin else "revoked"
    flash(f"Admin access {status} for {user.username}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("You can't delete your own account from the admin panel.", "error")
        return redirect(url_for("admin.users"))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f"User {username} deleted.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/products")
@admin_required
def products():
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    for product in all_products:
        product.tracker_count = UserProduct.query.filter_by(product_id=product.id).count()
    return render_template("admin/products.html", products=all_products)


@admin_bp.route("/products/<int:product_id>/scrape", methods=["POST"])
@admin_required
def trigger_scrape(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("admin.products"))
    from app.tasks.scrape_tasks import scrape_product
    scrape_product.delay(product_id)
    flash(f"Scrape queued for: {product.title or product.url[:60]}", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("admin.products"))
    title = product.title or product.url[:60]
    db.session.delete(product)
    db.session.commit()
    flash(f"Product deleted: {title}", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/jobs")
@admin_required
def jobs():
    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status", "")
    query = ScrapeJob.query.order_by(ScrapeJob.attempted_at.desc())
    if status_filter in ("success", "failed"):
        query = query.filter_by(status=status_filter)
    pagination = query.paginate(page=page, per_page=50, error_out=False)
    return render_template(
        "admin/jobs.html",
        jobs=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
    )