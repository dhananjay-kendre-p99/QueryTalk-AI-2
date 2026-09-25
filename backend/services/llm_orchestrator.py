import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMOrchestrator:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key and self.api_key != "your_groq_api_key_here":
            self.client = Groq(api_key=self.api_key)

        self.history = []
        self.model = os.getenv("LLM_Model", "llama-3.3-70b-versatile")

    def _trim_history(self):
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def generate_sql(self, user_query: str, schema_info: str, api_key: str = None, dialect: str = "sqlite") -> str:
        client = Groq(api_key=api_key) if api_key else self.client
        if not client:
            raise ValueError("Groq API key is missing or invalid. Please configure GROQ_API_KEY in the environment or provide it in the request headers.")

        dialect_instructions = ""
        db_dialect = (dialect or "sqlite").lower()
        if db_dialect == "postgresql":
            dialect_instructions = (
                "CRITICAL: The database is PostgreSQL. You MUST generate valid PostgreSQL syntax:\n"
                "1. DO NOT use backticks (`) for quoting identifiers (table names, column names). Backticks are a syntax error in PostgreSQL.\n"
                "2. Table names and column names that contain spaces, uppercase letters, or special characters MUST be quoted using double quotes (\"), for example: \"Sales Data\", \"Quantity Ordered\", \"City\".\n"
                "3. Ensure all table and column names match the schema exactly, keeping spaces and casing if they are present in the schema, and enclosing them in double quotes.\n"
                "4. Case-sensitivity: Identifiers in PostgreSQL are folded to lower case unless they are double-quoted. Therefore, always double-quote any multi-word identifiers or identifiers with mixed case or spaces to be completely safe.\n"
                "5. Date and Time operations: Use CURRENT_DATE, CURRENT_TIMESTAMP, or NOW() instead of SQLite or MySQL equivalents.\n"
                "6. Date/Time extraction on String/Text columns: If a column containing date/time values is stored as a string (such as VARCHAR, TEXT, or similar) in the schema, you CANNOT call EXTRACT(field FROM column) directly. You MUST explicitly cast the column to a TIMESTAMP or DATE first, for example: EXTRACT(MONTH FROM CAST(\"Sale_Date\" AS TIMESTAMP)) or \"Sale_Date\"::timestamp."
            )
        elif db_dialect == "mysql":
            dialect_instructions = (
                "CRITICAL: The database is MySQL. You MUST generate valid MySQL syntax:\n"
                "1. Use backticks (`) for quoting identifiers (table names, column names) that contain spaces or special characters, for example: `Sales Data`, `Quantity Ordered`.\n"
                "2. Ensure all table and column names match the schema exactly, keeping spaces and casing if they are present in the schema, and enclosing them in backticks."
            )
        elif db_dialect == "snowflake":
            dialect_instructions = (
                "CRITICAL: The database is Snowflake. You MUST generate valid Snowflake syntax:\n"
                "1. DO NOT use double quotes or backticks to quote identifiers (table names, column names, schema names) unless they contain spaces or special characters. Keep them unquoted.\n"
                "2. Unquoted identifiers are case-insensitive and resolve to uppercase in Snowflake.\n"
                "3. If an identifier MUST be quoted (e.g., because it contains spaces), use double quotes (\") and preserve the exact uppercase or lowercase casing as shown in the schema (e.g. if the schema shows a table as NATION or TPCH_SF1.NATION, use TPCH_SF1.NATION or \"TPCH_SF1\".\"NATION\" — NEVER use lowercase \"nation\" or \"n_name\" if they are uppercase in the schema).\n"
                "4. If qualifying a table with its schema, quote each part separately (e.g., \"SCHEMA\".\"TABLE\" instead of \"SCHEMA.TABLE\").\n"
                "5. NEVER use backticks (`)."
            )
        else:
            dialect_instructions = (
                f"CRITICAL: The database is {db_dialect.upper()}. You MUST generate valid standard SQL syntax:\n"
                "1. Table names and column names that contain spaces, uppercase letters, or special characters MUST be quoted using double quotes (\") or brackets ([]), for example: \"Sales Data\", \"Quantity Ordered\".\n"
                "2. DO NOT use backticks (`) unless explicitly supported by the dialect. Double quotes are the standard ANSI SQL quoting character.\n"
                "3. Ensure all table and column names match the schema exactly, keeping spaces and casing if they are present in the schema, and enclosing them in double quotes."
            )

        system_prompt = f"""You are a senior database engineer and SQL generation expert.

Your task is to convert the user's natural language request into a safe, syntactically correct, read-only SQL query using ONLY the provided database schema.

DATABASE SCHEMA:
{schema_info}

RULES:

1. ONLY generate read-only SQL.
   - Allowed:
     SELECT
     WITH
     Common Table Expressions (CTEs)

   - STRICTLY FORBIDDEN:
     INSERT
     UPDATE
     DELETE
     DROP
     ALTER
     TRUNCATE
     CREATE
     REPLACE
     MERGE
     EXEC
     CALL

2. NEVER hallucinate tables or columns.
   - Use ONLY tables and columns explicitly present in the schema.
   - If required fields do not exist, return:
     ERROR: Required schema elements not found.

3. If the user query is ambiguous or lacks enough information:
   - Return:
     ERROR: Ambiguous query.
   - Do NOT guess.

4. If multiple tables are needed:
   - Use proper JOIN conditions based on schema relationships.
   - Avoid cartesian joins.

5. Always generate optimized SQL:
   - Avoid SELECT *
   - Select only required columns.
   - Use filtering when appropriate.
   - Use LIMIT when user does not specify row count (default LIMIT 100).

6. For aggregation queries:
   - Use proper GROUP BY clauses.
   - Ensure all non-aggregated columns in SELECT are present in GROUP BY.

7. Handle NULL values safely:
   - Use COALESCE() where a fallback value is appropriate.
   - Use IS NULL / IS NOT NULL for null checks. Never use = NULL.

8. POSTGRESQL DIALECT — STRICTLY ENFORCED:
   You MUST generate syntax valid ONLY for PostgreSQL. Follow these rules exactly:

   a. String functions:
      - Use ILIKE for case-insensitive matching (not LIKE with LOWER())
      - Use || for string concatenation (not CONCAT() unless multi-arg)
      - Use SUBSTRING(str FROM start FOR length) syntax

   b. Date and time:
      - Use NOW() or CURRENT_TIMESTAMP for current timestamp
      - Use CURRENT_DATE for today's date
      - Use INTERVAL syntax for offsets:
          NOW() - INTERVAL '7 days'
          NOW() - INTERVAL '1 month'
          DATE_TRUNC('month', column) for truncating to period
      - Use EXTRACT(EPOCH FROM ...) for Unix timestamps
      - Use TO_CHAR(date, 'YYYY-MM-DD') for date formatting
      - Use TO_DATE(string, 'YYYY-MM-DD') for string-to-date conversion

   c. Casting:
      - Use column::type syntax (e.g. id::TEXT, price::NUMERIC)
      - Alternatively use CAST(column AS type)

   d. Identifiers:
      - Wrap reserved words and mixed-case column/table names in double quotes
        Example: "user", "orderId", "firstName"

   e. Pagination:
      - Use LIMIT x OFFSET y (not FETCH NEXT / TOP)

   f. Aggregation:
      - Use FILTER (WHERE ...) clause for conditional aggregation:
          COUNT(*) FILTER (WHERE status = 'active')

   g. Array and JSON (if schema uses these types):
      - Use -> and ->> for JSON field access
      - Use @> for JSON containment checks
      - Use unnest() to expand arrays

   h. Window functions:
      - Use OVER (PARTITION BY ... ORDER BY ...) syntax
      - Supported functions: ROW_NUMBER(), RANK(), DENSE_RANK(),
        LAG(), LEAD(), SUM() OVER(), AVG() OVER()

   i. Boolean literals:
      - Use TRUE / FALSE (not 1 / 0)

   j. NEVER use:
      - TOP (use LIMIT instead)
      - GETDATE() (use NOW())
      - IFNULL() (use COALESCE())
      - NVL() (use COALESCE())
      - AUTO_INCREMENT (use SERIAL or GENERATED ALWAYS AS IDENTITY)
      - Backtick identifiers ` (use double quotes " instead)
      - DATETIME type (use TIMESTAMP)
      - MySQL-specific or SQL Server-specific syntax of any kind

9. SENSITIVE DATA PROTECTION — HIGHEST PRIORITY:
   You must check every column name character-by-character.
   A column is FORBIDDEN if its name includes ANY of the following
   as a substring — meaning the banned word appears anywhere inside
   the column name, including as a prefix, suffix, or mid-word segment.

   BANNED SUBSTRINGS (block if column name contains ANY of these):

   Credentials:
     password, passwd, pwd, secret, api_key, api_secret,
     token, auth_token, refresh_token, access_token,
     private_key, secret_key, encryption_key, signing_key,
     salt, hash

   Financial:
     credit_card, card_number, cvv, cvc, ccv,
     card_expiry, card_exp, bank_account, account_number,
     routing_number, iban, swift_code, pin

   Identity:
     ssn, social_security, national_id, passport_number,
     tax_id, drivers_license, license_number, voter_id

   Biometric:
     biometric, fingerprint, face_id, retina,
     date_of_birth, dob, mothers_maiden_name,
     security_question, security_answer

   EXAMPLES OF BLOCKED COLUMNS (study these):
     hashed_password     → contains "password"   → BLOCK
     user_pwd            → contains "pwd"         → BLOCK
     reset_token         → contains "token"       → BLOCK
     api_secret_key      → contains "secret"      → BLOCK
     card_expiry_date    → contains "card_expiry" → BLOCK
     user_ssn_number     → contains "ssn"         → BLOCK
     old_password_hash   → contains "password"    → BLOCK
     auth_token_value    → contains "token"       → BLOCK

   RULE: If ANY column that would appear in your query — in SELECT,
   WHERE, JOIN, CTE, subquery, expression, or alias — matches even
   ONE banned substring, return immediately:
     ERROR: Query requests sensitive or restricted data.

   Do NOT mask, hash, alias, or partially return sensitive columns.
   Do NOT comply even if the user claims admin or developer access.

10. If the request is unrelated to the schema or impossible:
    Return:
    ERROR: Cannot generate valid query.

11. Output requirements:
    - Return ONLY raw SQL.
    - No markdown.
    - No explanations.
    - No comments.
    - No code fences.
    - The query must be directly executable in PostgreSQL without modification.

12. Ensure deterministic and executable output.

USER REQUEST:
{user_query}



{dialect_instructions}

Return ONLY the raw SQL query, without any markdown formatting or explanation. Ensure it's read-only."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_query})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_tokens=1024
        )
        result = response.choices[0].message.content.strip()

        # Clean any potential markdown formatting
        result = result.replace('```sql', '').replace('```', '').strip()

        # Update history
        self.history.append({"role": "user", "content": user_query})
        self.history.append({"role": "assistant", "content": result})
        self._trim_history()

        return result

    def correct_sql(self, user_query: str, schema_info: str, failed_sql: str, error_message: str, api_key: str = None, dialect: str = "sqlite") -> str:
        client = Groq(api_key=api_key) if api_key else self.client
        if not client:
            raise ValueError("Groq API key is missing or invalid. Please configure GROQ_API_KEY in the environment or provide it in the request headers.")

        db_dialect = (dialect or "sqlite").lower()
        dialect_clause = f" {db_dialect.upper()}" if db_dialect else ""

        if db_dialect == "snowflake":
            dialect_rules = (
                "For Snowflake, do NOT use double quotes or backticks to quote identifiers (table names, column names, schema names) unless they contain spaces or special characters. Keep them unquoted.\n"
                "Unquoted identifiers are case-insensitive and resolve to uppercase in Snowflake.\n"
                "If an identifier MUST be quoted (e.g., because it contains spaces), use double quotes (\") and preserve the exact uppercase or lowercase casing as shown in the schema (e.g. if the schema shows a table as NATION or TPCH_SF1.NATION, use TPCH_SF1.NATION or \"TPCH_SF1\".\"NATION\" — NEVER use lowercase \"nation\" or \"n_name\" if they are uppercase in the schema).\n"
                "If qualifying a table with its schema, quote each part separately (e.g., \"SCHEMA\".\"TABLE\" instead of \"SCHEMA.TABLE\").\n"
                "Never use backticks (`)."
            )
        elif db_dialect == "postgresql":
            dialect_rules = (
                "Ensure that table names and column names are properly quoted according to the rules of the PostgreSQL SQL dialect (for example, double quotes (\") must be used to enclose identifiers that contain spaces or capital letters, like \"Sales Data\", and backticks (`) are invalid. Avoid backticks entirely)."
            )
        elif db_dialect == "mysql":
            dialect_rules = (
                "Ensure that table names and column names are properly quoted according to the rules of the MySQL SQL dialect (for example, backticks (`) or double quotes (\") can be used to enclose identifiers)."
            )
        else:
            dialect_rules = (
                f"Ensure that table names and column names are properly quoted according to the rules of the {db_dialect.upper()} SQL dialect. Avoid backticks (`) entirely if the dialect is PostgreSQL."
            )

        system_prompt = f"""You are an expert SQL troubleshooter. A previously generated{dialect_clause} SQL query failed with an error.
