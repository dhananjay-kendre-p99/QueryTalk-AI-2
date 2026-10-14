from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import get_db, get_schema_info
from core.security import is_safe_query
from services.llm_orchestrator import llm_orchestrator

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/")
def chat_endpoint(request: Request, chat_req: ChatRequest, db: Session = Depends(get_db)):
    user_query = chat_req.message
    
    schema_info = get_schema_info()
    
    try:
        api_key = request.headers.get("X-API-Key")
        sql_query = llm_orchestrator.generate_sql(user_query, schema_info, api_key)
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
    
    except Exception as e:
        return {
            "reply": f"Error executing query: {str(e)}",
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
