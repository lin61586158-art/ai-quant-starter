# -*- coding: utf-8 -*-
"""
risk_agent.py — 風險評估 Agent

綜合多項指標給出風險等級（low / medium / high）：
    RSI 極端、波動率、單日漲跌幅、突破 swing 區、訊號分歧、MA 乖離
"""


def run_risk_agent(
    price: float,
    rsi: float | None,
    swing_high: float | None,
    swing_low: float | None,
    technical_signal: str,
    news_signal: str,
    ma_short: float | None = None,
    ma_long:  float | None = None,
    volatility: float | None = None,
    returns_1d: float | None = None,
) -> dict:
    risk_score = 0
    reasons:    list[str] = []

    # 1. RSI 極端
    if rsi is not None:
        if rsi >= 80 or rsi <= 20:
            risk_score += 2
            reasons.append(f"RSI 極端 ({rsi:.1f})")
        elif rsi >= 70 or rsi <= 30:
            risk_score += 1
            reasons.append(f"RSI 偏離中性 ({rsi:.1f})")

    # 2. 波動率
    if volatility is not None:
        if volatility > 0.05:
            risk_score += 2
            reasons.append(f"高波動 ({volatility:.3f})")
        elif volatility > 0.03:
            risk_score += 1
            reasons.append("中度波動")

    # 3. 單日大幅波動
    if returns_1d is not None and abs(returns_1d) > 0.05:
        risk_score += 1
        reasons.append(f"單日大幅 {returns_1d:+.1%}")

    # 4. 突破 swing 區
    if swing_high is not None and swing_low is not None and price is not None:
        if price > swing_high:
            risk_score += 1
            reasons.append("突破 swing high — 追高風險")
        elif price < swing_low:
            risk_score += 1
            reasons.append("跌破 swing low — 破底風險")

    # 5. 訊號分歧
    if (technical_signal == "bullish" and news_signal == "negative") or \
       (technical_signal == "bearish" and news_signal == "positive"):
        risk_score += 1
        reasons.append("技術面與消息面分歧")

    # 6. MA 乖離過大
    if ma_short is not None and ma_long is not None and ma_long != 0:
        gap = abs(ma_short - ma_long) / abs(ma_long)
        if gap > 0.10:
            risk_score += 1
            reasons.append(f"MA 乖離過大 ({gap:.1%})")

    # 等級判定
    if risk_score >= 4:
        risk_level = "high"
    elif risk_score >= 2:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_level":  risk_level,
        "risk_score":  risk_score,
        "risk_reason": "；".join(reasons) if reasons else "無顯著風險訊號。",
    }
