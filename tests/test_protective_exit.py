import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from backtest import BacktestingEngine
from multi_asset import MultiAssetValidator
from out_of_sample import OutOfSampleValidator
from protective_exit import ProtectiveExitDecision, ProtectiveExitPolicy
from research_evidence_compaction import compact_backtest_run
from risk_engine import RiskEngine
from validation_pipeline import StrategyValidationPipeline
from walk_forward import WalkForwardValidator


class Signals:
    def __init__(self, values):
        self.values = values

    def run(self, data):
        result = data.copy()
        result["Signal"] = self.values
        result["ALPHA_V2_ATR_RISK_DISTANCE"] = [2.0] * len(result)
        result["ALPHA_V2_REWARD_RISK_RATIO"] = [3.0] * len(result)
        return result


def market(signals=(1, 0, 0, 0), opens=None, highs=None, lows=None, closes=None):
    rows = len(signals)
    opens = list(opens or [100.0] * rows)
    highs = list(highs or [101.0] * rows)
    lows = list(lows or [99.0] * rows)
    closes = list(closes or opens)
    index = pd.date_range("2026-01-01T00:00:00Z", periods=rows, freq="6h")
    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": [1000.0] * rows,
        },
        index=index,
    )


def protected_backtester(signals, **kwargs):
    return BacktestingEngine(
        Signals(signals),
        initial_capital=10000.0,
        execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
        risk_engine=RiskEngine(
            risk_per_trade=0.01,
            max_position_fraction=1.0,
            min_reward_risk=3.0,
        ),
        protective_exit_policy=ProtectiveExitPolicy(),
        **kwargs,
    )


def test_policy_freezes_conservative_gap_intrabar_and_entry_bar_semantics():
    policy = ProtectiveExitPolicy()
    assert policy.as_dict() == {
        "risk_distance_column": "ALPHA_V2_ATR_RISK_DISTANCE",
        "reward_risk_ratio": 3.0,
        "reward_risk_ratio_column": "ALPHA_V2_REWARD_RISK_RATIO",
        "stop_and_target_same_bar": "STOP_FIRST",
        "stop_gap_fill": "OPEN",
        "target_gap_fill": "TARGET",
        "entry_bar_protection": True,
        "signal_observation": "COMPLETED_BAR_CLOSE",
        "entry_execution": "FOLLOWING_BAR_OPEN",
        "level_resolution": "SIGNAL_BAR_DISTANCE_FROM_EXECUTION_OPEN",
        "protective_costs": "NORMAL_SELL_COMMISSION_SLIPPAGE_SPREAD",
    }


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"risk_distance_column": ""}, "required"),
        ({"reward_risk_ratio": 0.0}, "positive"),
        ({"stop_and_target_same_bar": "TARGET_FIRST"}, "STOP_FIRST"),
        ({"stop_gap_fill": "STOP"}, "OPEN"),
        ({"target_gap_fill": "OPEN"}, "TARGET"),
        ({"entry_bar_protection": False}, "entry-bar"),
    ],
)
def test_policy_rejects_optimistic_or_unfrozen_semantics(kwargs, match):
    with pytest.raises((TypeError, ValueError), match=match):
        ProtectiveExitPolicy(**kwargs)


def test_levels_use_lagged_signal_distance_but_current_execution_open():
    policy = ProtectiveExitPolicy()
    levels = policy.resolve_levels(
        105.0,
        pd.Series(
            {
                "ALPHA_V2_ATR_RISK_DISTANCE": 2.0,
                "ALPHA_V2_REWARD_RISK_RATIO": 3.0,
            }
        ),
    )
    assert levels["stop_price"] == pytest.approx(103.0)
    assert levels["target_price"] == pytest.approx(111.0)
    assert levels["risk_distance"] == pytest.approx(2.0)
    assert levels["source"] == "SIGNAL_BAR_DISTANCE_EXECUTION_OPEN_LEVELS"


