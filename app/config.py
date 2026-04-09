import os
from dotenv import load_dotenv

load_dotenv()

NEWS_AGENT_MODE = os.getenv("NEWS_AGENT_MODE", "keyword").lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")