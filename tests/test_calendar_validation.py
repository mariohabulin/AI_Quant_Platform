import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from calendar_validation import (
    CalendarChronologicalDataSplitter,
    CalendarMultiAssetValidator,
    CalendarWalkForwardSplitter,
)
from backtest import BacktestingEngine


class RepeatedTradeEngine:
    strategy_name = "RepeatedTrade"

    def run(self, data):
        result = data.copy()
        result["Signal"] = 0
        for position in range(0, len(result) - 1, 2):
            result.iloc[position, result.columns.get_loc("Signal")] = 1
            result.iloc[position + 1, result.columns.get_loc("Signal")] = -1
        return result


class GapExecutionEngine:
    strategy_name = "GapExecution"

    def run(self, data):
        result = data.copy()
        result["Signal"] = [1, -1, 0]
        return result


def market_frame(hours=80, missing=()):
    index = pd.date_range("2024-01-01T00:00:00Z", periods=hours, freq="h")
    index = index.delete(list(missing))
    prices = np.arange(100.0, 100.0 + len(index))
    return pd.DataFrame(
        {
            "Open": prices,
            "High": prices + 1.0,
            "Low": prices - 1.0,
            "Close": prices + 0.5,
            "Volume": np.full(len(index), 10.0),
        },
        index=index,
    )


def test_calendar_oos_boundary_uses_expected_time_grid_not_observed_row_count():
    data = market_frame(hours=10, missing=(1, 2, 3))
    splitter = CalendarChronologicalDataSplitter(
        calendar_start="2024-01-01T00:00:00Z",
        calendar_end="2024-01-01T10:00:00Z",
        granularity_seconds=3600,
        in_sample_fraction=0.60,
    )

    result = splitter.split(data)

    boundary = pd.Timestamp("2024-01-01T06:00:00Z")
    assert result["split_boundary"] == boundary
    assert all(result["in_sample"].index < boundary)
    assert all(result["out_of_sample"].index >= boundary)
    assert result["in_sample_expected_rows"] == 6
    assert result["in_sample_rows"] == 3
    assert result["in_sample_missing_rows"] == 3
    assert result["out_of_sample_expected_rows"] == 4
    assert result["out_of_sample_missing_rows"] == 0


def test_calendar_alignment_is_independent_of_datetime_index_storage_unit():
    data = market_frame(hours=10, missing=(1, 2, 3))
    data.index = data.index.as_unit("us")
    splitter = CalendarChronologicalDataSplitter(
        calendar_start="2024-01-01T00:00:00Z",
        calendar_end="2024-01-01T10:00:00Z",
        granularity_seconds=3600,
        in_sample_fraction=0.60,
    )

    result = splitter.split(data)

    assert result["split_boundary"] == pd.Timestamp("2024-01-01T06:00:00Z")
    assert result["in_sample_missing_rows"] == 3


def test_calendar_walk_forward_windows_keep_exact_boundaries_with_sparse_rows():
    data = market_frame(hours=12, missing=(1, 5, 8))
    splitter = CalendarWalkForwardSplitter(
        train_size=4,
        test_size=2,
        step_size=2,
        expanding=True,
        calendar_start="2024-01-01T00:00:00Z",
        calendar_end="2024-01-01T12:00:00Z",
        granularity_seconds=3600,
    )

    windows = splitter.split(data)

    assert len(windows) == 4
    assert [window["calendar_test_start"] for window in windows] == list(
        pd.date_range("2024-01-01T04:00:00Z", periods=4, freq="2h")
    )
    assert all(window["test_expected_rows"] == 2 for window in windows)
    assert [window["test_missing_rows"] for window in windows] == [1, 0, 1, 0]
    assert windows[0]["calendar_test_end_exclusive"] == pd.Timestamp(
        "2024-01-01T06:00:00Z"
    )
    assert windows[-1]["calendar_test_end_exclusive"] == pd.Timestamp(
        "2024-01-01T12:00:00Z"
    )


@pytest.mark.parametrize(
    "data, message",
    [
        (market_frame(hours=8).tz_localize(None), "timezone-aware"),
        (market_frame(hours=8).iloc[::-1], "monotonic"),
    ],
)
def test_calendar_splitters_reject_invalid_timestamp_indexes(data, message):
    splitter = CalendarChronologicalDataSplitter(
        calendar_start="2024-01-01T00:00:00Z",
        calendar_end="2024-01-01T08:00:00Z",
        granularity_seconds=3600,
    )
    with pytest.raises(ValueError, match=message):
        splitter.split(data)


def test_calendar_multi_asset_validator_preserves_sparse_rows_and_time_windows():
    validator = CalendarMultiAssetValidator(
        RepeatedTradeEngine(),
        train_size=20,
        test_size=12,
        step_size=12,
        calendar_start="2024-01-01T00:00:00Z",
        calendar_end="2024-01-04T08:00:00Z",
        granularity_seconds=3600,
        simulations=100,
        random_seed=9,
        execution_timing="next_bar_open",
        min_assets=2,
    )
    assets = {
        "BTC-USD": market_frame(missing=(5, 21, 44)),
        "ETH-USD": market_frame(missing=(7, 22)),
    }

    result = validator.run(assets)

    assert result["asset_count"] == 2
    assert result["windowing"] == "CALENDAR_TIME_WITH_EXPLICIT_GAPS"
    btc = result["assets"]["BTC-USD"]
    assert btc["out_of_sample"]["split"]["split_boundary"] == pd.Timestamp(
        "2024-01-03T08:00:00Z"
    )
    assert btc["walk_forward"]["configuration"]["windowing"] == (
        "CALENDAR_TIME_WITH_EXPLICIT_GAPS"
    )
    assert btc["walk_forward"]["summary"]["window_count"] == 5
    assert any(
        window["test_missing_rows"] > 0
        for window in btc["walk_forward"]["windows"]
    )


def test_next_bar_open_across_gap_uses_next_observed_candle_without_fill():
    data = market_frame(hours=5, missing=(1, 2))
    backtester = BacktestingEngine(
        GapExecutionEngine(),
        execution_timing="next_bar_open",
    )

    backtester.run(data)

    assert len(data) == 3
    assert len(backtester.trade_history) == 1
    trade = backtester.trade_history[0]
    assert trade["entry_signal_index"] == pd.Timestamp("2024-01-01T00:00:00Z")
    assert trade["entry_index"] == pd.Timestamp("2024-01-01T03:00:00Z")
    assert trade["exit_index"] == pd.Timestamp("2024-01-01T04:00:00Z")
