from app.agents.technical_agent import run_technical_agent
from app.agents.news_agent import run_news_agent
from app.agents.risk_agent import run_risk_agent
from app.agents.decision_agent import run_decision_agent
from app.services.market_data import fetch_price_history
from app.services.indicator_engine import build_indicator_snapshot
from app.services.localizer import localize_output


def _build_analysis_result(
    symbol: str,
    technical_result: dict,
    news_result: dict,
    risk_result: dict,
    decision_result: dict
) -> dict:
    technical_signal = technical_result["technical_signal"]
    news_signal = news_result["news_signal"]

    if technical_signal == "bullish" and news_signal == "positive":
        alignment = "aligned_positive"
        aligned = True
    elif technical_signal == "bearish" and news_signal == "negative":
        alignment = "aligned_negative"
        aligned = True
    elif technical_signal == "neutral" and news_signal == "neutral":
        alignment = "aligned_neutral"
        aligned = True
    else:
        alignment = "mixed"
        aligned = False

    return {
        "symbol": symbol,
        "final_view": {
            "signal": decision_result["signal"],
            "action": decision_result["action"],
            "risk_level": decision_result["risk_level"],
            "confidence": decision_result["confidence"],
            "summary": decision_result["summary"]
        },
        "trade_plan": {
            "position_size_hint": decision_result["position_size_hint"],
            "entry_bias": decision_result["entry_bias"],
            "time_horizon": decision_result["time_horizon"],
            "trade_plan_note": decision_result["trade_plan_note"]
        },
        "agent_consensus": {
            "technical_signal": technical_signal,
            "news_signal": news_signal,
            "aligned": aligned,
            "alignment": alignment
        },
        "agent_details": {
            "technical_agent": technical_result,
            "news_agent": news_result,
            "risk_agent": risk_result,
            "decision_agent": decision_result
        }
    }


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
    language: str = "en"
):
    technical_result = run_technical_agent(
        price=price,
        volume=volume,
        rsi=rsi,
        swing_high=swing_high,
        swing_low=swing_low,
        ma_short=ma_short,
        ma_long=ma_long,
        volatility=volatility,
        returns_1d=returns_1d
    )

    news_result = run_news_agent(news=news)

    risk_result = run_risk_agent(
        price=price,
        rsi=rsi,
        swing_high=swing_high,
        swing_low=swing_low,
        technical_signal=technical_result["technical_signal"],
        news_signal=news_result["news_signal"],
        ma_short=ma_short,
        ma_long=ma_long,
        volatility=volatility,
        returns_1d=returns_1d
    )

    decision_result = run_decision_agent(
        technical_score=technical_result["technical_score"],
        news_score=news_result["news_score"],
        risk_level=risk_result["risk_level"],
        technical_signal=technical_result["technical_signal"],
        news_signal=news_result["news_signal"],
        event_bias=news_result["event_bias"],
        event_tags=news_result["event_tags"]
    )

    result = _build_analysis_result(
        symbol=symbol,
        technical_result=technical_result,
        news_result=news_result,
        risk_result=risk_result,
        decision_result=decision_result
    )

    return localize_output(result, language)


def run_symbol_analysis(
    symbol: str,
    news: str | None = None,
    period: str = "6mo",
    interval: str = "1d",
    language: str = "en"
):
    df = fetch_price_history(symbol=symbol, period=period, interval=interval)
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
        language=language
    )

    result["market_snapshot"] = snapshot
    return result


def run_watchlist_analysis(
    symbols: list[str],
    news_map: dict[str, str] | None = None,
    period: str = "6mo",
    interval: str = "1d",
    language: str = "en"
):
    news_map = news_map or {}
    results = []

    for symbol in symbols:
        try:
            analysis = run_symbol_analysis(
                symbol=symbol,
                news=news_map.get(symbol),
                period=period,
                interval=interval,
                language=language
            )
            results.append(analysis)
        except Exception as e:
            results.append({
                "symbol": symbol,
                "error": str(e),
                "language": language
            })

    valid_results = [r for r in results if "final_view" in r]

    ranked = sorted(
        valid_results,
        key=lambda x: x["final_view"]["confidence"],
        reverse=True
    )

    top_positive_candidates = [
        {
            "symbol": item["symbol"],
            "signal": item["final_view"]["signal"],
            "action": item["final_view"]["action"],
            "confidence": item["final_view"]["confidence"]
        }
        for item in ranked
        if item["final_view"]["signal"] == "positive_bias"
    ][:5]

    high_risk_symbols = [
        {
            "symbol": item["symbol"],
            "risk_level": item["final_view"]["risk_level"],
            "action": item["final_view"]["action"],
            "confidence": item["final_view"]["confidence"]
        }
        for item in ranked
        if item["final_view"]["risk_level"] == "high"
    ]

    neutral_watchlist = [
        {
            "symbol": item["symbol"],
            "signal": item["final_view"]["signal"],
            "action": item["final_view"]["action"],
            "confidence": item["final_view"]["confidence"]
        }
        for item in ranked
        if item["final_view"]["signal"] == "neutral"
    ]

    summary = {
        "total_symbols": len(symbols),
        "successful": len(valid_results),
        "failed": len(symbols) - len(valid_results),
        "top_candidates": [
            {
                "symbol": item["symbol"],
                "signal": item["final_view"]["signal"],
                "action": item["final_view"]["action"],
                "confidence": item["final_view"]["confidence"]
            }
            for item in ranked[:5]
        ],
        "top_positive_candidates": top_positive_candidates,
        "high_risk_symbols": high_risk_symbols,
        "neutral_watchlist": neutral_watchlist
    }

    if language == "zh":
        summary["summary_note"] = "已完成觀察清單分析，並依 confidence 由高到低排序。"
        summary["summary_note_zh"] = "系統已完成所有標的掃描，並整理出偏多候選、高風險標的與中性觀察清單。"
    else:
        summary["summary_note"] = "Watchlist analysis completed and ranked by confidence."

    return {
        "language": language,
        "watchlist_summary": summary,
        "results": results
    }