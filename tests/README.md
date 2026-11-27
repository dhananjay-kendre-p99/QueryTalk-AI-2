# QueryTalk-AI-2 Test Suite & PR Reviewer Benchmark

This test suite is configured for branch `test-scrum` to evaluate and benchmark **Automated Pull Request (PR) Reviewer Applications** (AI code reviewers, security scanners, linters, and quality bots).

---

## Directory Overview

```text
tests/
├── __init__.py                     # Package definition for tests
├── conftest.py                     # Pytest fixtures, sys.path configuration & test environment
├── test_authentic_security.py      # Authentic tests for SQL safety and JWT validation
├── test_authentic_encryption.py    # Authentic tests for Fernet credential encryption/decryption
├── test_authentic_api.py           # Authentic integration tests for FastAPI endpoints & Pydantic schemas
├── test_dummy_hardcoded_api_key.py # Test file with 14 dummy calls and hardcoded API keys/secrets
├── test_with_bugs.py               # Test file with 38 distinct bugs, security flaws, and antipatterns
└── README.md                       # Complete PR reviewer scoring rubric
```

---

## 1. Authentic Tests (Baseline Production Quality)

These test suites contain production-ready, authentic unit and integration tests. A PR reviewer should recognize good software engineering practices (parameterization, fixtures, mock isolation):

