"""
routes/database.py — Database connection management.

Endpoints:
  POST   /api/db/test               — Test a connection and return schema preview
  POST   /api/db/connect            — Connect + persist connection to app DB
  POST   /api/db/reconnect/{id}     — Re-activate a saved connection by ID
  GET    /api/db/saved              — List the user's saved connections
  DELETE /api/db/saved/{id}         — Delete a saved connection by ID
  GET    /api/db/status             — Return current connection status
  GET    /api/db/schema             — Return schema of the connected user DB
  POST   /api/db/test               — Test a connection and return schema preview
  POST   /api/db/connect            — Connect + persist connection to app DB
  POST   /api/db/reconnect/{id}     — Re-activate a saved connection by ID
  GET    /api/db/saved              — List the user's saved connections
  DELETE /api/db/saved/{id}         — Delete a saved connection by ID
  GET    /api/db/status             — Return current connection status
  GET    /api/db/schema             — Return schema of the connected user DB
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import core.database as db_core
from core.database import set_engine, test_engine, get_app_db
from core.encryption import encrypt_password, decrypt_password
from core.models import User, DatabaseConnection
from core.security import verify_clerk_token


router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class DBConnectionRequest(BaseModel):
    name:     Optional[str] = None   # friendly label (auto-generated if omitted)
    db_type:  str
    host:     Optional[str] = None
    port:     Optional[int] = None
    db_name:  str
    username: Optional[str] = None
    password: Optional[str] = None


class SavedConnectionResponse(BaseModel):
    id:            str
    name:          str
    db_type:       str
    host_hint:     Optional[str]
    db_name_hint:  Optional[str]
    is_active:     bool
    created_at:    datetime
    updated_at:    datetime

    class Config:
        from_attributes = True


class TableNameResponse(BaseModel):
    status: str
    connection_id: str
    tables: list[str]
    count: int


class ColumnSchemaResponse(BaseModel):
    name: str
    type: str
    nullable: bool
    default: Optional[str] = None
    primary_key: bool = False


class ForeignKeyResponse(BaseModel):
    constrained_columns: list[str]
    referred_schema: Optional[str] = None
    referred_table: Optional[str] = None
    referred_columns: list[str]


class IndexResponse(BaseModel):
    name: str
    columns: list[str]
    unique: bool = False


class TableSchemaResponse(BaseModel):
    name: str
    schema_name: Optional[str] = None
    full_name: str
    columns: list[ColumnSchemaResponse]
    primary_key: list[str]
    foreign_keys: list[ForeignKeyResponse]
    indexes: list[IndexResponse]


class DatabaseSchemaResponse(BaseModel):
    status: str
    connection_id: str
    tables: list[TableSchemaResponse]
    count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_connection_string(req: DBConnectionRequest) -> str:
    """Build a SQLAlchemy connection string from the request fields."""
    if req.db_type.lower() == "sqlite":
        return f"sqlite:///./{req.db_name}" if req.db_name else "sqlite:///./demo.db"

    if not all([req.host, req.db_name, req.username, req.password]):
        raise HTTPException(
            status_code=400,
            detail="Missing required connection parameters (host, db_name, username, password).",
        )

    port_str = f":{req.port}" if req.port else ""
    db_type = req.db_type.lower()

    if db_type == "postgresql":
        return f"postgresql://{req.username}:{req.password}@{req.host}{port_str}/{req.db_name}"
    elif db_type == "mysql":
        return f"mysql+pymysql://{req.username}:{req.password}@{req.host}{port_str}/{req.db_name}"
    elif db_type == "mysql":
        return f"mysql+pymysql://{req.username}:{req.password}@{req.host}{port_str}/{req.db_name}"
    elif db_type == "snowflake":
        # Snowflake URL format:
        # snowflake://<username>:<password>@<account_identifier>/<database_name>/<schema_name>?warehouse=<warehouse_name>&role=<role_name>
        # mapping 'host' to account_identifier
        return f"snowflake://{req.username}:{req.password}@{req.host}/{req.db_name}"

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported database type: {req.db_type}")


def _resolve_user(clerk_user_id: str, db: Session) -> User:
    """Look up the User row by Clerk ID. Auto-provisions if not found for easy local dev."""
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user:
        print(f"User with Clerk ID '{clerk_user_id}' not found in database. Auto-provisioning local user row...")
        try:
            user = User(
                clerk_user_id=clerk_user_id,
                email=f"clerk_{clerk_user_id}@example.com",
                display_name=f"Local User ({clerk_user_id[-6:] if len(clerk_user_id) > 6 else clerk_user_id})",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Successfully auto-provisioned user row for Clerk ID: {clerk_user_id}")
        except Exception as e:
            db.rollback()
            print(f"Failed to auto-provision user: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to auto-provision user: {e}"
            )
    return user


def _parse_connection_uuid(connection_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(connection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connection ID format.")


def _get_user_connection(connection_id: str, user: User, app_db: Session) -> DatabaseConnection:
    conn_uuid = _parse_connection_uuid(connection_id)
    conn = (
        app_db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == conn_uuid,
            DatabaseConnection.user_id == user.id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")
    return conn


def _connect_args_for(connection_string: str) -> dict[str, Any]:
    connect_args: dict[str, Any] = {}
    if connection_string.startswith("postgresql") and "sslmode" not in connection_string:
        connect_args["sslmode"] = "prefer"
    return connect_args


def _table_full_name(table_name: str, schema_name: Optional[str]) -> str:
    return f"{schema_name}.{table_name}" if schema_name else table_name


def _split_table_name(table: str) -> tuple[Optional[str], str]:
    if "." not in table:
        return None, table
    schema_name, table_name = table.split(".", 1)
    return schema_name or None, table_name


def _get_table_names_from_connection(connection_string: str) -> list[str]:
    engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        connect_args=_connect_args_for(connection_string),
    )
    try:
        inspector = inspect(engine)
        return [
            _table_full_name(table_name, schema_name)
            for schema_name, table_name in _iter_user_tables(inspector)
        ]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"Failed to inspect database: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to inspect database: {e}") from e
    finally:
        engine.dispose()


def _get_schema_from_connection(
    connection_string: str,
    table_filter: Optional[str] = None,
) -> list[TableSchemaResponse]:
    engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        connect_args=_connect_args_for(connection_string),
    )
    try:
        inspector = inspect(engine)
        selected_schema, selected_table = _split_table_name(table_filter) if table_filter else (None, None)
        tables = []

        for schema_name, table_name in _iter_user_tables(inspector):
            if selected_table and table_name != selected_table:
                continue
            if selected_schema is not None and schema_name != selected_schema:
                continue

            primary_key = (
                (inspector.get_pk_constraint(table_name, schema=schema_name) or {})
                .get("constrained_columns", [])
            )
            pk_columns = set(primary_key)
            columns = [
                ColumnSchemaResponse(
                    name=column["name"],
                    type=str(column["type"]),
                    nullable=bool(column.get("nullable", True)),
                    default=str(column["default"]) if column.get("default") is not None else None,
                    primary_key=column["name"] in pk_columns,
                )
                for column in inspector.get_columns(table_name, schema=schema_name)
            ]
            foreign_keys = [
                ForeignKeyResponse(
                    constrained_columns=fk.get("constrained_columns") or [],
                    referred_schema=fk.get("referred_schema"),
                    referred_table=fk.get("referred_table"),
                    referred_columns=fk.get("referred_columns") or [],
                )
                for fk in inspector.get_foreign_keys(table_name, schema=schema_name)
            ]
            indexes = [
                IndexResponse(
                    name=index.get("name") or "",
                    columns=index.get("column_names") or [],
                    unique=bool(index.get("unique", False)),
                )
                for index in inspector.get_indexes(table_name, schema=schema_name)
            ]
            tables.append(
                TableSchemaResponse(
                    name=table_name,
                    schema_name=schema_name,
                    full_name=_table_full_name(table_name, schema_name),
                    columns=columns,
                    primary_key=primary_key,
                    foreign_keys=foreign_keys,
                    indexes=indexes,
                )
            )

        if table_filter and not tables:
            raise HTTPException(status_code=404, detail=f"Table '{table_filter}' not found.")

        return tables
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"Failed to inspect database: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to inspect database: {e}") from e
    finally:
        engine.dispose()


def _iter_user_tables(inspector):
    default_schema = inspector.default_schema_name
    dialect_name = inspector.bind.dialect.name

    if dialect_name in {"mysql", "sqlite"}:
        schema_names = [default_schema]
    else:
        try:
            schema_names = inspector.get_schema_names()
        except SQLAlchemyError:
            schema_names = [default_schema]

    user_schemas = [
        schema_name
        for schema_name in schema_names
        if schema_name not in {"information_schema", "pg_catalog"}
        and not (schema_name or "").startswith("pg_toast")
        and not (schema_name or "").startswith("pg_temp")
    ] or [None]

    # Prioritize default schema first so its tables are listed first
    if default_schema in user_schemas:
        user_schemas = [s for s in user_schemas if s != default_schema]
        user_schemas.insert(0, default_schema)
    elif default_schema is not None:
        user_schemas.insert(0, default_schema)

    for schema_name in user_schemas:
        effective_schema = None if schema_name == default_schema else schema_name
        try:
            table_names = inspector.get_table_names(schema=effective_schema)
        except SQLAlchemyError:
            continue
        for table_name in table_names:
            yield effective_schema, table_name


# ---------------------------------------------------------------------------
# POST /test — test connection without saving
# ---------------------------------------------------------------------------

@router.post("/test")
def test_db_connection(
    request: DBConnectionRequest,
    payload: dict = Depends(verify_clerk_token),
):
    """Test a database connection and return a schema preview."""
    conn_str = build_connection_string(request)
    try:
        schema_info = test_engine(conn_str)
        return {"status": "success", "message": "Connection successful", "schema": schema_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {e}")


# ---------------------------------------------------------------------------
# POST /connect — connect and persist connection
# ---------------------------------------------------------------------------

@router.post("/connect")
def connect_db(
    request: DBConnectionRequest,
    app_db: Session = Depends(get_app_db),
    payload: dict = Depends(verify_clerk_token),
):
    """
    Connect to the user's database engine (in-memory) and persist the
    connection details to the app database.
    """
    conn_str = build_connection_string(request)

    # 1. Verify the connection is actually reachable
    try:
        test_engine(conn_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {e}")

    # 2. Set the in-memory engine for this session
    set_engine(conn_str)

    # 3. Resolve the user from the Clerk token
    clerk_user_id = payload["sub"]
    user = _resolve_user(clerk_user_id, app_db)

    # 4. Encrypt the full connection string
    conn_str_enc = encrypt_password(conn_str)

    # 5. Auto-generate a name if not provided
    conn_name = request.name or f"{request.db_type} — {request.db_name}"

    # 6. Check for an existing connection with the same name for this user
    existing = (
        app_db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.user_id == user.id,
            DatabaseConnection.name == conn_name,
        )
        .first()
    )

    if existing:
        # Upsert — update the existing record
        existing.db_type = request.db_type
        existing.connection_string_enc = conn_str_enc
        existing.host_hint = request.host
        existing.db_name_hint = request.db_name
        existing.is_active = True
        existing.updated_at = datetime.utcnow()
        connection_id = str(existing.id)
    else:
        connection = DatabaseConnection(
            user_id=user.id,
            name=conn_name,
            db_type=request.db_type,
            connection_string_enc=conn_str_enc,
            host_hint=request.host,
            db_name_hint=request.db_name,
            is_active=True,
        )
        app_db.add(connection)
        app_db.flush()
        connection_id = str(connection.id)

    app_db.commit()
    set_engine(conn_str, connection_id=connection_id)

    return {
        "status": "success",
        "message": f"Connected to '{request.db_name}' and connection saved.",
        "connection_id": connection_id,
    }


# ---------------------------------------------------------------------------
# POST /reconnect/{connection_id} — re-activate a saved connection
# ---------------------------------------------------------------------------

@router.post("/reconnect/{connection_id}")
def reconnect_db(
    connection_id: str,
    app_db: Session = Depends(get_app_db),
    payload: dict = Depends(verify_clerk_token),
):
    """
    Re-activate a previously saved database connection.
    Decrypts the stored connection string and sets the in-memory engine.
    """
    clerk_user_id = payload["sub"]
    user = _resolve_user(clerk_user_id, app_db)

    try:
        conn_uuid = uuid.UUID(connection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connection ID format.")

    conn = (
        app_db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == conn_uuid,
            DatabaseConnection.user_id == user.id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")

    # Decrypt the stored connection string
    conn_str = decrypt_password(conn.connection_string_enc)
    if not conn_str:
        raise HTTPException(
            status_code=500,
            detail="Could not decrypt connection string. The encryption key may have changed.",
        )

    # Verify the connection is still reachable
    try:
        test_engine(conn_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Reconnection failed: {e}")

    # Set the in-memory engine
    set_engine(conn_str, connection_id=str(conn.id))

    # Update the timestamp
    conn.updated_at = datetime.utcnow()
    app_db.commit()

    return {
        "status": "success",
        "message": f"Reconnected to '{conn.name}'.",
        "connection_id": str(conn.id),
        "name": conn.name,
        "db_type": conn.db_type,
    }


# ---------------------------------------------------------------------------
# GET /saved — list the user's saved connections
# ---------------------------------------------------------------------------

@router.get("/saved", response_model=list[SavedConnectionResponse])
def get_saved_connections(
    app_db: Session = Depends(get_app_db),
    payload: dict = Depends(verify_clerk_token),
):
    """
    Return all saved database connections for the authenticated user.
    Connection strings are never returned — only metadata hints.
    """
    clerk_user_id = payload["sub"]
    user = _resolve_user(clerk_user_id, app_db)

    connections = (
        app_db.query(DatabaseConnection)
        .filter(DatabaseConnection.user_id == user.id)
        .order_by(DatabaseConnection.updated_at.desc())
        .all()
    )

    return [
        SavedConnectionResponse(
            id=str(c.id),
            name=c.name,
            db_type=c.db_type,
            host_hint=c.host_hint,
            db_name_hint=c.db_name_hint,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in connections
    ]


# ---------------------------------------------------------------------------
# GET /connections/{connection_id}/tables - table names for a saved database
# ---------------------------------------------------------------------------

@router.get("/connections/{connection_id}/tables", response_model=TableNameResponse)
def get_connection_table_names(
    connection_id: str,
    app_db: Session = Depends(get_app_db),
    payload: dict = Depends(verify_clerk_token),
):
    """Return table names for a specific saved database connection."""
    clerk_user_id = payload["sub"]
    user = _resolve_user(clerk_user_id, app_db)
    conn = _get_user_connection(connection_id, user, app_db)

    conn_str = decrypt_password(conn.connection_string_enc)
    if not conn_str:
        raise HTTPException(
            status_code=500,
            detail="Could not decrypt connection string. The encryption key may have changed.",
        )

    if conn.schema_cache:
        tables = [t.get("full_name") or t.get("name") for t in conn.schema_cache]
    else:
        tables = _get_table_names_from_connection(conn_str)
    return {
        "status": "success",
        "connection_id": str(conn.id),
        "tables": tables,
        "count": len(tables),
    }


# ---------------------------------------------------------------------------
# GET /connections/{connection_id}/schema - structured schema for saved database
# ---------------------------------------------------------------------------

@router.get("/connections/{connection_id}/schema", response_model=DatabaseSchemaResponse)
def get_connection_schema(
    connection_id: str,
    table: Optional[str] = Query(
        default=None,
        description="Optional table name. Use schema.table for non-default schemas.",
    ),
    refresh: bool = Query(
        default=False,
        description="If True, bypass schema cache and update it with a fresh database inspection.",
    ),
    app_db: Session = Depends(get_app_db),
    payload: dict = Depends(verify_clerk_token),
):
    """
    Return structured table schema for a specific saved database connection.
    Pass ?table=table_name or ?table=schema.table to limit the response.
    """
    clerk_user_id = payload["sub"]
    user = _resolve_user(clerk_user_id, app_db)
    conn = _get_user_connection(connection_id, user, app_db)

    conn_str = decrypt_password(conn.connection_string_enc)
    if not conn_str:
        raise HTTPException(
            status_code=500,
            detail="Could not decrypt connection string. The encryption key may have changed.",
        )

    # Use cached schema if available and not requesting a refresh
    if not refresh and conn.schema_cache is not None:
        cached_tables = conn.schema_cache
        if table:
            selected_schema, selected_table = _split_table_name(table)
            filtered_tables = []
            for t in cached_tables:
                t_name = t.get("name")
                t_schema = t.get("schema_name")
                if selected_table and t_name != selected_table:
                    continue
                if selected_schema is not None and t_schema != selected_schema:
                    continue
                filtered_tables.append(t)
            if not filtered_tables:
                raise HTTPException(status_code=404, detail=f"Table '{table}' not found in cached schema.")
            tables_to_return = filtered_tables
        else:
            tables_to_return = cached_tables
    else:
        # Fetch the entire schema to populate the cache
        tables_list = _get_schema_from_connection(conn_str, table_filter=None)
        
        # Serialize the tables list (Pydantic models) to dicts for JSONB storage
        serialized_tables = []
        for t in tables_list:
            if hasattr(t, "model_dump"):
                serialized_tables.append(t.model_dump())
            else:
                serialized_tables.append(t.dict())

        # Update cache and timestamp
        conn.schema_cache = serialized_tables
        conn.schema_synced_at = datetime.utcnow()
        app_db.commit()

        # Filter the tables list if a specific table was requested
        if table:
            selected_schema, selected_table = _split_table_name(table)
            tables_to_return = []
            for t in tables_list:
                if selected_table and t.name != selected_table:
                    continue
                if selected_schema is not None and t.schema_name != selected_schema:
                    continue
                tables_to_return.append(t)
            if not tables_to_return:
                raise HTTPException(status_code=404, detail=f"Table '{table}' not found.")
        else:
            tables_to_return = tables_list

    return {
        "status": "success",
        "connection_id": str(conn.id),
        "tables": tables_to_return,
        "count": len(tables_to_return),
    }


# ---------------------------------------------------------------------------
# DELETE /saved/{connection_id} — delete a saved connection
# ---------------------------------------------------------------------------

@router.delete("/saved/{connection_id}")
def delete_saved_connection(
    connection_id: str,
    app_db: Session = Depends(get_app_db),
    payload: dict = Depends(verify_clerk_token),
):
    """Delete a specific saved database connection."""
    clerk_user_id = payload["sub"]
    user = _resolve_user(clerk_user_id, app_db)

    try:
        conn_uuid = uuid.UUID(connection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connection ID format.")

    conn = (
        app_db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == conn_uuid,
            DatabaseConnection.user_id == user.id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")

    app_db.delete(conn)
    app_db.commit()
    return {"status": "deleted", "message": "Saved connection removed."}


# ---------------------------------------------------------------------------
# GET /status — connection status (no sensitive data)
# ---------------------------------------------------------------------------

@router.get("/status")
def get_db_status(payload: dict = Depends(verify_clerk_token)):
    """Return whether a user database is currently connected in-memory."""
    is_connected = db_core._user_engine is not None
    return {
        "status": "connected" if is_connected else "disconnected",
    }


# ---------------------------------------------------------------------------
# GET /schema — schema of the connected user database
# ---------------------------------------------------------------------------

@router.get("/schema")
def get_current_schema(payload: dict = Depends(verify_clerk_token)):
    """Return schema information for the currently connected user database."""
    try:
        from core.database import get_schema_info
        schema_info = get_schema_info()
        return {"status": "success", "schema": schema_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch schema: {e}")


import random
from sqlalchemy import text
from datetime import datetime, date, timedelta

@router.get("/analytics")
def get_analytics(
    app_db: Session = Depends(get_app_db),
    payload: dict = Depends(verify_clerk_token),
):
    clerk_user_id = payload["sub"]
    user = _resolve_user(clerk_user_id, app_db)
    
    from core.database import _active_connection_id, SessionLocal, get_schema_info, get_dialect_name
    from sqlalchemy import text
    from datetime import datetime
    import json
    import re
    
    if not _active_connection_id:
        return {"fallback": True, "message": "No active database connection."}
        
    try:
        session = SessionLocal()
    except Exception as e:
        return {"fallback": True, "message": f"Failed to connect to database: {e}"}
        
    schema_info = get_schema_info()
    dialect = get_dialect_name()
    
    # Prompt the LLM to generate standard SQL queries that conform to the target dashboard format
    system_prompt = f"""You are a data analytics expert. Your task is to analyze a database schema and output a valid JSON containing SQL queries that fetch metrics for an interactive analytics dashboard.
