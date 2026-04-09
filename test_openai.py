from openai import OpenAI
import os

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("No OPENAI_API_KEY found.")
    raise SystemExit

client = OpenAI(api_key=api_key)

response = client.responses.create(
    model="gpt-4.1-mini",
    input="Reply with only: OpenAI API connection successful."
)

print(response.output_text)