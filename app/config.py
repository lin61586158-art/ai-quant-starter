import os
from dotenv import load_dotenv

load_dotenv()

# ── News Agent Mode ──────────────────────────────────────────────
# Options: "keyword" | "gemini" | "claude"
NEWS_AGENT_MODE = os.getenv("NEWS_AGENT_MODE", "keyword").lower()

# ── Gemini ───────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ── Anthropic Claude ─────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# ── OpenAI ───────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# ── Indicator defaults ───────────────────────────────────────────
MA_SHORT_WINDOW   = int(os.getenv("MA_SHORT_WINDOW", "5"))
MA_LONG_WINDOW    = int(os.getenv("MA_LONG_WINDOW", "20"))
VOLATILITY_WINDOW = int(os.getenv("VOLATILITY_WINDOW", "10"))
SWING_WINDOW      = int(os.getenv("SWING_WINDOW", "20"))