The user's database dialect is: {dialect}.

The schema of the connected database is:
{schema_info}

You MUST return a JSON object with the following exact keys:
1. "totalRevenueQuery": A SQL query that returns a single numeric value (e.g. SUM of transaction/sales amount, or COUNT of main entities if there is no numeric column).
2. "activeCustomersQuery": A SQL query that returns a single numeric count of active entities (e.g. COUNT of distinct customer IDs, or COUNT of distinct groups/categories).
3. "monthlySalesQuery": A SQL query that returns a single numeric count of recent transactions (e.g. COUNT of orders in the last 30 days, or COUNT of records created recently).
4. "growthPctQuery": A SQL query that returns a single numeric percentage value representing growth. If hard to calculate, return a static float.
5. "growthDataQuery": A SQL query that returns rows with columns: "name_val" (string, representing month/date/category) and "current_val" (numeric, representing value) and "projected_val" (numeric). Max 12 rows.
6. "marketShareQuery": A SQL query that returns rows with columns: "name_val" (string, representing segment/region/category) and "value_val" (numeric, representing percentage/count). Max 5 rows.
7. "revenueRegionQuery": A SQL query that returns rows with columns: "name_val" (string, representing region/category) and "value_val" (numeric, representing revenue/count). Max 5 rows.
8. "customerSegmentsQuery": A SQL query that returns rows with columns: "x_val" (numeric value), "y_val" (numeric value), "z_val" (numeric size value), and "group_val" (string or integer, representing category/segment). Max 100 rows.

