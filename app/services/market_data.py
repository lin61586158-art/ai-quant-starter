# -*- coding: utf-8 -*-
"""
market_data.py — 統一行情資料介面
支援：美股 / 台股 / 台股ETF / 加密貨幣（皆透過 yfinance）

回傳的 DataFrame 欄位（lowercase，indicator_engine 預期格式）：
    date, open, high, low, close, adj_close, volume
"""
import pandas as pd
import yfinance as yf


# ── Symbol 標準化 ───────────────────────────────────────────────

def normalize_symbol(symbol: str) -> str:
    """
    將使用者輸入的 symbol 轉成 yfinance 可讀格式。

    範例：
        AAPL        -> AAPL
        2330        -> 2330.TW
        0050        -> 0050.TW
        BTCUSDT     -> BTC-USD
        ETHUSDT     -> ETH-USD
        BTC-USD     -> BTC-USD（不變）
        2330.TW     -> 2330.TW（不變）
    """
    s = symbol.strip().upper()

    if not s:
        raise ValueError("Symbol is empty.")

    # 已經帶後綴的，直接回傳
    if "." in s or "-" in s:
        return s

    # 加密貨幣（Binance 風格）：BTCUSDT -> BTC-USD
    if s.endswith("USDT") and len(s) > 4:
        return f"{s[:-4]}-USD"
    if s.endswith("USDC") and len(s) > 4:
        return f"{s[:-4]}-USD"

    # 純數字：台股 / 台股 ETF（4~6 碼）
    if s.isdigit() and 4 <= len(s) <= 6:
        return f"{s}.TW"

    # 其他預設視為美股
    return s


# ── 抓取歷史價格 ────────────────────────────────────────────────

def fetch_price_history(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    回傳排序好的 OHLCV DataFrame（欄位皆 lowercase）。
    """
    ticker = normalize_symbol(symbol)

    df = yf.download(
        tickers=ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if df is None or df.empty:
        raise ValueError(
            f"No price data for symbol '{symbol}' (resolved as '{ticker}'). "
            f"Check the symbol or try a longer period."
        )

    # yfinance 在新版可能回傳 MultiIndex 欄位（即使單一 ticker）
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    rename_map = {
        "Date":      "date",
        "Datetime":  "date",
        "Open":      "open",
        "High":      "high",
        "Low":       "low",
        "Close":     "close",
        "Adj Close": "adj_close",
        "Volume":    "volume",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Price data missing columns: {missing}")

    df = df.dropna(subset=["close"]).reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    return df
