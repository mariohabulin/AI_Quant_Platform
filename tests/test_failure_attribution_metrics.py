import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from failure_attribution_metrics import FailureAttributionMetrics
from volume_research import VolumeResearchConfig


def market_frame(rows=12):
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="6h")
    close = 100.0 + np.arange(rows, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": [10, 10, 10, 40, 12, 8, 30, 10, 9, 25, 10, 11][:rows],
        },
        index=index,
    )


def trade(data, entry, exit_, gross, commission, execution_cost, terminal=False):
    total_costs = commission + execution_cost
    return {
        "entry_signal_index": data.index[entry - 1],
        "entry_index": data.index[entry],
        "exit_signal_index": None if terminal else data.index[exit_ - 1],
        "exit_index": data.index[exit_],
        "entry_market_price": float(data.iloc[entry]["Open"]),
        "exit_market_price": float(data.iloc[exit_]["Open"]),
        "shares": 2.0,
        "gross_profit_loss": gross,
        "entry_commission": commission * 0.4,
        "exit_commission": commission * 0.6,
        "total_commission": commission,
        "execution_cost": execution_cost,
        "total_costs": total_costs,
        "profit_loss": gross - total_costs,
    }


def asset_result(data, trades, equity):
    split_position = 3
    curve = [
        {"index": index, "equity": float(value)}
        for index, value in zip(data.index[split_position:], equity)
    ]
    return {
        "strategy": "example",
        "out_of_sample": {
            "split": {"split_position": split_position},
            "out_of_sample": {
                "initial_capital": 5000.0,
                "trade_history": trades,
                "equity_curve": curve,
                "comparison": {
                    "strategy_return": -0.1,
                    "benchmark_return": -0.2,
                    "excess_return": 0.1,
                },
                "performance": {"max_drawdown": 20.0},
            },
        },
        "walk_forward": {
            "summary": {
                "window_count": 2,
                "positive_test_excess_rate": 0.5,
            },
            "windows": [],
        },
        "falsification": {"passes_statistical_falsification": False},
        "classification": {"status": "REJECTED"},
    }


class FixedRegimeDetector:
    def detect(self, data):
        labels = pd.Series("SIDEWAYS_NORMAL", index=data.index, dtype=object)
        labels.iloc[2] = "BULLISH_HIGH"
        labels.iloc[3] = "BEARISH_LOW"
        return pd.DataFrame({"market_regime": labels}, index=data.index)


def analyzer():
    return FailureAttributionMetrics(
        granularity_seconds=21600,
        market_regime_detector=FixedRegimeDetector(),
        volume_configuration=VolumeResearchConfig(lookback=2),
    )


def test_cost_turnover_separates_gross_commission_execution_and_net():
    data = market_frame()
    trades = [
        trade(data, 3, 5, gross=100.0, commission=12.0, execution_cost=8.0),
        trade(data, 7, 9, gross=-30.0, commission=10.0, execution_cost=5.0),
    ]
    result = analyzer().analyze(
        data,
        asset_result(data, trades, [5000, 5100, 5080, 5070, 5050, 5035, 5020, 5010, 5005]),
    )
    costs = result["cost_turnover"]

    assert costs["trade_count"] == 2
    assert costs["gross_profit_loss"] == pytest.approx(70.0)
    assert costs["total_commission"] == pytest.approx(22.0)
    assert costs["execution_cost"] == pytest.approx(13.0)
    assert costs["total_costs"] == pytest.approx(35.0)
    assert costs["net_profit_loss"] == pytest.approx(35.0)
    assert costs["gross_minus_costs_equals_net"] is True
    assert costs["round_trip_notional"] > 0.0
    assert costs["turnover_multiple_of_initial_capital"] > 0.0


def test_exposure_and_holding_distinguish_next_open_and_terminal_close():
    data = market_frame()
    trades = [
        trade(data, 3, 5, gross=10.0, commission=0.0, execution_cost=0.0),
        trade(
            data,
            7,
            11,
            gross=20.0,
            commission=0.0,
            execution_cost=0.0,
            terminal=True,
        ),
    ]
    result = analyzer().analyze(
        data,
        asset_result(data, trades, [5000] * 9),
    )["exposure_holding"]

    assert result["holding_bars"] == [2, 5]
    assert result["holding_hours"] == pytest.approx([12.0, 30.0])
    assert result["mean_holding_bars"] == pytest.approx(3.5)
    assert result["median_holding_bars"] == pytest.approx(3.5)
    assert result["exposure_bars"] == 7
    assert result["oos_bars"] == 9
    assert result["exposure_percent"] == pytest.approx(700.0 / 9.0)
    assert result["terminal_force_close_count"] == 1


