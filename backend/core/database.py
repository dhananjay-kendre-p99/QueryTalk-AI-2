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


def set_engine(connection_string: str):
    """
    Set the active user database engine.
    Called when the user successfully connects a new database.
    """
    global _user_engine, _user_session_factory

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
                cols = [f"{c['name']} ({str(c['type'])})" for c in inspector.get_columns(table)]
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
    try:
        inspector = inspect(_user_engine)
        tables = inspector.get_table_names()
        lines = []
        for table in tables[:30]:
            cols = [f"{c['name']} ({str(c['type'])})" for c in inspector.get_columns(table)]
            lines.append(f"  {table} ({', '.join(cols)})")
        return "Tables:\n" + "\n".join(lines) if lines else "No tables found."
    except Exception as e:
        return f"Schema unavailable: {e}"


def get_db_dialect() -> str:
    """Return the dialect name of the currently connected user database."""
    if _user_engine is None:
        return "sqlite"
    try:
        return _user_engine.dialect.name
    except Exception:
        return "sqlite"


