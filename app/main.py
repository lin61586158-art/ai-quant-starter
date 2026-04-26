from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.orchestrator import run_analysis, run_symbol_analysis, run_watchlist_analysis
from app.services.market_data import fetch_price_history
from app.services.backtest_engine import run_backtest, run_multi_backtest

app = FastAPI(
    title="AI Quant Starter",
    version="2.0.0",
    description="Multi-agent AI quantitative analysis API with backtesting."
)


# ── Request Models ───────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    symbol:    str
    price:     float
    volume:    float
    news:      Optional[str]   = None
    rsi:       Optional[float] = None
    swing_high: Optional[float] = None
    swing_low:  Optional[float] = None
    ma_short:  Optional[float] = None
    ma_long:   Optional[float] = None
    volatility: Optional[float] = None
    returns_1d: Optional[float] = None
    # 新增指標
    macd_hist:    Optional[float] = None
    macd_cross:   Optional[str]   = None
    macd_crossover: Optional[str] = None
    bb_pct_b:     Optional[float] = None
    bb_position:  Optional[str]   = None
    bb_bandwidth: Optional[float] = None
    atr:          Optional[float] = None
    language: str = "en"


class AnalyzeSymbolRequest(BaseModel):
    symbol:   str
    news:     Optional[str] = None
    period:   str = "6mo"
    interval: str = "1d"
    language: str = "en"


class AnalyzeWatchlistRequest(BaseModel):
    symbols:  list[str]
    news_map: Optional[dict[str, str]] = None
    period:   str = "6mo"
    interval: str = "1d"
    language: str = "en"


class BacktestRequest(BaseModel):
    symbol:          str
    strategy:        str = Field(default="ma_crossover",
                                  description="ma_crossover | rsi | macd | bollinger")
    period:          str = "1y"
    interval:        str = "1d"
    initial_capital: float = 100_000.0
    commission:      float = 0.001


class BacktestMultiRequest(BaseModel):
    symbol:          str
    strategies:      Optional[list[str]] = None
    period:          str = "1y"
    interval:        str = "1d"
    initial_capital: float = 100_000.0
    commission:      float = 0.001


# ── Endpoints ────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "AI Quant Starter v2.0 is running"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return run_analysis(**req.model_dump())


@app.post("/analyze-symbol")
def analyze_symbol(req: AnalyzeSymbolRequest):
    return run_symbol_analysis(**req.model_dump())


@app.post("/analyze-watchlist")
def analyze_watchlist(req: AnalyzeWatchlistRequest):
    return run_watchlist_analysis(**req.model_dump())


@app.post("/backtest")
def backtest(req: BacktestRequest):
    """
    對單一股票執行指定策略的回測。
    strategy 可選：ma_crossover | rsi | macd | bollinger
    """
    try:
        df = fetch_price_history(
            symbol=req.symbol,
            period=req.period,
            interval=req.interval,
        )
        result = run_backtest(
            df=df,
            strategy=req.strategy,
            initial_capital=req.initial_capital,
            commission=req.commission,
        )
        result["symbol"] = req.symbol
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@app.post("/backtest-multi")
def backtest_multi(req: BacktestMultiRequest):
    """
    同時跑多個策略並依 Sharpe Ratio 排名。
    """
    try:
        df = fetch_price_history(
            symbol=req.symbol,
            period=req.period,
            interval=req.interval,
        )
        result = run_multi_backtest(
            df=df,
            strategies=req.strategies,
            initial_capital=req.initial_capital,
            commission=req.commission,
        )
        result["symbol"] = req.symbol
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-backtest failed: {str(e)}")
