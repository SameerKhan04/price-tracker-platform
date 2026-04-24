from app.products import products_bp


@products_bp.route("/")
def index():
    return "Products — coming soon", 200
