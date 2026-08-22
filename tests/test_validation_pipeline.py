import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from validation_pipeline import StrategyValidationPipeline, ValidationPolicy


class RepeatedTradeEngine:
    strategy_name = "RepeatedTrade"

    def run(self, data):
        result = data.copy()
        result["Signal"] = 0
        for position in range(0, len(result) - 1, 2):
            result.iloc[position, result.columns.get_loc("Signal")] = 1
            result.iloc[position + 1, result.columns.get_loc("Signal")] = -1
        return result


def market_data(rows=80):
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    prices = [100 + i for i in range(rows)]
    return pd.DataFrame(
        {
            "Open": prices,
            "High": [p + 1 for p in prices],
            "Low": [p - 1 for p in prices],
            "Close": prices,
            "Volume": [1000] * rows,
        },
        index=index,
    )


def fake_evidence(oos_return=0.1, oos_excess=0.02, persistence=0.8, statistical=True):
    oos = {"out_of_sample": {"comparison": {"strategy_return": oos_return, "excess_return": oos_excess}}}
    walk_forward = {"summary": {"positive_test_excess_rate": persistence}}
    falsification = {"passes_statistical_falsification": statistical}
    return oos, walk_forward, falsification


def test_policy_validates_when_all_gates_pass():
    result = ValidationPolicy().classify(*fake_evidence())
    assert result["status"] == "VALIDATED"
    assert all(result["gates"].values())


def test_policy_rejects_negative_oos_return():
    result = ValidationPolicy().classify(*fake_evidence(oos_return=-0.01))
    assert result["status"] == "REJECTED"
    assert result["gates"]["positive_oos_return"] is False


def test_policy_rejects_non_positive_oos_excess_return():
    result = ValidationPolicy().classify(*fake_evidence(oos_excess=0.0))
    assert result["status"] == "REJECTED"


def test_policy_rejects_failed_statistical_falsification():
    result = ValidationPolicy().classify(*fake_evidence(statistical=False))
    assert result["status"] == "REJECTED"


def test_policy_marks_conditional_when_hard_gates_pass_but_persistence_is_low():
    result = ValidationPolicy(0.75).classify(*fake_evidence(persistence=0.5))
    assert result["status"] == "CONDITIONAL"
    assert result["gates"]["walk_forward_persistence"] is False


def test_policy_accepts_boundary_persistence():
    result = ValidationPolicy(0.60).classify(*fake_evidence(persistence=0.60))
    assert result["gates"]["walk_forward_persistence"] is True


def test_policy_rejects_invalid_persistence_threshold():
    with pytest.raises(TypeError):
        ValidationPolicy("0.6")
    with pytest.raises(ValueError):
        ValidationPolicy(1.1)


def test_pipeline_returns_all_validation_layers():
    pipeline = StrategyValidationPipeline(
        RepeatedTradeEngine(),
        train_size=20,
        test_size=12,
        step_size=12,
        simulations=300,
        random_seed=7,
    )
    result = pipeline.run(market_data())

    assert result["strategy"] == "RepeatedTrade"
    assert set(result) == {
        "strategy", "out_of_sample", "walk_forward", "falsification", "classification"
    }
    assert result["classification"]["status"] in {"VALIDATED", "CONDITIONAL", "REJECTED"}


def test_pipeline_falsification_uses_only_walk_forward_test_trades():
    pipeline = StrategyValidationPipeline(
        RepeatedTradeEngine(),
        train_size=20,
        test_size=12,
        step_size=12,
        simulations=200,
        random_seed=3,
    )
    result = pipeline.run(market_data())
    expected_trade_count = sum(len(w["test"]["trade_history"]) for w in result["walk_forward"]["windows"])

    # Bootstrap observed expectancy is calculated from the unseen trade pool.
    unseen = []
    for window in result["walk_forward"]["windows"]:
        unseen.extend(t["profit_loss"] for t in window["test"]["trade_history"])
    assert expected_trade_count == len(unseen)
    assert result["falsification"]["bootstrap"]["observed_expectancy"] == pytest.approx(sum(unseen) / len(unseen))


def test_pipeline_is_reproducible_with_same_seed():
    kwargs = dict(train_size=20, test_size=12, step_size=12, simulations=200, random_seed=99)
    first = StrategyValidationPipeline(RepeatedTradeEngine(), **kwargs).run(market_data())
    second = StrategyValidationPipeline(RepeatedTradeEngine(), **kwargs).run(market_data())
    assert first["falsification"] == second["falsification"]
    assert first["classification"] == second["classification"]


def test_pipeline_propagates_execution_costs_through_validation():
    result = StrategyValidationPipeline(
        RepeatedTradeEngine(),
        train_size=20,
        test_size=12,
        step_size=12,
        commission_rate=0.001,
        slippage_rate=0.001,
        spread_rate=0.002,
        simulations=100,
    ).run(market_data())

    assert result["out_of_sample"]["out_of_sample"]["trade_history"][0]["total_costs"] > 0
    assert result["walk_forward"]["windows"][0]["test"]["trade_history"][0]["total_costs"] > 0


def test_pipeline_rejects_data_too_short_for_walk_forward():
    pipeline = StrategyValidationPipeline(
        RepeatedTradeEngine(), train_size=20, test_size=10, simulations=100
    )
    with pytest.raises(ValueError, match="at least 30 rows"):
        pipeline.run(market_data(25))


def test_pipeline_propagates_next_bar_open_through_all_validation_layers():
    result = StrategyValidationPipeline(
        RepeatedTradeEngine(),
        train_size=20,
        test_size=12,
        step_size=12,
        simulations=100,
        execution_timing="next_bar_open",
    ).run(market_data())

    assert result["out_of_sample"]["in_sample"]["execution_timing"] == (
        "next_bar_open"
    )
    assert result["out_of_sample"]["out_of_sample"]["benchmark"][
        "entry_price_column"
    ] == "Open"
    for window in result["walk_forward"]["windows"]:
        assert window["train"]["execution_timing"] == "next_bar_open"
        assert window["test"]["execution_timing"] == "next_bar_open"
