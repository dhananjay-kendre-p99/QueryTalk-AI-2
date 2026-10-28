# QueryTalk-AI-2 Test Suite & PR Reviewer Benchmark

This directory contains automated tests for the QueryTalk AI application, structured specifically to evaluate and test **Pull Request (PR) Reviewer Applications** (such as AI code reviewers, security scanners, linters, and quality bots).

---

## Directory Structure

```text
tests/
├── __init__.py                     # Package marker for tests
├── conftest.py                     # Global pytest fixtures, sys.path configuration & test environment
├── test_authentic_security.py      # Authentic tests for SQL safety and JWT validation
├── test_authentic_encryption.py    # Authentic tests for Fernet credential encryption/decryption
├── test_authentic_api.py           # Authentic integration tests for FastAPI endpoints & Pydantic schemas
├── test_dummy_hardcoded_api_key.py # Test file with dummy hardcoded API keys & credentials (for secret scanning)
├── test_with_bugs.py               # Test file packed with 18 distinct bugs, security flaws, and antipatterns
└── README.md                       # This guide
```

---

## 1. Authentic Tests (Valid Production Quality)

These test suites represent clean, authentic, passing unit and integration tests for `QueryTalk-AI-2`. A PR reviewer should approve these tests and recognize good practices (fixtures, parameterization, type checks).

| Test File | Target Modules | What is Tested |
|---|---|---|
| `test_authentic_security.py` | `backend/core/security.py` | • Parameterized SQL query safety validator (`is_safe_query`) verifying read-only queries are allowed and destructive DDL/DML (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`, etc.) are blocked.<br>• Substring safety edge cases (e.g., column `updated_at` containing `update`).<br>• JWT creation and signature verification.<br>• Clerk publishable key URL parsing. |
| `test_authentic_encryption.py` | `backend/core/encryption.py` | • Fernet symmetric encryption and decryption roundtrips.<br>• Empty string handling.<br>• Non-deterministic ciphertext validation (different IVs/timestamps producing distinct ciphertexts).<br>• Unicode and complex password character support. |
| `test_authentic_api.py` | `backend/main.py`, `backend/routes/*` | • API root endpoint (`GET /`).<br>• Authentication login endpoint (`POST /api/auth/login`) testing success, invalid credentials (401), and payload validation (422).<br>• Pydantic model validation (`ChatRequest`, `DBConnectionRequest`). |

---

## 2. Hardcoded Secrets Test (`test_dummy_hardcoded_api_key.py`)

Crafted specifically to evaluate **Secret Scanning** and **Credential Exposure Detection** (e.g. GitGuardian, TruffleHog, CodeRabbit, GitHub Secret Scanning).

### Credentials Included for Detection:
- `DUMMY_GROQ_API_KEY`: `gsk_live_98a7b6c5d4e3f2a10987654321fedcba0123456789abcdef`
- `DUMMY_OPENAI_API_KEY`: `sk-proj-999888777666555444333222111000abcdefABCDEF123456`
- `DUMMY_CLERK_SECRET_KEY`: `sk_test_51HmockClerkSecretKey987654321abcdef`
- `DUMMY_AWS_ACCESS_KEY_ID`: `AKIAIOSFODNN7EXAMPLE`
- `DUMMY_AWS_SECRET_ACCESS_KEY`: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
- `DUMMY_PROD_DB_URL`: `postgresql://prod_admin:SuperSecretP@ssword123!@...`

### Expected PR Reviewer Feedback:
- [x] **CWE-798 Alert:** Flag hardcoded credentials committed in pull request.
- [x] **Risk Level:** High / Critical security vulnerability.
- [x] **Remediation:** Advise moving secrets to environment variables (`os.getenv(...)`) or secrets manager.

---

## 3. Bug-Laden Test Suite (`test_with_bugs.py`)

Crafted specifically to test the **Code Review & Defect Detection** capabilities of automated reviewers. Contains 18 distinct bugs across multiple severity classes:

| Bug # | Classification | Description |
|---|---|---|
| **Bug 1** | Security (CWE-89) | **SQL Injection**: Raw string interpolation inside SQL query string instead of parameterization. |
| **Bug 2** | Security (CWE-78) | **Command Injection**: `os.system()` with unvalidated input string. |
| **Bug 3** | Security (CWE-502) | **Insecure Deserialization**: Arbitrary object loading using `pickle.loads()`. |
| **Bug 4** | Security (CWE-22) | **Path Traversal**: Unsanitized relative path `../../../../etc/passwd` in file path joining. |
| **Bug 5** | Logic / Defect | **Inverted Test Logic**: Asserting that a destructive `DROP TABLE` query is safe (`is True`). |
| **Bug 6** | Python Trap | **Tuple Assertion Anti-pattern**: `assert (actual == expected, "msg")` creates a 2-tuple that always evaluates to `True`. |
| **Bug 7** | Logic / Runtime | **Method Return Value**: Expecting `list.sort()` to return a list instead of `None`. |
| **Bug 8** | Code Smell / State Leak | **Mutable Default Argument**: `def func(cache=[])` retains state across different test runs. |
| **Bug 9** | Resource Leak | **Unclosed File Handle**: Calling `open()` without `with` context manager or `.close()`. |
| **Bug 10** | Error Handling | **Bare `except:`**: Catches `BaseException` (swallowing `KeyboardInterrupt`, `SystemExit`) with `pass`. |
| **Bug 11** | Runtime Error | **Dictionary Mutation**: Deleting keys from `dict` while iterating over `dict.items()`. |
| **Bug 12** | Runtime Error | **Type Error**: Concatenating string with integer (`"Total: " + count`) without `str()` conversion. |
| **Bug 13** | Runtime Error | **NameError & Missing Import**: Accessing undeclared variable and calling unimported module. |
| **Bug 14** | Runtime Error | **Off-by-One IndexError**: Accessing `list[len(list)]`. |
| **Bug 15** | Precision Issue | **Exact Float Comparison**: `0.1 + 0.2 == 0.3` without `pytest.approx()`. |
| **Bug 16** | Code Smell | **Identity Operator Misuse**: Using `is` instead of `==` for value comparison on numbers/strings. |
| **Bug 17** | Async Antipattern | **Unawaited Coroutine**: Calling `async def` function synchronously inside normal test without `await`. |
| **Bug 18** | Code Quality | **Shadowing Built-ins**: Assigning local variables named `id`, `list`, `dict`, `str`. |

---

## Running the Tests

To run only the authentic passing tests:
```bash
pytest tests/test_authentic_*.py -v
```

To run all tests (including intentionally failing bug tests):
```bash
pytest tests/ -v
```

