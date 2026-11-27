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

@router.post("/")
def chat_endpoint(request: Request, chat_req: ChatRequest, db: Session = Depends(get_db)):
    user_query = chat_req.message
    
    # ── Auto-reconnect active database connection if reset to bootstrap ──
    import core.database as db_core
    from core.security import verify_clerk_token
    from fastapi.security import HTTPAuthorizationCredentials
    from core.models import User, DatabaseConnection
    from core.encryption import decrypt_password

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = verify_clerk_token(HTTPAuthorizationCredentials(credentials=token, scheme="Bearer"))
            clerk_user_id = payload.get("sub")
        except Exception:
            clerk_user_id = None
        
        if clerk_user_id:
            app_db = db_core.AppSessionLocal()
            try:
                user = app_db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
                if user:
                    is_bootstrap = db_core._user_engine is None or "demo.db" in str(db_core._user_engine.url)
                    if is_bootstrap:
                        active_conn = (
                            app_db.query(DatabaseConnection)
                            .filter(
                                DatabaseConnection.user_id == user.id,
                                DatabaseConnection.is_active == True
                            )
                            .order_by(DatabaseConnection.updated_at.desc())
                            .first()
                        )
                        if active_conn:
                            conn_str = decrypt_password(active_conn.connection_string_enc)
                            if conn_str:
                                db_core.set_engine(conn_str, connection_id=str(active_conn.id))
                                db = db_core.SessionLocal()
            finally:
                app_db.close()

    schema_info = get_schema_info()
    dialect = get_dialect_name()
    
    try:
        api_key = request.headers.get("X-API-Key")
        sql_query = llm_orchestrator.generate_sql(user_query, schema_info, dialect, api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation Error: {str(e)}")

    # Intercept schema mismatch / unrelated question responses
    sql_lower = sql_query.lower().strip()
    if "cannot answer" in sql_lower or "not related" in sql_lower:
        return {
            "reply": "I'm sorry, but your question does not seem to be related to the available database schema. Please ask a question about the data in the database.",
            "sql": None,
            "data": None
        }

    max_retries = 2
    retry_count = 0
    success = False
    last_error = None
    data = None

    while retry_count <= max_retries and not success:
        if not is_safe_query(sql_query):
            return {
                "reply": "I'm sorry, but I cannot execute that query due to security restrictions.",
                "sql": None,
                "data": None
            }
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
                    last_error = f"Error executing query: {last_error} (Correction failed: {str(llm_err)})"
                    break
            else:
                last_error = f"Error executing query: {last_error}"

    if not success:
        return {
            "reply": last_error,
            "sql": None,
            "data": None
        }

    try:
        api_key = request.headers.get("X-API-Key")
        summary = llm_orchestrator.summarize_results(user_query, sql_query, data[:10], api_key)
    except Exception as e:
        summary = "Could not generate summary due to LLM error."

    return {
        "reply": summary,
        "sql": sql_query,
        "data": data
    }