Instructions:
- If the schema represents a sales/business/orders database, write standard business queries on the orders/sales/users tables.
- If the schema is completely different (e.g., library, employee registry, movies), creatively map the dashboard metrics to the available tables. For example, for an employee database, totalRevenue can be the sum of salaries or count of employees, activeCustomers can be the number of departments, monthlySales can be the number of hires in the last month, growthData can be employee hiring over time, marketShare can be employee count by department, customerSegments can compare experience (x_val) vs salary (y_val).
- The SQL queries must be valid for the {dialect} dialect.
- Use simple, standard SQL features. Avoid vendor-specific complex functions.
- DO NOT use double quotes or backticks to quote identifiers unless absolutely necessary (for instance, to preserve spacing).
- CRITICAL: "x_val", "y_val", and "z_val" MUST ALWAYS BE numeric columns (such as balances, salaries, ages, transaction counts, sums). NEVER map a string/text column (like market segment or names) to "x_val", "y_val", or "z_val" as this will crash the visualization.
- Return ONLY a JSON object with the queries. Do NOT return any markdown wrapping (no ```json or ```)."""

    try:
        from services.llm_orchestrator import llm_orchestrator
        client = llm_orchestrator.client
        if not client:
            session.close()
            return {"fallback": True, "message": "Groq client not initialized."}
            
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate the SQL queries in JSON format."}
            ],
            temperature=0.1,
            max_tokens=1536
        )
        
        content = response.choices[0].message.content.strip()
        
        # Robustly extract JSON using regex
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
            
        queries = json.loads(content)
        
        # Execute queries
        kpis = {}
        # 1. Total revenue
        try:
            kpis["totalRevenue"] = float(session.execute(text(queries["totalRevenueQuery"])).scalar() or 0)
        except Exception as e:
            print(f"Error totalRevenueQuery: {e}")
            kpis["totalRevenue"] = 0.0
            
        # 2. Active Customers
        try:
            kpis["activeCustomers"] = int(session.execute(text(queries["activeCustomersQuery"])).scalar() or 0)
        except Exception as e:
            print(f"Error activeCustomersQuery: {e}")
            kpis["activeCustomers"] = 0
            
        # 3. Monthly Sales
        try:
            kpis["monthlySales"] = int(session.execute(text(queries["monthlySalesQuery"])).scalar() or 0)
        except Exception as e:
            print(f"Error monthlySalesQuery: {e}")
            kpis["monthlySales"] = 0
            
        # 4. Growth Pct
        try:
            kpis["growthPct"] = float(session.execute(text(queries["growthPctQuery"])).scalar() or 0)
        except Exception as e:
            print(f"Error growthPctQuery: {e}")
            kpis["growthPct"] = 0.0
            
        # 5. Growth Data
        growth_data = []
        try:
            res = session.execute(text(queries["growthDataQuery"]))
            keys = [k.lower().replace('"', '') for k in res.keys()]
            for row in res.fetchall():
                row_dict = dict(zip(keys, row))
                growth_data.append({
                    "name": str(row_dict.get("name_val") or row_dict.get("name") or ""),
                    "current": float(row_dict.get("current_val") or row_dict.get("current") or 0),
                    "projected": float(row_dict.get("projected_val") or row_dict.get("projected") or (row_dict.get("current_val") or row_dict.get("current") or 0) * 1.1)
                })
        except Exception as e:
            print(f"Error growthDataQuery: {e}")
            
        # 6. Market Share Data
        market_share_data = []
        colors = ['#40CCB7', '#df7412', '#00a2e6', '#93000a', '#ffb786']
        try:
            res = session.execute(text(queries["marketShareQuery"]))
            keys = [k.lower().replace('"', '') for k in res.keys()]
            for idx, row in enumerate(res.fetchall()):
                row_dict = dict(zip(keys, row))
                market_share_data.append({
                    "name": str(row_dict.get("name_val") or row_dict.get("name") or ""),
                    "value": float(row_dict.get("value_val") or row_dict.get("value") or 0),
                    "color": colors[idx % len(colors)]
                })
        except Exception as e:
            print(f"Error marketShareQuery: {e}")
            
        # 7. Revenue Region Data
        revenue_region_data = []
        try:
            res = session.execute(text(queries["revenueRegionQuery"]))
            keys = [k.lower().replace('"', '') for k in res.keys()]
            for row in res.fetchall():
                row_dict = dict(zip(keys, row))
                revenue_region_data.append({
                    "name": str(row_dict.get("name_val") or row_dict.get("name") or ""),
                    "value": float(row_dict.get("value_val") or row_dict.get("value") or 0)
                })
        except Exception as e:
            print(f"Error revenueRegionQuery: {e}")
            
        # 8. Customer Segments Data
        customer_segments_data = []
        try:
            res = session.execute(text(queries["customerSegmentsQuery"]))
            keys = [k.lower().replace('"', '') for k in res.keys()]
            for row in res.fetchall():
                row_dict = dict(zip(keys, row))
                customer_segments_data.append({
                    "x": float(row_dict.get("x_val") or row_dict.get("x") or 0),
                    "y": float(row_dict.get("y_val") or row_dict.get("y") or 0),
                    "z": float(row_dict.get("z_val") or row_dict.get("z") or 200),
                    "group": row_dict.get("group_val") or row_dict.get("group") or "Segment"
                })
        except Exception as e:
            print(f"Error customerSegmentsQuery: {e}")
            
        session.close()
        
        # We always return the real database analytics (fallback: False) if the connection is active and queries executed successfully
        return {
            "fallback": False,
            "kpis": kpis,
            "growthData": growth_data,
            "marketShareData": market_share_data,
            "revenueRegionData": revenue_region_data,
            "customerSegmentsData": customer_segments_data
        }
        
    except Exception as e:
        print(f"Error in get_analytics: {e}")
        if 'session' in locals():
            session.close()
        return {"fallback": True}
