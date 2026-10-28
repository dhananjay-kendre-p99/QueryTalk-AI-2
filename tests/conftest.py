"""
tests/conftest.py — Global pytest fixtures and environment setup for QueryTalk-AI-2.
"""

import os
import sys
from pathlib import Path
import pytest
from cryptography.fernet import Fernet

# 1. Ensure 'backend' directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 2. Set deterministic environment variables for test execution
os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("CLERK_PUBLISHABLE_KEY", "pk_test_bW9jay1jbGVyay1hcGkudGVzdC5kZXYk")

from fastapi.testclient import TestClient
from main import app
from core.security import create_access_token


@pytest.fixture(scope="session")
def test_client():
    """
    FastAPI TestClient fixture for running integration tests against the API.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def valid_auth_token():
    """
    Generates a valid legacy JWT authentication token for protected routes.
    """
    token = create_access_token({"sub": "admin@querytalk.ai", "role": "admin"})
    return token


@pytest.fixture(scope="session")
def auth_headers(valid_auth_token):
    """
    Returns standard Bearer authorization headers with a valid token.
    """
    return {"Authorization": f"Bearer {valid_auth_token}"}

