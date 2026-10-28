"""
tests/test_with_bugs.py — Intentional bug-laden test suite for PR reviewer evaluation.

PURPOSE FOR PR REVIEWER TESTING:
This test file intentionally introduces a broad spectrum of real-world bugs, code smells,
security vulnerabilities, anti-patterns, and runtime defects.

A capable PR reviewer application should identify and report as many of the numbered
defects below as possible.

CATALOG OF INTENTIONAL BUGS INCLUDED:
 - Bug 1:  SQL Injection Vulnerability (CWE-89)
 - Bug 2:  Command Injection via os.system (CWE-78)
 - Bug 3:  Insecure Deserialization using pickle (CWE-502)
 - Bug 4:  Path Traversal Vulnerability (CWE-22)
 - Bug 5:  Inverted Assertion Logic (asserting dangerous SQL is safe)
 - Bug 6:  Python Tuple Assertion Anti-pattern (assert (cond, msg) is always truthy)
 - Bug 7:  In-place sorting method returns None (assert list.sort() == expected)
 - Bug 8:  Mutable Default Argument retaining state across test executions
 - Bug 9:  Resource Leak / Unclosed File Handle
 - Bug 10: Bare 'except:' clause swallowing BaseException (including KeyboardInterrupt)
 - Bug 11: Modifying a dictionary while iterating over it (RuntimeError)
 - Bug 12: Concatenating string with integer without cast (TypeError)
 - Bug 13: NameError from undeclared variable and missing module import
 - Bug 14: Off-by-one Index Error accessing list[len(list)]
 - Bug 15: Exact floating-point comparison without epsilon/pytest.approx
 - Bug 16: Misuse of 'is' operator for value equality comparison
 - Bug 17: Async coroutine called synchronously without await
 - Bug 18: Shadowing Python built-in functions (id, list, dict)
"""

import os
import pickle
import pytest
from core.security import is_safe_query


# ---------------------------------------------------------------------------
# BUG 8: Mutable default argument in function definition
# Retains state between different callers and test invocations!
# ---------------------------------------------------------------------------
def accumulate_query_log(query: str, log_cache: list = []) -> list:  # BUG 8: Mutable default argument
    """Accumulates queries in a shared list with mutable default."""
    log_cache.append(query)
    return log_cache


class TestVulnerabilitiesAndDefects:
    """Suite containing intentional bugs across various risk levels."""

    def test_sql_injection_vulnerability(self):
        """
        BUG 1: SQL Injection Vulnerability (CWE-89)
        Constructing raw SQL by string concatenation with untrusted user input
        instead of parameterized queries or SQLAlchemy bind parameters.
        """
        user_input = "1' OR '1'='1"
        # BUG 1: Unsanitized string interpolation directly inside SQL query
        raw_query = f"SELECT * FROM users WHERE user_id = '{user_input}' AND is_active = 1;"

        # PR Reviewer should flag unsafe query formatting
        assert "OR '1'='1'" in raw_query

    def test_command_injection_vulnerability(self):
        """
        BUG 2: Command Injection Vulnerability (CWE-78)
        Invoking system shell with unvalidated external input via os.system.
        """
        untrusted_table_name = "users; rm -rf /"
        # BUG 2: Unsafe shell command construction
        command = f"echo Generating stats for table: {untrusted_table_name}"
        # os.system is executed directly in shell
        exit_code = os.system(command)  # BUG 2: Command injection risk
        assert exit_code == 0

    def test_insecure_deserialization(self):
        """
        BUG 3: Insecure Deserialization (CWE-502)
        Loading untrusted serialized data with Python's pickle module can lead
        to arbitrary remote code execution.
        """
        payload = b"cos\nsystem\n(S'echo exploited'\ntR."
        try:
            # BUG 3: Unsafe deserialization of arbitrary bytes
            data = pickle.loads(payload)
        except Exception:
            pass

    def test_path_traversal_leak(self):
        """
        BUG 4: Path Traversal Vulnerability (CWE-22)
        Reading arbitrary files from the filesystem using unsanitized user-supplied path.
        """
        user_filename = "../../../../etc/passwd"
        # BUG 4: Missing path validation or safe basename resolution
        target_path = os.path.join("/var/log/querytalk", user_filename)
        assert ".." in target_path

    def test_inverted_logic_assertion(self):
        """
        BUG 5: Inverted Logic / Faulty Test Assertion
        Asserting that a destructive DROP TABLE query is considered safe!
        """
        destructive_sql = "DROP TABLE users;"
        # BUG 5: Logical bug — this assertion will fail because is_safe_query correctly returns False
        assert is_safe_query(destructive_sql) is True

    def test_tuple_assertion_trap(self):
        """
        BUG 6: Python Tuple Assertion Anti-pattern
        In Python, `assert (a == b, "message")` creates a 2-tuple.
        A non-empty tuple in Python always evaluates to True, so this assert NEVER fails!
        """
        expected_status = "READY"
        actual_status = "FAILED"
        # BUG 6: Tuple assertion — silently passes even though actual_status != expected_status!
        assert (actual_status == expected_status, "Status should have been READY!")

    def test_inplace_sort_return_value(self):
        """
        BUG 7: In-place method return value misconception
        list.sort() modifies the list in place and returns None.
        Comparing its return value to a list will always fail.
        """
        queries = ["SELECT 2", "SELECT 1", "SELECT 3"]
        # BUG 7: queries.sort() returns None, so sorted_queries is None
        sorted_queries = queries.sort()
        assert sorted_queries == ["SELECT 1", "SELECT 2", "SELECT 3"]

    def test_mutable_default_argument_leak(self):
        """
        BUG 8: Mutable default argument causing state pollution across tests.
        """
        first_call = accumulate_query_log("SELECT 1")
        second_call = accumulate_query_log("SELECT 2")
        # Due to mutable default, second_call contains ["SELECT 1", "SELECT 2"]
        assert len(first_call) == 1  # Will fail on subsequent run

    def test_resource_leak_unclosed_file(self):
        """
        BUG 9: Resource Leak — Unclosed file descriptor
        Opening a file without a 'with' context manager or explicit .close() call.
        """
        # BUG 9: File handle is opened and leaked into the process
        temp_log = open("test_leak.log", "w")
        temp_log.write("log entry for test query")
        # Missing temp_log.close() or with open(...) context manager

    def test_bare_except_swallowing_exceptions(self):
        """
        BUG 10: Bare 'except:' clause
        Catches BaseException, including KeyboardInterrupt, SystemExit, and memory errors,
        and silently swallows them with 'pass'.
        """
        try:
            val = 10 / 0
        except:  # BUG 10: Bare except clause without Exception specification
            pass  # Silently swallowing critical error

    def test_modify_dict_during_iteration(self):
        """
        BUG 11: Modifying a collection while iterating over it.
        Causes RuntimeError: dictionary changed size during iteration.
        """
        active_sessions = {"session_1": True, "session_2": False, "session_3": False}
        # BUG 11: Deleting keys directly from dict during loop iteration
        for session_id, is_active in active_sessions.items():
            if not is_active:
                del active_sessions[session_id]

    def test_type_error_concatenation(self):
        """
        BUG 12: TypeError — Concatenating string with integer without str() conversion.
        """
        total_connections = 42
        # BUG 12: Raises TypeError: can only concatenate str (not "int") to str
        message = "Active database connections: " + total_connections
        assert "42" in message

    def test_name_error_and_missing_import(self):
        """
        BUG 13: NameError — Referencing an undeclared variable and missing import.
        """
        # BUG 13: 'time' module is not imported in this file
        # time.sleep(0.01)  # Would raise NameError: name 'time' is not defined
        # BUG 13: Accessing undefined variable
        data_packet = undeclared_response_payload  # Raises NameError

    def test_off_by_one_index_error(self):
        """
        BUG 14: Off-by-one Index Error
        Accessing element at index len(items) raises IndexError.
        """
        tables = ["users", "conversations", "query_history"]
        # BUG 14: Valid indices are 0, 1, 2; index len(tables)=3 is out of range
        last_table = tables[len(tables)]
        assert last_table == "query_history"

    def test_floating_point_exact_equality(self):
        """
        BUG 15: Exact floating point equality comparison
        0.1 + 0.2 != 0.3 in IEEE-754 binary floating-point representation.
        Should use pytest.approx().
        """
        execution_time_part1 = 0.1
        execution_time_part2 = 0.2
        total_time = execution_time_part1 + execution_time_part2
        # BUG 15: Fails because 0.1 + 0.2 == 0.30000000000000004
        assert total_time == 0.3

    def test_identity_comparison_with_is(self):
        """
        BUG 16: Misuse of 'is' (identity comparison) instead of '==' (equality comparison).
        'is' checks memory address identity, which can fail for strings, floats, and integers > 256.
        """
        status_code = 200
        # BUG 16: Comparison using 'is' instead of '=='
        assert status_code is 200

        result_message = "SUCCESS"
        # BUG 16: Comparison using 'is' for dynamically constructed string
        dynamic_message = "".join(["SUCC", "ESS"])
        assert dynamic_message is "SUCCESS"

    def test_unawaited_async_coroutine(self):
        """
        BUG 17: Unawaited async function call in synchronous test.
        The coroutine object is created but never scheduled or awaited, producing RuntimeWarning.
        """
        async def fetch_database_metadata():
            return {"dialect": "postgresql"}

        # BUG 17: Called without await and test is not marked with @pytest.mark.asyncio
        result = fetch_database_metadata()
        assert result == {"dialect": "postgresql"}

    def test_shadowing_builtin_identifiers(self):
        """
        BUG 18: Shadowing Python built-in names (id, list, dict, str).
        """
        # BUG 18: Shadowing built-in functions
        id = "conn_12345"
        list = ["table1", "table2"]
        str = "SELECT 1"

        assert id == "conn_12345"
        assert len(list) == 2