def test_drawdown_retains_peak_trough_recovery_and_year_concentration():
    data = market_frame()
    result = analyzer().analyze(
        data,
        asset_result(
            data,
            [],
            [5000, 5500, 5000, 4400, 4600, 5500, 5600, 5300, 5700],
        ),
    )["drawdown"]

    assert result["max_drawdown_percent"] == pytest.approx(20.0)
    assert result["peak_index"] == data.index[4]
    assert result["trough_index"] == data.index[6]
    assert result["recovery_index"] == data.index[8]
    assert result["recovered"] is True
    assert result["underwater_bar_count"] == 4
    assert result["underwater_percent"] == pytest.approx(400.0 / 9.0)
    assert result["max_drawdown_by_year_percent"] == {"2024": pytest.approx(20.0)}


def test_market_regime_attribution_uses_signal_bar_and_separates_costs():
    data = market_frame()
    one_trade = trade(
        data,
        3,
        5,
        gross=100.0,
        commission=12.0,
        execution_cost=8.0,
    )
    result = analyzer().analyze(
        data,
        asset_result(data, [one_trade], [5000] * 9),
    )["market_regime"]

    assert result["signal_bar_attribution"] is True
    assert result["regimes"]["BULLISH_HIGH"]["trade_count"] == 1
    assert result["regimes"]["BULLISH_HIGH"]["gross_profit_loss"] == pytest.approx(100.0)
    assert result["regimes"]["BULLISH_HIGH"]["total_costs"] == pytest.approx(20.0)
    assert result["regimes"]["BULLISH_HIGH"]["net_profit_loss"] == pytest.approx(80.0)


def test_volume_evidence_includes_rvol_dollar_volume_and_obv_context():
    data = market_frame()
    one_trade = trade(
        data,
        3,
        5,
        gross=100.0,
        commission=12.0,
        execution_cost=8.0,
    )
    result = analyzer().analyze(
        data,
        asset_result(data, [one_trade], [5000] * 9),
    )["volume"]

    assert result["signal_bar_attribution"] is True
    assert result["volume_regimes"]["NORMAL"]["trade_count"] == 1
    assert result["entry_context"]["mean_relative_volume"] == pytest.approx(1.0)
    assert result["entry_context"]["mean_relative_dollar_volume"] > 0.0
    assert result["obv_directions"]["RISING"]["trade_count"] == 1


def test_empty_trade_evidence_is_explicit_and_finite():
    data = market_frame()
    result = analyzer().analyze(
        data,
        asset_result(data, [], [5000] * 9),
    )

    assert result["cost_turnover"]["trade_count"] == 0
    assert result["cost_turnover"]["turnover_multiple_of_initial_capital"] == 0.0
    assert result["exposure_holding"]["holding_bars"] == []
    assert result["exposure_holding"]["mean_holding_bars"] is None
    assert result["market_regime"]["attributed_trade_count"] == 0
    assert result["volume"]["attributed_trade_count"] == 0


@pytest.mark.parametrize(
    "problem",
    ["wrong_data", "bad_result", "bad_trade", "bad_equity", "cost_identity"],
)
def test_metrics_fail_closed_on_malformed_evidence(problem):
    data = market_frame()
    result = asset_result(data, [], [5000] * 9)
    if problem == "wrong_data":
        data = []
    elif problem == "bad_result":
        result = {}
    elif problem == "bad_trade":
        result["out_of_sample"]["out_of_sample"]["trade_history"] = [{}]
    elif problem == "bad_equity":
        result["out_of_sample"]["out_of_sample"]["equity_curve"][0]["equity"] = np.nan
    else:
        malformed = trade(data, 3, 5, 10.0, 1.0, 1.0)
        malformed["profit_loss"] = 99.0
        result["out_of_sample"]["out_of_sample"]["trade_history"] = [malformed]

    with pytest.raises((TypeError, ValueError)):
        analyzer().analyze(data, result)
