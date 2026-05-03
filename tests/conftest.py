"""
tests/conftest.py
-----------------
Shared pytest fixtures for the entire test suite.

Uses an in-memory SQLite database so tests never touch the real PostgreSQL
instance. Each test function gets a fresh database via function-scoped
fixtures — no state leaks between tests.
"""

import pytest
from app import create_app
from app.extensions import db as _db
from app.models.product import Product
from app.models.user import User
from app.models.user_product import UserProduct


@pytest.fixture(scope="session")
def app():
    """Create a Flask app configured for testing."""
    app = create_app("testing")
    return app


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_user(db):
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db):
    user = User(username="adminuser", email="admin@example.com", is_admin=True)
    user.set_password("adminpass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_product(db):
    product = Product(
        url="https://www.amazon.com.au/dp/B123456789",
        title="Test Product",
        current_price=49.99,
        source_site="amazon.com.au",
        scrape_status="ok",
    )
    db.session.add(product)
    db.session.commit()
    return product


@pytest.fixture
def tracked_product(db, test_user, test_product):
    up = UserProduct(user_id=test_user.id, product_id=test_product.id)
    db.session.add(up)
    db.session.commit()
    return test_product


def login(client, email, password):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )