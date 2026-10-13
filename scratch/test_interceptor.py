import os
import sys
from unittest.mock import MagicMock

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

# Mock modules that might try to connect to database or rely on environment during import
sys.modules['core.database'] = MagicMock()
sys.modules['core.security'] = MagicMock()

# Now we can import the routing components and llm orchestrator logic
from routes.chat import chat_endpoint, ChatRequest
from services.llm_orchestrator import llm_orchestrator

# Setup mocks
mock_request = MagicMock()
mock_request.headers = {"X-API-Key": "dummy-key"}

mock_db = MagicMock()

def run_test():
    print("Running interceptor tests...")
    
    # Case 1: Unrelated question that LLM says it cannot answer
    # Mock LLM generation returning "Cannot answer with provided schema."
    llm_orchestrator.generate_sql = MagicMock(return_value="Cannot answer with provided schema.")
    chat_req = ChatRequest(message="What is the weather in Tokyo?")
    
    res = chat_endpoint(mock_request, chat_req, mock_db)
    print("\nTest 1 (cannot answer):")
    print("Response:", res)
    assert res["sql"] is None, "SQL should be None for unrelated questions"
    assert "not seem to be related" in res["reply"], "Reply should contain friendly message"
    print("Test 1 Passed!")

    # Case 2: Unrelated question that LLM returns fallback message for
    llm_orchestrator.generate_sql = MagicMock(return_value="The question is not related to the provided schema, so no SQL query can be generated.")
    chat_req = ChatRequest(message="Tell me a joke")
    
    res = chat_endpoint(mock_request, chat_req, mock_db)
    print("\nTest 2 (not related):")
    print("Response:", res)
    assert res["sql"] is None, "SQL should be None for unrelated questions"
    assert "not seem to be related" in res["reply"], "Reply should contain friendly message"
    print("Test 2 Passed!")

    # Case 3: A valid SQL query is generated
    llm_orchestrator.generate_sql = MagicMock(return_value="SELECT * FROM users;")
    
    # Mock is_safe_query return value since core.security is mocked
    import routes.chat as chat_module
    chat_module.is_safe_query = MagicMock(return_value=True)
    
    # Mock db execution results
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [("user1", "admin"), ("user2", "member")]
    mock_result.keys.return_value = ["username", "role"]
    mock_db.execute.return_value = mock_result
    
    # Mock summary method
    llm_orchestrator.summarize_results = MagicMock(return_value="Here are the users.")
    
    chat_req = ChatRequest(message="Show me the users")
    res = chat_endpoint(mock_request, chat_req, mock_db)
    print("\nTest 3 (valid SQL query):")
    print("Response:", res)
    assert res["sql"] == "SELECT * FROM users;", "SQL should match generated query"
    assert res["reply"] == "Here are the users.", "Reply should match LLM summary"
    assert len(res["data"]) == 2, "Data list should be fetched"
    print("Test 3 Passed!")

    # Case 4: Self-healing query correction
    llm_orchestrator.generate_sql = MagicMock(return_value="SELECT p.p_manufact FROM part p;")
    llm_orchestrator.correct_sql = MagicMock(return_value="SELECT p.p_mfgr FROM part p;")
    
    # Mock db execution to fail on first attempt, then succeed on second
    mock_result_correct = MagicMock()
    mock_result_correct.fetchall.return_value = [("manufacturer_name",)]
    mock_result_correct.keys.return_value = ["p_mfgr"]
    
    mock_db.execute.side_effect = [
        Exception("invalid identifier 'P.P_MANUFACT'"),
        mock_result_correct
    ]
    
    llm_orchestrator.summarize_results = MagicMock(return_value="Here is the corrected report.")
    
    chat_req = ChatRequest(message="Show me the product manufacturer")
    res = chat_endpoint(mock_request, chat_req, mock_db)
    print("\nTest 4 (self-healing query correction):")
    print("Response:", res)
    assert res["sql"] == "SELECT p.p_mfgr FROM part p;", "SQL should match corrected query"
    assert res["reply"] == "Here is the corrected report.", "Reply should match LLM summary"
    assert len(res["data"]) == 1, "Data list should be fetched from corrected execution"
    print("Test 4 Passed!")

    # Case 5: Auto-reconnect active database connection if reset to bootstrap
    import core.security as security_module
    import routes.chat as chat_module
    
    # Mock token verification
    mock_request.headers = {
        "X-API-Key": "dummy-key",
        "Authorization": "Bearer dummy_token"
    }
    security_module.verify_clerk_token = MagicMock(return_value={"sub": "clerk_user_123"})
    
    # Mock database models and decryption
    import core.database as db_core
    from core.models import User, DatabaseConnection
    
    mock_app_db = MagicMock()
    db_core.AppSessionLocal = MagicMock(return_value=mock_app_db)
    
    mock_user = User(id="user_uuid_123", clerk_user_id="clerk_user_123")
    mock_app_db.query.return_value.filter.return_value.first.side_effect = [
        mock_user,  # First query: User lookup
        DatabaseConnection(
            user_id="user_uuid_123",
            is_active=True,
            connection_string_enc="enc_snowflake_conn"
        )  # Second query: DatabaseConnection lookup
    ]
    
    import core.encryption as encryption_module
    encryption_module.decrypt_password = MagicMock(return_value="snowflake://username:password@account/db")
    
    # Mock bootstrap engine (containing demo.db in url)
    mock_bootstrap_engine = MagicMock()
    mock_bootstrap_engine.url = "sqlite:///./demo.db"
    db_core._user_engine = mock_bootstrap_engine
    
    # Mock set_engine
    db_core.set_engine = MagicMock()
    
    # Mock chat execution dependencies for test 5
    llm_orchestrator.generate_sql = MagicMock(return_value="SELECT 1;")
    mock_result_reconnected = MagicMock()
    mock_result_reconnected.fetchall.return_value = [(1,)]
    mock_result_reconnected.keys.return_value = ["one"]
    mock_db.execute = MagicMock(return_value=mock_result_reconnected)
    db_core.SessionLocal = MagicMock(return_value=mock_db)
    
    chat_req = ChatRequest(message="Test auto-reconnect")
    res = chat_endpoint(mock_request, chat_req, mock_db)
    print("\nTest 5 (auto-reconnect active database connection):")
    print("Response:", res)
    db_core.set_engine.assert_called_once_with("snowflake://username:password@account/db")
    print("Test 5 Passed!")

if __name__ == "__main__":
    run_test()
