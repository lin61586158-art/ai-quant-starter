# -*- coding: utf-8 -*-
"""
backtest_engine.py — 基礎四策略回測

支援策略：ma_crossover | rsi | macd | bollinger
所有策略採 long-only：訊號=1 進場做多，訊號=-1 出場（不做空）。
"""
import numpy as np
import pandas as pd

from app.services.indicator_engine import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
)


SUPPORTED_STRATEGIES = ["ma_crossover", "rsi", "macd", "bollinger"]


# ── 策略訊號 ────────────────────────────────────────────────────

def _signals_ma_crossover(df: pd.DataFrame, short: int = 20, long: int = 50) -> pd.Series:
    close = df["close"]
    s = close.rolling(short).mean()
    l = close.rolling(long).mean()
    sig = pd.Series(0, index=df.index)
    sig[s > l] = 1
    sig[s < l] = -1
    return sig


def _signals_rsi(df: pd.DataFrame, low: float = 30, high: float = 70) -> pd.Series:
    rsi = calculate_rsi(df["close"])
    sig = pd.Series(0, index=df.index)
    sig[rsi < low]  = 1   # 超賣 → 做多
    sig[rsi > high] = -1  # 超買 → 出場
    return sig


def _signals_macd(df: pd.DataFrame) -> pd.Series:
    macd = calculate_macd(df["close"])
    hist = macd["histogram"]
    sig = pd.Series(0, index=df.index)
    sig[hist > 0] = 1
    sig[hist < 0] = -1
    return sig


def _signals_bollinger(df: pd.DataFrame) -> pd.Series:
    bb = calculate_bollinger_bands(df["close"])
    close = df["close"]
    sig = pd.Series(0, index=df.index)
    sig[close < bb["lower"]] = 1   # 跌破下軌 → 進場
    sig[close > bb["upper"]] = -1  # 突破上軌 → 出場
    return sig


_STRATEGY_FUNCS = {
    "ma_crossover": _signals_ma_crossover,
    "rsi":          _signals_rsi,
    "macd":         _signals_macd,
    "bollinger":    _signals_bollinger,
}


def _build_signals(df: pd.DataFrame, strategy: str) -> pd.Series:
    fn = _STRATEGY_FUNCS.get(strategy)
    if fn is None:
        raise ValueError(
            f"Unknown strategy '{strategy}'. Supported: {SUPPORTED_STRATEGIES}"
        )
    return fn(df)


# ── 回測核心 ────────────────────────────────────────────────────

def run_backtest(
    df: pd.DataFrame,
    strategy: str = "ma_crossover",
    initial_capital: float = 100_000.0,
    commission: float = 0.001,
) -> dict:
    """
    對單一策略執行 long-only 向量化回測。
    """
    if df is None or df.empty:
        raise ValueError("Empty price DataFrame.")
    if len(df) < 60:
        raise ValueError(f"Need at least 60 rows for backtest (got {len(df)}).")

    df = df.reset_index(drop=True).copy()
    raw_sig = _build_signals(df, strategy)

    # long-only：1=持倉，-1 視為出場 (0)，0 維持上一狀態
    pos = raw_sig.replace(-1, 0).where(raw_sig != 0).ffill().fillna(0)

    # 部位變化 → 交易（首日無前置部位，視為 0；若首日就持倉，下面 fillna 後仍然會記錄一筆）
    trades = pos.diff()
    trades.iloc[0] = pos.iloc[0]
    trade_count = int(trades.abs().sum())

    # 日報酬：上一天部位 × 今日報酬
    daily_ret = df["close"].pct_change().fillna(0)
    strat_ret = pos.shift(1).fillna(0) * daily_ret

    # 手續費（進出場時扣）
    cost = trades.abs() * commission
    strat_ret = strat_ret - cost

    # 權益曲線
    equity = (1 + strat_ret).cumprod() * initial_capital
    final_equity = float(equity.iloc[-1])

    # 績效指標
    total_return = final_equity / initial_capital - 1
    days = len(df)
    cagr = (final_equity / initial_capital) ** (252 / max(days, 1)) - 1 if final_equity > 0 else -1.0

    std = float(strat_ret.std())
    sharpe = (float(strat_ret.mean()) / std) * np.sqrt(252) if std > 0 else 0.0

    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    max_dd = float(drawdown.min()) if len(drawdown) else 0.0

    # 勝率（以每段持倉週期判定）
    win_rate, avg_trade_ret = _trade_stats(pos, daily_ret)

    # 對比 buy-and-hold
    bh_return = float(df["close"].iloc[-1] / df["close"].iloc[0] - 1)

    equity_curve = [
        {"date": d, "equity": round(float(e), 2)}
        for d, e in zip(df["date"], equity)
    ]

    return {
        "strategy":             strategy,
        "bars":                 days,
        "initial_capital":      initial_capital,
        "final_equity":         round(final_equity, 2),
        "total_return":         round(float(total_return), 4),
        "cagr":                 round(float(cagr), 4),
        "sharpe_ratio":         round(float(sharpe), 3),
        "max_drawdown":         round(max_dd, 4),
        "trade_count":          trade_count,
        "win_rate":             round(win_rate, 3),
        "avg_trade_return":     round(avg_trade_ret, 4),
        "buy_and_hold_return":  round(bh_return, 4),
        "outperform_bh":        round(float(total_return) - bh_return, 4),
        "equity_curve":         equity_curve,
    }


def _trade_stats(pos: pd.Series, daily_ret: pd.Series) -> tuple[float, float]:
    """以每段持倉期間累積報酬計算勝率 & 平均報酬。"""
    wins = 0
    total = 0
    cum_returns: list[float] = []

    in_pos = False
    seg_ret = 0.0
    for i in range(1, len(pos)):
        held = pos.iloc[i - 1] > 0
        if held:
            in_pos = True
            seg_ret = (1 + seg_ret) * (1 + daily_ret.iloc[i]) - 1
        if in_pos and not held:
            cum_returns.append(seg_ret)
            if seg_ret > 0:
                wins += 1
            total += 1
            seg_ret = 0.0
            in_pos = False

    if in_pos:
        cum_returns.append(seg_ret)
        if seg_ret > 0:
            wins += 1
        total += 1

    if total == 0:
        return 0.0, 0.0
    return wins / total, sum(cum_returns) / total


# ── 多策略比較 ──────────────────────────────────────────────────

def run_multi_backtest(
    df: pd.DataFrame,
    strategies: list[str] | None = None,
    initial_capital: float = 100_000.0,
    commission: float = 0.001,
) -> dict:
    """
    跑多個策略並依 Sharpe Ratio 排名。
    """
    strategies = strategies or SUPPORTED_STRATEGIES
    results: list[dict] = []

    for strat in strategies:
        try:
            r = run_backtest(df, strat, initial_capital, commission)
            # 從多策略結果剝除 equity_curve 以節省 payload
            r_summary = {k: v for k, v in r.items() if k != "equity_curve"}
            results.append(r_summary)
        except Exception as e:
            results.append({"strategy": strat, "error": str(e)})

    valid = [r for r in results if "error" not in r]
    ranked = sorted(valid, key=lambda x: x["sharpe_ratio"], reverse=True)

    return {
        "strategies_tested": strategies,
        "ranked_by_sharpe":  ranked,
        "best_strategy":     ranked[0]["strategy"] if ranked else None,
        "all_results":       results,
    }
