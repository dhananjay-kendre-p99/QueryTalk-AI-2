import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import DatabaseConnection, User
from core.encryption import decrypt_password
import core.database as db_core
import httpx

load_dotenv()

def run_chat_diagnostic():
    # Find a user and their connection
    engine = create_engine(os.getenv('DATABASE_URL'))
    Session = sessionmaker(bind=engine)
    s = Session()
    
    conn = s.query(DatabaseConnection).order_by(DatabaseConnection.updated_at.desc()).first()
    if not conn:
        print("No connections found.")
        return
        
    user = s.query(User).filter(User.id == conn.user_id).first()
    print("User clerk ID:", user.clerk_user_id)
    print("Connection Name:", conn.name)
    
    # We can invoke the chat endpoint logic directly in Python to see the exception!
    db_core.set_engine(decrypt_password(conn.connection_string_enc), connection_id=str(conn.id))
    
    from routes.chat import chat_endpoint, ChatRequest
    from fastapi import Request
    
    # Create a mock Request object
    # We can mock the headers
    class MockRequest:
        def __init__(self, headers):
            self.headers = headers
            
    # Mock verify_clerk_token in core.security so that when routes.chat imports it, it's already mocked!
    import core.security
    core.security.verify_clerk_token = lambda credentials: {"sub": user.clerk_user_id}
    
    from routes.chat import chat_endpoint, ChatRequest
    from fastapi import Request
    
    # Also mock Depends(get_db)
    from core.database import SessionLocal
    db_sess = SessionLocal()
    
    mock_req = MockRequest(headers={
        "Authorization": "Bearer mocked_token",
        "X-API-Key": ""
    })
    
    chat_req = ChatRequest(
        message="what is the total revenue?",
        conversation_id="cc72214a-cf9d-471c-96b8-eff4f746a91d",
        connection_id=str(conn.id)
    )
    
    print("\nCalling chat_endpoint directly...")
    try:
        res = chat_endpoint(request=mock_req, chat_req=chat_req, db=db_sess)
        print("Response successful:", res)
    except Exception as e:
        print("Exception raised in chat_endpoint:")
        import traceback
        traceback.print_exc()
        
    db_sess.close()
    s.close()

if __name__ == '__main__':
    run_chat_diagnostic()
