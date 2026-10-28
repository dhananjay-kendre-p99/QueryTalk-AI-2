"""
tests/test_with_bugs.py — Expanded bug-laden test suite for PR reviewer evaluation.

PURPOSE FOR PR REVIEWER TESTING:
This test file intentionally introduces 38 distinct real-world bugs, security vulnerabilities,
anti-patterns, runtime crashes, and architectural defects.

A high-performing PR reviewer (AI code reviewer, SonarQube, Bandit, CodeRabbit, etc.)
should detect and flag as many of these numbered issues as possible.

CATALOG OF 38 INTENTIONAL BUGS INCLUDED:
-----------------------------------------------------------------------------------
Category 1: Security Vulnerabilities (CWEs)
 - Bug 1:  SQL Injection Vulnerability via string formatting (CWE-89)
 - Bug 2:  Blind SQL Injection via condition concatenation (CWE-89)
 - Bug 3:  Command Injection via subprocess with shell=True (CWE-78)
 - Bug 4:  Command Injection via os.system (CWE-78)
 - Bug 5:  Insecure Deserialization using pickle (CWE-502)
 - Bug 6:  Path Traversal Vulnerability (CWE-22)
 - Bug 7:  Insecure Temporary File Creation with mktemp (CWE-377)
 - Bug 8:  Weak Cryptographic Hash Algorithm MD5 for Passwords (CWE-327)
 - Bug 9:  Server-Side Request Forgery / SSRF targeting cloud metadata (CWE-918)
 - Bug 10: ReDoS — Regular Expression Denial of Service (CWE-1333)

Category 2: Test Logic Bugs & Python Assertion Traps
 - Bug 11: Inverted Assertion Logic (asserting dangerous SQL is safe)
 - Bug 12: Python Tuple Assertion Anti-pattern (assert (cond, msg) is always truthy)
 - Bug 13: In-place sorting method returns None (assert list.sort() == expected)
 - Bug 14: In-place append method returns None (assert list.append(x) is not None)
 - Bug 15: Exact floating-point comparison without pytest.approx (0.1 + 0.2 == 0.3)
 - Bug 16: Misuse of 'is' operator for value equality on numbers and strings
 - Bug 17: Infinite loop condition where loop counter is never updated
 - Bug 18: Unreachable dead code after unconditional return

Category 3: Resource Leaks & Concurrency Anti-Patterns
 - Bug 19: Resource Leak — Unclosed file handle (missing with context manager)
 - Bug 20: Resource Leak — Unclosed raw socket connection
 - Bug 21: Mutable Default Argument retaining state across test executions
 - Bug 22: Unsynchronized Race Condition on shared global state across threads
 - Bug 23: Deadlock Anti-pattern — Acquiring non-reentrant Lock twice in same thread

Category 4: Exception Handling & Control Flow Anti-Patterns
 - Bug 24: Bare 'except:' clause swallowing BaseException (including KeyboardInterrupt)
 - Bug 25: Exception chain loss — Raising new exception without 'from err'
 - Bug 26: Return statement inside 'finally' block silencing active exceptions

Category 5: Python Runtime & Type Errors
 - Bug 27: Modifying a dictionary while iterating over it (RuntimeError)
 - Bug 28: Modifying a list while iterating over it (skipping elements)
 - Bug 29: TypeError — Concatenating string with integer without str() conversion
 - Bug 30: TypeError — Calling a non-callable object
 - Bug 31: NameError — Referencing an undeclared variable and missing import
 - Bug 32: IndexError — Off-by-one index access list[len(list)]
 - Bug 33: KeyError — Accessing non-existent dictionary key directly without .get()

Category 6: Async, Performance & Code Quality Smells
 - Bug 34: Unawaited async coroutine in synchronous test function
 - Bug 35: Blocking synchronous I/O (time.sleep) inside an async function
 - Bug 36: Shadowing Python built-in functions (id, list, dict, str, type)
 - Bug 37: Quadratic list lookup in loop instead of using a set (O(N^2) complexity)
 - Bug 38: Comparing boolean expression to True using == instead of direct truthiness
-----------------------------------------------------------------------------------
"""

import os
import re
import socket
import pickle
import hashlib
import tempfile
import threading
import subprocess
import pytest
from core.security import is_safe_query


