import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from out_of_sample import ChronologicalDataSplitter, OutOfSampleValidator


class ThresholdStrategyEngine:
    def run(self, data):
        result = data.copy()
        result["Signal"] = 0
        if len(result) >= 2:
            result.iloc[0, result.columns.get_loc("Signal")] = 1
            result.iloc[-1, result.columns.get_loc("Signal")] = -1
        return result


def market_data(prices=(100, 101, 102, 103, 104, 105, 106, 107, 108, 109)):
    index = pd.date_range("2024-01-01", periods=len(prices), freq="D")
    return pd.DataFrame(
        {
            "Open": prices,
            "High": [price + 1 for price in prices],
            "Low": [price - 1 for price in prices],
            "Close": prices,
            "Volume": [1000] * len(prices),
        },
        index=index,
    )


def test_chronological_split_preserves_order_and_ratio():
    result = ChronologicalDataSplitter(0.70).split(market_data())

    assert result["in_sample_rows"] == 7
    assert result["out_of_sample_rows"] == 3
    assert result["in_sample"].index[-1] < result["out_of_sample"].index[0]
    assert list(result["in_sample"]["Close"]) == list(range(100, 107))
    assert list(result["out_of_sample"]["Close"]) == list(range(107, 110))


def test_split_returns_independent_dataframe_copies():
    data = market_data()
    result = ChronologicalDataSplitter().split(data)

    result["in_sample"].iloc[0, result["in_sample"].columns.get_loc("Close")] = 999

    assert data.iloc[0]["Close"] == 100


def test_split_never_produces_empty_partition_for_small_valid_dataset():
    data = market_data((100, 101))
    result = ChronologicalDataSplitter(0.99).split(data)

    assert result["in_sample_rows"] == 1
    assert result["out_of_sample_rows"] == 1


def test_split_rejects_invalid_fraction():
    with pytest.raises(TypeError, match="must be a number"):
        ChronologicalDataSplitter("0.7")
    with pytest.raises(ValueError, match="between 0 and 1"):
        ChronologicalDataSplitter(0)
    with pytest.raises(ValueError, match="between 0 and 1"):
        ChronologicalDataSplitter(1)


def test_split_rejects_invalid_input():
    splitter = ChronologicalDataSplitter()

    with pytest.raises(TypeError, match="DataFrame"):
        splitter.split([100, 101])
    with pytest.raises(ValueError, match="empty"):
        splitter.split(pd.DataFrame())
    with pytest.raises(ValueError, match="at least two rows"):
        splitter.split(market_data((100,)))


def test_split_rejects_non_chronological_index():
    data = market_data().sort_index(ascending=False)

    with pytest.raises(ValueError, match="monotonic increasing"):
        ChronologicalDataSplitter().split(data)


def test_oos_validator_runs_both_partitions_independently():
    validator = OutOfSampleValidator(
        ThresholdStrategyEngine(),
        in_sample_fraction=0.60,
        initial_capital=10000,
    )

    result = validator.run(market_data())

    assert result["split"]["in_sample_rows"] == 6
    assert result["split"]["out_of_sample_rows"] == 4
    assert result["in_sample"]["initial_capital"] == 10000
    assert result["out_of_sample"]["initial_capital"] == 10000
    assert result["in_sample"]["final_capital"] > 10000
    assert result["out_of_sample"]["final_capital"] > 10000


def test_oos_validator_includes_benchmark_and_excess_return():
    result = OutOfSampleValidator(ThresholdStrategyEngine()).run(market_data())

    for partition in ("in_sample", "out_of_sample"):
        assert result[partition]["benchmark"]["benchmark"] == "buy_and_hold"
        assert "strategy_return" in result[partition]["comparison"]
        assert "benchmark_return" in result[partition]["comparison"]
        assert "excess_return" in result[partition]["comparison"]


def test_oos_validator_exposes_generalization_summary():
    result = OutOfSampleValidator(ThresholdStrategyEngine()).run(market_data())

    assert set(result["generalization"]) == {
        "in_sample_strategy_return",
        "out_of_sample_strategy_return",
        "in_sample_excess_return",
        "out_of_sample_excess_return",
    }


def test_oos_validator_uses_same_execution_costs_for_strategy_and_benchmark():
    result = OutOfSampleValidator(
        ThresholdStrategyEngine(),
        commission_rate=0.001,
        slippage_rate=0.002,
        spread_rate=0.004,
    ).run(market_data())

    for partition in ("in_sample", "out_of_sample"):
        assert result[partition]["benchmark"]["total_costs"] > 0
        assert result[partition]["trade_history"][0]["total_costs"] > 0


def test_oos_validator_rejects_invalid_execution_configuration():
    with pytest.raises(ValueError, match="cannot be negative"):
        OutOfSampleValidator(
            ThresholdStrategyEngine(),
            commission_rate=-0.001,
        )
