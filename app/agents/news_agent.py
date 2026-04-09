from app.config import NEWS_AGENT_MODE
from app.services.llm_client import analyze_news_with_llm


def analyze_news_with_keywords(news: str | None = None):
    positive_keywords = ["growth", "upgrade", "profit", "strong", "beat", "surge"]
    negative_keywords = ["loss", "downgrade", "risk", "weak", "miss", "drop"]

    event_keyword_map = {
        "earnings": ["earnings", "revenue", "profit", "beat", "miss", "guidance"],
        "upgrade": ["upgrade", "raised rating", "outperform", "buy rating"],
        "downgrade": ["downgrade", "cut rating", "underperform", "sell rating"],
        "guidance": ["guidance", "outlook", "forecast"],
        "product_launch": ["launch", "product", "release", "new chip", "new platform"],
        "partnership": ["partnership", "collaboration", "agreement", "joint venture"],
        "regulation": ["regulation", "investigation", "probe", "antitrust", "compliance"],
        "lawsuit": ["lawsuit", "sued", "legal", "court", "settlement"],
        "merger_acquisition": ["acquisition", "merger", "takeover", "buyout"]
    }

    positive_count = 0
    negative_count = 0
    reasons = []
    event_tags = []

    if news:
        news_lower = news.lower()

        for word in positive_keywords:
            if word in news_lower:
                positive_count += 1

        for word in negative_keywords:
            if word in news_lower:
                negative_count += 1

        for tag, keywords in event_keyword_map.items():
            for keyword in keywords:
                if keyword in news_lower:
                    event_tags.append(tag)
                    break

        if positive_count > 0:
            reasons.append(f"Detected {positive_count} positive news keyword(s).")
        if negative_count > 0:
            reasons.append(f"Detected {negative_count} negative news keyword(s).")
        if positive_count == 0 and negative_count == 0:
            reasons.append("No strong sentiment keyword detected in news.")

        if event_tags:
            reasons.append(f"Detected event tag(s): {', '.join(event_tags)}.")
        else:
            reasons.append("No major event tag detected.")
    else:
        reasons.append("No news provided.")

    news_score = (positive_count * 0.08) - (negative_count * 0.08)

    positive_event_tags = {"earnings", "upgrade", "guidance", "product_launch", "partnership", "merger_acquisition"}
    negative_event_tags = {"downgrade", "regulation", "lawsuit"}

    event_score = 0.0
    for tag in event_tags:
        if tag in positive_event_tags:
            event_score += 0.05
        elif tag in negative_event_tags:
            event_score -= 0.05

    total_news_score = news_score + event_score

    if event_score > 0:
        event_bias = "positive_event_bias"
    elif event_score < 0:
        event_bias = "negative_event_bias"
    else:
        event_bias = "neutral_event_bias"

    if total_news_score >= 0.16:
        news_signal = "positive"
    elif total_news_score <= -0.16:
        news_signal = "negative"
    else:
        news_signal = "neutral"

    return {
        "news_signal": news_signal,
        "news_score": round(total_news_score, 2),
        "sentiment_score": round(news_score, 2),
        "event_score": round(event_score, 2),
        "event_bias": event_bias,
        "event_tags": event_tags,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "news_reason": " ".join(reasons),
        "news_mode": "keyword"
    }
from app.config import NEWS_AGENT_MODE
from app.services.llm_client import analyze_news_with_llm

def run_news_agent(news: str | None = None):
    if NEWS_AGENT_MODE in {"gemini", "claude"} and news:
        return analyze_news_with_llm(news)

    return analyze_news_with_keywords(news)