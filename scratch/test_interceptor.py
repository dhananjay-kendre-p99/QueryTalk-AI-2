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

if __name__ == "__main__":
    run_test()
