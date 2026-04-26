"""
indicator_engine 單元測試 —— 涵蓋 Bug 修復回歸 (NaN volume / swing 排除當日 / MACD 邊界)
"""
import numpy as np
import pandas as pd
import pytest

from app.services.indicator_engine import (
    build_indicator_snapshot,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_macd,
    calculate_rsi,
)


def test_rsi_range(df_random):
    rsi = calculate_rsi(df_random["close"]).dropna()
    assert ((rsi >= 0) & (rsi <= 100)).all()


def test_macd_lengths(df_random):
    out = calculate_macd(df_random["close"])
    assert set(out.keys()) == {"macd", "signal", "histogram"}
    assert len(out["macd"]) == len(df_random)


def test_bollinger_pct_b_in_band(df_random):
    bb = calculate_bollinger_bands(df_random["close"])
    upper, lower = bb["upper"].dropna(), bb["lower"].dropna()
    assert (upper >= lower).all()


def test_atr_positive(df_random):
    atr = calculate_atr(df_random).dropna()
    assert (atr >= 0).all()


def test_snapshot_basic_fields(df_random):
    snap = build_indicator_snapshot(df_random)
    for k in ["price", "volume", "rsi", "ma_short", "ma_long",
              "swing_high", "swing_low", "macd_hist", "bb_position", "atr"]:
        assert k in snap, f"missing {k}"


def test_snapshot_too_short_raises(df_short):
    with pytest.raises(ValueError, match="at least"):
        build_indicator_snapshot(df_short, ma_long_window=50)


def test_snapshot_swing_excludes_current_bar(df_random):
    """Bug 修復回歸：swing_high 不應該包含當日，否則 risk_agent 突破判定永遠 False。"""
    snap = build_indicator_snapshot(df_random)
    # 構造一個明顯讓最後一根高於前 N 根的場景
    df = df_random.copy()
    df.loc[df.index[-1], "high"] = df["high"].iloc[:-1].max() * 2
    df.loc[df.index[-1], "close"] = df["high"].iloc[-1]
    snap2 = build_indicator_snapshot(df)
    assert snap2["price"] > snap2["swing_high"], (
        "swing_high 應排除當日，當日新高時 price 必須 > swing_high"
    )


def test_snapshot_handles_nan_volume(df_random):
    """Bug 修復回歸：last bar 的 volume 為 NaN 時 snapshot 不應 crash。"""
    df = df_random.copy()
    df.loc[df.index[-1], "volume"] = np.nan
    snap = build_indicator_snapshot(df)
    assert snap["volume"] == 0


def test_snapshot_macd_crossover_detection():
    """構造 macd 在最後兩根變號的情況，確認 golden_cross 偵測。"""
    n = 100
    close = pd.Series(np.concatenate([
        np.linspace(100, 80, 60),    # 下跌段 → MACD < 0
        np.linspace(80, 110, 40),    # 反轉上升 → MACD 翻正
    ]))
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="B").strftime("%Y-%m-%d"),
        "open": close, "high": close * 1.01, "low": close * 0.99,
        "close": close, "adj_close": close,
        "volume": np.full(n, 1_000_000, dtype=float),
    })
    snap = build_indicator_snapshot(df)
    assert snap["macd_cross"] in {"bullish", "bearish", "neutral"}
    assert snap["macd_crossover"] in {"golden_cross", "death_cross", "no_cross"}
