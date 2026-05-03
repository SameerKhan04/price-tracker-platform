"""
tests/test_auth.py
------------------
Tests for the /auth/* routes: register, login, logout.
"""

import pytest
from tests.conftest import login


class TestRegister:
    def test_register_page_loads(self, client):
        r = client.get("/auth/register")
        assert r.status_code == 200
        assert b"Register" in r.data

    def test_successful_registration(self, client, db):
        r = client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
                "confirm_password": "securepass123",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"newuser" in r.data or b"dashboard" in r.data.lower()

    def test_passwords_must_match(self, client, db):
        r = client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
                "confirm_password": "different",
            },
            follow_redirects=True,
        )
        assert b"do not match" in r.data.lower()

    def test_duplicate_email_rejected(self, client, test_user):
        r = client.post(
            "/auth/register",
            data={
                "username": "otheruser",
                "email": "test@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"register" in r.data.lower() or b"already" in r.data.lower()

    def test_missing_fields_rejected(self, client, db):
        r = client.post(
            "/auth/register",
            data={"username": "", "email": "", "password": ""},
            follow_redirects=True,
        )
        assert b"required" in r.data.lower()

    def test_invalid_email_rejected(self, client, db):
        r = client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "email": "notanemail",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        assert b"valid email" in r.data.lower()

    def test_logged_in_user_redirected(self, client, test_user):
        login(client, "test@example.com", "password123")
        r = client.get("/auth/register", follow_redirects=True)
        assert b"register" not in r.data.lower() or b"dashboard" in r.data.lower()


class TestLogin:
    def test_login_page_loads(self, client):
        r = client.get("/auth/login")
        assert r.status_code == 200
        assert b"Login" in r.data or b"login" in r.data.lower()

    def test_successful_login(self, client, test_user):
        r = login(client, "test@example.com", "password123")
        assert r.status_code == 200
        assert b"testuser" in r.data or b"dashboard" in r.data.lower()

    def test_wrong_password_rejected(self, client, test_user):
        r = login(client, "test@example.com", "wrongpassword")
        assert b"Invalid email or password" in r.data

    def test_unknown_email_rejected(self, client, db):
        r = login(client, "nobody@example.com", "password123")
        assert b"Invalid email or password" in r.data

    def test_empty_credentials_rejected(self, client):
        r = client.post(
            "/auth/login",
            data={"email": "", "password": ""},
            follow_redirects=True,
        )
        assert b"required" in r.data.lower()


class TestLogout:
    def test_logout_redirects_to_login(self, client, test_user):
        login(client, "test@example.com", "password123")
        r = client.get("/auth/logout", follow_redirects=True)
        assert r.status_code == 200
        assert b"logged out" in r.data.lower() or b"login" in r.data.lower()

    def test_logout_requires_login(self, client):
        r = client.get("/auth/logout", follow_redirects=False)
        assert r.status_code == 302