"""
tests/test_dummy_hardcoded_api_key.py — Test suite with extensive hardcoded credentials and dummy API calls.

PURPOSE FOR PR REVIEWER TESTING:
This test file intentionally contains multiple hardcoded API keys, tokens, webhook URLs,
database URIs, and unmocked dummy external API calls.

It serves to evaluate whether PR reviewer applications, secret scanners (e.g. GitGuardian,
TruffleHog, CodeRabbit, GitHub Secret Scanning), and security linters detect:
1. CWE-798: Use of Hard-coded Credentials (API keys, JWT secrets, passwords).
2. Unmocked external HTTP requests in unit tests (network dependency anti-pattern).
3. Leakage of private webhooks, internal IP addresses, and third-party SaaS tokens.
"""

import json
import pytest
import httpx
from fastapi.testclient import TestClient

# ===========================================================================
# INTENTIONAL SECURITY VIOLATION: Catalog of Hardcoded Dummy Secrets & Tokens
# ===========================================================================
# 1. LLM Provider Keys
DUMMY_GROQ_API_KEY = "gsk_live_98a7b6c5d4e3f2a10987654321fedcba0123456789abcdef"
DUMMY_OPENAI_API_KEY = "sk-proj-999888777666555444333222111000abcdefABCDEF123456"
DUMMY_ANTHROPIC_API_KEY = "sk-ant-api03-abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890-aBcDeF"

# 2. Authentication & Payment Secrets
DUMMY_CLERK_SECRET_KEY = "sk_test_51HmockClerkSecretKey987654321abcdef012345"
DUMMY_STRIPE_SECRET_KEY = "sk_live_51Mz0DummyStripeKey0099887766554433221100"
DUMMY_JWT_SIGNING_SECRET = "super_insecure_hardcoded_jwt_secret_key_dont_commit_123456!"

# 3. Cloud Provider & Infrastructure Keys
DUMMY_AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
DUMMY_AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DUMMY_GITHUB_PAT = "ghp_1234567890abcdefghijklmnopqrstuvwxyzAB"
DUMMY_SENDGRID_API_KEY = "SG.9876543210abcdef.1234567890abcdefghijklmnopqrstuvwxyz123456"
DUMMY_PINECONE_API_KEY = "pcsk_dummy_vector_db_key_998877665544332211"
DUMMY_DATADOG_API_KEY = "9876543210fedcba9876543210fedcba"

# 4. Webhooks, Embedded Connection Strings & Internal Network Targets
DUMMY_SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/T00000000/B00000000/XXXXYYYYZZZZ111222333444"
DUMMY_PROD_DB_URL = "postgresql://prod_admin:SuperSecretP@ssword123!@db-prod.internal.querytalk.ai:5432/querytalk_production"
DUMMY_SNOWFLAKE_CONN_STR = "snowflake://snowflake_admin:SnowflakeSuperPass#2026!@xy12345.us-east-1/ANALYTICS_DB/PUBLIC?warehouse=COMPUTE_WH"
DUMMY_INTERNAL_SYNC_URL = "http://192.168.1.105:8080/internal/sync-db"


