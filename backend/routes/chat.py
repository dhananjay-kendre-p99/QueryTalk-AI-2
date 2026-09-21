from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import get_db, get_schema_info, get_dialect_name
from core.security import is_safe_query
from services.llm_orchestrator import llm_orchestrator

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: str
    connection_id: str

@router.get("/conversations")
def get_conversations(
    request: Request,
    connection_id: str,
):
    import core.database as db_core
    from core.security import verify_clerk_token
    from fastapi.security import HTTPAuthorizationCredentials
    from core.models import User, Conversation
    from routes.database import _resolve_user
    import uuid

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        payload = verify_clerk_token(HTTPAuthorizationCredentials(credentials=token, scheme="Bearer"))
        clerk_user_id = payload.get("sub")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Authentication failed")

    try:
        connection_uuid = uuid.UUID(connection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connection ID format.")

    app_db = db_core.AppSessionLocal()
    try:
        user = _resolve_user(clerk_user_id, app_db)
        
        conversations = (
            app_db.query(Conversation)
            .filter(
                Conversation.user_id == user.id,
                Conversation.connection_id == connection_uuid
            )
            .order_by(Conversation.updated_at.desc())
            .all()
        )
        
        result = []
        for c in conversations:
            sorted_messages = sorted(c.messages, key=lambda m: m.created_at)
            result.append({
                "id": str(c.id),
                "title": c.title,
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "sql": m.sql_generated,
                        "data": m.query_result
                    }
                    for m in sorted_messages
                ]
            })
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")
    finally:
        app_db.close()


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    request: Request,
    conversation_id: str,
):
    import core.database as db_core
    from core.security import verify_clerk_token
    from fastapi.security import HTTPAuthorizationCredentials
    from core.models import User, Conversation, Message
    from routes.database import _resolve_user
    import uuid

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        payload = verify_clerk_token(HTTPAuthorizationCredentials(credentials=token, scheme="Bearer"))
        clerk_user_id = payload.get("sub")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Authentication failed")

    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format.")

    app_db = db_core.AppSessionLocal()
    try:
        user = _resolve_user(clerk_user_id, app_db)
        
        conversation = (
            app_db.query(Conversation)
            .filter(
                Conversation.id == conv_uuid,
                Conversation.user_id == user.id
            )
            .first()
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
            
        app_db.query(Message).filter(Message.conversation_id == conv_uuid).delete()
        app_db.delete(conversation)
        app_db.commit()
        
        return {"status": "success", "message": "Conversation deleted."}
    except HTTPException:
        raise
    except Exception as e:
        app_db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")
    finally:
        app_db.close()


@router.post("/")
def chat_endpoint(request: Request, chat_req: ChatRequest, db: Session = Depends(get_db)):
    user_query = chat_req.message
    
    import core.database as db_core
    from core.security import verify_clerk_token
    from fastapi.security import HTTPAuthorizationCredentials
    from core.models import User, DatabaseConnection, Conversation, Message
    from routes.database import _resolve_user
    from core.encryption import decrypt_password
    from datetime import datetime
    import uuid

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        payload = verify_clerk_token(HTTPAuthorizationCredentials(credentials=token, scheme="Bearer"))
        clerk_user_id = payload.get("sub")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Authentication failed")

    app_db = db_core.AppSessionLocal()
    try:
        user = _resolve_user(clerk_user_id, app_db)
        
        try:
            conv_uuid = uuid.UUID(chat_req.conversation_id)
            conn_uuid = uuid.UUID(chat_req.connection_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid conversation or connection ID format.")
            
        conn = (
            app_db.query(DatabaseConnection)
            .filter(
                DatabaseConnection.id == conn_uuid,
                DatabaseConnection.user_id == user.id,
            )
            .first()
        )
        if not conn:
            raise HTTPException(status_code=404, detail="Database connection not found.")
            
        # Reconnect dynamic user engine if needed
        is_bootstrap = (
            db_core._user_engine is None or 
            "demo.db" in str(db_core._user_engine.url) or 
            db_core._active_connection_id != str(conn_uuid)
        )
        if is_bootstrap:
            conn_str = decrypt_password(conn.connection_string_enc)
            if conn_str:
                db_core.set_engine(conn_str, connection_id=str(conn_uuid))
                db = db_core.SessionLocal()
            else:
                raise HTTPException(status_code=500, detail="Could not decrypt connection string.")
                
        # Find or create Conversation
        conversation = (
            app_db.query(Conversation)
            .filter(
                Conversation.id == conv_uuid,
                Conversation.user_id == user.id,
            )
            .first()
        )
        
        if not conversation:
            title = chat_req.message[:30] + "..." if len(chat_req.message) > 30 else chat_req.message
            conversation = Conversation(
                id=conv_uuid,
                user_id=user.id,
                connection_id=conn_uuid,
                title=title
            )
            app_db.add(conversation)
            app_db.flush()
    except HTTPException:
        app_db.close()
        raise
    except Exception as e:
        app_db.rollback()
        app_db.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        app_db.close()

    # Now run the SQL generation, execution, and summarization in a safe block
    sql_query = None
    summary = None
    data = None
    error_occurred = False
    error_message = None

    try:
        schema_info = get_schema_info()
        dialect = get_dialect_name()
        
        try:
            api_key = request.headers.get("X-API-Key")
            sql_query = llm_orchestrator.generate_sql(user_query, schema_info, dialect, api_key)
        except Exception as e:
            error_occurred = True
            err_str = str(e).lower()
            if "429" in err_str or "rate" in err_str:
                error_message = "Rate limit reached for the AI service. Please wait a moment and try again."
            else:
                error_message = "An error occurred while generating the SQL query. Please try again."
            
        if not error_occurred:
            sql_lower = sql_query.lower().strip()
            if "cannot answer" in sql_lower or "not related" in sql_lower:
                error_occurred = True
                error_message = "I'm sorry, but your question does not seem to be related to the available database schema. Please ask a question about the data in the database."
                sql_query = None
                
        if not error_occurred:
            max_retries = 2
            retry_count = 0
            success = False
            last_error = None
            
            while retry_count <= max_retries and not success:
                if not is_safe_query(sql_query):
                    error_occurred = True
                    error_message = "I'm sorry, but I cannot execute that query due to security restrictions."
                    sql_query = None
                    break
                try:
                    result = db.execute(text(sql_query))
                    rows = result.fetchall()
                    columns = result.keys()
                    data = [dict(zip(columns, row)) for row in rows]
                    success = True
                except Exception as e:
                    last_error = str(e)
                    retry_count += 1
                    if retry_count <= max_retries:
                        try:
                            api_key = request.headers.get("X-API-Key")
                            sql_query = llm_orchestrator.correct_sql(
                                user_query=user_query,
                                schema_info=schema_info,
                                failed_sql=sql_query,
                                error_message=last_error,
                                dialect=dialect,
                                api_key=api_key
                            )
                        except Exception as llm_err:
                            llm_err_str = str(llm_err).lower()
                            if "429" in llm_err_str or "rate" in llm_err_str:
                                last_error = "Rate limit reached for the AI service. Please wait a moment and try again."
                            else:
                                last_error = f"Error executing query: {last_error} (Correction failed)"
                            break
                    else:
                        last_error = f"Error executing query: {last_error}"
                        
            if not success and not error_occurred:
                error_occurred = True
                error_message = last_error
                
        if not error_occurred:
            try:
                api_key = request.headers.get("X-API-Key")
                summary = llm_orchestrator.summarize_results(user_query, sql_query, data[:10], api_key)
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "rate" in err_str:
                    summary = "Rate limit reached for the AI service. Please wait a moment and try again."
                else:
                    summary = "Could not generate summary due to an AI service error. The SQL query succeeded but summary generation failed."
                
    except Exception as e:
        error_occurred = True
        err_str = str(e).lower()
        if "429" in err_str or "rate" in err_str:
            error_message = "Rate limit reached for the AI service. Please wait a moment and try again."
        else:
            error_message = "Internal server error processing request. Please try again."

    # Determine final response elements
    final_reply = error_message if error_occurred else summary
    final_sql = sql_query
    final_data = data

    # Save both user and assistant messages atomically
    try:
        app_db = db_core.AppSessionLocal()
        
        user_msg = Message(
            conversation_id=conv_uuid,
            role="user",
            content=chat_req.message
        )
        app_db.add(user_msg)
        
        assistant_msg = Message(
            conversation_id=conv_uuid,
            role="assistant",
            content=final_reply,
            sql_generated=final_sql,
            query_result=final_data
        )
        app_db.add(assistant_msg)
        
        conversation = app_db.query(Conversation).filter(Conversation.id == conv_uuid).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
            
        app_db.commit()
    except Exception as e:
        app_db.rollback()
        print(f"Error saving chat messages atomically to database: {e}")
    finally:
        app_db.close()

    return {
        "reply": final_reply,
        "sql": final_sql,
        "data": final_data
    }
