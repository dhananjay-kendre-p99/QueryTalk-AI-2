"""
tests/test_authentic_api.py — Authentic integration tests for FastAPI routes and schemas.
"""

from fastapi.testclient import TestClient
from routes.chat import ChatRequest
from routes.database import DBConnectionRequest
import pytest


class TestGeneralEndpoints:
    """Authentic tests for application health and root endpoints."""

    def test_read_root(self, test_client: TestClient):
        """Verifies the API root returns 200 OK with the welcome message."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to QueryTalk AI API"}


class TestAuthEndpoints:
    """Authentic tests for the authentication endpoints."""

    def test_login_success(self, test_client: TestClient):
        """Verifies successful login with valid administrative credentials."""
        payload = {
            "username": "admin@querytalk.ai",
            "password": "admin1234",
        }
        response = test_client.post("/api/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"

    def test_login_invalid_credentials(self, test_client: TestClient):
        """Verifies login failure when supplying incorrect credentials."""
        payload = {
            "username": "admin@querytalk.ai",
            "password": "wrongpassword999",
        }
        response = test_client.post("/api/auth/login", json=payload)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_validation_error(self, test_client: TestClient):
        """Verifies Pydantic rejection when required payload fields are missing."""
        payload = {"username": "admin@querytalk.ai"}  # missing 'password'
        response = test_client.post("/api/auth/login", json=payload)
        assert response.status_code == 422


class TestPydanticModelValidation:
    """Authentic tests validating request models and data schemas."""

    def test_chat_request_valid(self):
        """ChatRequest model accepts valid message."""
        req = ChatRequest(message="What is the average sales volume per region?")
        assert req.message == "What is the average sales volume per region?"

    def test_chat_request_missing_message_fails(self):
        """ChatRequest model rejects missing message payload."""
        with pytest.raises(Exception):
            ChatRequest()

    def test_db_connection_request_defaults(self):
        """DBConnectionRequest validates required and optional fields correctly."""
        req = DBConnectionRequest(
            db_type="postgresql",
            db_name="analytics_warehouse",
            host="db.internal.network",
            port=5432,
            username="analyst_readonly",
        )
        assert req.db_type == "postgresql"
        assert req.db_name == "analytics_warehouse"
        assert req.password is None
        assert req.name is None

