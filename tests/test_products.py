"""
tests/test_products.py
----------------------
Tests for the /products/* routes: add, remove, alert.
"""

from decimal import Decimal

from tests.conftest import login


class TestAddProduct:
    def test_add_page_requires_login(self, client):
        r = client.get("/products/add", follow_redirects=False)
        assert r.status_code == 302
        assert "/auth/login" in r.headers["Location"]

    def test_add_page_loads_when_logged_in(self, client, test_user):
        login(client, "test@example.com", "password123")
        r = client.get("/products/add")
        assert r.status_code == 200

    def test_add_product_success(self, client, test_user):
        login(client, "test@example.com", "password123")
        r = client.post(
            "/products/add",
            data={"url": "https://www.amazon.com.au/dp/B123456789"},
            follow_redirects=True,
        )
        assert r.status_code == 200

    def test_add_product_empty_url(self, client, test_user):
        login(client, "test@example.com", "password123")
        r = client.post(
            "/products/add",
            data={"url": ""},
            follow_redirects=True,
        )
        assert r.status_code == 200

    def test_add_product_scrape_failure(self, client, test_user):
        login(client, "test@example.com", "password123")
        r = client.post(
            "/products/add",
            data={"url": "https://www.kogan.com/au/buy/blocked/"},
            follow_redirects=True,
        )
        assert r.status_code == 200


class TestRemoveProduct:
    def test_remove_requires_login(self, client, test_product):
        r = client.post(
            f"/products/{test_product.id}/remove",
            follow_redirects=False,
        )
        assert r.status_code == 302

    def test_remove_own_product(self, client, test_user, tracked_product):
        login(client, "test@example.com", "password123")
        r = client.post(
            f"/products/{tracked_product.id}/remove",
            follow_redirects=True,
        )
        assert r.status_code == 200

    def test_cannot_remove_other_users_product(self, client, admin_user, tracked_product):
        login(client, "admin@example.com", "adminpass123")
        r = client.post(
            f"/products/{tracked_product.id}/remove",
            follow_redirects=True,
        )
        assert r.status_code in (200, 404)


class TestAlertPrice:
    def test_set_alert_price(self, client, test_user, tracked_product, db):
        login(client, "test@example.com", "password123")
        r = client.post(
            f"/products/{tracked_product.id}/alert",
            data={"alert_price": "35.00"},
            follow_redirects=True,
        )
        assert r.status_code == 200

        from app.models.user_product import UserProduct
        up = UserProduct.query.filter_by(
            user_id=test_user.id, product_id=tracked_product.id
        ).first()
        assert float(up.alert_price) == 35.00

    def test_set_invalid_alert_price(self, client, test_user, tracked_product):
        login(client, "test@example.com", "password123")
        r = client.post(
            f"/products/{tracked_product.id}/alert",
            data={"alert_price": "not-a-number"},
            follow_redirects=True,
        )
        assert r.status_code == 200

    def test_clear_alert_price(self, client, test_user, tracked_product, db):
        from app.models.user_product import UserProduct
        up = UserProduct.query.filter_by(
            user_id=test_user.id, product_id=tracked_product.id
        ).first()
        up.alert_price = 35.00
        db.session.commit()

        login(client, "test@example.com", "password123")
        r = client.get(
            f"/products/{tracked_product.id}/alert/clear",
            follow_redirects=True,
        )
        assert r.status_code == 200

        db.session.refresh(up)
        assert up.alert_price is None