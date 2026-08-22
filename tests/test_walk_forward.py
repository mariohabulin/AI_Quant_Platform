import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from walk_forward import WalkForwardSplitter, WalkForwardValidator


class ThresholdStrategyEngine:
    def run(self, data):
        result = data.copy()
        result["Signal"] = 0
        if len(result) >= 2:
            result.iloc[0, result.columns.get_loc("Signal")] = 1
            result.iloc[-1, result.columns.get_loc("Signal")] = -1
        return result


def market_data(rows=14):
    prices = list(range(100, 100 + rows))
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    return pd.DataFrame(
        {
            "Open": prices,
            "High": [price + 1 for price in prices],
            "Low": [price - 1 for price in prices],
            "Close": prices,
            "Volume": [1000] * rows,
        },
        index=index,
    )


def test_expanding_split_creates_expected_windows():
    windows = WalkForwardSplitter(6, 2).split(market_data(12))
    assert len(windows) == 3
    assert [window["train_rows"] for window in windows] == [6, 8, 10]
    assert [window["test_rows"] for window in windows] == [2, 2, 2]


def test_rolling_split_keeps_fixed_train_size():
    windows = WalkForwardSplitter(6, 2, expanding=False).split(market_data(12))
    assert [window["train_rows"] for window in windows] == [6, 6, 6]


def test_windows_are_strictly_chronological_without_train_test_overlap():
    windows = WalkForwardSplitter(5, 3, step_size=3).split(market_data(14))
    for window in windows:
        assert window["train_end"] < window["test_start"]
        assert set(window["train"].index).isdisjoint(window["test"].index)


def test_custom_step_size_is_respected():
    windows = WalkForwardSplitter(5, 2, step_size=1).split(market_data(9))
    assert len(windows) == 3
    assert windows[1]["test_start"] - windows[0]["test_start"] == pd.Timedelta(days=1)


def test_split_returns_independent_dataframe_copies():
    data = market_data(10)
    windows = WalkForwardSplitter(6, 2).split(data)
    windows[0]["train"].iloc[0, windows[0]["train"].columns.get_loc("Close")] = 999
    assert data.iloc[0]["Close"] == 100


def test_splitter_rejects_invalid_configuration():
    with pytest.raises(TypeError, match="Train size"):
        WalkForwardSplitter(6.0, 2)
    with pytest.raises(ValueError, match="Test size"):
        WalkForwardSplitter(6, 0)
    with pytest.raises(ValueError, match="Step size"):
        WalkForwardSplitter(6, 2, step_size=0)
    with pytest.raises(TypeError, match="Expanding"):
        WalkForwardSplitter(6, 2, expanding="yes")


def test_splitter_rejects_invalid_or_insufficient_data():
    splitter = WalkForwardSplitter(6, 2)
    with pytest.raises(TypeError, match="DataFrame"):
        splitter.split([1, 2, 3])
    with pytest.raises(ValueError, match="empty"):
        splitter.split(pd.DataFrame())
    with pytest.raises(ValueError, match="at least 8 rows"):
        splitter.split(market_data(7))


def test_splitter_rejects_non_chronological_and_duplicate_indexes():
    splitter = WalkForwardSplitter(6, 2)
    with pytest.raises(ValueError, match="monotonic increasing"):
        splitter.split(market_data(10).sort_index(ascending=False))

    duplicate = market_data(10)
    duplicate.index = list(duplicate.index[:-1]) + [duplicate.index[-2]]
    with pytest.raises(ValueError, match="duplicates"):
        splitter.split(duplicate)


def test_validator_evaluates_train_and_unseen_test_for_every_window():
    result = WalkForwardValidator(ThresholdStrategyEngine(), 6, 2).run(market_data(12))
    assert result["summary"]["window_count"] == 3
    for window in result["windows"]:
        assert window["train"]["final_capital"] > 10000
        assert window["test"]["final_capital"] > 10000
        assert window["train_end"] < window["test_start"]


def test_validator_includes_benchmark_comparison_and_summary():
    result = WalkForwardValidator(ThresholdStrategyEngine(), 6, 2).run(market_data(12))
    for window in result["windows"]:
        assert window["test"]["benchmark"]["benchmark"] == "buy_and_hold"
        assert "excess_return" in window["test"]["comparison"]
    assert set(result["summary"]) == {
        "window_count",
        "mean_test_strategy_return",
        "mean_test_excess_return",
        "positive_test_return_windows",
        "positive_test_excess_windows",
        "positive_test_return_rate",
        "positive_test_excess_rate",
    }


def test_validator_preserves_execution_costs_across_windows():
    result = WalkForwardValidator(
        ThresholdStrategyEngine(),
        6,
        2,
        commission_rate=0.001,
        slippage_rate=0.002,
        spread_rate=0.004,
    ).run(market_data(12))
    for window in result["windows"]:
        assert window["test"]["trade_history"][0]["total_costs"] > 0
        assert window["test"]["benchmark"]["total_costs"] > 0


def test_validator_rejects_invalid_execution_configuration():
    with pytest.raises(ValueError, match="cannot be negative"):
        WalkForwardValidator(
            ThresholdStrategyEngine(),
            6,
            2,
            commission_rate=-0.001,
        )


def test_validator_propagates_next_bar_open_to_every_window_partition():
    data = market_data(12)
    data["Open"] = data["Close"] + 10.0
    validator = WalkForwardValidator(
        ThresholdStrategyEngine(),
        6,
        2,
        execution_timing=" next_bar_open ",
    )

    result = validator.run(data)

    assert validator.execution_timing == "next_bar_open"
    for window in result["windows"]:
        for partition_name in ("train", "test"):
            partition = window[partition_name]
            assert partition["execution_timing"] == "next_bar_open"
            assert partition["benchmark"]["entry_price_column"] == "Open"
