from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.dashboard import dashboard_bp


@dashboard_bp.route("/")
@login_required
def index():
    # Stub — full implementation in Phase 4
    return render_template("dashboard/index.html")


@dashboard_bp.route("/notifications")
@login_required
def notifications():
    # Stub — full implementation in Phase 5
    return redirect(url_for("dashboard.index"))
