import pandas as pd


# ── 基礎指標計算 ────────────────────────────────────────────────

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs       = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> dict[str, pd.Series]:
    ema_fast    = close.ewm(span=fast, adjust=False).mean()
    ema_slow    = close.ewm(span=slow, adjust=False).mean()
    macd_line   = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram   = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def calculate_bollinger_bands(
    close: pd.Series,
    window: int = 20,
    num_std: float = 2.0
) -> dict[str, pd.Series]:
    sma    = close.rolling(window).mean()
    std    = close.rolling(window).std()
    upper  = sma + num_std * std
    lower  = sma - num_std * std
    bw     = (upper - lower) / sma          # Bandwidth
    pct_b  = (close - lower) / (upper - lower)  # %B
    return {"upper": upper, "middle": sma, "lower": lower, "bandwidth": bw, "pct_b": pct_b}


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, prev_close = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ── Snapshot ────────────────────────────────────────────────────

def build_indicator_snapshot(
    df: pd.DataFrame,
    ma_short_window:  int = 5,
    ma_long_window:   int = 20,
    volatility_window: int = 10,
    swing_window:     int = 20,
) -> dict:
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    min_rows = max(ma_long_window, volatility_window, swing_window, 26, 15)
    if len(df) < min_rows:
        raise ValueError(f"Need at least {min_rows} rows to calculate indicators (got {len(df)}).")

    w = df.copy()

    # ── 基本 ──────────────────────────────────
    w["returns_1d"] = w["close"].pct_change()
    w["ma_short"]   = w["close"].rolling(ma_short_window).mean()
    w["ma_long"]    = w["close"].rolling(ma_long_window).mean()
    w["volatility"] = w["returns_1d"].rolling(volatility_window).std()
    w["rsi"]        = calculate_rsi(w["close"])

    # ── MACD ──────────────────────────────────
    macd_data       = calculate_macd(w["close"])
    w["macd"]       = macd_data["macd"]
    w["macd_signal"]= macd_data["signal"]
    w["macd_hist"]  = macd_data["histogram"]

    # ── Bollinger Bands ───────────────────────
    bb              = calculate_bollinger_bands(w["close"])
    w["bb_upper"]   = bb["upper"]
    w["bb_middle"]  = bb["middle"]
    w["bb_lower"]   = bb["lower"]
    w["bb_bandwidth"]= bb["bandwidth"]
    w["bb_pct_b"]   = bb["pct_b"]

    # ── ATR ───────────────────────────────────
    w["atr"]        = calculate_atr(w)

    latest = w.iloc[-1]
    # swing 區間排除當日，才有「突破/跌破」的意義
    swing_lookback = w.iloc[-(swing_window + 1):-1] if len(w) > swing_window else w.iloc[:-1]

    def _f(val, ndigits=4):
        return round(float(val), ndigits) if pd.notna(val) else None

    # ── MACD 訊號方向 ─────────────────────────
    cur_hist  = _f(latest["macd_hist"])
    prev_hist = _f(w["macd_hist"].iloc[-2]) if len(w) >= 2 else None
    if cur_hist is None:
        macd_cross, macd_crossover = "neutral", "no_cross"
    else:
        macd_cross = "bullish" if cur_hist > 0 else "bearish" if cur_hist < 0 else "neutral"
        if prev_hist is not None and prev_hist < 0 < cur_hist:
            macd_crossover = "golden_cross"
        elif prev_hist is not None and prev_hist > 0 > cur_hist:
            macd_crossover = "death_cross"
        else:
            macd_crossover = "no_cross"

    # ── Bollinger 位置 ────────────────────────
    pct_b_val = _f(latest["bb_pct_b"])
    if pct_b_val is not None:
        if pct_b_val > 1.0:
            bb_position = "above_upper"
        elif pct_b_val > 0.8:
            bb_position = "near_upper"
        elif pct_b_val < 0.0:
            bb_position = "below_lower"
        elif pct_b_val < 0.2:
            bb_position = "near_lower"
        else:
            bb_position = "middle_band"
    else:
        bb_position = None

    snapshot = {
        # ── 基本 ──────────────────────────────
        "price":        _f(latest["close"]),
        "volume":       int(latest["volume"]) if pd.notna(latest["volume"]) else 0,
        "returns_1d":   _f(latest["returns_1d"], 6),
        "snapshot_date": str(latest["date"]),

        # ── 移動平均 ──────────────────────────
        "ma_short":     _f(latest["ma_short"]),
        "ma_long":      _f(latest["ma_long"]),
        "volatility":   _f(latest["volatility"], 6),

        # ── RSI ───────────────────────────────
        "rsi":          _f(latest["rsi"]),

        # ── Fibonacci swing（排除當日） ───────
        "swing_high":   _f(swing_lookback["high"].max()) if not swing_lookback.empty else None,
        "swing_low":    _f(swing_lookback["low"].min())  if not swing_lookback.empty else None,

        # ── MACD ──────────────────────────────
        "macd":         _f(latest["macd"]),
        "macd_signal":  _f(latest["macd_signal"]),
        "macd_hist":    _f(latest["macd_hist"]),
        "macd_cross":   macd_cross,
        "macd_crossover": macd_crossover,

        # ── Bollinger Bands ───────────────────
        "bb_upper":     _f(latest["bb_upper"]),
        "bb_middle":    _f(latest["bb_middle"]),
        "bb_lower":     _f(latest["bb_lower"]),
        "bb_bandwidth": _f(latest["bb_bandwidth"]),
        "bb_pct_b":     pct_b_val,
        "bb_position":  bb_position,

        # ── ATR ───────────────────────────────
        "atr":          _f(latest["atr"]),
    }

    return snapshot
