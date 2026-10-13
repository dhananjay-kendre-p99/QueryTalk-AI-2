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

    def _trim_history(self):
        # Keep last 10 messages (5 user, 5 assistant)
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def generate_sql(self, user_query: str, schema_info: str, dialect: str = None, api_key: str = None) -> str:
        client = Groq(api_key=api_key) if api_key else self.client
        dialect_clause = f" {dialect}" if dialect else ""
        
        if dialect and dialect.lower() == "snowflake":
            dialect_rules = (
                "For Snowflake, do NOT use double quotes or backticks to quote identifiers (table names, column names, schema names) unless they contain spaces or special characters. Keep them unquoted. "
                "Unquoted identifiers are case-insensitive and resolve to uppercase in Snowflake. "
                "If an identifier MUST be quoted (e.g., because it contains spaces), use double quotes `\"` and preserve the exact uppercase or lowercase casing as shown in the schema (e.g. if the schema shows a table as `NATION` or `TPCH_SF1.NATION`, use `TPCH_SF1.NATION` or `\"TPCH_SF1\".\"NATION\"` — NEVER use lowercase `\"nation\"` or `\"n_name\"` if they are uppercase in the schema). "
                "If qualifying a table with its schema, quote each part separately (e.g., `\"SCHEMA\".\"TABLE\"` instead of `\"SCHEMA.TABLE\"`). "
                "Never use backticks `` ` ``."
            )
        else:
            dialect_rules = f"Ensure that table names and column names are properly quoted according to the rules of the{dialect_clause} SQL dialect (for example, in PostgreSQL double quotes `\"` must be used to enclose identifiers that contain spaces or capital letters, like `\"Sales Data\"`, and backticks `` ` `` are invalid. In SQLite or MySQL, backticks `` ` `` or double quotes `\"` can be used). Avoid backticks `` ` `` entirely if the dialect is PostgreSQL."

        system_prompt = f"""You are an expert SQL generator. Your task is to convert the user's natural language question into a valid{dialect_clause} SQL query.
Use the following database schema to form your query:
{schema_info},if the result generated is not related to the schema, or if the question cannot be answered with the given schema, respond with "The question is not related to the provided schema, so no SQL query can be generated."

Return ONLY the raw SQL query, without any markdown formatting or explanation. Ensure it's read-only.
{dialect_rules}"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_query})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1,
            max_tokens=1024
        )
        result = response.choices[0].message.content.strip()

        # Clean any potential markdown formatting
        result = result.replace('```sql', '').replace('```', '').strip()
        if "cannot answer" in result.lower():
            result = "The question is not related to the provided schema, so no SQL query can be generated."
        # Update history
        self.history.append({"role": "user", "content": user_query})
        self.history.append({"role": "assistant", "content": result})
        self._trim_history()

        return result

    def correct_sql(self, user_query: str, schema_info: str, failed_sql: str, error_message: str, dialect: str = None, api_key: str = None) -> str:
        client = Groq(api_key=api_key) if api_key else self.client
        dialect_clause = f" {dialect}" if dialect else ""
        
        if dialect and dialect.lower() == "snowflake":
            dialect_rules = (
                "For Snowflake, do NOT use double quotes or backticks to quote identifiers (table names, column names, schema names) unless they contain spaces or special characters. Keep them unquoted. "
                "Unquoted identifiers are case-insensitive and resolve to uppercase in Snowflake. "
                "If an identifier MUST be quoted (e.g., because it contains spaces), use double quotes `\"` and preserve the exact uppercase or lowercase casing as shown in the schema (e.g. if the schema shows a table as `NATION` or `TPCH_SF1.NATION`, use `TPCH_SF1.NATION` or `\"TPCH_SF1\".\"NATION\"` — NEVER use lowercase `\"nation\"` or `\"n_name\"` if they are uppercase in the schema). "
                "If qualifying a table with its schema, quote each part separately (e.g., `\"SCHEMA\".\"TABLE\"` instead of `\"SCHEMA.TABLE\"`). "
                "Never use backticks `` ` ``."
            )
        else:
            dialect_rules = f"Ensure that table names and column names are properly quoted according to the rules of the{dialect_clause} SQL dialect (for example, in PostgreSQL double quotes `\"` must be used to enclose identifiers that contain spaces or capital letters, like `\"Sales Data\"`, and backticks `` ` `` are invalid. In SQLite or MySQL, backticks `` ` `` or double quotes `\"` can be used). Avoid backticks `` ` `` entirely if the dialect is PostgreSQL."

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

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1,
            max_tokens=1024
        )
        result = response.choices[0].message.content.strip()
        result = result.replace('```sql', '').replace('```', '').strip()
        return result


    def summarize_results(self, user_query: str, sql_query: str, data_result: list, api_key: str = None) -> str:
        client = Groq(api_key=api_key) if api_key else self.client
        if not client:
            return "Mock summary because API Key is missing."

        system_prompt = "You are a data analyst. Provide a brief, insightful summary of the data retrieved."
        user_prompt = f"User question: {user_query}\nSQL executed: {sql_query}\nData result: {data_result}\n\nProvide a natural language summary and insights."

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
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

llm_orchestrator = LLMOrchestrator()