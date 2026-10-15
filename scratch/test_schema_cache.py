import sys
import os
import time

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from core.database import AppSessionLocal, set_engine, get_schema_info
from core.models import User, DatabaseConnection
from routes.database import _get_schema_from_connection

def main():
    print("Testing schema caching setup...")
    
    # 1. Fetch or create a user and a connection record
    db = AppSessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("No users found in database, creating a test user...")
            user = User(clerk_user_id="test_clerk_id", email="test@example.com", display_name="Test User")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # We will use the demo sqlite DB as connection for testing
        connection_name = "Test SQLite Connection"
        conn = db.query(DatabaseConnection).filter(DatabaseConnection.name == connection_name).first()
        if not conn:
            print("Creating test connection...")
            from core.encryption import encrypt_password
            conn = DatabaseConnection(
                user_id=user.id,
                name=connection_name,
                db_type="sqlite",
                connection_string_enc=encrypt_password("sqlite:///./backend/demo.db"),
                is_active=True
            )
            db.add(conn)
            db.commit()
            db.refresh(conn)
            
        print(f"Test connection ID: {conn.id}")
        
        # 2. Create a test table in backend/demo.db so we have something to inspect
        import sqlite3
        sqlite_conn = sqlite3.connect("backend/demo.db")
        sqlite_conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT);")
        sqlite_conn.commit()
        sqlite_conn.close()
        
        # 3. Test live schema fetching
        from core.encryption import decrypt_password
        conn_str = decrypt_password(conn.connection_string_enc)
        print(f"Decrypted connection string: {conn_str}")
        
        print("Bypassing cache to fetch and serialize schema...")
        tables_list = _get_schema_from_connection(conn_str, table_filter=None)
        print(f"Fetched {len(tables_list)} tables.")
        
        serialized_tables = []
        for t in tables_list:
            if hasattr(t, "model_dump"):
                serialized_tables.append(t.model_dump())
            else:
                serialized_tables.append(t.dict())
                
        # 3. Save cache
        conn.schema_cache = serialized_tables
        db.commit()
        db.refresh(conn)
        print("Schema cache successfully saved to DatabaseConnection!")
        
        # 4. Now, verify setting the engine with connection ID
        set_engine(conn_str, connection_id=str(conn.id))
        
        # 5. Measure time to get schema info using cache
        start_time = time.perf_counter()
        schema_info_cached = get_schema_info()
        duration_cached = time.perf_counter() - start_time
        print(f"Retrieved schema info via cache in {duration_cached:.6f} seconds.")
        
        # 6. Measure time to get schema info *without* cache (temp reset)
        set_engine(conn_str, connection_id=None)
        start_time = time.perf_counter()
        schema_info_live = get_schema_info()
        duration_live = time.perf_counter() - start_time
        print(f"Retrieved schema info live in {duration_live:.6f} seconds.")
        
        print(f"Speedup: {duration_live / duration_cached:.2f}x faster with cache.")
        
        assert "Tables:" in schema_info_cached, "Failed to get schema info from cache"
        print("Test passed successfully!")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
