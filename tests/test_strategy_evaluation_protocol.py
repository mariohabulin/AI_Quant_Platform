import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import strategy_evaluation_protocol as protocol_module
from strategy_evaluation_protocol import (
    ExecutionCostProfile,
    StrategyCandidate,
    StrategyEvaluationConfig,
    StrategyEvaluationPolicy,
    StrategyEvaluationProtocol,
)
from validation_pipeline import ValidationPolicy


class NamedEngine:
    strategy_name = "EMA_20_50"

    def run(self, data):
        result = data.copy()
        result["Signal"] = 0
        for position in range(0, len(result) - 1, 2):
            result.iloc[position, result.columns.get_loc("Signal")] = 1
            result.iloc[position + 1, result.columns.get_loc("Signal")] = -1
        return result


def candidate(assets=("BTC-USD", "ETH-USD")):
    return StrategyCandidate(
        candidate_id="ema-20-50-v1",
        strategy_name="EMA_20_50",
        hypothesis="A persistent trend should survive costs and unseen windows.",
        parameter_set_id="fast=20;slow=50",
        data_version="coinbase-1m-2024-v1",
        timeframe="1m",
        assets=assets,
    )


def config(**overrides):
    values = {
        "train_size": 60,
        "test_size": 20,
        "baseline_costs": ExecutionCostProfile(
            label="reviewed_baseline",
            commission_rate=0.001,
            slippage_rate=0.0005,
            spread_rate=0.001,
        ),
        "stressed_costs": ExecutionCostProfile(
            label="two_x_stress",
            commission_rate=0.002,
            slippage_rate=0.001,
            spread_rate=0.002,
        ),
        "min_walk_forward_windows": 5,
        "min_unseen_trades_per_asset": 30,
        "max_oos_drawdown_percent": 20.0,
    }
    values.update(overrides)
    return StrategyEvaluationConfig(**values)


def asset_result(
    status=ValidationPolicy.VALIDATED,
    window_count=5,
    trades_per_window=6,
    drawdown=10.0,
):
    windows = [
        {
            "test": {
                "trade_history": [
                    {"profit_loss": 1.0}
                    for _ in range(trades_per_window)
                ]
            }
        }
        for _ in range(window_count)
    ]
    return {
        "strategy": "EMA_20_50",
        "classification": {"status": status},
        "walk_forward": {
            "windows": windows,
            "summary": {"window_count": window_count},
        },
        "out_of_sample": {
            "out_of_sample": {
                "performance": {"max_drawdown": drawdown},
            }
        },
    }


def multi_asset_result(
    status=ValidationPolicy.VALIDATED,
    strategy="EMA_20_50",
    assets=("BTC-USD", "ETH-USD"),
    **asset_overrides,
):
    results = {
        name: asset_result(**asset_overrides)
        for name in assets
    }
    return {
        "strategy": strategy,
        "asset_count": len(results),
        "assets": results,
        "classification": {"status": status},
    }


def market_frame(rows=100):
    index = pd.date_range("2024-01-01", periods=rows, freq="min")
    prices = [100.0 + position for position in range(rows)]
    return pd.DataFrame(
        {
            "Open": prices,
            "High": [price + 1.0 for price in prices],
            "Low": [price - 1.0 for price in prices],
            "Close": prices,
            "Volume": [1000.0] * rows,
        },
        index=index,
    )


def test_candidate_is_immutable_and_canonicalizes_asset_scope():
    item = candidate(("ETH-USD", "BTC-USD"))

    assert item.assets == ("BTC-USD", "ETH-USD")
    assert item.as_dict()["assets"] == ["BTC-USD", "ETH-USD"]
    with pytest.raises(AttributeError):
        item.strategy_name = "changed"


@pytest.mark.parametrize(
    "overrides, error",
    [
        ({"candidate_id": ""}, ValueError),
        ({"strategy_name": 42}, TypeError),
        ({"assets": ("BTC-USD", "BTC-USD")}, ValueError),
        ({"assets": ()}, ValueError),
    ],
)
def test_candidate_rejects_incomplete_or_ambiguous_declaration(overrides, error):
    values = candidate().as_dict()
    values["assets"] = tuple(values["assets"])
    values.update(overrides)

    with pytest.raises(error):
        StrategyCandidate(**values)


def test_cost_profile_rejects_invalid_rates_and_exposes_total_rate():
    profile = ExecutionCostProfile("baseline", 0.001, 0.002, 0.004)
    assert profile.total_rate == pytest.approx(0.007)

    with pytest.raises(ValueError, match="cannot be negative"):
        ExecutionCostProfile("invalid", -0.001, 0.0, 0.0)
    with pytest.raises(TypeError, match="Slippage rate"):
        ExecutionCostProfile("invalid", 0.0, "0.1", 0.0)


