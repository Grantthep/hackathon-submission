from dotenv import load_dotenv
import os
load_dotenv()
k = os.getenv("OPENAI_API_KEY")
print("loaded:", bool(k), "prefix:", (k or "")[:3])
