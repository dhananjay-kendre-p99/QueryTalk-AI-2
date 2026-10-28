"""
tests/test_authentic_security.py — Authentic unit tests for core/security.py.

Tests query safety validation (blocking destructive SQL commands) and legacy JWT handling.
"""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from core.security import (
    is_safe_query,
    create_access_token,
    verify_legacy_token,
    _parse_clerk_frontend_api,
)


class TestQuerySafetyGuard:
    """Authentic tests for the SQL query safety validator."""

    @pytest.mark.parametrize(
        "safe_query",
        [
            "SELECT * FROM users;",
            "SELECT id, username, email FROM accounts WHERE is_active = true;",
            "SELECT u.name, count(c.id) FROM users u LEFT JOIN connections c ON u.id = c.user_id GROUP BY u.name;",
            "WITH ranked_sales AS (SELECT emp_id, sum(amount) as total FROM sales GROUP BY emp_id) SELECT * FROM ranked_sales;",
            "SELECT updated_at, timestamp FROM audit_logs WHERE id = 10;",  # 'updated_at' contains 'update' as substring
            "SELECT dropbox_id FROM integrations WHERE id = 5;",             # 'dropbox' contains 'drop' as substring
            "SELECT execution_time_ms FROM query_metrics ORDER BY execution_time_ms DESC LIMIT 10;", # 'execution' contains 'exec'
        ],
    )
    def test_safe_queries_allowed(self, safe_query: str):
        """Verifies read-only queries and legitimate column names are permitted."""
        assert is_safe_query(safe_query) is True

    @pytest.mark.parametrize(
        "destructive_query",
        [
            "DROP TABLE users;",
            "drop table users cascade;",
            "DELETE FROM database_connections WHERE id = '123';",
            "delete from accounts;",
            "UPDATE users SET plan = 'pro' WHERE id = '456';",
            "INSERT INTO audit_logs (action) VALUES ('manual_override');",
            "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;",
            "TRUNCATE TABLE query_history;",
            "GRANT ALL PRIVILEGES ON DATABASE querytalk TO anonymous;",
            "REVOKE SELECT ON users FROM public;",
            "EXEC xp_cmdshell('whoami');",
            "exec sp_executesql N'SELECT 1';",
        ],
    )
    def test_destructive_queries_blocked(self, destructive_query: str):
        """Verifies destructive DDL and DML commands are intercepted and blocked."""
        assert is_safe_query(destructive_query) is False


class TestLegacyAuthentication:
    """Authentic tests for legacy JWT token creation and verification."""

    def test_create_and_verify_access_token(self):
        """Generates a valid token and successfully verifies its payload."""
        payload = {"sub": "developer@querytalk.ai", "role": "developer"}
        token = create_access_token(payload)

        assert isinstance(token, str)
        assert len(token) > 0

        credentials = HTTPAuthorizationCredentials(credentials=token, scheme="Bearer")
        decoded = verify_legacy_token(credentials)

        assert decoded.get("sub") == "developer@querytalk.ai"
        assert decoded.get("role") == "developer"
        assert "exp" in decoded

    def test_verify_invalid_token_raises_401(self):
        """Verifies that tampering with a token causes an HTTP 401 unauthorized exception."""
        tampered_credentials = HTTPAuthorizationCredentials(
            credentials="invalid.token.payload",
            scheme="Bearer",
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_legacy_token(tampered_credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail


class TestClerkKeyParsing:
    """Authentic tests for Clerk publishable key URL derivation."""

    def test_parse_valid_clerk_publishable_key(self):
        """Derives Clerk frontend URL correctly from base64 publishable key."""
        # 'Y2xlcmsuZXhhbXBsZS5jb20k' base64 decodes to 'clerk.example.com$'
        test_pk = "pk_test_Y2xlcmsuZXhhbXBsZS5jb20k"
        url = _parse_clerk_frontend_api(test_pk)
        assert url == "https://clerk.example.com"

    def test_parse_invalid_clerk_key_raises_runtime_error(self):
        """Throws RuntimeError if publishable key is malformed."""
        with pytest.raises(RuntimeError):
            _parse_clerk_frontend_api("invalid-key-without-proper-prefix")

