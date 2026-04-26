# -*- coding: utf-8 -*-
"""
localizer.py — 輸出多語言本地化
支援 language: "en" | "zh"
"""


ZH_SIGNAL_MAP = {
    "positive_bias": "偏多",
    "neutral":       "中性",
    "negative_bias": "偏空",
}

ZH_ACTION_MAP = {
    "possible_entry":   "可考慮進場",
    "wait_pullback":    "等待回測",
    "avoid_chasing":    "避免追高",
    "reduce_risk":      "降低風險",
    "watch":            "觀望",
    "no_trade":         "不交易",
}

ZH_RISK_MAP = {
    "low":    "低",
    "medium": "中",
    "high":   "高",
}

ZH_POSITION_SIZE_MAP = {
    "normal":  "正常倉位",
    "small":   "小倉",
    "minimal": "極小倉位",
    "reduce":  "減倉",
}

ZH_ENTRY_BIAS_MAP = {
    "pullback_or_breakout":   "回測或突破均可進場",
    "pullback_preferred":     "偏好回測進場",
    "avoid_breakout_chasing": "避免追突破",
    "exit_or_reduce":         "出場或減倉",
    "wait":                   "等待",
}

ZH_TIME_HORIZON_MAP = {
    "very_short_term":    "極短線",
    "short_term":         "短線",
    "short_to_medium_term": "短中線",
}

ZH_ALIGNMENT_MAP = {
    "aligned_positive": "技術面與消息面同向偏多",
    "aligned_negative": "技術面與消息面同向偏空",
    "aligned_neutral":  "技術面與消息面同為中性",
    "mixed":            "訊號分歧",
}

ZH_TECH_SIGNAL_MAP = {
    "bullish": "偏多",
    "bearish": "偏空",
    "neutral": "中性",
}

ZH_NEWS_SIGNAL_MAP = {
    "positive": "正面",
    "negative": "負面",
    "neutral":  "中性",
}

ZH_EVENT_TAG_MAP = {
    "earnings":   "財報",
    "macro":      "總體",
    "regulation": "監管",
    "merger":     "併購",
    "guidance":   "展望",
    "product":    "產品",
}

ZH_TRADE_NOTE_MAP = {
    "Bias remains positive, but wait for a better pullback entry.":
        "偏多趨勢持續，建議等待更好的回測進場點。",
    "Constructive setup; entry can be considered with defined risk.":
        "結構良好，可在設定停損的前提下考慮進場。",
    "Risk is elevated; reduce exposure and avoid aggressive positioning.":
        "風險偏高，應降低倉位，避免過度進場。",
    "No strong edge detected; patience is preferred.":
        "目前無明顯優勢，建議耐心觀望。",
    "Stay selective and manage risk carefully.":
        "保持選擇性，謹慎管理風險。",
    "Bias remains positive with supportive event flow, but wait for a better pullback entry.":
        "偏多且事件面支撐，但建議等待回測後再進場。",
    "Event risk is elevated; even if the setup looks constructive, stay selective.":
        "事件風險偏高，即使結構良好，仍應保持謹慎。",
}


def _build_summary_zh(localized: dict) -> str:
    """從 agent_details / agent_consensus 組出中文 summary，對應 decision_agent 的英文格式。"""
    details   = localized.get("agent_details", {}) or {}
    consensus = localized.get("agent_consensus", {}) or {}
    decision  = details.get("decision_agent", {}) or {}
    tech      = details.get("technical_agent", {}) or {}
    news      = details.get("news_agent", {}) or {}

    combined  = decision.get("combined_score")
    tech_sig  = ZH_TECH_SIGNAL_MAP.get(consensus.get("technical_signal"), consensus.get("technical_signal", "?"))
    news_sig  = ZH_NEWS_SIGNAL_MAP.get(consensus.get("news_signal"), consensus.get("news_signal", "?"))
    risk_lv   = ZH_RISK_MAP.get(decision.get("risk_level"), decision.get("risk_level", "?"))
    tech_sc   = tech.get("technical_score")
    news_sc   = news.get("news_score")
    tags      = news.get("event_tags") or []
    tags_zh   = [ZH_EVENT_TAG_MAP.get(t, t) for t in tags]

    parts = []
    if combined is not None:
        parts.append(f"合成分數 {combined:+.2f}")
    parts.append(f"技術面：{tech_sig}" + (f" ({tech_sc:+.2f})" if tech_sc is not None else ""))
    parts.append(f"消息面：{news_sig}" + (f" ({news_sc:+.2f})" if news_sc is not None else ""))
    parts.append(f"風險：{risk_lv}")
    if tags_zh:
        parts.append(f"事件：{','.join(tags_zh)}")
    return " | ".join(parts)


def localize_output(result: dict, language: str = "en") -> dict:
    if language not in {"en", "zh"}:
        language = "en"

    result["language"] = language

    if language == "en":
        return result

    localized = result.copy()

    # ── final_view ───────────────────────────────────────────────
    if "final_view" in localized:
        fv = localized["final_view"].copy()
        signal_label = ZH_SIGNAL_MAP.get(fv.get("signal"), fv.get("signal"))
        action_label = ZH_ACTION_MAP.get(fv.get("action"), fv.get("action"))
        risk_label   = ZH_RISK_MAP.get(fv.get("risk_level"), fv.get("risk_level"))

        fv["signal_label"]     = signal_label
        fv["action_label"]     = action_label
        fv["risk_level_label"] = risk_label
        fv["summary_zh"]       = _build_summary_zh(localized)
        fv["summary_short_zh"] = f"當前訊號【{signal_label}】，建議：{action_label}，風險：{risk_label}。"
        localized["final_view"] = fv

    # ── trade_plan ───────────────────────────────────────────────
    if "trade_plan" in localized:
        tp = localized["trade_plan"].copy()
        tp["position_size_hint_label"] = ZH_POSITION_SIZE_MAP.get(
            tp.get("position_size_hint"), tp.get("position_size_hint"))
        tp["entry_bias_label"] = ZH_ENTRY_BIAS_MAP.get(
            tp.get("entry_bias"), tp.get("entry_bias"))
        tp["time_horizon_label"] = ZH_TIME_HORIZON_MAP.get(
            tp.get("time_horizon"), tp.get("time_horizon"))
        tp["trade_plan_note_zh"] = ZH_TRADE_NOTE_MAP.get(
            tp.get("trade_plan_note"), tp.get("trade_plan_note"))
        localized["trade_plan"] = tp

    # ── agent_consensus ──────────────────────────────────────────
    if "agent_consensus" in localized:
        ac = localized["agent_consensus"].copy()
        ac["alignment_label"] = ZH_ALIGNMENT_MAP.get(ac.get("alignment"), ac.get("alignment"))
        localized["agent_consensus"] = ac

    localized["language"] = "zh"
    return localized
