import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

OPENROUTER_MODEL_CHEAP = os.getenv("OPENROUTER_MODEL_CHEAP", "openrouter/free")
OPENROUTER_MODEL_STRONG = os.getenv("OPENROUTER_MODEL_STRONG", "meta-llama/llama-3.3-70b-instruct:free")

APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Africa/Tunis")

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set. Check your .env file.")