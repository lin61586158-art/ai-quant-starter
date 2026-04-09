from fastapi import FastAPI
from pydantic import BaseModel
from app.orchestrator import run_analysis, run_symbol_analysis, run_watchlist_analysis

app = FastAPI(title="AI Quant Starter")


class AnalyzeRequest(BaseModel):
    symbol: str
    price: float
    volume: float
    news: str | None = None
    rsi: float | None = None
    swing_high: float | None = None
    swing_low: float | None = None
    ma_short: float | None = None
    ma_long: float | None = None
    volatility: float | None = None
    returns_1d: float | None = None
    language: str = "en"


class AnalyzeSymbolRequest(BaseModel):
    symbol: str
    news: str | None = None
    period: str = "6mo"
    interval: str = "1d"
    language: str = "en"


class AnalyzeWatchlistRequest(BaseModel):
    symbols: list[str]
    news_map: dict[str, str] | None = None
    period: str = "6mo"
    interval: str = "1d"
    language: str = "en"


@app.get("/")
def root():
    return {"message": "AI Quant Starter is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return run_analysis(
        symbol=req.symbol,
        price=req.price,
        volume=req.volume,
        news=req.news,
        rsi=req.rsi,
        swing_high=req.swing_high,
        swing_low=req.swing_low,
        ma_short=req.ma_short,
        ma_long=req.ma_long,
        volatility=req.volatility,
        returns_1d=req.returns_1d,
        language=req.language
    )


@app.post("/analyze-symbol")
def analyze_symbol(req: AnalyzeSymbolRequest):
    return run_symbol_analysis(
        symbol=req.symbol,
        news=req.news,
        period=req.period,
        interval=req.interval,
        language=req.language
    )


@app.post("/analyze-watchlist")
def analyze_watchlist(req: AnalyzeWatchlistRequest):
    return run_watchlist_analysis(
        symbols=req.symbols,
        news_map=req.news_map,
        period=req.period,
        interval=req.interval,
        language=req.language
    )