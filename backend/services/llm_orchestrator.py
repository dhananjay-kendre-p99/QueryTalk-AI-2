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

    def generate_sql(self, user_query: str, schema_info: str, api_key: str = None, dialect: str = "sqlite") -> str:
        client = Groq(api_key=api_key) if api_key else self.client
        
        dialect_instructions = ""
        db_dialect = (dialect or "sqlite").lower()
        if db_dialect == "postgresql":
            dialect_instructions = (
                "CRITICAL: The database is PostgreSQL. You MUST generate valid PostgreSQL syntax:\n"
                "1. DO NOT use backticks (`) for quoting identifiers (table names, column names). Backticks are a syntax error in PostgreSQL.\n"
                "2. Table names and column names that contain spaces, uppercase letters, or special characters MUST be quoted using double quotes (\"), for example: \"Sales Data\", \"Quantity Ordered\", \"City\".\n"
                "3. Ensure all table and column names match the schema exactly, keeping spaces and casing if they are present in the schema, and enclosing them in double quotes.\n"
                "4. Case-sensitivity: Identifiers in PostgreSQL are folded to lower case unless they are double-quoted. Therefore, always double-quote any multi-word identifiers or identifiers with mixed case or spaces to be completely safe."
            )
        elif db_dialect == "mysql":
            dialect_instructions = (
                "CRITICAL: The database is MySQL. You MUST generate valid MySQL syntax:\n"
                "1. Use backticks (`) for quoting identifiers (table names, column names) that contain spaces or special characters, for example: `Sales Data`, `Quantity Ordered`.\n"
                "2. Ensure all table and column names match the schema exactly, keeping spaces and casing if they are present in the schema, and enclosing them in backticks."
            )
        else:
            dialect_instructions = (
                f"CRITICAL: The database is {db_dialect.upper()}. You MUST generate valid standard SQL syntax:\n"
                "1. Table names and column names that contain spaces, uppercase letters, or special characters MUST be quoted using double quotes (\") or brackets ([]), for example: \"Sales Data\", \"Quantity Ordered\".\n"
                "2. DO NOT use backticks (`) unless explicitly supported by the dialect. Double quotes are the standard ANSI SQL quoting character.\n"
                "3. Ensure all table and column names match the schema exactly, keeping spaces and casing if they are present in the schema, and enclosing them in double quotes."
            )

        system_prompt = f"""You are an expert SQL generator. Your task is to convert the user's natural language question into a valid SQL query.
Use the following database schema to form your query:
{schema_info},if the result generated is not related to the schema, or if the question cannot be answered with the given schema, respond with "The question is not related to the provided schema, so no SQL query can be generated."

{dialect_instructions}

Return ONLY the raw SQL query, without any markdown formatting or explanation. Ensure it's read-only."""

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