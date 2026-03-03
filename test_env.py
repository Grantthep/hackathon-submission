from dotenv import load_dotenv
import os

load_dotenv()

print("LLM_API_KEY:", "SET" if os.getenv("LLM_API_KEY") else "MISSING")
print("SUPABASE_URL:", os.getenv("SUPABASE_URL") or "MISSING")
