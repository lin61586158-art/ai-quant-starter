def run_decision_agent(
    technical_score: float,
    news_score: float,
    risk_level: str,
    technical_signal: str,
    news_signal: str,
    event_bias: str = "neutral_event_bias",
    event_tags: list[str] | None = None
):
    reasons = []
    event_tags = event_tags or []

    combined_score = technical_score + news_score

    # 1. Event-aware score adjustment
    event_adjustment = 0.0

    if event_bias == "positive_event_bias":
        event_adjustment += 0.03
        reasons.append("Positive event bias strengthens conviction.")
    elif event_bias == "negative_event_bias":
        event_adjustment -= 0.05
        reasons.append("Negative event bias reduces conviction.")

    high_risk_event_tags = {"lawsuit", "regulation", "downgrade"}
    positive_conviction_tags = {"earnings", "upgrade", "guidance", "partnership", "product_launch", "merger_acquisition"}

    if any(tag in high_risk_event_tags for tag in event_tags):
        event_adjustment -= 0.05
        reasons.append("High-risk event tag detected, adding caution.")

    if any(tag in positive_conviction_tags for tag in event_tags):
        event_adjustment += 0.02
        reasons.append("Constructive event tag detected.")

    adjusted_score = combined_score + event_adjustment

    # 2. Final signal
    if adjusted_score >= 0.35:
        signal = "positive_bias"
        reasons.append("Adjusted combined score supports a positive bias.")
    elif adjusted_score <= -0.20:
        signal = "negative_bias"
        reasons.append("Adjusted combined score supports a negative bias.")
    else:
        signal = "neutral"
        reasons.append("Adjusted combined score suggests a neutral view.")

    # 3. Action logic
    if signal == "positive_bias":
        if risk_level == "low":
            action = "possible_entry"
            reasons.append("Low risk supports possible entry.")
        elif risk_level == "medium":
            if event_bias == "negative_event_bias":
                action = "watch"
                reasons.append("Medium risk with negative event bias suggests caution.")
            else:
                action = "wait_pullback"
                reasons.append("Medium risk suggests waiting for a pullback.")
        else:
            action = "avoid_chasing"
            reasons.append("High risk suggests avoiding chasing.")
    elif signal == "negative_bias":
        if risk_level == "high":
            action = "reduce_risk"
            reasons.append("High risk and negative bias suggest reducing risk.")
        else:
            action = "watch"
            reasons.append("Negative bias is present, but immediate action is limited.")
    else:
        if risk_level == "low":
            action = "watch"
            reasons.append("Neutral signal with low risk suggests observation.")
        else:
            action = "no_trade"
            reasons.append("Neutral signal with elevated risk suggests no trade.")

    # 4. Confidence
    confidence = 0.50 + adjusted_score

    if risk_level == "medium":
        confidence -= 0.08
    elif risk_level == "high":
        confidence -= 0.15

    if any(tag in high_risk_event_tags for tag in event_tags):
        confidence -= 0.05

    if confidence < 0.05:
        confidence = 0.05
    if confidence > 0.95:
        confidence = 0.95

    # 5. Position size hint
    if signal == "positive_bias":
        if risk_level == "low":
            position_size_hint = "normal"
        elif risk_level == "medium":
            position_size_hint = "small"
        else:
            position_size_hint = "minimal"
    elif signal == "negative_bias":
        if risk_level == "high":
            position_size_hint = "reduce"
        else:
            position_size_hint = "minimal"
    else:
        position_size_hint = "minimal"

    # 6. Entry bias
    if action == "possible_entry":
        entry_bias = "pullback_or_breakout"
    elif action == "wait_pullback":
        entry_bias = "pullback_preferred"
    elif action == "avoid_chasing":
        entry_bias = "avoid_breakout_chasing"
    elif action == "reduce_risk":
        entry_bias = "exit_or_reduce"
    else:
        entry_bias = "wait"

    # 7. Time horizon
    if risk_level == "high":
        time_horizon = "very_short_term"
    elif risk_level == "medium":
        time_horizon = "short_term"
    else:
        time_horizon = "short_to_medium_term"

    # 8. Trade plan note
    if "lawsuit" in event_tags or "regulation" in event_tags:
        trade_plan_note = "Event risk is elevated; even if the setup looks constructive, stay selective."
    elif signal == "positive_bias" and risk_level == "medium" and event_bias == "positive_event_bias":
        trade_plan_note = "Bias remains positive with supportive event flow, but wait for a better pullback entry."
    elif signal == "positive_bias" and risk_level == "low":
        trade_plan_note = "Constructive setup; entry can be considered with defined risk."
    elif signal == "negative_bias" and risk_level == "high":
        trade_plan_note = "Risk is elevated; reduce exposure and avoid aggressive positioning."
    elif signal == "neutral":
        trade_plan_note = "No strong edge detected; patience is preferred."
    else:
        trade_plan_note = "Stay selective and manage risk carefully."

    # 9. Summary
    summary = (
        f"Technical signal is {technical_signal}, news signal is {news_signal}, "
        f"event bias is {event_bias}, and overall risk level is {risk_level}."
    )

    return {
        "signal": signal,
        "action": action,
        "risk_level": risk_level,
        "confidence": round(confidence, 2),
        "position_size_hint": position_size_hint,
        "entry_bias": entry_bias,
        "time_horizon": time_horizon,
        "trade_plan_note": trade_plan_note,
        "event_adjustment": round(event_adjustment, 2),
        "decision_reason": " ".join(reasons),
        "summary": summary
    }