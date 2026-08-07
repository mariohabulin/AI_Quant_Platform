import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from benchmark import BuyAndHoldBenchmark, compare_strategy_to_benchmark


def market_data(prices=(100.0, 110.0)):
    return pd.DataFrame({"Close": list(prices)})


def test_buy_and_hold_zero_cost_return():
    result = BuyAndHoldBenchmark(initial_capital=10000).run(market_data())
    assert result["final_capital"] == pytest.approx(11000.0)
    assert result["total_return"] == pytest.approx(0.10)
    assert result["net_profit_loss"] == pytest.approx(1000.0)


def test_buy_and_hold_flat_market_has_zero_return_without_costs():
    result = BuyAndHoldBenchmark().run(market_data((100.0, 100.0)))
    assert result["total_return"] == pytest.approx(0.0)


def test_benchmark_applies_commission_slippage_and_spread():
    result = BuyAndHoldBenchmark(
        commission_rate=0.001,
        slippage_rate=0.002,
        spread_rate=0.004,
    ).run(market_data())
    assert result["entry_price"] > result["entry_market_price"]
    assert result["exit_price"] < result["exit_market_price"]
    assert result["total_commission"] > 0
    assert result["execution_cost"] > 0
    assert result["total_costs"] > 0
    assert result["final_capital"] < 11000.0


def test_benchmark_is_deterministic():
    engine = BuyAndHoldBenchmark(commission_rate=0.001, slippage_rate=0.001)
    assert engine.run(market_data()) == engine.run(market_data())


def test_benchmark_rejects_invalid_input():
    engine = BuyAndHoldBenchmark()
    with pytest.raises(TypeError, match="DataFrame"):
        engine.run([100, 110])
    with pytest.raises(ValueError, match="empty"):
        engine.run(pd.DataFrame())
    with pytest.raises(ValueError, match="Close"):
        engine.run(pd.DataFrame({"Open": [100, 110]}))


def test_benchmark_rejects_invalid_close_prices():
    engine = BuyAndHoldBenchmark()
    with pytest.raises(ValueError, match="positive numeric"):
        engine.run(market_data((100, 0)))
    with pytest.raises(ValueError, match="positive numeric"):
        engine.run(market_data((100, "bad")))


def test_benchmark_rejects_invalid_execution_parameters():
    with pytest.raises(ValueError, match="greater than zero"):
        BuyAndHoldBenchmark(initial_capital=0)
    with pytest.raises(ValueError, match="cannot be negative"):
        BuyAndHoldBenchmark(commission_rate=-0.01)
    with pytest.raises(ValueError, match="less than 1.0"):
        BuyAndHoldBenchmark(slippage_rate=1.0)


def test_compare_strategy_to_benchmark_reports_excess_return():
    benchmark = BuyAndHoldBenchmark(initial_capital=10000).run(market_data())
    comparison = compare_strategy_to_benchmark(12000, benchmark)
    assert comparison["strategy_return"] == pytest.approx(0.20)
    assert comparison["benchmark_return"] == pytest.approx(0.10)
    assert comparison["excess_return"] == pytest.approx(0.10)


def test_compare_strategy_can_underperform_benchmark():
    benchmark = BuyAndHoldBenchmark(initial_capital=10000).run(market_data())
    comparison = compare_strategy_to_benchmark(10500, benchmark)
    assert comparison["excess_return"] == pytest.approx(-0.05)


def test_compare_rejects_invalid_inputs():
    benchmark = BuyAndHoldBenchmark().run(market_data())
    with pytest.raises(TypeError, match="final capital"):
        compare_strategy_to_benchmark("11000", benchmark)
    with pytest.raises(TypeError, match="dictionary"):
        compare_strategy_to_benchmark(11000, [])
    with pytest.raises(ValueError, match="required fields"):
        compare_strategy_to_benchmark(11000, {})
