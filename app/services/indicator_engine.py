import pandas as pd


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def build_indicator_snapshot(
    df: pd.DataFrame,
    ma_short_window: int = 5,
    ma_long_window: int = 20,
    volatility_window: int = 10,
    swing_window: int = 20
) -> dict:
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if len(df) < max(ma_long_window, volatility_window, swing_window, 15):
        raise ValueError("Not enough data to calculate indicators.")

    work_df = df.copy()

    work_df["returns_1d"] = work_df["close"].pct_change()
    work_df["ma_short"] = work_df["close"].rolling(ma_short_window).mean()
    work_df["ma_long"] = work_df["close"].rolling(ma_long_window).mean()
    work_df["volatility"] = work_df["returns_1d"].rolling(volatility_window).std()
    work_df["rsi"] = calculate_rsi(work_df["close"], period=14)

    latest = work_df.iloc[-1]
    recent = work_df.tail(swing_window)

    snapshot = {
        "price": round(float(latest["close"]), 4),
        "volume": int(latest["volume"]),
        "rsi": round(float(latest["rsi"]), 4) if pd.notna(latest["rsi"]) else None,
        "ma_short": round(float(latest["ma_short"]), 4) if pd.notna(latest["ma_short"]) else None,
        "ma_long": round(float(latest["ma_long"]), 4) if pd.notna(latest["ma_long"]) else None,
        "volatility": round(float(latest["volatility"]), 6) if pd.notna(latest["volatility"]) else None,
        "returns_1d": round(float(latest["returns_1d"]), 6) if pd.notna(latest["returns_1d"]) else None,
        "swing_high": round(float(recent["high"].max()), 4),
        "swing_low": round(float(recent["low"].min()), 4),
        "snapshot_date": str(latest["date"])
    }

    return snapshot