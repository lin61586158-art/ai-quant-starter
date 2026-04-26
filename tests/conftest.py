"""
共用 pytest fixtures —— 產生模擬 OHLCV DataFrame，避免測試依賴外網。
"""
import numpy as np
import pandas as pd
import pytest


def _make_ohlcv(n: int, seed: int = 42, start_price: float = 100.0,
                drift: float = 0.0005, vol: float = 0.02) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, n)
    close = start_price * np.exp(np.cumsum(rets))
    high  = close * (1 + np.abs(rng.normal(0, 0.005, n)))
    low   = close * (1 - np.abs(rng.normal(0, 0.005, n)))
    open_ = close * (1 + rng.normal(0, 0.003, n))
    volume = rng.integers(500_000, 5_000_000, n).astype(float)
    dates = pd.date_range("2024-01-01", periods=n, freq="B").strftime("%Y-%m-%d")
    return pd.DataFrame({
        "date": dates, "open": open_, "high": high, "low": low,
        "close": close, "adj_close": close, "volume": volume,
    })


@pytest.fixture
def df_uptrend():
    return _make_ohlcv(120, seed=1, drift=0.003, vol=0.015)


@pytest.fixture
def df_random():
    return _make_ohlcv(120, seed=2, drift=0.0, vol=0.02)


@pytest.fixture
def df_short():
    return _make_ohlcv(40)
