# -*- coding: utf-8 -*-
"""
technical_agent.py — 技術面評分 Agent

設計：每個指標寫成 (threshold, score, reason) 規則表，由 _eval_numeric / _eval_enum
通用評估器處理。新增/調整門檻只要動表，不必改邏輯。

回傳欄位與舊版完全相容。
"""
from typing import Callable


# ── 通用評估器 ───────────────────────────────────────────────────

def _eval_numeric(
    value: float | None,
    rules: list[tuple[Callable[[float], bool], float, str]],
    missing_reason: str,
) -> tuple[float, str]:
    """依序套用規則，第一個命中即回傳。"""
    if value is None:
        return 0.0, missing_reason
    for cond, score, reason in rules:
        if cond(value):
            return score, reason
    return 0.0, ""


def _eval_enum(
    value: str | None,
    table: dict[str, tuple[float, str]],
    missing_reason: str,
) -> tuple[float, str]:
    if value is None:
        return 0.0, missing_reason
    score, reason = table.get(value, (0.0, ""))
    return score, reason


# ── 規則表 ───────────────────────────────────────────────────────

PRICE_RULES = [
    (lambda x: x >= 200, 0.20, "Price is very strong."),
    (lambda x: x >= 100, 0.12, "Price is relatively strong."),
    (lambda x: x >= 50,  0.06, "Price is stable."),
    (lambda x: True,    -0.05, "Price is relatively weak."),
]

VOLUME_RULES = [
    (lambda x: x >= 3_000_000, 0.20, "Trading volume is extremely high."),
    (lambda x: x >= 1_000_000, 0.12, "Trading volume is high."),
    (lambda x: x >= 300_000,   0.05, "Trading volume is normal."),
    (lambda x: True,          -0.05, "Trading volume is low."),
]

RSI_RULES = [
    (lambda x: x < 30,   0.15,  "RSI indicates oversold condition."),
    (lambda x: x < 45,   0.08,  "RSI is in a relatively supportive zone."),
    (lambda x: x <= 55,  0.00,  "RSI is neutral."),
    (lambda x: x <= 70, -0.05,  "RSI is moderately elevated."),
    (lambda x: True,    -0.15,  "RSI indicates overbought condition."),
]

VOLATILITY_RULES = [
    (lambda x: x > 0.05,  -0.12, "Volatility is high."),
    (lambda x: x >= 0.02, -0.03, "Volatility is moderate."),
    (lambda x: True,       0.03, "Volatility is relatively low."),
]

RETURN_RULES = [
    (lambda x: x > 0.05,  -0.08, "One-day return is very strong, chasing risk may exist."),
    (lambda x: x > 0.01,   0.04, "One-day return is positive."),
    (lambda x: x >= -0.03, 0.00, "One-day return is neutral."),
    (lambda x: True,      -0.06, "One-day return is weak."),
]

BB_POSITION_TABLE = {
    "below_lower":  ( 0.12, "Price is below Bollinger lower band — potential reversal zone."),
    "near_lower":   ( 0.06, "Price is near Bollinger lower band — support zone."),
    "above_upper":  (-0.12, "Price is above Bollinger upper band — overbought zone."),
    "near_upper":   (-0.05, "Price is near Bollinger upper band — resistance zone."),
    "middle_band":  ( 0.00, "Price is within Bollinger middle band."),
}

# Fibonacci 命中時的中段加分
FIB_MIDRANGE_SCORE = {
    "61.8%":  0.12,
    "50.0%":  0.08,
    "38.2%":  0.06,
    "78.6%": -0.05,
}


# ── 主流程 ───────────────────────────────────────────────────────