class TestHardcodedSecretsAndDummyCalls:
    """Suite executing dummy API calls with hardcoded credentials for PR review benchmarking."""

    # -----------------------------------------------------------------------
    # DUMMY CALL 1: External Groq LLM Completion Call
    # -----------------------------------------------------------------------
    def test_dummy_call_groq_completions(self):
        """
        DUMMY CALL: Direct call to Groq API endpoint with hardcoded secret key.
        PR Reviewer should flag: Hardcoded API key + unmocked external network dependency.
        """
        headers = {
            "Authorization": f"Bearer {DUMMY_GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": "Generate a test SQL query."}],
            "temperature": 0.2,
        }
        # In actual test run, we simulate the request or check config structure
        assert headers["Authorization"].startswith("Bearer gsk_live_")
        assert payload["model"] == "llama-3.3-70b-versatile"

    # -----------------------------------------------------------------------
    # DUMMY CALL 2: External OpenAI Embeddings Call
    # -----------------------------------------------------------------------
    def test_dummy_call_openai_embeddings(self):
        """
        DUMMY CALL: Direct call to OpenAI Embeddings endpoint with hardcoded secret.
        PR Reviewer should flag: Hardcoded OpenAI key (sk-proj-...).
        """
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {DUMMY_OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "input": "Database table schema embedding",
            "model": "text-embedding-3-small",
        }
        assert "sk-proj-" in headers["Authorization"]
        assert url == "https://api.openai.com/v1/embeddings"

    # -----------------------------------------------------------------------
    # DUMMY CALL 3: Anthropic Claude Messages Call
    # -----------------------------------------------------------------------
    def test_dummy_call_anthropic_claude(self):
        """
        DUMMY CALL: Direct call to Anthropic Claude API with hardcoded secret.
        PR Reviewer should flag: Hardcoded Anthropic key (sk-ant-api03-...).
        """
        headers = {
            "x-api-key": DUMMY_ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        assert headers["x-api-key"].startswith("sk-ant-api03-")

    # -----------------------------------------------------------------------
    # DUMMY CALL 4: Clerk Admin User Management API
    # -----------------------------------------------------------------------
    def test_dummy_call_clerk_backend_api(self):
        """
        DUMMY CALL: Fetching Clerk user profile using backend secret key.
        PR Reviewer should flag: Hardcoded Clerk secret key (sk_test_...).
        """
        user_id = "user_29w83sxmVTxm306AeTebgLkPpZs"
        endpoint = f"https://api.clerk.com/v1/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {DUMMY_CLERK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        assert headers["Authorization"] == f"Bearer {DUMMY_CLERK_SECRET_KEY}"
        assert "clerk.com" in endpoint

    # -----------------------------------------------------------------------
    # DUMMY CALL 5: Stripe Billing Customer API
    # -----------------------------------------------------------------------
    def test_dummy_call_stripe_billing_sync(self):
        """
        DUMMY CALL: Querying Stripe customer plan with hardcoded live secret key.
        PR Reviewer should flag: Hardcoded live Stripe secret key (sk_live_...).
        """
        stripe_url = "https://api.stripe.com/v1/customers/cus_N9XkO8wPq2"
        headers = {
            "Authorization": f"Bearer {DUMMY_STRIPE_SECRET_KEY}",
        }
        assert headers["Authorization"].startswith("Bearer sk_live_")

    # -----------------------------------------------------------------------
    # DUMMY CALL 6: Slack Incident Webhook Notification
    # -----------------------------------------------------------------------
    def test_dummy_call_slack_incoming_webhook(self):
        """
        DUMMY CALL: Posting database connection failure alert to Slack webhook.
        PR Reviewer should flag: Leaked internal Slack incoming webhook URL.
        """
        alert_payload = {
            "text": "CRITICAL: Database connection failed for user prod_admin",
            "attachments": [
                {"color": "danger", "text": "Exception: Connection timeout on port 5432"}
            ],
        }
        webhook_target = DUMMY_SLACK_WEBHOOK_URL
        assert webhook_target.startswith("https://hooks.slack.com/services/")
        assert "prod_admin" in alert_payload["text"]

    # -----------------------------------------------------------------------
    # DUMMY CALL 7: GitHub Workflow Dispatch Trigger
    # -----------------------------------------------------------------------
    def test_dummy_call_github_repo_dispatch(self):
        """
        DUMMY CALL: Triggering GitHub actions workflow using a personal access token.
        PR Reviewer should flag: Hardcoded GitHub PAT (ghp_...).
        """
        headers = {
            "Authorization": f"token {DUMMY_GITHUB_PAT}",
            "Accept": "application/vnd.github.v3+json",
        }
        repo_url = "https://api.github.com/repos/querytalk/querytalk-ai/dispatches"
        assert headers["Authorization"].startswith("token ghp_")
        assert "api.github.com" in repo_url

    # -----------------------------------------------------------------------
    # DUMMY CALL 8: AWS S3 Database Backup Upload
    # -----------------------------------------------------------------------
    def test_dummy_call_aws_s3_upload(self):
        """
        DUMMY CALL: Simulated S3 upload with hardcoded AWS access key & secret key.
        PR Reviewer should flag: Hardcoded AWS credentials (AKIA...).
        """
        s3_client_config = {
            "aws_access_key_id": DUMMY_AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": DUMMY_AWS_SECRET_ACCESS_KEY,
            "region_name": "us-east-1",
            "bucket_name": "querytalk-encrypted-backups",
        }
        assert s3_client_config["aws_access_key_id"].startswith("AKIA")
        assert len(s3_client_config["aws_secret_access_key"]) == 40

    # -----------------------------------------------------------------------
    # DUMMY CALL 9: SendGrid Email Notification
    # -----------------------------------------------------------------------
    def test_dummy_call_sendgrid_dispatch(self):
        """
        DUMMY CALL: Sending automated email with hardcoded SendGrid API key.
        PR Reviewer should flag: Hardcoded SendGrid key (SG....).
        """
        headers = {
            "Authorization": f"Bearer {DUMMY_SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "personalizations": [{"to": [{"email": "admin@querytalk.ai"}]}],
            "from": {"email": "no-reply@querytalk.ai"},
            "subject": "Weekly QueryTalk Report",
        }
        assert headers["Authorization"].startswith("Bearer SG.")

    # -----------------------------------------------------------------------
    # DUMMY CALL 10: Pinecone Vector Database Search
    # -----------------------------------------------------------------------
    def test_dummy_call_pinecone_vector_index(self):
        """
        DUMMY CALL: Querying schema vector embeddings using hardcoded API key.
        PR Reviewer should flag: Hardcoded Vector DB API key.
        """
        headers = {
            "Api-Key": DUMMY_PINECONE_API_KEY,
            "Content-Type": "application/json",
        }
        assert headers["Api-Key"].startswith("pcsk_")

    # -----------------------------------------------------------------------
    # DUMMY CALL 11: Datadog Custom Metric Submission
    # -----------------------------------------------------------------------
    def test_dummy_call_datadog_metric_event(self):
        """
        DUMMY CALL: Submitting telemetry to Datadog with hardcoded token.
        PR Reviewer should flag: Hardcoded Datadog API key.
        """
        headers = {
            "DD-API-KEY": DUMMY_DATADOG_API_KEY,
            "Content-Type": "application/json",
        }
        assert len(headers["DD-API-KEY"]) == 32

    # -----------------------------------------------------------------------
    # DUMMY CALL 12: Snowflake Cloud Data Warehouse Connection
    # -----------------------------------------------------------------------
    def test_dummy_call_snowflake_warehouse_connect(self):
        """
        DUMMY CALL: Establishing Snowflake connection using credentials embedded in URL.
        PR Reviewer should flag: Plaintext database password in connection URI.
        """
        conn_string = DUMMY_SNOWFLAKE_CONN_STR
        assert "snowflake_admin" in conn_string
        assert "SnowflakeSuperPass#2026!" in conn_string

    # -----------------------------------------------------------------------
    # DUMMY CALL 13: Internal Microservice Sync (Hardcoded IP & Basic Auth)
    # -----------------------------------------------------------------------
    def test_dummy_call_internal_microservice_sync(self):
        """
        DUMMY CALL: Synchronizing database catalog with internal LAN microservice.
        PR Reviewer should flag: Hardcoded private IP address (192.168.1.105) and basic auth.
        """
        sync_target = DUMMY_INTERNAL_SYNC_URL
        auth_tuple = ("internal_service_user", "SuperSecretInternalPass!")
        assert "192.168.1.105" in sync_target
        assert auth_tuple[1] == "SuperSecretInternalPass!"

    # -----------------------------------------------------------------------
    # DUMMY CALL 14: QueryTalk Internal API with Custom Header Credentials
    # -----------------------------------------------------------------------
    def test_dummy_call_internal_chat_endpoint_with_secrets(self, test_client: TestClient):
        """
        DUMMY CALL: Hitting FastAPI chat endpoint forwarding multiple hardcoded keys in headers.
        PR Reviewer should flag: Hardcoded secrets transmitted via HTTP headers.
        """
        headers = {
            "X-API-Key": DUMMY_GROQ_API_KEY,
            "X-OpenAI-Key": DUMMY_OPENAI_API_KEY,
            "X-Clerk-Secret": DUMMY_CLERK_SECRET_KEY,
            "Content-Type": "application/json",
        }
        payload = {"message": "SELECT * FROM sales_data LIMIT 5;"}

        response = test_client.post("/api/chat/", json=payload, headers=headers)
        # Endpoint attempts to contact LLM orchestrator; returns 200 or 500 depending on network
        assert response.status_code in [200, 500]

