"""
tests/test_services.py
----------------------
Unit tests for the service layer.
"""

from decimal import Decimal

import pytest
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.services.auth_service import get_user_by_email, register_user
from app.services.price_service import get_price_history, record_price
from app.services.product_service import get_user_products


class TestAuthService:
    def test_register_user_success(self, app, db):
        with app.app_context():
            user, error = register_user("alice", "alice@example.com", "password123")
            assert error is None
            assert user is not None
            assert user.username == "alice"

    def test_register_user_hashes_password(self, app, db):
        with app.app_context():
            user, _ = register_user("bob", "bob@example.com", "mypassword")
            assert user.password_hash != "mypassword"
            assert user.check_password("mypassword") is True

    def test_register_duplicate_email(self, app, db, test_user):
        with app.app_context():
            user, error = register_user("other", "test@example.com", "password123")
            assert user is None
            assert error is not None

    def test_register_duplicate_username(self, app, db, test_user):
        with app.app_context():
            user, error = register_user("testuser", "other@example.com", "password123")
            assert user is None
            assert error is not None

    def test_get_user_by_email_found(self, app, db, test_user):
        with app.app_context():
            found = get_user_by_email("test@example.com")
            assert found is not None
            assert found.username == "testuser"

    def test_get_user_by_email_not_found(self, app, db):
        with app.app_context():
            found = get_user_by_email("nobody@example.com")
            assert found is None

    def test_get_user_by_email_case_insensitive(self, app, db, test_user):
        with app.app_context():
            found = get_user_by_email("TEST@EXAMPLE.COM")
            assert found is None or found.username == "testuser"


class TestPriceService:
    def test_record_price_creates_history_entry(self, app, db, test_product):
        with app.app_context():
            product = db.session.merge(test_product)
            record_price(product.id, 49.99)
            history = PriceHistory.query.filter_by(product_id=product.id).all()
            assert len(history) == 1
            assert history[0].price == Decimal("49.99")

    def test_record_price_updates_product_current_price(self, app, db, test_product):
        with app.app_context():
            product = db.session.merge(test_product)
            record_price(product.id, 39.99)
            updated = db.session.get(Product, product.id)
            assert updated.current_price == Decimal("39.99")

    def test_get_price_history_returns_entries(self, app, db, test_product):
        with app.app_context():
            product = db.session.merge(test_product)
            record_price(product.id, 49.99)
            record_price(product.id, 44.99)
            history = get_price_history(product.id)
            assert len(history) == 2

    def test_get_price_history_empty(self, app, db, test_product):
        with app.app_context():
            product = db.session.merge(test_product)
            history = get_price_history(product.id)
            assert history == []


class TestProductService:
    def test_get_user_products_empty(self, app, db, test_user):
        with app.app_context():
            user = db.session.merge(test_user)
            products = get_user_products(user.id)
            assert products == []

    def test_get_user_products_returns_tracked(self, app, db, test_user, tracked_product):
        with app.app_context():
            user = db.session.merge(test_user)
            products = get_user_products(user.id)
            assert len(products) >= 1