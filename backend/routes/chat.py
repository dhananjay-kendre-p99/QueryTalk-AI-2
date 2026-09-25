from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import get_db, get_schema_info, get_db_dialect
from core.security import is_safe_query
from services.llm_orchestrator import llm_orchestrator

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/")
def chat_endpoint(request: Request, chat_req: ChatRequest, db: Session = Depends(get_db)):
    user_query = chat_req.message
    
    schema_info = get_schema_info()
    dialect = get_db_dialect()
    
    # Get all column names from the active database
    all_columns = []
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        for table_name in inspector.get_table_names():
            if table_name.startswith("sqlite_"):
                continue
            for col in inspector.get_columns(table_name):
                if col['name'] not in all_columns:
                    all_columns.append(col['name'])
    except Exception:
        pass

    if not all_columns:
        all_columns = [
            "Product_ID", "Sale_Date", "Sales_Rep", "Region", "Sales_Amount",
            "Quantity_Sold", "Product_Category", "Unit_Cost", "Unit_Price",
            "Customer_Type", "Discount", "Payment_Method", "Sales_Channel",
            "Region_and_Sales_Rep"
        ]

    try:
        from matcher import match_columns
        match_res = match_columns(user_query, all_columns)
    except Exception as e:
        print(f"Error in match_columns: {e}")
        match_res = {
            "matched_columns": all_columns,
            "keyword_matched": [],
            "semantic_matched": [],
            "fallback_used": True
        }

    try:
        api_key = request.headers.get("X-API-Key")
        sql_query = llm_orchestrator.generate_sql(user_query, schema_info, api_key, dialect=dialect)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation Error: {str(e)}")

    if not is_safe_query(sql_query):
        return {
            "reply": "I'm sorry, but I cannot execute that query due to security restrictions.",
            "sql": sql_query,
            "data": None,
            "columns": [],
            "rows": None,
            "error": "Security Restriction",
            "matched_columns": match_res["matched_columns"],
            "keyword_matched": match_res["keyword_matched"],
            "semantic_matched": match_res["semantic_matched"],
            "fallback_used": match_res["fallback_used"]
        }

    try:
        result = db.execute(text(sql_query))
        rows = result.fetchall()
        cols = list(result.keys())
        data = [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        return {
            "reply": f"Error executing query: {str(e)}",
            "sql": sql_query,
            "data": None,
            "columns": [],
            "rows": None,
            "error": str(e),
            "matched_columns": match_res["matched_columns"],
            "keyword_matched": match_res["keyword_matched"],
            "semantic_matched": match_res["semantic_matched"],
            "fallback_used": match_res["fallback_used"]
        }

    try:
        api_key = request.headers.get("X-API-Key")
        summary = llm_orchestrator.summarize_results(user_query, sql_query, data[:10], api_key)
    except Exception as e:
        summary = "Could not generate summary due to LLM error."

    return {
        "reply": summary,
        "sql": sql_query,
        "data": data,
        "columns": cols,
        "rows": data,
        "error": None,
        "matched_columns": match_res["matched_columns"],
        "keyword_matched": match_res["keyword_matched"],
        "semantic_matched": match_res["semantic_matched"],
        "fallback_used": match_res["fallback_used"]
    }
