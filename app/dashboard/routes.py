from app.dashboard import dashboard_bp


@dashboard_bp.route("/")
def index():
    return "Dashboard — coming soon", 200
