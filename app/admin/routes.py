from app.admin import admin_bp


@admin_bp.route("/")
def index():
    return "Admin — coming soon", 200
