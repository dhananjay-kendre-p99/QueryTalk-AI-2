"""
core/database.py — SQLAlchemy engine, session, and schema helpers.

Two separate database contexts are maintained:
  1. app_engine / AppSessionLocal  — The Neon PostgreSQL database that stores
                                     the application's own data (credentials table, etc.)
  2. user_engine / SessionLocal    — The user's external database (SQLite, PG, MySQL)
                                     which is set dynamically via set_engine().
"""

import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

load_dotenv()


# ---------------------------------------------------------------------------
# 1. Application database (Neon PostgreSQL — stores credentials, etc.)
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///./demo.db",   # fallback for local dev without Neon
)

# psycopg2 doesn't accept the "postgres://" scheme used by some services
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # detect stale connections
    pool_size=5,
    max_overflow=10,
    connect_args={"sslmode": "require"} if "postgresql" in DATABASE_URL else {},
)

AppSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=app_engine,
)


def get_app_db():
    """FastAPI dependency — yields a session for the app's own Neon DB."""
    db = AppSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 2. User's external database (set dynamically at runtime)
# ---------------------------------------------------------------------------
_user_engine = None
_user_session_factory = None
_active_connection_id = None


def set_engine(connection_string: str, connection_id: str = None):
    """
    Set the active user database engine.
    Called when the user successfully connects a new database.
    """
    global _user_engine, _user_session_factory, _active_connection_id

    connect_args = {}
    if connection_string.startswith("postgresql") and "sslmode" not in connection_string:
        connect_args["sslmode"] = "prefer"

    _user_engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    _user_session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_user_engine,
    )
    _active_connection_id = connection_id


# Bootstrap with the default demo SQLite DB so the app always has an engine
set_engine("sqlite:///./demo.db")

# Convenient alias kept for backward compatibility with chat.py / database.py
SessionLocal = None  # set dynamically below


def _get_session_factory():
    return _user_session_factory


def get_db():
    """FastAPI dependency — yields a session for the user's connected database."""
    factory = _get_session_factory()
    if factory is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="No database connected. Please connect a database first.")
    db = factory()
    try:
        yield db
    finally:
        db.close()


# Alias for legacy code that uses SessionLocal directly
class _SessionProxy:
    """Proxy that always delegates to the current user session factory."""
    def __call__(self):
        factory = _get_session_factory()
        if factory is None:
            raise RuntimeError("No user database connected.")
        return factory()


SessionLocal = _SessionProxy()


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def test_engine(connection_string: str) -> str:
    """
    Test that a connection string is reachable and return a brief schema summary.
    Raises on failure so the caller can wrap it in an HTTPException.
    """
    connect_args = {}
    if connection_string.startswith("postgresql") and "sslmode" not in connection_string:
        connect_args["sslmode"] = "prefer"

    engine = create_engine(connection_string, connect_args=connect_args)
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            lines = []
            for table in tables[:20]:  # cap at 20 tables
                cols = [c["name"] for c in inspector.get_columns(table)]
                lines.append(f"  {table} ({', '.join(cols)})")
            return "Tables:\n" + "\n".join(lines) if lines else "No tables found."
    except OperationalError as e:
        raise RuntimeError(f"Cannot reach database: {e}") from e
    finally:
        engine.dispose()


def get_schema_info() -> str:
    """Return schema information for the currently connected user database."""
    if _user_engine is None:
        return "No database connected."

    global _active_connection_id
    if _active_connection_id:
        try:
            db = AppSessionLocal()
            try:
                from core.models import DatabaseConnection
                import uuid
                conn_uuid = uuid.UUID(_active_connection_id) if isinstance(_active_connection_id, str) else _active_connection_id
                conn = db.query(DatabaseConnection).filter(DatabaseConnection.id == conn_uuid).first()
                if conn and conn.schema_cache:
                    lines = []
                    for table in conn.schema_cache:
                        full_name = table.get("full_name") or table.get("name")
                        cols = [c["name"] for c in table.get("columns", [])]
                        lines.append(f"  {full_name} ({', '.join(cols)})")
                    if lines:
                        return "Tables:\n" + "\n".join(lines)
            finally:
                db.close()
        except Exception as e:
            print(f"Error reading schema cache in get_schema_info: {e}")

    try:
        inspector = inspect(_user_engine)
        default_schema = inspector.default_schema_name
        dialect_name = _user_engine.dialect.name

        if dialect_name in {"mysql", "sqlite"}:
            schema_names = [default_schema]
        else:
            try:
                schema_names = inspector.get_schema_names()
            except Exception:
                schema_names = [default_schema]

        user_schemas = [
            schema_name
            for schema_name in schema_names
            if schema_name not in {"information_schema", "pg_catalog"}
            and not (schema_name or "").startswith("pg_toast")
            and not (schema_name or "").startswith("pg_temp")
        ] or [None]

        # Prioritize default schema first so its tables are guaranteed to be listed first
        if default_schema in user_schemas:
            user_schemas = [s for s in user_schemas if s != default_schema]
            user_schemas.insert(0, default_schema)
        elif default_schema is not None:
            user_schemas.insert(0, default_schema)

        lines = []
        count = 0
        for schema_name in user_schemas:
            effective_schema = None if schema_name == default_schema else schema_name
            try:
                table_names = inspector.get_table_names(schema=effective_schema)
            except Exception:
                continue
            for table_name in table_names:
                if count >= 50:
                    break
                try:
                    cols = [c["name"] for c in inspector.get_columns(table_name, schema=effective_schema)]
                    full_name = f"{schema_name}.{table_name}" if effective_schema else table_name
                    lines.append(f"  {full_name} ({', '.join(cols)})")
                    count += 1
                except Exception:
                    continue
            if count >= 50:
                break

        return "Tables:\n" + "\n".join(lines) if lines else "No tables found."
    except Exception as e:
        return f"Schema unavailable: {e}"


def get_dialect_name() -> str:
    """Return the dialect name of the currently connected user database (e.g. 'sqlite', 'postgresql', 'mysql')."""
    global _user_engine
    if _user_engine is not None:
        return _user_engine.dialect.name
    return "sqlite"


