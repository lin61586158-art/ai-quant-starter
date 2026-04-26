# -*- coding: utf-8 -*-
"""
decision_agent.py — 最終決策整合 Agent

輸入：技術面分數、新聞分數、風險等級、各 agent 訊號 / 事件偏向
輸出：signal / action / risk_level / confidence / summary
      + 交易計畫（position_size_hint / entry_bias / time_horizon / trade_plan_note）

trade_plan_note 採用英文常見短語，由 localizer.py 對應中譯。
"""


# trade_plan_note 對應 localizer.py 的 ZH_TRADE_NOTE_MAP
NOTE_CONSTRUCTIVE   = "Constructive setup; entry can be considered with defined risk."
NOTE_WAIT_PULLBACK  = "Bias remains positive, but wait for a better pullback entry."
NOTE_HIGH_RISK      = "Risk is elevated; reduce exposure and avoid aggressive positioning."
NOTE_REDUCE         = "Stay selective and manage risk carefully."
NOTE_NEUTRAL        = "No strong edge detected; patience is preferred."
NOTE_EVENT_BULL     = "Bias remains positive with supportive event flow, but wait for a better pullback entry."
NOTE_EVENT_RISK     = "Event risk is elevated; even if the setup looks constructive, stay selective."


def run_decision_agent(
    technical_score: float,
    news_score:      float,
    risk_level:      str,
    technical_signal: str,
    news_signal:      str,
    event_bias:       str,
    event_tags:       list,
) -> dict:
    # 加權合成分數：技術面 70% / 新聞面 30%
    combined = technical_score * 0.7 + news_score * 0.3

    # ── 主訊號 ──────────────────────────────────────────────
    if combined >= 0.20:
        signal = "positive_bias"
    elif combined <= -0.15:
        signal = "negative_bias"
    else:
        signal = "neutral"

    # ── action / 部位 / 進場偏好 / 計畫 ────────────────────
    if signal == "positive_bias":
        if risk_level == "low":
            action             = "possible_entry"
            position_size_hint = "normal"
            entry_bias         = "pullback_or_breakout"
            trade_plan_note    = NOTE_CONSTRUCTIVE
        elif risk_level == "medium":
            action             = "wait_pullback"
            position_size_hint = "small"
            entry_bias         = "pullback_preferred"
            trade_plan_note    = NOTE_WAIT_PULLBACK
        else:  # high
            action             = "avoid_chasing"
            position_size_hint = "minimal"
            entry_bias         = "avoid_breakout_chasing"
            trade_plan_note    = NOTE_HIGH_RISK
    elif signal == "negative_bias":
        action             = "reduce_risk"
        position_size_hint = "reduce"
        entry_bias         = "exit_or_reduce"
        trade_plan_note    = NOTE_REDUCE
    else:
        action             = "watch"
        position_size_hint = "minimal"
        entry_bias         = "wait"
        trade_plan_note    = NOTE_NEUTRAL

    # ── 事件面修飾 ─────────────────────────────────────────
    if signal == "positive_bias" and event_bias == "bullish_event" and risk_level != "high":
        trade_plan_note = NOTE_EVENT_BULL
    if signal == "positive_bias" and risk_level == "high" and event_bias != "none":
        trade_plan_note = NOTE_EVENT_RISK

    # ── 時間框架 ───────────────────────────────────────────
    if risk_level == "high":
        time_horizon = "very_short_term"
    elif risk_level == "medium":
        time_horizon = "short_term"
    else:
        time_horizon = "short_to_medium_term"

    # ── 信心度（合成分數絕對值放大，封頂 1.0） ────────────
    confidence = round(min(1.0, abs(combined) * 1.8), 2)

    summary = (
        f"Combined {combined:+.2f} | Tech: {technical_signal} ({technical_score:+.2f}) "
        f"| News: {news_signal} ({news_score:+.2f}) | Risk: {risk_level}"
    )
    if event_tags:
        summary += f" | Events: {','.join(event_tags)}"

    return {
        "signal":             signal,
        "action":             action,
        "risk_level":         risk_level,
        "confidence":         confidence,
        "combined_score":     round(float(combined), 3),
        "summary":            summary,
        "position_size_hint": position_size_hint,
        "entry_bias":         entry_bias,
        "time_horizon":       time_horizon,
        "trade_plan_note":    trade_plan_note,
    }