def test_config_requires_nonzero_baseline_and_strictly_harsher_stress_costs():
    zero = ExecutionCostProfile("zero", 0.0, 0.0, 0.0)
    baseline = ExecutionCostProfile("baseline", 0.001, 0.001, 0.001)

    with pytest.raises(ValueError, match="Baseline costs must be non-zero"):
        config(baseline_costs=zero)
    with pytest.raises(ValueError, match="at least as high"):
        config(
            baseline_costs=baseline,
            stressed_costs=ExecutionCostProfile("lower", 0.0005, 0.001, 0.001),
        )
    with pytest.raises(ValueError, match="strictly higher"):
        config(baseline_costs=baseline, stressed_costs=baseline)


def test_config_blocks_overlapping_walk_forward_test_windows():
    with pytest.raises(ValueError, match="must not overlap"):
        config(step_size=10)


def test_config_freezes_attainable_execution_and_terminal_semantics():
    frozen = config(execution_timing=" next_bar_open ")

    assert frozen.execution_timing == "next_bar_open"
    assert frozen.terminal_position_policy == "force_close_at_final_close"
    assert frozen.validator_kwargs(frozen.baseline_costs)[
        "execution_timing"
    ] == "next_bar_open"
    assert frozen.as_dict()["signal_observation"] == "bar_close"
    assert frozen.as_dict()["benchmark_entry_timing"] == "first_bar_open"


@pytest.mark.parametrize(
    "overrides, error, message",
    [
        ({"execution_timing": 42}, TypeError, "Execution timing"),
        (
            {"execution_timing": "same_bar_close"},
            ValueError,
            "requires next_bar_open",
        ),
        (
            {"terminal_position_policy": "leave_open"},
            ValueError,
            "requires force_close_at_final_close",
        ),
    ],
)
def test_config_rejects_unattainable_or_ambiguous_execution_semantics(
    overrides,
    error,
    message,
):
    with pytest.raises(error, match=message):
        config(**overrides)


def test_policy_promotes_only_complete_baseline_and_stress_evidence():
    report = StrategyEvaluationPolicy(config()).review(
        candidate(),
        multi_asset_result(),
        multi_asset_result(),
    )

    assert report["status"] == "PAPER_CANDIDATE"
    assert all(report["gates"].values())
    assert report["next_stage"] == "BOUNDED_FORWARD_PAPER"
    assert report["live_execution_authorized"] is False
    assert report["failed_gates"] == []


def test_policy_holds_conditional_evidence_for_more_research():
    report = StrategyEvaluationPolicy(config()).review(
        candidate(),
        multi_asset_result(),
        multi_asset_result(status=ValidationPolicy.CONDITIONAL),
    )

    assert report["status"] == "RESEARCH_HOLD"
    assert report["gates"]["cost_stress_validated"] is False
    assert report["next_stage"] == "RESEARCH"


@pytest.mark.parametrize("which", ["baseline", "stress"])
def test_policy_rejects_failed_edge_evidence(which):
    baseline = multi_asset_result()
    stress = multi_asset_result()
    if which == "baseline":
        baseline["classification"]["status"] = ValidationPolicy.REJECTED
    else:
        stress["classification"]["status"] = ValidationPolicy.REJECTED

    report = StrategyEvaluationPolicy(config()).review(candidate(), baseline, stress)

    assert report["status"] == "REJECTED"
    assert report["next_stage"] == "RESEARCH"
    assert report["live_execution_authorized"] is False


def test_policy_holds_insufficient_walk_forward_windows():
    evidence = multi_asset_result(window_count=4, trades_per_window=8)
    report = StrategyEvaluationPolicy(config()).review(candidate(), evidence, evidence)

    assert report["status"] == "RESEARCH_HOLD"
    assert report["gates"]["minimum_walk_forward_windows"] is False


def test_policy_holds_insufficient_unseen_trades():
    evidence = multi_asset_result(window_count=5, trades_per_window=5)
    report = StrategyEvaluationPolicy(config()).review(candidate(), evidence, evidence)

    assert report["status"] == "RESEARCH_HOLD"
    assert report["gates"]["minimum_unseen_trades_per_asset"] is False


def test_policy_holds_excessive_unseen_drawdown():
    stress = multi_asset_result(drawdown=20.01)
    report = StrategyEvaluationPolicy(config()).review(
        candidate(), multi_asset_result(), stress
    )

    assert report["status"] == "RESEARCH_HOLD"
    assert report["gates"]["oos_drawdown_within_limit"] is False


