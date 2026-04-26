"""
Agent 單元測試
"""
import pytest

from app.agents.decision_agent import run_decision_agent
from app.agents.news_agent import _extract_json, _keyword_analyze, run_news_agent
from app.agents.risk_agent import run_risk_agent
from app.agents.technical_agent import run_technical_agent


# ── technical_agent ──────────────────────────────────────────────

def test_technical_agent_neutral_minimal():
    """只給 price/volume，其餘 None 應正常回傳，不應 crash。"""
    r = run_technical_agent(price=100, volume=500_000)
    assert r["technical_signal"] in {"bullish", "bearish", "neutral"}
    assert "score_breakdown" in r


def test_technical_agent_bullish_signals_aggregate():
    r = run_technical_agent(
        price=250, volume=5_000_000, rsi=35,
        ma_short=110, ma_long=100,
        macd_hist=0.5, macd_crossover="golden_cross",
        bb_position="near_lower",
    )
    assert r["technical_signal"] == "bullish"
    assert r["technical_score"] > 0


def test_technical_agent_score_breakdown_sums_to_total():
    """重構回歸：各分項加總應等於 technical_score（容許 round 誤差）。"""
    r = run_technical_agent(
        price=150, volume=2_000_000, rsi=40,
        swing_high=160, swing_low=140,
        ma_short=148, ma_long=145,
        volatility=0.025, returns_1d=0.02,
        macd_hist=0.3, macd_cross="bullish", macd_crossover="no_cross",
        bb_position="near_lower", bb_bandwidth=0.08,
        atr=2.5,
    )
    parts = sum(r["score_breakdown"].values())
    assert abs(parts - r["technical_score"]) < 0.05  # 各項分別 round(2) 累加誤差


def test_technical_agent_bearish_signals_aggregate():
    r = run_technical_agent(
        price=30, volume=100_000, rsi=82,
        ma_short=90, ma_long=100,
        macd_hist=-0.5, macd_crossover="death_cross",
        bb_position="above_upper",
        volatility=0.08, returns_1d=-0.06,
    )
    assert r["technical_signal"] == "bearish"
    assert r["technical_score"] < 0


# ── risk_agent ───────────────────────────────────────────────────

def test_risk_agent_swing_breakout_now_triggers():
    """Bug 修復回歸：當 price > swing_high 時 risk_score 應增加。"""
    r = run_risk_agent(
        price=110, rsi=50, swing_high=100, swing_low=80,
        technical_signal="bullish", news_signal="neutral",
    )
    assert "突破" in r["risk_reason"] or "swing" in r["risk_reason"].lower()


def test_risk_agent_high_when_extreme():
    r = run_risk_agent(
        price=100, rsi=85, swing_high=90, swing_low=70,
        technical_signal="bullish", news_signal="negative",
        volatility=0.08, returns_1d=0.07,
    )
    assert r["risk_level"] == "high"


def test_risk_agent_low_when_calm():
    r = run_risk_agent(
        price=100, rsi=50, swing_high=110, swing_low=90,
        technical_signal="neutral", news_signal="neutral",
        volatility=0.01, returns_1d=0.005,
    )
    assert r["risk_level"] == "low"


# ── news_agent (keyword mode) ────────────────────────────────────

def test_news_agent_empty():
    r = run_news_agent(None)
    assert r["news_signal"] == "neutral"
    r2 = run_news_agent("   ")
    assert r2["news_signal"] == "neutral"


def test_news_agent_positive_keywords():
    r = _keyword_analyze("Company beats earnings, surge in revenue, upgrade to buy rating")
    assert r["news_signal"] == "positive"
    assert r["news_score"] > 0
    assert "earnings" in r["event_tags"]


def test_news_agent_negative_keywords():
    r = _keyword_analyze("Stock crashes after lawsuit and fraud investigation, downgrade to sell")
    assert r["news_signal"] == "negative"
    assert r["news_score"] < 0


def test_news_agent_chinese_keywords():
    r = _keyword_analyze("公司財報超預期，獲利創新高，分析師看好")
    assert r["news_signal"] == "positive"


def test_extract_json_simple():
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_with_prose():
    assert _extract_json('Here is the analysis: {"signal":"positive","score":0.5}. Done.') \
        == {"signal": "positive", "score": 0.5}


def test_extract_json_handles_nested():
    """巢狀物件不應被貪婪正則吃掉。"""
    out = _extract_json('Result: {"a":1,"b":{"c":2}} extra junk')
    assert out == {"a": 1, "b": {"c": 2}}


def test_extract_json_skips_invalid_candidate():
    """第一個 { 是無效 JSON 時應跳到下一個 candidate。"""
    text = 'broken {not json} but here {"signal":"positive"} works'
    assert _extract_json(text) == {"signal": "positive"}


def test_extract_json_empty():
    assert _extract_json("") == {}
    assert _extract_json("no braces here") == {}


def test_extract_json_braces_inside_string():
    """字串內的 { } 不應被誤算進 brace 深度。"""
    assert _extract_json('{"text":"hi {fake} bye","n":1}') == {"text": "hi {fake} bye", "n": 1}


# ── decision_agent ───────────────────────────────────────────────

def test_decision_aligned_positive_low_risk():
    r = run_decision_agent(
        technical_score=0.4, news_score=0.3,
        risk_level="low", technical_signal="bullish",
        news_signal="positive", event_bias="bullish_event",
        event_tags=["earnings"],
    )
    assert r["signal"] == "positive_bias"
    assert r["action"] == "possible_entry"


def test_decision_negative():
    r = run_decision_agent(
        technical_score=-0.3, news_score=-0.2,
        risk_level="medium", technical_signal="bearish",
        news_signal="negative", event_bias="bearish_event",
        event_tags=[],
    )
    assert r["signal"] == "negative_bias"
    assert r["action"] == "reduce_risk"


def test_decision_high_risk_caps_action():
    """positive_bias + high risk 應退化成 avoid_chasing。"""
    r = run_decision_agent(
        technical_score=0.5, news_score=0.4,
        risk_level="high", technical_signal="bullish",
        news_signal="positive", event_bias="bullish_event",
        event_tags=["earnings"],
    )
    assert r["signal"] == "positive_bias"
    assert r["action"] == "avoid_chasing"


def test_decision_confidence_capped_at_one():
    r = run_decision_agent(
        technical_score=0.9, news_score=0.9,
        risk_level="low", technical_signal="bullish",
        news_signal="positive", event_bias="bullish_event",
        event_tags=[],
    )
    assert 0.0 <= r["confidence"] <= 1.0
