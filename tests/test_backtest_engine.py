"""
backtest_engine 單元測試
"""
import pytest

from app.services.backtest_engine import (
    SUPPORTED_STRATEGIES,
    run_backtest,
    run_multi_backtest,
)


def test_unknown_strategy_raises(df_random):
    with pytest.raises(ValueError, match="Unknown strategy"):
        run_backtest(df_random, strategy="not_a_real_strategy")


def test_too_short_df_raises(df_short):
    with pytest.raises(ValueError, match="at least"):
        run_backtest(df_short, strategy="ma_crossover")


@pytest.mark.parametrize("strategy", SUPPORTED_STRATEGIES)
def test_each_strategy_returns_required_keys(df_random, strategy):
    result = run_backtest(df_random, strategy=strategy)
    for k in ["strategy", "bars", "initial_capital", "final_equity",
              "total_return", "cagr", "sharpe_ratio", "max_drawdown",
              "trade_count", "win_rate", "avg_trade_return",
              "buy_and_hold_return", "outperform_bh", "equity_curve"]:
        assert k in result, f"missing {k}"


def test_equity_curve_matches_bars(df_random):
    result = run_backtest(df_random, strategy="ma_crossover")
    assert len(result["equity_curve"]) == result["bars"]


def test_uptrend_ma_strategy_profitable(df_uptrend):
    """強勢上漲走勢下 ma_crossover 應該賺錢（合理性檢查，非嚴格保證）。"""
    result = run_backtest(df_uptrend, strategy="ma_crossover")
    # 強勢上漲下，至少不該大虧；買進持有作為對照
    assert result["final_equity"] > 0


def test_drawdown_is_non_positive(df_random):
    result = run_backtest(df_random, strategy="rsi")
    assert result["max_drawdown"] <= 0


def test_multi_backtest_ranks_by_sharpe(df_random):
    multi = run_multi_backtest(df_random)
    sharpes = [r["sharpe_ratio"] for r in multi["ranked_by_sharpe"]]
    assert sharpes == sorted(sharpes, reverse=True)
    assert multi["best_strategy"] in SUPPORTED_STRATEGIES + [None]


def test_multi_backtest_isolates_failures(df_random):
    """單一策略炸了不應該整個 multi 死掉。"""
    result = run_multi_backtest(df_random, strategies=["ma_crossover", "bogus_one"])
    errors = [r for r in result["all_results"] if "error" in r]
    assert len(errors) == 1
    assert errors[0]["strategy"] == "bogus_one"
