import json
from google import genai
import anthropic

from app.config import (
    NEWS_AGENT_MODE,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
)


def _build_news_prompt(news: str) -> str:
    return f"""
You are a financial news analysis engine.

Analyze the following news and return ONLY valid JSON.
Do not include markdown.
Do not include explanations outside JSON.

Required JSON format:
{{
  "news_signal": "positive|neutral|negative",
  "news_score": float,
  "sentiment_score": float,
  "event_score": float,
  "event_bias": "positive_event_bias|neutral_event_bias|negative_event_bias",
  "event_tags": ["tag1", "tag2"],
  "positive_count": int,
  "negative_count": int,
  "news_reason": "short explanation"
}}

Rules:
- news_score should roughly reflect total news impact in range -1.0 to 1.0
- sentiment_score should reflect textual sentiment in range -1.0 to 1.0
- event_score should reflect event importance in range -1.0 to 1.0
- positive_count and negative_count are estimated counts of positive/negative cues
- event_tags should be concise, e.g. ["earnings", "guidance", "lawsuit", "regulation", "upgrade", "downgrade", "partnership", "product_launch"]
- Be conservative and structured.

News:
{news}
"""


def _normalize_result(parsed: dict, mode_name: str) -> dict:
    return {
        "news_signal": parsed.get("news_signal", "neutral"),
        "news_score": round(float(parsed.get("news_score", 0.0)), 2),
        "sentiment_score": round(float(parsed.get("sentiment_score", 0.0)), 2),
        "event_score": round(float(parsed.get("event_score", 0.0)), 2),
        "event_bias": parsed.get("event_bias", "neutral_event_bias"),
        "event_tags": parsed.get("event_tags", []),
        "positive_count": int(parsed.get("positive_count", 0)),
        "negative_count": int(parsed.get("negative_count", 0)),
        "news_reason": parsed.get("news_reason", f"{mode_name} analysis completed."),
        "news_mode": mode_name,
    }


def analyze_news_with_gemini(news: str) -> dict:
    if not GEMINI_API_KEY:
        return {
            "news_signal": "neutral",
            "news_score": 0.0,
            "sentiment_score": 0.0,
            "event_score": 0.0,
            "event_bias": "neutral_event_bias",
            "event_tags": [],
            "positive_count": 0,
            "negative_count": 0,
            "news_reason": "Gemini mode requested, but GEMINI_API_KEY is not configured.",
            "news_mode": "gemini_mock",
        }

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = _build_news_prompt(news)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        parsed = json.loads(response.text.strip())
        return _normalize_result(parsed, "gemini")
    except Exception as e:
        return {
            "news_signal": "neutral",
            "news_score": 0.0,
            "sentiment_score": 0.0,
            "event_score": 0.0,
            "event_bias": "neutral_event_bias",
            "event_tags": [],
            "positive_count": 0,
            "negative_count": 0,
            "news_reason": f"Gemini analysis failed: {str(e)}",
            "news_mode": "gemini_error",
        }


def analyze_news_with_claude(news: str) -> dict:
    if not ANTHROPIC_API_KEY:
        return {
            "news_signal": "neutral",
            "news_score": 0.0,
            "sentiment_score": 0.0,
            "event_score": 0.0,
            "event_bias": "neutral_event_bias",
            "event_tags": [],
            "positive_count": 0,
            "negative_count": 0,
            "news_reason": "Claude mode requested, but ANTHROPIC_API_KEY is not configured.",
            "news_mode": "claude_mock",
        }

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = _build_news_prompt(news)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=800,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        raw_text = response.content[0].text.strip()
        parsed = json.loads(raw_text)
        return _normalize_result(parsed, "claude")
    except Exception as e:
        return {
            "news_signal": "neutral",
            "news_score": 0.0,
            "sentiment_score": 0.0,
            "event_score": 0.0,
            "event_bias": "neutral_event_bias",
            "event_tags": [],
            "positive_count": 0,
            "negative_count": 0,
            "news_reason": f"Claude analysis failed: {str(e)}",
            "news_mode": "claude_error",
        }


def analyze_news_with_llm(news: str) -> dict:
    mode = NEWS_AGENT_MODE

    if mode == "gemini":
        return analyze_news_with_gemini(news)
    if mode == "claude":
        return analyze_news_with_claude(news)

    return {
        "news_signal": "neutral",
        "news_score": 0.0,
        "sentiment_score": 0.0,
        "event_score": 0.0,
        "event_bias": "neutral_event_bias",
        "event_tags": [],
        "positive_count": 0,
        "negative_count": 0,
        "news_reason": f"Unsupported LLM mode: {mode}",
        "news_mode": "llm_error",
    }