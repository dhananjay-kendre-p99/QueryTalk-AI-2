import os
import sys
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

load_dotenv(dotenv_path='../backend/.env')

from groq import Groq

api_key = os.getenv("GROQ_API_KEY")
print("API Key:", api_key)

client = Groq(api_key=api_key)
try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.1,
        max_tokens=1024
    )
    print("Success:", response.choices[0].message.content)
except Exception as e:
    print("Failed:", str(e))
