"""
market_data 單元測試（純 normalize_symbol，避免外網依賴）
"""
import pytest

from app.services.market_data import normalize_symbol


@pytest.mark.parametrize("inp,expected", [
    ("AAPL",     "AAPL"),
    ("aapl",     "AAPL"),
    ("2330",     "2330.TW"),
    ("0050",     "0050.TW"),
    ("BTCUSDT",  "BTC-USD"),
    ("ETHUSDT",  "ETH-USD"),
    ("SOLUSDC",  "SOL-USD"),
    ("BTC-USD",  "BTC-USD"),
    ("2330.TW",  "2330.TW"),
])
def test_normalize_symbol(inp, expected):
    assert normalize_symbol(inp) == expected


def test_normalize_symbol_empty_raises():
    with pytest.raises(ValueError):
        normalize_symbol("")
    with pytest.raises(ValueError):
        normalize_symbol("   ")
