import os
from dotenv import load_dotenv

print("Current directory:", os.getcwd())
print("Files in directory:", os.listdir('.'))

load_dotenv()

api_key = os.getenv("GROK_API_KEY")
print(f"\nAPI Key loaded: {api_key[:20] if api_key else 'NOT FOUND'}...")
print(f"API Key length: {len(api_key) if api_key else 0}")