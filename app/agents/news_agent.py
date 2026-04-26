# -*- coding: utf-8 -*-
"""
news_agent.py — 新聞情緒分析 Agent

三種模式（由 NEWS_AGENT_MODE 環境變數切換）：
    keyword — 純規則式關鍵字計分（不需 API Key）
    gemini  — 呼叫 Gemini 做情緒/事件分類
    claude  — 呼叫 Anthropic Claude 做情緒/事件分類

任一 LLM 模式失敗會自動 fallback 到 keyword。
"""
import json

from app.config import (
    NEWS_AGENT_MODE,
    GEMINI_API_KEY, GEMINI_MODEL,
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
)


# ── 關鍵字字典 ──────────────────────────────────────────────────

POSITIVE_KEYWORDS = [
    "beat", "beats", "surge", "surges", "rally", "rallies", "growth",
    "record high", "upgrade", "buy rating", "strong", "profit", "exceed",
    "expansion", "breakthrough", "approval", "partnership", "acquisition",
    "獲利", "成長", "創新高", "突破", "上調", "看好", "強勁", "超預期", "利多",
    "受惠", "增持", "買進", "回升",
]

NEGATIVE_KEYWORDS = [
    "miss", "misses", "drop", "drops", "fall", "falls", "decline",
    "downgrade", "sell rating", "weak", "loss", "bankrupt", "fraud",
    "investigation", "lawsuit", "crash", "warn", "warning", "cut",
    "下跌", "虧損", "下修", "看淡", "疲弱", "利空", "破產", "調查",
    "罰款", "減持", "賣出", "暴跌",
]

EVENT_TAG_KEYWORDS = {
    "earnings":   ["earnings", "eps", "revenue", "財報", "營收", "獲利"],
    "macro":      ["fed", "rate hike", "rate cut", "cpi", "inflation",
                   "升息", "降息", "通膨"],
    "regulation": ["sec ", "regulation", "lawsuit", "監管", "罰款", "違規"],
    "merger":     ["merger", "acquisition", "buyout", "併購", "收購"],
    "guidance":   ["guidance", "outlook", "forecast", "展望", "預測", "預期"],
    "product":    ["launch", "release", "unveil", "發表", "上市", "推出"],
}


# ── Helper ──────────────────────────────────────────────────────

def _empty_result() -> dict:
    return {
        "news_signal": "neutral",
        "news_score":  0.0,
        "event_bias":  "none",
        "event_tags":  [],
        "news_reason": "No news provided.",
        "news_mode":   NEWS_AGENT_MODE,
    }


def _classify(score: float) -> tuple[str, str]:
    if score >= 0.15:
        return "positive", "bullish_event"
    if score <= -0.15:
        return "negative", "bearish_event"
    return "neutral", "none"


def _detect_tags(text: str) -> list[str]:
    low = text.lower()
    return [tag for tag, kws in EVENT_TAG_KEYWORDS.items()
            if any(kw in low for kw in kws)]


def _extract_json(text: str) -> dict:
    """
    從 LLM 文字輸出抽出第一個 top-level JSON 物件。
    使用 brace-counting 處理巢狀結構，比貪婪正則安全。
    """
    if not text:
        return {}
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break  # 從下一個 { 重試
        start = text.find("{", start + 1)
    return {}


# ── Mode 1: keyword ─────────────────────────────────────────────

def _keyword_analyze(news: str) -> dict:
    low = news.lower()
    pos_hits = [w for w in POSITIVE_KEYWORDS if w.lower() in low]
    neg_hits = [w for w in NEGATIVE_KEYWORDS if w.lower() in low]

    raw = len(pos_hits) * 0.1 - len(neg_hits) * 0.1
    score = max(-0.6, min(0.6, raw))
    signal, bias = _classify(score)

    return {
        "news_signal": signal,
        "news_score":  round(score, 3),
        "event_bias":  bias,
        "event_tags":  _detect_tags(news),
        "news_reason": (
            f"Keyword scan: +{len(pos_hits)} positive, -{len(neg_hits)} negative."
        ),
        "news_mode":   "keyword",
    }


# ── Mode 2: Gemini ──────────────────────────────────────────────

_GEMINI_PROMPT = (
    "You are a financial news sentiment classifier. "
    "Analyze the news and respond ONLY with a JSON object: "
    '{"signal":"positive|neutral|negative","score":-1.0 to 1.0,'
    '"event_bias":"bullish_event|bearish_event|none",'
    '"event_tags":["earnings","macro","regulation","merger","guidance","product"],'
    '"reason":"one short sentence"}'
    "\n\nNews:\n"
)


def _gemini_analyze(news: str) -> dict:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=_GEMINI_PROMPT + news,
        )
        data = _extract_json(getattr(resp, "text", "") or "")
        if not data:
            raise ValueError("Empty/invalid JSON from Gemini")

        score = float(data.get("score", 0))
        signal = data.get("signal") or _classify(score)[0]
        bias   = data.get("event_bias") or _classify(score)[1]

        return {
            "news_signal": signal,
            "news_score":  round(score, 3),
            "event_bias":  bias,
            "event_tags":  data.get("event_tags") or _detect_tags(news),
            "news_reason": data.get("reason", "Gemini analysis."),
            "news_mode":   "gemini",
        }
    except Exception as e:
        fallback = _keyword_analyze(news)
        fallback["news_reason"] = f"Gemini failed ({e}); fallback. " + fallback["news_reason"]
        fallback["news_mode"]   = "gemini_fallback"
        return fallback


# ── Mode 3: Claude ──────────────────────────────────────────────

def _claude_analyze(news: str) -> dict:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": _GEMINI_PROMPT + news}],
        )
        text = "".join(
            getattr(b, "text", "") for b in msg.content if hasattr(b, "text")
        )
        data = _extract_json(text)
        if not data:
            raise ValueError("Empty/invalid JSON from Claude")

        score = float(data.get("score", 0))
        signal = data.get("signal") or _classify(score)[0]
        bias   = data.get("event_bias") or _classify(score)[1]

        return {
            "news_signal": signal,
            "news_score":  round(score, 3),
            "event_bias":  bias,
            "event_tags":  data.get("event_tags") or _detect_tags(news),
            "news_reason": data.get("reason", "Claude analysis."),
            "news_mode":   "claude",
        }
    except Exception as e:
        fallback = _keyword_analyze(news)
        fallback["news_reason"] = f"Claude failed ({e}); fallback. " + fallback["news_reason"]
        fallback["news_mode"]   = "claude_fallback"
        return fallback


# ── Public ──────────────────────────────────────────────────────

def run_news_agent(news: str | None = None) -> dict:
    if not news or not news.strip():
        return _empty_result()

    mode = NEWS_AGENT_MODE
    if mode == "gemini" and GEMINI_API_KEY:
        return _gemini_analyze(news)
    if mode == "claude" and ANTHROPIC_API_KEY:
        return _claude_analyze(news)
    return _keyword_analyze(news)
