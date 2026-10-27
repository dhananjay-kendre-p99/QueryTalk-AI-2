import sqlite3
import os

db_path = 'backend/demo.db'
if not os.path.exists(db_path):
    print(f"File not found: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    for table_name in tables:
        t_name = table_name[0]
        cursor.execute(f"PRAGMA table_info(\"{t_name}\");")
        cols = cursor.fetchall()
        print(f"Columns for {t_name}:", [c[1] for c in cols])
    conn.close()
