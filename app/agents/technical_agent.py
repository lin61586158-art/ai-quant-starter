def run_technical_agent(
    price: float,
    volume: float,
    rsi: float | None = None,
    swing_high: float | None = None,
    swing_low: float | None = None,
    ma_short: float | None = None,
    ma_long: float | None = None,
    volatility: float | None = None,
    returns_1d: float | None = None
):
    price_score = 0.0
    volume_score = 0.0
    rsi_score = 0.0
    fib_score = 0.0
    trend_score = 0.0
    volatility_score = 0.0
    return_score = 0.0
    reasons = []

    fib_levels = {}
    nearest_fib_level = None

    # 1. Price logic
    if price >= 200:
        price_score = 0.20
        reasons.append("Price is very strong.")
    elif price >= 100:
        price_score = 0.12
        reasons.append("Price is relatively strong.")
    elif price >= 50:
        price_score = 0.06
        reasons.append("Price is stable.")
    else:
        price_score = -0.05
        reasons.append("Price is relatively weak.")

    # 2. Volume logic
    if volume >= 3000000:
        volume_score = 0.20
        reasons.append("Trading volume is extremely high.")
    elif volume >= 1000000:
        volume_score = 0.12
        reasons.append("Trading volume is high.")
    elif volume >= 300000:
        volume_score = 0.05
        reasons.append("Trading volume is normal.")
    else:
        volume_score = -0.05
        reasons.append("Trading volume is low.")

    # 3. RSI logic
    if rsi is not None:
        if rsi < 30:
            rsi_score = 0.15
            reasons.append("RSI indicates oversold condition.")
        elif 30 <= rsi < 45:
            rsi_score = 0.08
            reasons.append("RSI is in a relatively supportive zone.")
        elif 45 <= rsi <= 55:
            rsi_score = 0.00
            reasons.append("RSI is neutral.")
        elif 55 < rsi <= 70:
            rsi_score = -0.05
            reasons.append("RSI is moderately elevated.")
        else:
            rsi_score = -0.15
            reasons.append("RSI indicates overbought condition.")
    else:
        reasons.append("No RSI provided.")

    # 4. Fibonacci logic
    if swing_high is not None and swing_low is not None and swing_high > swing_low:
        diff = swing_high - swing_low

        fib_levels = {
            "23.6%": round(swing_high - diff * 0.236, 2),
            "38.2%": round(swing_high - diff * 0.382, 2),
            "50.0%": round(swing_high - diff * 0.500, 2),
            "61.8%": round(swing_high - diff * 0.618, 2),
            "78.6%": round(swing_high - diff * 0.786, 2),
        }

        nearest_name = None
        nearest_value = None
        min_distance = None

        for level_name, level_value in fib_levels.items():
            distance = abs(price - level_value)
            if min_distance is None or distance < min_distance:
                min_distance = distance
                nearest_name = level_name
                nearest_value = level_value

        nearest_fib_level = {
            "name": nearest_name,
            "value": nearest_value,
            "distance": round(min_distance, 2) if min_distance is not None else None
        }

        if price > swing_high:
            fib_score = 0.15
            reasons.append("Price is above swing high, showing breakout strength.")
        elif price < swing_low:
            fib_score = -0.15
            reasons.append("Price is below swing low, showing breakdown weakness.")
        else:
            if nearest_name == "61.8%":
                fib_score = 0.12
                reasons.append("Price is near the 61.8% Fibonacci level.")
            elif nearest_name == "50.0%":
                fib_score = 0.08
                reasons.append("Price is near the 50.0% Fibonacci level.")
            elif nearest_name == "38.2%":
                fib_score = 0.06
                reasons.append("Price is near the 38.2% Fibonacci level.")
            elif nearest_name == "78.6%":
                fib_score = -0.05
                reasons.append("Price is near the 78.6% Fibonacci level.")
            else:
                fib_score = 0.00
                reasons.append("Price is not near a major Fibonacci support zone.")
    else:
        reasons.append("No valid Fibonacci swing range provided.")

    # 5. Moving average trend logic
    if ma_short is not None and ma_long is not None:
        if ma_short > ma_long:
            trend_score = 0.15
            reasons.append("Short moving average is above long moving average.")
        elif ma_short < ma_long:
            trend_score = -0.15
            reasons.append("Short moving average is below long moving average.")
        else:
            trend_score = 0.0
            reasons.append("Short and long moving averages are equal.")
    else:
        reasons.append("Moving average inputs are incomplete.")

    # 6. Volatility logic
    if volatility is not None:
        if volatility > 0.05:
            volatility_score = -0.12
            reasons.append("Volatility is high.")
        elif 0.02 <= volatility <= 0.05:
            volatility_score = -0.03
            reasons.append("Volatility is moderate.")
        else:
            volatility_score = 0.03
            reasons.append("Volatility is relatively low.")
    else:
        reasons.append("No volatility provided.")

    # 7. Daily return logic
    if returns_1d is not None:
        if returns_1d > 0.05:
            return_score = -0.08
            reasons.append("One-day return is very strong, chasing risk may exist.")
        elif 0.01 < returns_1d <= 0.05:
            return_score = 0.04
            reasons.append("One-day return is positive.")
        elif -0.03 <= returns_1d <= 0.01:
            return_score = 0.0
            reasons.append("One-day return is neutral.")
        else:
            return_score = -0.06
            reasons.append("One-day return is weak.")
    else:
        reasons.append("No daily return provided.")

    technical_score = (
        price_score
        + volume_score
        + rsi_score
        + fib_score
        + trend_score
        + volatility_score
        + return_score
    )

    if technical_score >= 0.30:
        technical_signal = "bullish"
    elif technical_score <= -0.20:
        technical_signal = "bearish"
    else:
        technical_signal = "neutral"

    return {
        "technical_signal": technical_signal,
        "technical_score": round(technical_score, 2),
        "price_score": round(price_score, 2),
        "volume_score": round(volume_score, 2),
        "rsi_score": round(rsi_score, 2),
        "fib_score": round(fib_score, 2),
        "trend_score": round(trend_score, 2),
        "volatility_score": round(volatility_score, 2),
        "return_score": round(return_score, 2),
        "nearest_fib_level": nearest_fib_level,
        "fib_levels": fib_levels,
        "technical_reason": " ".join(reasons)
    }