def test_levels_fail_closed_on_missing_nonpositive_or_drifted_signal_evidence():
    policy = ProtectiveExitPolicy()
    with pytest.raises(ValueError, match="signal-bar column"):
        policy.resolve_levels(
            100.0, pd.Series({"ALPHA_V2_REWARD_RISK_RATIO": 3.0})
        )
    with pytest.raises(ValueError, match="positive"):
        policy.resolve_levels(
            100.0,
            pd.Series(
                {
                    "ALPHA_V2_ATR_RISK_DISTANCE": 0.0,
                    "ALPHA_V2_REWARD_RISK_RATIO": 3.0,
                }
            ),
        )
    with pytest.raises(ValueError, match="changed"):
        policy.resolve_levels(
            100.0,
            pd.Series(
                {
                    "ALPHA_V2_ATR_RISK_DISTANCE": 2.0,
                    "ALPHA_V2_REWARD_RISK_RATIO": 2.0,
                }
            ),
        )


def test_stop_gap_uses_first_available_open_and_target_gap_is_conservative():
    policy = ProtectiveExitPolicy()
    stop = policy.evaluate_long_open(95.0, 98.0, 106.0)
    target = policy.evaluate_long_open(110.0, 98.0, 106.0)
    assert stop.exit_type == "STOP_GAP"
    assert stop.market_price == pytest.approx(95.0)
    assert stop.trigger_price == pytest.approx(98.0)
    assert stop.fill_reference == "FIRST_AVAILABLE_OPEN"
    assert target.exit_type == "TARGET_GAP"
    assert target.market_price == pytest.approx(106.0)
    assert target.fill_reference == "CONSERVATIVE_TARGET_PRICE"


def test_same_bar_stop_and_target_touch_selects_stop_first():
    decision = ProtectiveExitPolicy().evaluate_long_intrabar(
        high_price=107.0,
        low_price=97.0,
        stop_price=98.0,
        target_price=106.0,
    )
    assert decision.status == "EXIT"
    assert decision.exit_type == "STOP_INTRABAR"
    assert decision.market_price == pytest.approx(98.0)
    assert decision.same_bar_conflict is True


def test_intrabar_target_stop_and_hold_are_distinct():
    policy = ProtectiveExitPolicy()
    target = policy.evaluate_long_intrabar(107.0, 99.0, 98.0, 106.0)
    stop = policy.evaluate_long_intrabar(105.0, 97.0, 98.0, 106.0)
    hold = policy.evaluate_long_intrabar(105.0, 99.0, 98.0, 106.0)
    assert target.exit_type == "TARGET_INTRABAR"
    assert target.market_price == pytest.approx(106.0)
    assert stop.exit_type == "STOP_INTRABAR"
    assert hold == ProtectiveExitDecision(status="HOLD")


@pytest.mark.parametrize(
    "mutate,match",
    [
        (lambda frame: frame.drop(columns=["High"]), "OHLC"),
        (lambda frame: frame.assign(High=np.inf), "finite"),
        (lambda frame: frame.assign(Low=0.0), "positive"),
        (lambda frame: frame.assign(High=50.0), "geometry"),
    ],
)
def test_market_data_validation_fails_closed(mutate, match):
    with pytest.raises(ValueError, match=match):
        ProtectiveExitPolicy.validate_market_data(mutate(market()))


def test_backtester_executes_intrabar_stop_and_records_complete_evidence():
    data = market(
        opens=[100.0, 100.0, 100.0, 100.0],
        highs=[101.0, 101.0, 101.0, 101.0],
        lows=[99.0, 99.0, 97.0, 99.0],
    )
    engine = protected_backtester((1, 0, 0, 0))
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["entry_signal_index"] == data.index[0]
    assert trade["entry_index"] == data.index[1]
    assert trade["exit_index"] == data.index[2]
    assert trade["exit_signal_index"] is None
    assert trade["exit_reason"] == "PROTECTIVE_STOP"
    assert trade["protective_exit_executed"] is True
    assert trade["protective_exit_type"] == "STOP_INTRABAR"
    assert trade["protective_trigger_price"] == pytest.approx(98.0)
    assert trade["planned_stop_price"] == pytest.approx(98.0)
    assert trade["planned_target_price"] == pytest.approx(106.0)
    assert trade["shares"] == pytest.approx(50.0)
    assert trade["profit_loss"] == pytest.approx(-100.0)
    assert engine.capital == pytest.approx(9900.0)