# ===========================================================================
# GLOBAL STATE & HELPERS FOR TESTING BUGGY PATTERNS
# ===========================================================================

# BUG 21: Mutable default argument in function definition
def accumulate_query_log(query: str, log_cache: list = []) -> list:  # BUG 21: Mutable default argument
    """Accumulates queries in a shared list with mutable default argument."""
    log_cache.append(query)
    return log_cache


# Shared variable for Bug 22 (Race condition)
_global_query_counter = 0


# ===========================================================================
# SUITE 1: SECURITY VULNERABILITIES (BUGS 1 - 10)
# ===========================================================================

class TestSecurityVulnerabilities:
    """Intentionally vulnerable test cases for evaluating security scanners."""

    def test_sql_injection_vulnerability(self):
        """
        BUG 1: SQL Injection Vulnerability (CWE-89)
        Constructing raw SQL by string concatenation with untrusted user input.
        """
        user_input = "1' OR '1'='1"
        # BUG 1: Unsanitized string interpolation directly inside SQL query
        raw_query = f"SELECT * FROM users WHERE user_id = '{user_input}' AND is_active = 1;"
        assert "OR '1'='1'" in raw_query

    def test_blind_sql_injection(self):
        """
        BUG 2: Blind SQL Injection (CWE-89)
        Concatenating condition directly into database filter clause.
        """
        user_filter = "admin' AND (SELECT SUBSTRING(password,1,1) FROM users)='a"
        # BUG 2: Direct string formatting into SQL clause
        query = "SELECT id FROM accounts WHERE username = '" + user_filter + "';"
        assert "SUBSTRING" in query

    def test_subprocess_shell_injection(self):
        """
        BUG 3: Command Injection via subprocess with shell=True (CWE-78)
        Executing shell commands with shell=True and untrusted user input.
        """
        user_param = "test.txt; cat /etc/passwd"
        # BUG 3: shell=True with unescaped input allows arbitrary command chaining
        proc = subprocess.Popen(
            f"echo Processing file: {user_param}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = proc.communicate()
        assert b"Processing file" in stdout

    def test_os_system_command_injection(self):
        """
        BUG 4: Command Injection via os.system (CWE-78)
        Invoking system shell with unvalidated external input.
        """
        untrusted_table_name = "users; rm -rf /tmp/test"
        # BUG 4: Unsafe shell command construction
        command = f"echo Generating stats for table: {untrusted_table_name}"
        exit_code = os.system(command)  # BUG 4: Command injection risk
        assert exit_code == 0

    def test_insecure_deserialization(self):
        """
        BUG 5: Insecure Deserialization (CWE-502)
        Loading untrusted serialized data with Python's pickle module allows RCE.
        """
        payload = b"cos\nsystem\n(S'echo exploited'\ntR."
        try:
            # BUG 5: Unsafe deserialization of arbitrary bytes
            data = pickle.loads(payload)
        except Exception:
            pass

    def test_path_traversal_leak(self):
        """
        BUG 6: Path Traversal Vulnerability (CWE-22)
        Reading arbitrary files from the filesystem using unsanitized user path.
        """
        user_filename = "../../../../etc/passwd"
        # BUG 6: Missing path validation or safe basename resolution
        target_path = os.path.join("/var/log/querytalk", user_filename)
        assert ".." in target_path

    def test_insecure_temporary_file_mktemp(self):
        """
        BUG 7: Insecure Temporary File Creation (CWE-377)
        tempfile.mktemp() is deprecated and susceptible to symlink race conditions.
        """
        # BUG 7: Deprecated insecure temporary filename generation
        temp_path = tempfile.mktemp(suffix=".sql")
        assert temp_path.endswith(".sql")

    def test_weak_cryptographic_hash(self):
        """
        BUG 8: Weak Cryptographic Hash MD5 for Passwords (CWE-327)
        MD5 is broken and cryptographically insecure for password storage.
        """
        raw_password = "user_master_password_2026"
        # BUG 8: MD5 used for sensitive credential hashing
        weak_hash = hashlib.md5(raw_password.encode("utf-8")).hexdigest()
        assert len(weak_hash) == 32

    def test_server_side_request_forgery_ssrf(self):
        """
        BUG 9: Server-Side Request Forgery / SSRF (CWE-918)
        Constructing HTTP request to cloud instance metadata endpoint without validation.
        """
        untrusted_webhook_url = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
        # BUG 9: SSRF vulnerability accessing AWS metadata
        assert untrusted_webhook_url.startswith("http://169.254.169.254")

    def test_regular_expression_dos_redos(self):
        """
        BUG 10: ReDoS — Regular Expression Denial of Service (CWE-1333)
        Catastrophic backtracking vulnerability in nested repetition regex.
        """
        # BUG 10: Evil regex with exponential time complexity on non-matching inputs
        evil_regex = r"^(a+)+$"
        pattern = re.compile(evil_regex)
        assert pattern.match("aaaaa") is not None


# ===========================================================================
# SUITE 2: TEST LOGIC BUGS & ASSERTION TRAPS (BUGS 11 - 18)
# ===========================================================================

class TestLogicAndAssertionDefects:
    """Intentionally flawed assertions and test logic bugs."""

    def test_inverted_logic_assertion(self):
        """
        BUG 11: Inverted Logic / Faulty Test Assertion
        Asserting that a destructive DROP TABLE query is considered safe!
        """
        destructive_sql = "DROP TABLE users;"
        # BUG 11: Logical bug — this assertion will fail because is_safe_query returns False
        assert is_safe_query(destructive_sql) is True

    def test_tuple_assertion_trap(self):
        """
        BUG 12: Python Tuple Assertion Anti-pattern
        In Python, `assert (a == b, "message")` creates a 2-tuple.
        A non-empty tuple always evaluates to True, so this assert NEVER fails!
        """
        expected_status = "READY"
        actual_status = "FAILED"
        # BUG 12: Tuple assertion — silently passes even though actual != expected!
        assert (actual_status == expected_status, "Status should have been READY!")

    def test_inplace_sort_return_value(self):
        """
        BUG 13: In-place method return value misconception
        list.sort() modifies the list in place and returns None.
        """
        queries = ["SELECT 2", "SELECT 1", "SELECT 3"]
        # BUG 13: queries.sort() returns None, so sorted_queries is None
        sorted_queries = queries.sort()
        assert sorted_queries == ["SELECT 1", "SELECT 2", "SELECT 3"]

    def test_inplace_append_return_value(self):
        """
        BUG 14: In-place append returns None
        list.append() returns None, not the mutated list.
        """
        history = ["SELECT 1"]
        # BUG 14: history.append(...) evaluates to None
        res = history.append("SELECT 2")
        assert res is not None

    def test_floating_point_exact_equality(self):
        """
        BUG 15: Exact floating point equality comparison
        0.1 + 0.2 != 0.3 in IEEE-754 binary floating-point representation.
        """
        execution_time_part1 = 0.1
        execution_time_part2 = 0.2
        total_time = execution_time_part1 + execution_time_part2
        # BUG 15: Fails because 0.1 + 0.2 == 0.30000000000000004
        assert total_time == 0.3

    def test_identity_comparison_with_is(self):
        """
        BUG 16: Misuse of 'is' (identity comparison) instead of '==' (equality comparison).
        'is' checks memory address identity, which can fail for strings and large numbers.
        """
        status_code = 200
        # BUG 16: Comparison using 'is' instead of '=='
        assert status_code is 200

        # Dynamic string construction check with 'is'
        dynamic_message = "".join(["SUCC", "ESS"])
        assert dynamic_message is "SUCCESS"

    def test_infinite_loop_bug(self):
        """
        BUG 17: Infinite loop condition
        Counter is not incremented inside the while loop body.
        """
        count = 0
        limit = 5
        while count < limit:
            # BUG 17: Missing count += 1 causes infinite loop; break included to prevent hanging test runner
            break
        assert count == 5

    def test_unreachable_dead_code(self):
        """
        BUG 18: Unreachable dead code after unconditional return.
        """
        return True
        # BUG 18: Dead code that will never be reached or executed
        dead_var = 100 + 200
        assert dead_var == 300


# ===========================================================================
# SUITE 3: RESOURCE LEAKS & CONCURRENCY ISSUES (BUGS 19 - 23)
# ===========================================================================

class TestResourceLeaksAndConcurrency:
    """Resource management failures, leaks, and concurrency hazards."""

    def test_resource_leak_unclosed_file(self):
        """
        BUG 19: Resource Leak — Unclosed file handle
        Opening a file without a 'with' context manager or explicit .close() call.
        """
        # BUG 19: File handle is opened and leaked into the process
        temp_log = open("test_leak.log", "w")
        temp_log.write("log entry for test query")
        # Missing temp_log.close() or with open(...)

    def test_resource_leak_unclosed_socket(self):
        """
        BUG 20: Resource Leak — Unclosed socket descriptor
        """
        # BUG 20: Raw socket opened without close() or context manager
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert sock.fileno() > 0
        # Missing sock.close()

    def test_mutable_default_argument_leak(self):
        """
        BUG 21: Mutable default argument causing state pollution across tests.
        """
        first_call = accumulate_query_log("SELECT 1")
        second_call = accumulate_query_log("SELECT 2")
        # Due to mutable default, second_call contains ["SELECT 1", "SELECT 2"]
        assert len(first_call) == 1

    def test_concurrency_race_condition(self):
        """
        BUG 22: Race Condition — Unsynchronized global mutation across threads.
        """
        global _global_query_counter
        _global_query_counter = 0

        def increment_counter():
            global _global_query_counter
            for _ in range(100):
                # BUG 22: Non-atomic read-modify-write without Lock
                current = _global_query_counter
                _global_query_counter = current + 1

        threads = [threading.Thread(target=increment_counter) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert _global_query_counter == 500

    def test_deadlock_non_reentrant_lock(self):
        """
        BUG 23: Deadlock Hazard — Acquiring non-reentrant Lock twice in the same thread.
        """
        lock = threading.Lock()
        acquired_first = lock.acquire(timeout=0.1)
        assert acquired_first is True

        # BUG 23: Attempting to acquire non-reentrant lock again will deadlock if timeout is not used
        acquired_second = lock.acquire(timeout=0.01)
        assert acquired_second is True  # Fails: standard Lock is not reentrant!
        lock.release()


# ===========================================================================
# SUITE 4: EXCEPTION HANDLING DEFECTS (BUGS 24 - 26)
# ===========================================================================

class TestExceptionHandlingDefects:
    """Anti-patterns in exception handling and stack unwinding."""

    def test_bare_except_swallowing_exceptions(self):
        """
        BUG 24: Bare 'except:' clause
        Catches BaseException, including KeyboardInterrupt, SystemExit, and memory errors,
        and silently swallows them with 'pass'.
        """
        try:
            val = 10 / 0
        except:  # BUG 24: Bare except clause without Exception specification
            pass  # Silently swallowing critical error

    def test_loss_of_exception_traceback(self):
        """
        BUG 25: Exception chaining loss
        Re-raising a new exception without 'from err' destroys root cause context.
        """
        try:
            int("invalid_number_abc")
        except ValueError as err:
            # BUG 25: Missing 'from err' causes loss of original exception context
            raise RuntimeError("Data conversion failed")

    def test_return_inside_finally_silences_exception(self):
        """
        BUG 26: Return inside 'finally' block suppresses active exceptions!
        In Python, a return statement in finally discards any exception raised in try.
        """
        def buggy_executor():
            try:
                raise ValueError("Critical database connection error!")
            finally:
                # BUG 26: This return discards the ValueError above!
                return "Suppressed!"

        result = buggy_executor()
        assert result == "Suppressed!"


# ===========================================================================
# SUITE 5: RUNTIME & TYPE DEFECTS (BUGS 27 - 33)
# ===========================================================================

class TestRuntimeAndTypeErrors:
    """Python type mismatches, iteration defects, and runtime crashes."""

    def test_modify_dict_during_iteration(self):
        """
        BUG 27: Modifying a collection while iterating over it.
        Causes RuntimeError: dictionary changed size during iteration.
        """
        active_sessions = {"session_1": True, "session_2": False, "session_3": False}
        # BUG 27: Deleting keys directly from dict during loop iteration
        for session_id, is_active in active_sessions.items():
            if not is_active:
                del active_sessions[session_id]

    def test_modify_list_during_iteration(self):
        """
        BUG 28: Modifying list during iteration causes skipped elements.
        """
        numbers = [1, 2, 3, 4, 5]
        # BUG 28: Mutating list index during loop causes elements to be skipped
        for n in numbers:
            if n % 2 == 0:
                numbers.remove(n)
        assert numbers == [1, 3, 5]

    def test_type_error_concatenation(self):
        """
        BUG 29: TypeError — Concatenating string with integer without str() conversion.
        """
        total_connections = 42
        # BUG 29: Raises TypeError: can only concatenate str (not "int") to str
        message = "Active database connections: " + total_connections
        assert "42" in message

    def test_calling_non_callable_object(self):
        """
        BUG 30: TypeError — Attempting to call an integer or non-callable.
        """
        total_count = 100
        # BUG 30: Calling total_count() as a function
        result = total_count()
        assert result == 100

    def test_name_error_and_missing_import(self):
        """
        BUG 31: NameError — Referencing an undeclared variable and missing import.
        """
        # BUG 31: Accessing undefined variable
        data_packet = undeclared_response_payload  # Raises NameError

    def test_off_by_one_index_error(self):
        """
        BUG 32: Off-by-one Index Error
        Accessing element at index len(items) raises IndexError.
        """
        tables = ["users", "conversations", "query_history"]
        # BUG 32: Valid indices are 0, 1, 2; index len(tables)=3 is out of range
        last_table = tables[len(tables)]
        assert last_table == "query_history"

    def test_key_error_missing_dictionary_key(self):
        """
        BUG 33: KeyError on accessing non-existent key directly.
        Should use .get() or check key existence.
        """
        schema_meta = {"dialect": "postgres"}
        # BUG 33: Direct key access for unverified key raises KeyError
        port = schema_meta["database_port"]
        assert port == 5432


# ===========================================================================
# SUITE 6: ASYNC, PERFORMANCE & CODE QUALITY SMELLS (BUGS 34 - 38)
# ===========================================================================

class TestAsyncPerformanceAndSmells:
    """Async pitfalls, performance bottlenecks, and code smells."""

    def test_unawaited_async_coroutine(self):
        """
        BUG 34: Unawaited async function call in synchronous test.
        The coroutine object is created but never scheduled or awaited, producing RuntimeWarning.
        """
        async def fetch_database_metadata():
            return {"dialect": "postgresql"}

        # BUG 34: Called without await and test is not marked with @pytest.mark.asyncio
        result = fetch_database_metadata()
        assert result == {"dialect": "postgresql"}

    def test_blocking_io_in_async_context(self):
        """
        BUG 35: Blocking synchronous I/O inside async code.
        Calling time.sleep() instead of asyncio.sleep() blocks the entire event loop.
        """
        import time

        async def query_runner():
            # BUG 35: Blocking sleep in async function
            time.sleep(0.01)
            return True

        res = query_runner()
        assert res is not None

    def test_shadowing_builtin_identifiers(self):
        """
        BUG 36: Shadowing Python built-in names (id, list, dict, str, type).
        """
        # BUG 36: Shadowing built-in functions
        id = "conn_12345"
        list = ["table1", "table2"]
        str = "SELECT 1"
        type = "relational"

        assert id == "conn_12345"
        assert len(list) == 2
        assert type == "relational"

    def test_quadratic_complexity_lookup(self):
        """
        BUG 37: Performance Smell — Repeated list lookups causing O(N^2) complexity.
        Should convert large_pool to a set for O(1) membership checks.
        """
        large_pool = [f"table_{i}" for i in range(1000)]
        queries = ["table_5", "table_99", "table_non_existent"]
        found = []
        # BUG 37: Checking membership in list repeatedly is O(M * N)
        for q in queries:
            if q in large_pool:
                found.append(q)
        assert len(found) == 2

    def test_comparison_to_true_boolean_smell(self):
        """
        BUG 38: Code Smell — Comparing boolean expression to True using ==.
        Pythonic convention is 'if is_valid:' or 'assert is_valid', not '== True'.
        """
        is_authenticated = bool(1)
        # BUG 38: Redundant comparison with '== True'
        assert (is_authenticated == True) is True

