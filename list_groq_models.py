import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("GROQ_API_KEY not found in .env")
else:
    client = Groq(api_key=api_key)
    models = client.models.list()
    print("Available Models:")
    for m in models.data:
        print(f"- {m.id}")