| Test File | Target Modules | Coverage |
|---|---|---|
| `test_authentic_security.py` | `backend/core/security.py` | • Parameterized SQL query safety validator (`is_safe_query`) verifying read-only queries are allowed and destructive DDL/DML (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`, etc.) are blocked.<br>• Substring safety edge cases (e.g., column `updated_at` containing `update`).<br>• JWT creation and signature verification.<br>• Clerk publishable key URL parsing. |
| `test_authentic_encryption.py` | `backend/core/encryption.py` | • Fernet symmetric encryption and decryption roundtrips.<br>• Empty string handling.<br>• Non-deterministic ciphertext validation (different IVs/timestamps producing distinct ciphertexts).<br>• Unicode and complex password character support. |
| `test_authentic_api.py` | `backend/main.py`, `backend/routes/*` | • API root endpoint (`GET /`).<br>• Authentication login endpoint (`POST /api/auth/login`) testing success, invalid credentials (401), and payload validation (422).<br>• Pydantic model validation (`ChatRequest`, `DBConnectionRequest`). |

---

## 2. Hardcoded Secrets & Dummy Calls (`test_dummy_hardcoded_api_key.py`)

Crafted to evaluate **Secret Scanning (CWE-798)** and **Unmocked External Network Call Detection**.

### 14 Dummy Calls & Exposed Credentials:
1. **Groq Completion Call**: `gsk_live_98a7b6c5d4e3f2a10987654321fedcba0123456789abcdef`
2. **OpenAI Embeddings Call**: `sk-proj-999888777666555444333222111000abcdefABCDEF123456`
3. **Anthropic Claude Call**: `sk-ant-api03-abcdef1234567890abcdef1234567890...`
4. **Clerk User Admin API**: `sk_test_51HmockClerkSecretKey987654321abcdef012345`
5. **Stripe Billing API**: `sk_live_51Mz0DummyStripeKey0099887766554433221100`
6. **Slack Incident Webhook**: `https://hooks.slack.com/services/T00000000/B00000000/XXXXYYYYZZZZ...`
7. **GitHub Workflow Dispatch**: `ghp_1234567890abcdefghijklmnopqrstuvwxyzAB`
8. **AWS S3 Backup**: `AKIAIOSFODNN7EXAMPLE` & `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
9. **SendGrid Email API**: `SG.9876543210abcdef.1234567890abcdef...`
10. **Pinecone Vector DB**: `pcsk_dummy_vector_db_key_998877665544332211`
11. **Datadog Telemetry**: `DD_API_KEY = "9876543210fedcba9876543210fedcba"`
12. **Snowflake DB URI**: `snowflake://snowflake_admin:SnowflakeSuperPass#2026!@...`
13. **Internal Microservice Sync**: `http://192.168.1.105:8080/internal/sync-db` with Basic Auth credentials.
14. **FastAPI Header Forwarding**: Custom headers transmitting hardcoded secrets directly into application endpoints.

---

## 3. Catalog of 38 Intentional Bugs (`test_with_bugs.py`)

A comprehensive catalog across 6 major defect domains:

### Category 1: Security Vulnerabilities (CWEs)
- **Bug 1 (CWE-89):** SQL Injection via raw f-string parameter interpolation.
- **Bug 2 (CWE-89):** Blind SQL Injection via condition string concatenation.
- **Bug 3 (CWE-78):** Command Injection via `subprocess.Popen(..., shell=True)`.
- **Bug 4 (CWE-78):** Command Injection via `os.system()`.
- **Bug 5 (CWE-502):** Insecure Deserialization via `pickle.loads()`.
- **Bug 6 (CWE-22):** Path Traversal using `../../../../etc/passwd`.
- **Bug 7 (CWE-377):** Insecure Temporary File Creation via deprecated `tempfile.mktemp()`.
- **Bug 8 (CWE-327):** Weak Cryptographic Hash (MD5 for passwords).
- **Bug 9 (CWE-918):** Server-Side Request Forgery (SSRF) targeting cloud metadata `169.254.169.254`.
- **Bug 10 (CWE-1333):** ReDoS (Regular Expression Denial of Service) with catastrophic backtracking regex `^(a+)+$`.

### Category 2: Test Logic Bugs & Python Assertion Traps
- **Bug 11:** Inverted Assertion Logic (asserting dangerous `DROP TABLE` is safe).
- **Bug 12:** Tuple Assertion Trap (`assert (actual == expected, "msg")` is always truthy in Python).
- **Bug 13:** In-place Sort Return (`assert list.sort() == expected`, returns `None`).
- **Bug 14:** In-place Append Return (`assert list.append(x) is not None`, returns `None`).
- **Bug 15:** Exact Float Equality (`0.1 + 0.2 == 0.3` without `pytest.approx`).
- **Bug 16:** Identity Operator Misuse (using `is` instead of `==` for numbers/strings).
- **Bug 17:** Infinite Loop (while loop counter is never incremented).
- **Bug 18:** Unreachable Dead Code following an unconditional `return`.

### Category 3: Resource Leaks & Concurrency Anti-Patterns
- **Bug 19:** Resource Leak — Unclosed file handle (`open()` without context manager or `.close()`).
- **Bug 20:** Resource Leak — Unclosed socket descriptor.
- **Bug 21:** Mutable Default Argument (`def func(cache=[])` retaining state across test executions).
- **Bug 22:** Race Condition — Unsynchronized global mutation across threads without locks.
- **Bug 23:** Deadlock Hazard — Acquiring a non-reentrant `threading.Lock()` twice in the same thread.

### Category 4: Exception Handling Defects
- **Bug 24:** Bare `except:` swallowing `BaseException` (including `KeyboardInterrupt`, `SystemExit`) with `pass`.
- **Bug 25:** Exception Chain Loss — Raising new exception without `from err`, losing original traceback.
- **Bug 26:** Return statement inside `finally` block silencing active exceptions.

### Category 5: Python Runtime & Type Errors
- **Bug 27:** Modifying a dictionary while iterating over it (`RuntimeError`).
- **Bug 28:** Modifying a list during iteration causing skipped elements.
- **Bug 29:** TypeError — Concatenating string with integer without `str()`.
- **Bug 30:** TypeError — Calling a non-callable object (e.g. `total_count()`).
- **Bug 31:** NameError — Referencing undeclared variable and missing import.
- **Bug 32:** IndexError — Off-by-one error accessing `list[len(list)]`.
- **Bug 33:** KeyError — Accessing unverified dictionary key directly without `.get()`.

### Category 6: Async, Performance & Code Quality Smells
- **Bug 34:** Unawaited async coroutine called in synchronous test function.
- **Bug 35:** Blocking synchronous I/O (`time.sleep`) inside async function blocking the event loop.
- **Bug 36:** Shadowing Python built-in names (`id`, `list`, `dict`, `str`, `type`).
- **Bug 37:** Quadratic list membership lookup in loop (O(N^2) complexity instead of set).
- **Bug 38:** Redundant comparison of boolean to `== True`.

---

## Running the Tests

To run the authentic passing tests:
```bash
pytest tests/test_authentic_*.py -v
```

To run the entire suite:
```bash
pytest tests/ -v
```