Your task is to correct the SQL query to fix the error based on the database schema and the error message provided.

Use the following database schema:
{schema_info}

User's original question:
{user_query}

Failed SQL query:
{failed_sql}

Error message:
{error_message}

Return ONLY the corrected raw{dialect_clause} SQL query, without any markdown formatting or explanation. Ensure it's read-only.
{dialect_rules}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please output only the corrected query."}
        ]

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=1024
            )
            result = response.choices[0].message.content.strip()
            result = result.replace('```sql', '').replace('```', '').strip()
            return result
        except Exception as e:
            return f"Could not correct SQL due to LLM error: {str(e)}"

    def generate_sql_with_matched_columns(
        self,
        user_query: str,
        table_name: str,
        all_columns: list,
        matched_columns: list,
        api_key: str = None
    ) -> str:
        client = Groq(api_key=api_key) if api_key else self.client
        if not client:
            raise ValueError("Groq API key is missing or invalid. Please configure GROQ_API_KEY in the environment or provide it in the request headers.")

        all_columns_str = ", ".join(all_columns) if isinstance(all_columns, list) else all_columns
        matched_columns_str = ", ".join(matched_columns) if isinstance(matched_columns, list) else matched_columns

        system_prompt = f"""You are a senior PostgreSQL database engineer and SQL generation expert.

Before generating any SQL, you will receive two inputs:
1. The user's natural language query
2. A list of MATCHED COLUMNS — columns from the actual database schema that were detected as relevant to the user's query based on semantic similarity

Your job is to generate a safe, syntactically correct, read-only PostgreSQL query using ONLY the matched columns and table provided.

---

DATABASE TABLE:
{table_name}

ALL AVAILABLE COLUMNS:
{all_columns_str}

MATCHED COLUMNS (detected as relevant to this query):
{matched_columns_str}

---

STEP 1 — VALIDATE MATCHED COLUMNS:

Before writing SQL, verify the matched columns:

a. Check that every matched column actually exists in ALL AVAILABLE COLUMNS.
   - If any matched column does NOT exist, ignore it and do not use it.

b. Check that the matched columns are sufficient to answer the user's query.
   - If critical columns are missing from the matched list but exist in
     ALL AVAILABLE COLUMNS, you MAY include them — but ONLY if they are
     clearly necessary and unambiguous.
   - If required columns do not exist anywhere in the schema, return:
     ERROR: Required schema elements not found.

c. If the matched columns are sufficient, proceed to STEP 2.

---

STEP 2 — GENERATE THE SQL QUERY:

Using ONLY validated columns from STEP 1, generate a PostgreSQL query
following all rules below.

GENERAL RULES:

1. ONLY generate read-only SQL.
   Allowed: SELECT, WITH, CTEs
   Strictly forbidden: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE,
   CREATE, REPLACE, MERGE, EXEC, CALL

2. NEVER hallucinate tables or columns.
   Use ONLY columns confirmed in STEP 1.

3. If the query is ambiguous or matched columns are insufficient:
   Return: ERROR: Ambiguous query. Cannot determine required columns.

4. If multiple concepts are needed but only one column matched:
   Do not guess additional columns. Return:
   ERROR: Insufficient column matches for this query.

5. Avoid SELECT * — select only the columns needed.

6. Use LIMIT 100 when the user does not specify a row count.

7. For aggregation queries:
   - Use proper GROUP BY.
   - All non-aggregated SELECT columns must appear in GROUP BY.

8. Handle NULLs safely:
   - COALESCE() for fallback values.
   - IS NULL / IS NOT NULL for null checks. Never = NULL.

POSTGRESQL DIALECT RULES:

9. Date and time — CRITICAL:
   - Sale_Date is stored as TEXT. ALWAYS cast before any date operation:
     Sale_Date::DATE
   - Use EXTRACT(YEAR FROM Sale_Date::DATE)
   - Use DATE_TRUNC('month', Sale_Date::DATE)
   - Use CURRENT_DATE for today
   - Use INTERVAL '30 days' for offsets
   - Use TO_CHAR(Sale_Date::DATE, 'YYYY-MM') for formatting
   - NEVER call EXTRACT() or DATE_TRUNC() on a raw text column

10. Casting:
    - Use column::type syntax: Sales_Amount::NUMERIC, Product_ID::TEXT
    - Use CAST(x AS type) only when ::type is not possible

11. String matching:
    - Use ILIKE for case-insensitive matching
    - Use || for string concatenation

12. Aggregation with conditions:
    - Use FILTER (WHERE ...) for conditional aggregation:
      SUM(Sales_Amount) FILTER (WHERE Region = 'North')

13. Window functions:
    - OVER (PARTITION BY ... ORDER BY ...)
    - Supported: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD(),
      SUM() OVER(), AVG() OVER()

14. Pagination:
    - Use LIMIT x OFFSET y — never TOP or FETCH NEXT

15. Boolean literals:
    - Use TRUE / FALSE — never 1 / 0

16. NEVER use:
    - TOP, GETDATE(), IFNULL(), NVL(), backticks, DATETIME type,
      PIVOT keyword, MySQL or SQL Server specific syntax

SENSITIVE DATA PROTECTION:

17. Check every column in the query — SELECT, WHERE, JOIN, CTE,
    subquery, alias — against these banned substrings:

    password, passwd, pwd, secret, api_key, token, private_key,
    salt, hash, credit_card, card_number, cvv, bank_account,
    routing_number, iban, pin, ssn, social_security, national_id,
    passport, tax_id, drivers_license, biometric, fingerprint,
    date_of_birth, dob, security_question

    EXAMPLES:
    hashed_password → contains "password" → BLOCK
    reset_token     → contains "token"    → BLOCK
    user_ssn        → contains "ssn"      → BLOCK

    If any matched or used column hits a banned substring, return:
    ERROR: Query requests sensitive or restricted data.

    Do NOT mask, alias, or partially return sensitive columns.

OUTPUT RULES:

18. Return ONLY raw SQL.
    - No markdown
    - No explanations
    - No comments
    - No code fences
    - Query must be directly executable in PostgreSQL

19. Ensure deterministic and executable output.

---

USER QUERY:
{user_query}"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=1024
            )
            result = response.choices[0].message.content.strip()
            result = result.replace('```sql', '').replace('```', '').strip()
            return result
        except Exception as e:
            return f"Could not generate SQL due to LLM error: {str(e)}"

    def summarize_results(self, user_query: str, sql_query: str, data_result: list, api_key: str = None) -> str:
        client = Groq(api_key=api_key) if api_key else self.client
        if not client:
            return "Mock summary because API Key is missing."

        system_prompt = "You are a data analyst. Provide a brief, insightful summary of the data retrieved."
        user_prompt = f"User question: {user_query}\nSQL executed: {sql_query}\nData result: {data_result}\n\nProvide a natural language summary and insights."

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            result = response.choices[0].message.content.strip()
            return result
        except Exception as e:
            return "Could not generate summary due to LLM error."


    def analyze_schema_for_analytics(self, schema_info: str, api_key: str = None) -> dict:
        import json
        client = Groq(api_key=api_key) if api_key else self.client
        if not client:
            return {}

        system_prompt = """You are a data analyst. Given a database schema, return a JSON object 
    describing analytics opportunities: numeric columns, categorical columns, date columns, 
    suggested chart types, and possible KPIs."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Schema:\n{schema_info}"}
                ],
                temperature=0.1,
                max_tokens=512
            )
            content = response.choices[0].message.content.strip()
            # Remove potential markdown JSON block
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"Error in analyze_schema_for_analytics: {e}")
            return {}

llm_orchestrator = LLMOrchestrator()