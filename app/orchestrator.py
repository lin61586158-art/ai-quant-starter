from app.agents.technical_agent import run_technical_agent
from app.agents.news_agent      import run_news_agent
from app.agents.risk_agent      import run_risk_agent
from app.agents.decision_agent  import run_decision_agent
from app.services.market_data   import fetch_price_history
from app.services.indicator_engine import build_indicator_snapshot
from app.services.localizer     import localize_output


# ── 結果組裝 ────────────────────────────────────────────────────

def _build_analysis_result(
    symbol: str,
    technical_result: dict,
    news_result: dict,
    risk_result: dict,
    decision_result: dict,
) -> dict:
    tech_sig = technical_result["technical_signal"]
    news_sig = news_result["news_signal"]

    if tech_sig == "bullish" and news_sig == "positive":
        alignment, aligned = "aligned_positive", True
    elif tech_sig == "bearish" and news_sig == "negative":
        alignment, aligned = "aligned_negative", True
    elif tech_sig == "neutral" and news_sig == "neutral":
        alignment, aligned = "aligned_neutral", True
    else:
        alignment, aligned = "mixed", False

    return {
        "symbol": symbol,
        "final_view": {
            "signal":     decision_result["signal"],
            "action":     decision_result["action"],
            "risk_level": decision_result["risk_level"],
            "confidence": decision_result["confidence"],
            "summary":    decision_result["summary"],
        },
        "trade_plan": {
            "position_size_hint": decision_result["position_size_hint"],
            "entry_bias":         decision_result["entry_bias"],
            "time_horizon":       decision_result["time_horizon"],
            "trade_plan_note":    decision_result["trade_plan_note"],
        },
        "agent_consensus": {
            "technical_signal": tech_sig,
            "news_signal":      news_sig,
            "aligned":          aligned,
            "alignment":        alignment,
        },
        "agent_details": {
            "technical_agent": technical_result,
            "news_agent":      news_result,
            "risk_agent":      risk_result,
            "decision_agent":  decision_result,
        },
    }


# ── 手動輸入分析 ─────────────────────────────────────────────────

def run_analysis(
    symbol: str,
    price: float,
    volume: float,
    news: str | None = None,
    rsi: float | None = None,
    swing_high: float | None = None,
    swing_low: float | None = None,
    ma_short: float | None = None,
    ma_long: float | None = None,
    volatility: float | None = None,
    returns_1d: float | None = None,
    # ── 新增指標 ──────────────────
    macd_hist: float | None = None,
    macd_cross: str | None = None,
    macd_crossover: str | None = None,
    bb_pct_b: float | None = None,
    bb_position: str | None = None,
    bb_bandwidth: float | None = None,
    atr: float | None = None,
    language: str = "en",
):
    technical_result = run_technical_agent(
        price=price, volume=volume, rsi=rsi,
        swing_high=swing_high, swing_low=swing_low,
        ma_short=ma_short, ma_long=ma_long,
        volatility=volatility, returns_1d=returns_1d,
        macd_hist=macd_hist, macd_cross=macd_cross,
        macd_crossover=macd_crossover,
        bb_pct_b=bb_pct_b, bb_position=bb_position,
        bb_bandwidth=bb_bandwidth, atr=atr,
    )
    news_result = run_news_agent(news=news)
    risk_result = run_risk_agent(
        price=price, rsi=rsi,
        swing_high=swing_high, swing_low=swing_low,
        technical_signal=technical_result["technical_signal"],
        news_signal=news_result["news_signal"],
        ma_short=ma_short, ma_long=ma_long,
        volatility=volatility, returns_1d=returns_1d,
    )
    decision_result = run_decision_agent(
        technical_score=technical_result["technical_score"],
        news_score=news_result["news_score"],
        risk_level=risk_result["risk_level"],
        technical_signal=technical_result["technical_signal"],
        news_signal=news_result["news_signal"],
        event_bias=news_result["event_bias"],
        event_tags=news_result["event_tags"],
    )

    result = _build_analysis_result(symbol, technical_result, news_result, risk_result, decision_result)
    return localize_output(result, language)


# ── 自動抓取資料分析 ─────────────────────────────────────────────

def run_symbol_analysis(
    symbol: str,
    news: str | None = None,
    period: str = "6mo",
    interval: str = "1d",
    language: str = "en",
):
    df       = fetch_price_history(symbol=symbol, period=period, interval=interval)
    snapshot = build_indicator_snapshot(df)

    result = run_analysis(
        symbol=symbol,
        price=snapshot["price"],
        volume=snapshot["volume"],
        news=news,
        rsi=snapshot["rsi"],
        swing_high=snapshot["swing_high"],
        swing_low=snapshot["swing_low"],
        ma_short=snapshot["ma_short"],
        ma_long=snapshot["ma_long"],
        volatility=snapshot["volatility"],
        returns_1d=snapshot["returns_1d"],
        # ── 傳遞新指標 ──────────────
        macd_hist=snapshot.get("macd_hist"),
        macd_cross=snapshot.get("macd_cross"),
        macd_crossover=snapshot.get("macd_crossover"),
        bb_pct_b=snapshot.get("bb_pct_b"),
        bb_position=snapshot.get("bb_position"),
        bb_bandwidth=snapshot.get("bb_bandwidth"),
        atr=snapshot.get("atr"),
        language=language,
    )
    result["market_snapshot"] = snapshot
    return result


# ── Watchlist 批次分析 ───────────────────────────────────────────

def run_watchlist_analysis(
    symbols: list[str],
    news_map: dict[str, str] | None = None,
    period: str = "6mo",
    interval: str = "1d",
    language: str = "en",
):
    news_map = news_map or {}
    results  = []

    for symbol in symbols:
        try:
            analysis = run_symbol_analysis(
                symbol=symbol,
                news=news_map.get(symbol),
                period=period,
                interval=interval,
                language=language,
            )
            results.append(analysis)
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e), "language": language})

    valid   = [r for r in results if "final_view" in r]
    ranked  = sorted(valid, key=lambda x: x["final_view"]["confidence"], reverse=True)

    def _compact(item):
        return {
            "symbol":     item["symbol"],
            "signal":     item["final_view"]["signal"],
            "action":     item["final_view"]["action"],
            "confidence": item["final_view"]["confidence"],
        }

    top_positive = [_compact(r) for r in ranked if r["final_view"]["signal"] == "positive_bias"][:5]
    high_risk    = [
        {**_compact(r), "risk_level": r["final_view"]["risk_level"]}
        for r in ranked if r["final_view"]["risk_level"] == "high"
    ]
    neutral_list = [_compact(r) for r in ranked if r["final_view"]["signal"] == "neutral"]

    summary = {
        "total_symbols":         len(symbols),
        "successful":            len(valid),
        "failed":                len(symbols) - len(valid),
        "top_candidates":        [_compact(r) for r in ranked[:5]],
        "top_positive_candidates": top_positive,
        "high_risk_symbols":     high_risk,
        "neutral_watchlist":     neutral_list,
        "summary_note": (
            "自選股分析完成，依信心分數排列。" if language == "zh"
            else "Watchlist analysis completed and ranked by confidence."
        ),
    }

    return {"language": language, "watchlist_summary": summary, "results": results}
