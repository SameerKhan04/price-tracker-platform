from app.dashboard import dashboard_bp
from app.services.notification_service import (get_user_notifications,
                                               mark_all_read)
from app.services.product_service import get_user_products
from flask import redirect, render_template, url_for
from flask_login import current_user, login_required


@dashboard_bp.route("/")
@login_required
def index():
    user_products = get_user_products(current_user.id)
    return render_template("dashboard/index.html", user_products=user_products)


@dashboard_bp.route("/notifications")
@login_required
def notifications():
    notifs = get_user_notifications(current_user.id)
    mark_all_read(current_user.id)
    return render_template("dashboard/notifications.html", notifications=notifs)