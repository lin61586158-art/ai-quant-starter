def run_risk_agent(
    price: float,
    rsi: float | None = None,
    swing_high: float | None = None,
    swing_low: float | None = None,
    technical_signal: str | None = None,
    news_signal: str | None = None,
    ma_short: float | None = None,
    ma_long: float | None = None,
    volatility: float | None = None,
    returns_1d: float | None = None
):
    risk_score = 0.0
    reasons = []

    # 1. RSI risk
    if rsi is not None:
        if rsi > 70:
            risk_score += 0.20
            reasons.append("RSI is above 70, indicating overbought risk.")
        elif rsi < 30:
            risk_score += 0.05
            reasons.append("RSI is below 30, market may be unstable despite oversold condition.")
        else:
            reasons.append("RSI is within a manageable range.")
    else:
        reasons.append("No RSI provided for risk evaluation.")

    # 2. Price location risk
    if swing_high is not None and swing_low is not None and swing_high > swing_low:
        range_size = swing_high - swing_low

        if price > swing_high:
            risk_score += 0.25
            reasons.append("Price is above swing high, breakout may carry chasing risk.")
        elif price < swing_low:
            risk_score += 0.30
            reasons.append("Price is below swing low, breakdown risk is elevated.")
        else:
            upper_zone = swing_high - range_size * 0.10
            lower_zone = swing_low + range_size * 0.10

            if price >= upper_zone:
                risk_score += 0.12
                reasons.append("Price is close to the top of the swing range.")
            elif price <= lower_zone:
                risk_score += 0.08
                reasons.append("Price is close to the bottom of the swing range.")
            else:
                reasons.append("Price is positioned within the middle of the swing range.")
    else:
        reasons.append("No valid swing range provided for price location risk.")

    # 3. Signal conflict risk
    if technical_signal and news_signal:
        if technical_signal == "bullish" and news_signal == "negative":
            risk_score += 0.15
            reasons.append("Technical and news signals are conflicting.")
        elif technical_signal == "bearish" and news_signal == "positive":
            risk_score += 0.15
            reasons.append("Technical and news signals are conflicting.")
        else:
            reasons.append("Technical and news signals are aligned.")
    else:
        reasons.append("Signal conflict check is incomplete.")

    # 4. Trend conflict risk
    if ma_short is not None and ma_long is not None:
        if technical_signal == "bullish" and ma_short < ma_long:
            risk_score += 0.12
            reasons.append("Bullish technical view conflicts with moving average trend.")
        elif technical_signal == "bearish" and ma_short > ma_long:
            risk_score += 0.12
            reasons.append("Bearish technical view conflicts with moving average trend.")
        else:
            reasons.append("Moving average trend is not conflicting.")
    else:
        reasons.append("Moving average trend risk check is incomplete.")

    # 5. Volatility risk
    if volatility is not None:
        if volatility > 0.05:
            risk_score += 0.18
            reasons.append("Volatility is high, raising execution and reversal risk.")
        elif volatility > 0.02:
            risk_score += 0.06
            reasons.append("Volatility is moderate.")
        else:
            reasons.append("Volatility is relatively controlled.")
    else:
        reasons.append("No volatility provided for risk evaluation.")

    # 6. One-day return chasing risk
    if returns_1d is not None:
        if returns_1d > 0.05:
            risk_score += 0.15
            reasons.append("One-day return is very high, chasing risk is elevated.")
        elif returns_1d < -0.05:
            risk_score += 0.10
            reasons.append("One-day return is sharply negative, instability risk is elevated.")
        else:
            reasons.append("One-day return is within a normal range.")
    else:
        reasons.append("No daily return provided for risk evaluation.")

    # 7. Risk level mapping
    if risk_score >= 0.45:
        risk_level = "high"
    elif risk_score >= 0.18:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_level": risk_level,
        "risk_score": round(risk_score, 2),
        "risk_reason": " ".join(reasons)
    }