def test_policy_rejects_strategy_or_asset_scope_integrity_mismatch():
    wrong_strategy = multi_asset_result(strategy="RSI")
    report = StrategyEvaluationPolicy(config()).review(
        candidate(), wrong_strategy, multi_asset_result()
    )
    assert report["status"] == "REJECTED"
    assert report["gates"]["strategy_identity_frozen"] is False

    wrong_scope = multi_asset_result(assets=("BTC-USD", "SOL-USD"))
    report = StrategyEvaluationPolicy(config()).review(
        candidate(), wrong_scope, multi_asset_result()
    )
    assert report["status"] == "REJECTED"
    assert report["gates"]["asset_scope_frozen"] is False


def test_policy_reports_per_asset_evidence_and_thresholds():
    report = StrategyEvaluationPolicy(config()).review(
        candidate(), multi_asset_result(), multi_asset_result(drawdown=12.0)
    )

    btc = report["evidence"]["assets"]["BTC-USD"]
    assert btc["walk_forward_windows"] == 5
    assert btc["unseen_trade_count"] == 30
    assert btc["baseline_oos_max_drawdown_percent"] == 10.0
    assert btc["stressed_oos_max_drawdown_percent"] == 12.0
    assert report["thresholds"]["min_unseen_trades_per_asset"] == 30
    assert report["configuration"]["random_seed"] == 42
    assert report["configuration"]["step_size"] == 20
    assert report["configuration"]["baseline_costs"]["total_rate"] > 0.0


def test_protocol_requires_declared_strategy_and_exact_asset_scope():
    with pytest.raises(ValueError, match="does not match declared strategy"):
        StrategyEvaluationProtocol(
            type("OtherEngine", (), {"strategy_name": "RSI"})(),
            candidate(),
            config(),
        )

    runner = StrategyEvaluationProtocol(NamedEngine(), candidate(), config())
    with pytest.raises(ValueError, match="exactly match"):
        runner.run({"BTC-USD": market_frame(), "SOL-USD": market_frame()})


def test_protocol_runs_same_frozen_pipeline_under_baseline_and_stress_costs(monkeypatch):
    calls = []

    class FakeMultiAssetValidator:
        def __init__(self, strategy_engine, **kwargs):
            calls.append(kwargs)

        def run(self, assets):
            return multi_asset_result()

    monkeypatch.setattr(
        protocol_module,
        "MultiAssetValidator",
        FakeMultiAssetValidator,
    )
    assets = {"BTC-USD": market_frame(), "ETH-USD": market_frame()}

    report = StrategyEvaluationProtocol(NamedEngine(), candidate(), config()).run(assets)

    assert report["status"] == "PAPER_CANDIDATE"
    assert len(calls) == 2
    assert calls[0]["commission_rate"] == pytest.approx(0.001)
    assert calls[1]["commission_rate"] == pytest.approx(0.002)
    assert calls[0]["train_size"] == calls[1]["train_size"] == 60
    assert calls[0]["execution_timing"] == calls[1]["execution_timing"] == (
        "next_bar_open"
    )
    assert report["execution_assumptions"]["baseline"]["label"] == "reviewed_baseline"
    assert report["execution_assumptions"]["stress"]["label"] == "two_x_stress"
    assert report["execution_assumptions"]["signal_observation"] == "bar_close"
    assert report["execution_assumptions"]["order_execution"] == "next_bar_open"
    assert report["execution_assumptions"]["terminal_position_policy"] == (
        "force_close_at_final_close"
    )
    assert report["execution_assumptions"]["benchmark_entry_timing"] == (
        "first_bar_open"
    )


def test_protocol_integrates_with_existing_multi_asset_validation_stack():
    integration_config = config(
        train_size=40,
        test_size=20,
        simulations=100,
        min_walk_forward_windows=3,
        min_unseen_trades_per_asset=20,
    )
    assets = {
        "BTC-USD": market_frame(100),
        "ETH-USD": market_frame(100) * 1.1,
    }

    report = StrategyEvaluationProtocol(
        NamedEngine(),
        candidate(),
        integration_config,
    ).run(assets)

    assert report["status"] in {
        "PAPER_CANDIDATE",
        "RESEARCH_HOLD",
        "REJECTED",
    }
    assert report["baseline_evaluation"]["asset_count"] == 2
    assert report["cost_stress_evaluation"]["asset_count"] == 2
    assert report["live_execution_authorized"] is False
