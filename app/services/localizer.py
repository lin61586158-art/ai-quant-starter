def localize_output(result: dict, language: str = "en") -> dict:
    if language not in {"en", "zh"}:
        language = "en"

    if language == "en":
        result["language"] = "en"
        return result

    zh_signal_map = {
        "positive_bias": "偏多",
        "neutral": "中性",
        "negative_bias": "偏空"
    }

    zh_action_map = {
        "possible_entry": "可考慮進場",
        "wait_pullback": "等待拉回",
        "avoid_chasing": "避免追價",
        "reduce_risk": "降低風險",
        "watch": "觀察",
        "no_trade": "不交易"
    }

    zh_risk_map = {
        "low": "低",
        "medium": "中",
        "high": "高"
    }

    zh_position_size_map = {
        "normal": "正常倉位",
        "small": "小倉位",
        "minimal": "極小倉位",
        "reduce": "減碼"
    }

    zh_entry_bias_map = {
        "pullback_or_breakout": "拉回或突破皆可",
        "pullback_preferred": "以拉回進場為主",
        "avoid_breakout_chasing": "避免突破追價",
        "exit_or_reduce": "出場或減碼",
        "wait": "等待"
    }

    zh_time_horizon_map = {
        "very_short_term": "超短期",
        "short_term": "短期",
        "short_to_medium_term": "短中期"
    }

    zh_alignment_map = {
        "aligned_positive": "正向一致",
        "aligned_negative": "負向一致",
        "aligned_neutral": "中性一致",
        "mixed": "訊號分歧"
    }

    localized = result.copy()

    if "final_view" in localized:
        fv = localized["final_view"].copy()
        fv["signal_label"] = zh_signal_map.get(fv.get("signal"), fv.get("signal"))
        fv["action_label"] = zh_action_map.get(fv.get("action"), fv.get("action"))
        fv["risk_level_label"] = zh_risk_map.get(fv.get("risk_level"), fv.get("risk_level"))

        signal_label = fv["signal_label"]
        action_label = fv["action_label"]
        risk_label = fv["risk_level_label"]
        fv["summary_zh"] = f"整體判斷為{signal_label}，目前建議{action_label}，風險等級為{risk_label}。"

        localized["final_view"] = fv

    if "trade_plan" in localized:
        tp = localized["trade_plan"].copy()
        tp["position_size_hint_label"] = zh_position_size_map.get(tp.get("position_size_hint"), tp.get("position_size_hint"))
        tp["entry_bias_label"] = zh_entry_bias_map.get(tp.get("entry_bias"), tp.get("entry_bias"))
        tp["time_horizon_label"] = zh_time_horizon_map.get(tp.get("time_horizon"), tp.get("time_horizon"))

        note_map = {
            "Bias remains positive, but wait for a better pullback entry.": "整體仍偏多，但建議等待更好的拉回進場點。",
            "Constructive setup; entry can be considered with defined risk.": "整體結構正向，可在風險可控前提下考慮進場。",
            "Risk is elevated; reduce exposure and avoid aggressive positioning.": "目前風險偏高，建議降低曝險並避免積極加碼。",
            "No strong edge detected; patience is preferred.": "目前沒有明確優勢，建議耐心觀察。",
            "Stay selective and manage risk carefully.": "建議審慎挑選標的並嚴格控管風險。",
            "Bias remains positive with supportive event flow, but wait for a better pullback entry.": "整體偏多且事件面支持，但仍建議等待更好的拉回進場點。",
            "Event risk is elevated; even if the setup looks constructive, stay selective.": "事件風險偏高，即使結構尚可，仍應審慎選擇。"
        }
        tp["trade_plan_note_zh"] = note_map.get(tp.get("trade_plan_note"), tp.get("trade_plan_note"))

        localized["trade_plan"] = tp

    if "agent_consensus" in localized:
        ac = localized["agent_consensus"].copy()
        ac["alignment_label"] = zh_alignment_map.get(ac.get("alignment"), ac.get("alignment"))
        localized["agent_consensus"] = ac

    localized["language"] = "zh"
    return localized