def test_backtester_executes_target_and_realizes_three_planned_risk_before_costs():
    data = market(
        highs=[101.0, 101.0, 107.0, 101.0],
        lows=[99.0, 99.0, 99.0, 99.0],
    )
    engine = protected_backtester((1, 0, 0, 0))
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["exit_reason"] == "PROTECTIVE_TARGET"
    assert trade["protective_exit_type"] == "TARGET_INTRABAR"
    assert trade["exit_market_price"] == pytest.approx(106.0)
    assert trade["gross_profit_loss"] == pytest.approx(300.0)
    assert trade["planned_monetary_risk"] == pytest.approx(100.0)
    assert engine.capital == pytest.approx(10300.0)


def test_entry_bar_is_protected_and_ambiguous_touch_uses_stop_first():
    data = market(
        highs=[101.0, 107.0, 101.0, 101.0],
        lows=[99.0, 97.0, 99.0, 99.0],
    )
    engine = protected_backtester((1, 0, 0, 0))
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["entry_index"] == trade["exit_index"] == data.index[1]
    assert trade["protective_exit_type"] == "STOP_INTRABAR"
    assert trade["protective_same_bar_conflict"] is True


def test_existing_position_stop_gap_executes_at_worse_open():
    data = market(
        opens=[100.0, 100.0, 95.0, 100.0],
        highs=[101.0, 101.0, 96.0, 101.0],
        lows=[99.0, 99.0, 94.0, 99.0],
        closes=[100.0, 100.0, 95.0, 100.0],
    )
    engine = protected_backtester((1, 0, 0, 0))
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["protective_exit_type"] == "STOP_GAP"
    assert trade["exit_market_price"] == pytest.approx(95.0)
    assert trade["protective_trigger_price"] == pytest.approx(98.0)
    assert trade["profit_loss"] == pytest.approx(-250.0)


def test_target_gap_does_not_assume_unearned_open_price_improvement():
    data = market(
        opens=[100.0, 100.0, 110.0, 100.0],
        highs=[101.0, 101.0, 111.0, 101.0],
        lows=[99.0, 99.0, 109.0, 99.0],
        closes=[100.0, 100.0, 110.0, 100.0],
    )
    engine = protected_backtester((1, 0, 0, 0))
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["protective_exit_type"] == "TARGET_GAP"
    assert trade["exit_market_price"] == pytest.approx(106.0)
    assert trade["profit_loss"] == pytest.approx(300.0)


def test_protective_gap_has_priority_over_pending_signal_exit_at_same_open():
    data = market(
        signals=(1, -1, 0, 0),
        opens=[100.0, 100.0, 95.0, 100.0],
        highs=[101.0, 101.0, 96.0, 101.0],
        lows=[99.0, 99.0, 94.0, 99.0],
        closes=[100.0, 100.0, 95.0, 100.0],
    )
    engine = protected_backtester((1, -1, 0, 0))
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["protective_exit_type"] == "STOP_GAP"
    assert trade["exit_signal_index"] is None


def test_protective_exit_applies_normal_sell_slippage_spread_and_commission():
    data = market(highs=[101.0, 101.0, 107.0, 101.0])
    engine = protected_backtester(
        (1, 0, 0, 0),
        commission_rate=0.001,
        slippage_rate=0.002,
        spread_rate=0.004,
    )
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["exit_market_price"] == pytest.approx(106.0)
    assert trade["exit_price"] == pytest.approx(105.576)
    assert trade["exit_commission"] > 0.0
    assert trade["execution_cost"] > 0.0
    assert trade["profit_loss"] == pytest.approx(
        trade["gross_profit_loss"] - trade["total_costs"]
    )


def test_levels_are_taken_from_signal_bar_not_execution_bar():
    data = market()

    class ChangingDistance(Signals):
        def run(self, frame):
            result = super().run(frame)
            result["ALPHA_V2_ATR_RISK_DISTANCE"] = [2.0, 50.0, 50.0, 50.0]
            return result

    engine = BacktestingEngine(
        ChangingDistance((1, 0, 0, 0)),
        execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
        risk_engine=RiskEngine(risk_per_trade=0.01, min_reward_risk=3.0),
        protective_exit_policy=ProtectiveExitPolicy(),
    )
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["planned_stop_price"] == pytest.approx(98.0)
    assert trade["planned_target_price"] == pytest.approx(106.0)


