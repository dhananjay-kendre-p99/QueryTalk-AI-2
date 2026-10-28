"""
tests/test_dummy_hardcoded_api_key.py — Test suite with intentional hardcoded credentials.

PURPOSE FOR PR REVIEWER TESTING:
This test file intentionally contains dummy hardcoded API keys, tokens, and connection strings
to verify that automated PR code reviewers and secret scanners (e.g. GitGuardian, TruffleHog,
CodeRabbit, SonarQube, GitHub Secret Scanning) correctly flag CWE-798 (Use of Hard-coded Credentials)
and sensitive information leaks in pull requests.

EXPECTED PR REVIEWER FINDINGS:
1. High Severity: Hardcoded API keys and tokens committed in version control.
2. High Severity: Database connection string containing plaintext credentials.
3. Recommendation: Replace with environment variables (os.getenv) or mock test secrets.
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# INTENTIONAL SECURITY VIOLATION: Hardcoded dummy secrets
# ---------------------------------------------------------------------------
# The automated PR reviewer should flag these variables immediately:
DUMMY_GROQ_API_KEY = "gsk_live_98a7b6c5d4e3f2a10987654321fedcba0123456789abcdef"
DUMMY_OPENAI_API_KEY = "sk-proj-999888777666555444333222111000abcdefABCDEF123456"
DUMMY_CLERK_SECRET_KEY = "sk_test_51HmockClerkSecretKey987654321abcdef"
DUMMY_AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
DUMMY_AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Embedded plaintext password in database URI
DUMMY_PROD_DB_URL = "postgresql://prod_admin:SuperSecretP@ssword123!@db-prod.internal.querytalk.ai:5432/querytalk_production"


class TestHardcodedSecretsInPR:
    """
    Test suite demonstrating credential leakage anti-patterns for PR reviewer benchmarking.
    """

    def test_llm_request_with_hardcoded_groq_key(self, test_client: TestClient):
        """
        Anti-pattern: Sending a hardcoded proprietary API key directly in client request headers
        rather than configuring it securely through environment variables or mock fixtures.
        """
        headers = {
            "X-API-Key": DUMMY_GROQ_API_KEY,  # PR Reviewer should flag this hardcoded secret
            "Content-Type": "application/json",
        }
        payload = {"message": "SELECT count(*) FROM users;"}

        # Making request with hardcoded secret
        response = test_client.post("/api/chat/", json=payload, headers=headers)
        # We assert status code is handled (either 200 or 500 depending on downstream external network)
        assert response.status_code in [200, 500]

    def test_openai_client_initialization_with_hardcoded_key(self):
        """
        Anti-pattern: Instantiating API clients using inline raw key literals.
        """
        # Simulated client config with inline credential
        client_config = {
            "api_key": DUMMY_OPENAI_API_KEY,  # PR Reviewer should flag this hardcoded secret
            "timeout": 30.0,
            "max_retries": 3,
        }
        assert client_config["api_key"].startswith("sk-proj-")
        assert len(client_config["api_key"]) > 20

    def test_database_connection_with_hardcoded_credentials(self):
        """
        Anti-pattern: Hardcoded production database connection string containing username and password.
        """
        conn_str = DUMMY_PROD_DB_URL  # PR Reviewer should flag password exposure
        assert "SuperSecretP@ssword123!" in conn_str
        assert "prod_admin" in conn_str

    def test_aws_s3_backup_credentials_leak(self):
        """
        Anti-pattern: AWS credentials hardcoded in backup test utility.
        """
        s3_credentials = {
            "aws_access_key_id": DUMMY_AWS_ACCESS_KEY_ID,          # PR Reviewer should flag AWS key
            "aws_secret_access_key": DUMMY_AWS_SECRET_ACCESS_KEY,  # PR Reviewer should flag AWS secret
            "region_name": "us-east-1",
        }
        assert s3_credentials["aws_access_key_id"].startswith("AKIA")
        assert len(s3_credentials["aws_secret_access_key"]) == 40

