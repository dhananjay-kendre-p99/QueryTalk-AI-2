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

    def generate_sql(self, user_query: str, schema_info: str, api_key: str = None) -> str:
        client = Groq(api_key=api_key) if api_key else self.client
        system_prompt = f"""You are an expert SQL generator. Your task is to convert the user's natural language question into a valid SQL query.
Use the following database schema to form your query:
{schema_info},if the result generated is not related to the schema, or if the question cannot be answered with the given schema, respond with "The question is not related to the provided schema, so no SQL query can be generated."

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