def run_technical_agent(
    price: float,
    volume: float,
    rsi: float | None = None,
    swing_high: float | None = None,
    swing_low: float | None = None,
    ma_short: float | None = None,
    ma_long: float | None = None,
    volatility: float | None = None,
    returns_1d: float | None = None,
    macd_hist: float | None = None,
    macd_cross: str | None = None,
    macd_crossover: str | None = None,
    bb_pct_b: float | None = None,
    bb_position: str | None = None,
    bb_bandwidth: float | None = None,
    atr: float | None = None,
):
    reasons: list[str] = []

    def _apply(value, rules, missing):
        score, reason = _eval_numeric(value, rules, missing)
        if reason:
            reasons.append(reason)
        return score

    # 1-3, 6-7：純 numeric 規則
    price_score      = _apply(price,      PRICE_RULES,      "No price provided.")
    volume_score     = _apply(volume,     VOLUME_RULES,     "No volume provided.")
    rsi_score        = _apply(rsi,        RSI_RULES,        "No RSI provided.")
    volatility_score = _apply(volatility, VOLATILITY_RULES, "No volatility provided.")
    return_score     = _apply(returns_1d, RETURN_RULES,     "No daily return provided.")

    # 4. Fibonacci（特殊：要輸出 fib_levels / nearest_fib_level）
    fib_score, fib_levels, nearest_fib_level = _eval_fibonacci(price, swing_high, swing_low, reasons)

    # 5. MA 趨勢
    if ma_short is not None and ma_long is not None:
        if ma_short > ma_long:
            trend_score = 0.15; reasons.append("Short MA is above long MA (uptrend).")
        elif ma_short < ma_long:
            trend_score = -0.15; reasons.append("Short MA is below long MA (downtrend).")
        else:
            trend_score = 0.0; reasons.append("Short and long MA are equal.")
    else:
        trend_score = 0.0; reasons.append("Moving average inputs are incomplete.")

    # 8. MACD（crossover 優先於 cross）
    macd_score = 0.0
    if macd_hist is not None:
        if macd_crossover == "golden_cross":
            macd_score = 0.15;  reasons.append("MACD golden cross detected — bullish momentum.")
        elif macd_crossover == "death_cross":
            macd_score = -0.15; reasons.append("MACD death cross detected — bearish momentum.")
        elif macd_cross == "bullish":
            macd_score = 0.08;  reasons.append("MACD histogram is positive — upward momentum.")
        elif macd_cross == "bearish":
            macd_score = -0.08; reasons.append("MACD histogram is negative — downward momentum.")
    else:
        reasons.append("No MACD data provided.")

    # 9. Bollinger Bands
    bb_score, bb_reason = _eval_enum(bb_position, BB_POSITION_TABLE, "No Bollinger Band data provided.")
    if bb_reason:
        reasons.append(bb_reason)
    if bb_bandwidth is not None and bb_bandwidth < 0.05:
        reasons.append("Bollinger Band squeeze detected — potential breakout approaching.")

    technical_score = (
        price_score + volume_score + rsi_score + fib_score
        + trend_score + volatility_score + return_score
        + macd_score + bb_score
    )

    if technical_score >= 0.35:
        technical_signal = "bullish"
    elif technical_score <= -0.25:
        technical_signal = "bearish"
    else:
        technical_signal = "neutral"

    return {
        "technical_signal": technical_signal,
        "technical_score":  round(technical_score, 2),
        "score_breakdown": {
            "price_score":      round(price_score, 2),
            "volume_score":     round(volume_score, 2),
            "rsi_score":        round(rsi_score, 2),
            "fib_score":        round(fib_score, 2),
            "trend_score":      round(trend_score, 2),
            "volatility_score": round(volatility_score, 2),
            "return_score":     round(return_score, 2),
            "macd_score":       round(macd_score, 2),
            "bb_score":         round(bb_score, 2),
        },
        "nearest_fib_level": nearest_fib_level,
        "fib_levels":        fib_levels,
        "technical_reason":  " ".join(reasons),
    }


def _eval_fibonacci(price, swing_high, swing_low, reasons):
    if not (swing_high is not None and swing_low is not None and swing_high > swing_low):
        reasons.append("No valid Fibonacci swing range provided.")
        return 0.0, {}, None

    diff = swing_high - swing_low
    fib_levels = {
        "23.6%": round(swing_high - diff * 0.236, 2),
        "38.2%": round(swing_high - diff * 0.382, 2),
        "50.0%": round(swing_high - diff * 0.500, 2),
        "61.8%": round(swing_high - diff * 0.618, 2),
        "78.6%": round(swing_high - diff * 0.786, 2),
    }
    nearest_name  = min(fib_levels, key=lambda k: abs(price - fib_levels[k]))
    nearest_value = fib_levels[nearest_name]
    nearest_fib_level = {
        "name": nearest_name,
        "value": nearest_value,
        "distance": round(abs(price - nearest_value), 2),
    }

    if price > swing_high:
        reasons.append("Price is above swing high, showing breakout strength.")
        return 0.15, fib_levels, nearest_fib_level
    if price < swing_low:
        reasons.append("Price is below swing low, showing breakdown weakness.")
        return -0.15, fib_levels, nearest_fib_level

    score = FIB_MIDRANGE_SCORE.get(nearest_name, 0.0)
    reasons.append(f"Price is near the {nearest_name} Fibonacci level.")
    return score, fib_levels, nearest_fib_level
