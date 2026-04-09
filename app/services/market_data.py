import yfinance as yf
import pandas as pd


def fetch_price_history(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"No market data returned for symbol: {symbol}")

    df = df.reset_index()

    # Normalize column names
    rename_map = {
        "Date": "date",
        "Datetime": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }
    df = df.rename(columns=rename_map)

    required_cols = ["date", "open", "high", "low", "close", "volume"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' for symbol: {symbol}")

    return df[required_cols]