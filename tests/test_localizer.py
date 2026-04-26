"""
localizer 單元測試 —— summary 中譯
"""
from app.services.localizer import localize_output


def _make_result():
    return {
        "symbol": "AAPL",
        "final_view": {
            "signal": "positive_bias", "action": "possible_entry",
            "risk_level": "low", "confidence": 0.85,
            "summary": "Combined +0.32 | Tech: bullish (+0.25) | News: positive (+0.20) | Risk: low | Events: earnings",
        },
        "trade_plan": {
            "position_size_hint": "normal",
            "entry_bias": "pullback_or_breakout",
            "time_horizon": "short_to_medium_term",
            "trade_plan_note": "Constructive setup; entry can be considered with defined risk.",
        },
        "agent_consensus": {
            "technical_signal": "bullish", "news_signal": "positive",
            "aligned": True, "alignment": "aligned_positive",
        },
        "agent_details": {
            "technical_agent": {"technical_score": 0.25},
            "news_agent":      {"news_score": 0.20, "event_tags": ["earnings", "guidance"]},
            "decision_agent":  {"combined_score": 0.32, "risk_level": "low"},
        },
    }


def test_english_pass_through():
    result = localize_output(_make_result(), "en")
    assert result["language"] == "en"
    assert "summary_zh" not in result["final_view"]


def test_zh_summary_includes_chinese_signals():
    result = localize_output(_make_result(), "zh")
    summary = result["final_view"]["summary_zh"]
    assert "技術面：偏多" in summary
    assert "消息面：正面" in summary
    assert "風險：低" in summary
    assert "合成分數" in summary
    assert "+0.32" in summary


def test_zh_summary_translates_event_tags():
    result = localize_output(_make_result(), "zh")
    summary = result["final_view"]["summary_zh"]
    assert "財報" in summary
    assert "展望" in summary


def test_zh_short_summary_format():
    result = localize_output(_make_result(), "zh")
    short = result["final_view"]["summary_short_zh"]
    assert "偏多" in short and "可考慮進場" in short and "低" in short


def test_zh_trade_plan_note_translated():
    result = localize_output(_make_result(), "zh")
    note_zh = result["trade_plan"]["trade_plan_note_zh"]
    assert note_zh == "結構良好，可在設定停損的前提下考慮進場。"


def test_zh_agent_consensus_alignment():
    result = localize_output(_make_result(), "zh")
    assert result["agent_consensus"]["alignment_label"] == "技術面與消息面同向偏多"


def test_zh_handles_missing_event_tags():
    r = _make_result()
    r["agent_details"]["news_agent"]["event_tags"] = []
    result = localize_output(r, "zh")
    summary = result["final_view"]["summary_zh"]
    assert "事件" not in summary  # 沒有 tags 時不該出現此區塊


def test_zh_handles_missing_combined_score():
    r = _make_result()
    del r["agent_details"]["decision_agent"]["combined_score"]
    result = localize_output(r, "zh")
    summary = result["final_view"]["summary_zh"]
    assert "合成分數" not in summary  # 缺欄位時優雅省略
    assert "技術面：偏多" in summary  # 其他欄位仍存在
