def analyze_market(
    symbol: str,
    price: float,
    volume: float,
    news: str | None = None,
    rsi: float | None = None,
    swing_high: float | None = None,
    swing_low: float | None = None
):
    price_score = 0.0
    volume_score = 0.0
    news_score = 0.0
    rsi_score = 0.0
    fib_score = 0.0
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

    # 3. News logic
    positive_keywords = ["growth", "upgrade", "profit", "strong", "beat", "surge"]
    negative_keywords = ["loss", "downgrade", "risk", "weak", "miss", "drop"]

    positive_count = 0
    negative_count = 0

    if news:
        news_lower = news.lower()

        for word in positive_keywords:
            if word in news_lower:
                positive_count += 1

        for word in negative_keywords:
            if word in news_lower:
                negative_count += 1

    news_score = (positive_count * 0.08) - (negative_count * 0.08)

    if positive_count > 0:
        reasons.append(f"Detected {positive_count} positive news keyword(s).")
    if negative_count > 0:
        reasons.append(f"Detected {negative_count} negative news keyword(s).")
    if not news:
        reasons.append("No news provided.")

    # 4. RSI logic
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
        else:  # rsi > 70
            rsi_score = -0.15
            reasons.append("RSI indicates overbought condition.")
    else:
        reasons.append("No RSI provided.")

    # 5. Fibonacci logic
    if swing_high is not None and swing_low is not None and swing_high > swing_low:
        diff = swing_high - swing_low

        fib_levels = {
            "23.6%": round(swing_high - diff * 0.236, 2),
            "38.2%": round(swing_high - diff * 0.382, 2),
            "50.0%": round(swing_high - diff * 0.500, 2),
            "61.8%": round(swing_high - diff * 0.618, 2),
            "78.6%": round(swing_high - diff * 0.786, 2),
        }

        # Find nearest Fibonacci retracement level
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

        # Simple Fibonacci scoring logic
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

    # 6. Total score
    total_score = price_score + volume_score + news_score + rsi_score + fib_score

    # 7. Confidence mapping
    confidence = 0.50 + total_score
    if confidence < 0.05:
        confidence = 0.05
    if confidence > 0.95:
        confidence = 0.95

    # 8. Signal decision
    if total_score >= 0.30:
        signal = "positive_bias"
    elif total_score <= -0.20:
        signal = "negative_bias"
    else:
        signal = "neutral"

    return {
        "symbol": symbol,
        "signal": signal,
        "confidence": round(confidence, 2),
        "price_score": round(price_score, 2),
        "volume_score": round(volume_score, 2),
        "news_score": round(news_score, 2),
        "rsi_score": round(rsi_score, 2),
        "fib_score": round(fib_score, 2),
        "total_score": round(total_score, 2),
        "nearest_fib_level": nearest_fib_level,
        "fib_levels": fib_levels,
        "reason": " ".join(reasons)
    }