def test_terminal_force_close_is_distinct_from_protective_and_signal_exit():
    data = market(signals=(1, 0), opens=[100.0, 100.0], highs=[101.0, 101.0], lows=[99.0, 99.0])
    engine = protected_backtester((1, 0))
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["exit_reason"] == "TERMINAL_FORCE_CLOSE"
    assert trade["protective_exit_executed"] is False
    assert trade["exit_signal_index"] is None


def test_protective_configuration_requires_risk_engine_next_open_and_matching_rr():
    with pytest.raises(ValueError, match="Risk Engine"):
        BacktestingEngine(
            Signals((1, 0)),
            execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
            protective_exit_policy=ProtectiveExitPolicy(),
        )
    with pytest.raises(ValueError, match="next_bar_open"):
        BacktestingEngine(
            Signals((1, 0)),
            risk_engine=RiskEngine(min_reward_risk=3.0),
            protective_exit_policy=ProtectiveExitPolicy(),
        )
    with pytest.raises(ValueError, match="must match"):
        BacktestingEngine(
            Signals((1, 0)),
            execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
            risk_engine=RiskEngine(min_reward_risk=2.0),
            protective_exit_policy=ProtectiveExitPolicy(),
        )


def test_legacy_risk_managed_backtest_does_not_activate_protective_exits():
    data = market(signals=(1, 0, -1, 0))
    data["Stop"] = 98.0
    data["Target"] = 106.0
    engine = BacktestingEngine(
        Signals((1, 0, -1, 0)),
        risk_engine=RiskEngine(risk_per_trade=0.01, min_reward_risk=3.0),
    )
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["exit_reason"] == "SIGNAL"
    assert trade["protective_exit_executed"] is False


def test_oos_partition_executes_and_reports_active_protective_policy():
    class OneSetupPerPartition:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1] + [0] * (len(result) - 1)
            result["ALPHA_V2_ATR_RISK_DISTANCE"] = 2.0
            result["ALPHA_V2_REWARD_RISK_RATIO"] = 3.0
            return result

    data = market(
        signals=tuple([0] * 8),
        highs=[101.0, 101.0, 107.0, 101.0] * 2,
        lows=[99.0] * 8,
    )
    policy = ProtectiveExitPolicy()
    result = OutOfSampleValidator(
        OneSetupPerPartition(),
        in_sample_fraction=0.5,
        execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
        risk_engine=RiskEngine(risk_per_trade=0.01, min_reward_risk=3.0),
        protective_exit_policy=policy,
    ).run(data)
    for partition in ("in_sample", "out_of_sample"):
        evidence = result[partition]
        assert evidence["protective_exit_policy"] == policy.as_dict()
        assert evidence["trade_history"][0]["protective_exit_type"] == (
            "TARGET_INTRABAR"
        )


def test_research_evidence_compaction_retains_protective_policy():
    policy = ProtectiveExitPolicy().as_dict()
    compacted = compact_backtest_run(
        {
            "initial_capital": 10000.0,
            "final_capital": 10300.0,
            "protective_exit_policy": policy,
            "trade_history": [],
            "equity_curve": [],
        }
    )
    assert compacted["protective_exit_policy"] == policy


def test_protective_policy_propagates_through_every_standard_validation_layer():
    risk = RiskEngine(risk_per_trade=0.005, min_reward_risk=3.0)
    policy = ProtectiveExitPolicy()
    common = {
        "execution_timing": BacktestingEngine.NEXT_BAR_OPEN,
        "risk_engine": risk,
        "protective_exit_policy": policy,
    }
    oos = OutOfSampleValidator(Signals((1, 0)), **common)
    walk = WalkForwardValidator(
        Signals((1, 0)), train_size=2, test_size=2, **common
    )
    pipeline = StrategyValidationPipeline(
        Signals((1, 0)), train_size=2, test_size=2, **common
    )
    multi = MultiAssetValidator(
        Signals((1, 0)), train_size=2, test_size=2, **common
    )
    assert oos.risk_engine is risk
    assert oos.protective_exit_policy is policy
    assert walk._partition_validator.risk_engine is risk
    assert walk._partition_validator.protective_exit_policy is policy
    assert pipeline.oos_validator.protective_exit_policy is policy
    assert pipeline.walk_forward_validator._partition_validator.risk_engine is risk
    assert multi.pipeline_kwargs["risk_engine"] is risk
    assert multi.pipeline_kwargs["protective_exit_policy"] is policy
