import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.models import DatabaseConnection
from core.encryption import decrypt_password
import core.database as db_core
import json

load_dotenv()

def run_diagnostics():
    engine = create_engine(os.getenv('DATABASE_URL'))
    Session = sessionmaker(bind=engine)
    s = Session()
    
    # Get the active connection (most recently updated)
    conn = s.query(DatabaseConnection).order_by(DatabaseConnection.updated_at.desc()).first()
    if not conn:
        print("No database connections found in database.")
        return
        
    print('Testing connection:', conn.name, 'Dialect:', conn.db_type)
    conn_str = decrypt_password(conn.connection_string_enc)
    db_core.set_engine(conn_str, connection_id=str(conn.id))
    
    schema_info = db_core.get_schema_info()
    dialect = db_core.get_dialect_name()
    
    print('Schema info length:', len(schema_info))
    
    # Query LLM
    from services.llm_orchestrator import llm_orchestrator
    client = llm_orchestrator.client
    if not client:
        print("Error: Groq client is not initialized.")
        return
        
    system_prompt = f"""You are a data analytics expert. Your task is to analyze a database schema and output a valid JSON containing SQL queries that fetch metrics for an interactive analytics dashboard.
The user's database dialect is: {dialect}.

The schema of the connected database is:
{schema_info}

You MUST return a JSON object with the following exact keys:
1. "totalRevenueQuery": A SQL query that returns a single numeric value (e.g. SUM of transaction/sales amount, or COUNT of main entities if there is no numeric column).
2. "activeCustomersQuery": A SQL query that returns a single numeric count of active entities (e.g. COUNT of distinct customer IDs, or COUNT of distinct groups/categories).
3. "monthlySalesQuery": A SQL query that returns a single numeric count of recent transactions (e.g. COUNT of orders in the last 30 days, or COUNT of records created recently).
4. "growthPctQuery": A SQL query that returns a single numeric percentage value representing growth. If hard to calculate, return a static float.
5. "growthDataQuery": A SQL query that returns rows with columns: "name" (string, representing month/date/category) and "current" (numeric, representing value) and "projected" (numeric). Max 12 rows.
6. "marketShareQuery": A SQL query that returns rows with columns: "name" (string, representing segment/region/category) and "value" (numeric, representing percentage). Max 5 rows.
7. "revenueRegionQuery": A SQL query that returns rows with columns: "name" (string, representing region/category) and "value" (numeric, representing revenue/count). Max 5 rows.
8. "customerSegmentsQuery": A SQL query that returns rows with columns: "x" (numeric value), "y" (numeric value), "z" (numeric size value), and "group" (string or integer, representing category/segment). Max 100 rows.

Instructions:
- If the schema represents a sales/business/orders database, write standard business queries on the orders/sales/users tables.
- If the schema is completely different (e.g., library, employee registry, movies), creatively map the dashboard metrics to the available tables. For example, for an employee database, totalRevenue can be the sum of salaries or count of employees, activeCustomers can be the number of departments, monthlySales can be the number of hires in the last month, growthData can be employee hiring over time, marketShare can be employee count by department, customerSegments can compare experience (x) vs salary (y).
- The SQL queries must be valid for the {dialect} dialect.
- Use simple, standard SQL features. Avoid vendor-specific complex functions.
- Return ONLY a JSON object with the queries. Do NOT return any markdown wrapping (no ```json or ```)."""

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
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    print("\n--- LLM Response CONTENT ---")
    print(content)
    print("----------------------------\n")
    
    queries = json.loads(content)
    session = db_core.SessionLocal()
    
    print("\n--- Executing queries ---")
    for key, sql in queries.items():
        print(f"\n[{key}]: {sql}")
        try:
            res = session.execute(text(sql))
            if "Query" in key:
                print("Result (scalar):", res.scalar())
            else:
                rows = res.fetchall()
                print("Result (rows):", rows[:5])
        except Exception as e:
            print("FAILED:", str(e))
            
    session.close()

if __name__ == '__main__':
    run_diagnostics()
