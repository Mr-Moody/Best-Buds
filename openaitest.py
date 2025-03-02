import openai
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set it in your environment.")

try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.models.list()
    print("API Key is working! Available models:", [model.id for model in response.data])
except Exception as e:
    print("API Key issue:", e)
