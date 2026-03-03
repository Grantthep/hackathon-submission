from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a friendly visa consultant."},
        {"role": "user", "content": "I'm American and in Bali. Can I apply from here?"}
    ],
)

print(response.choices[0].message.content)
