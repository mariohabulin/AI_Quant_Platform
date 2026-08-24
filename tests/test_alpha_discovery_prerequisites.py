import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from alpha_discovery_features import CausalEMATrendStructure
from backtest import BacktestingEngine
from protective_exit import ProtectiveExitPolicy
from risk_engine import RiskEngine


class DiscoverySignals:
    def __init__(self, signals):
        self.signals = signals

    def run(self, data):
        result = data.copy()
        result["Signal"] = self.signals
        result["ALPHA_V2_ATR_RISK_DISTANCE"] = 2.0
        result["ALPHA_V2_REWARD_RISK_RATIO"] = 3.0
        return result


def market(signals, opens, highs, lows, closes=None):
    rows = len(signals)
    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes or opens,
            "Volume": [1000.0] * rows,
        },
        index=pd.date_range("2026-01-01T00:00:00Z", periods=rows, freq="6h"),
    )


def protected_engine(signals, *, breakeven_trigger_r=None, **engine_kwargs):
    return BacktestingEngine(
        DiscoverySignals(signals),
        initial_capital=10000.0,
        execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
        risk_engine=RiskEngine(
            risk_per_trade=0.01,
            max_position_fraction=1.0,
            min_reward_risk=3.0,
        ),
        protective_exit_policy=ProtectiveExitPolicy(
            breakeven_trigger_r=breakeven_trigger_r
        ),
        **engine_kwargs,
    )


def test_causal_ema_trend_structure_is_prefix_stable_and_exact():
    index = pd.date_range("2026-01-01T00:00:00Z", periods=9, freq="6h")
    data = pd.DataFrame(
        {"Close": np.arange(1.0, 10.0), "Volume": 1000.0},
        index=index,
    )
    feature = CausalEMATrendStructure(
        fast_period=3,
        slow_period=5,
        slope_lookback=2,
    )

    full = feature.generate(data)
    prefix = feature.generate(data.iloc[:8])

    pd.testing.assert_frame_equal(full.iloc[:8], prefix)
    assert full.index.equals(data.index)
    assert full["ALPHA_DISCOVERY_TREND_STRUCTURE"].iloc[:4].eq(False).all()
    assert full["ALPHA_DISCOVERY_TREND_STRUCTURE"].iloc[4:].eq(True).all()
    assert full["ALPHA_DISCOVERY_EMA_3_SLOPE_2"].iloc[-1] > 0.0


@pytest.mark.parametrize(
    "mutator,match",
    [
        (lambda frame: frame.drop(columns=["Close"]), "Close"),
        (lambda frame: frame.assign(Close=np.inf), "finite"),
        (lambda frame: frame.assign(Close=0.0), "positive"),
        (
            lambda frame: frame.set_axis(
                list(frame.index[:-1]) + [frame.index[-2]], axis=0
            ),
            "unique chronological",
        ),
    ],
)
def test_causal_ema_trend_structure_fails_closed(mutator, match):
    data = pd.DataFrame(
        {"Close": np.arange(1.0, 10.0)},
        index=pd.date_range("2026-01-01", periods=9, freq="6h", tz="UTC"),
    )
    with pytest.raises(ValueError, match=match):
        CausalEMATrendStructure(3, 5, 2).generate(mutator(data))


def test_completed_bar_break_even_is_not_retroactive_on_trigger_bar():
    signals = (1, 0, 0, 0)
    data = market(
        signals,
        opens=[100.0, 100.0, 101.0, 100.0],
        highs=[101.0, 102.5, 101.5, 101.0],
        lows=[99.0, 98.5, 99.5, 99.0],
    )
    engine = protected_engine(signals, breakeven_trigger_r=1.0)

    engine.run(data)
    trade = engine.trade_history[0]

    assert trade["entry_index"] == data.index[1]
    assert trade["exit_index"] == data.index[2]
    assert trade["planned_stop_price"] == pytest.approx(98.0)
    assert trade["active_protective_stop_price_at_exit"] == pytest.approx(100.0)
    assert trade["protective_break_even_triggered"] is True
    assert trade["protective_break_even_trigger_index"] == data.index[1]
    assert trade["protective_exit_type"] == "STOP_INTRABAR"
    assert trade["gross_profit_loss"] == pytest.approx(0.0)


def test_break_even_gap_uses_worse_next_open_not_the_entry_price():
    signals = (1, 0, 0, 0)
    data = market(
        signals,
        opens=[100.0, 100.0, 95.0, 100.0],
        highs=[101.0, 102.5, 96.0, 101.0],
        lows=[99.0, 99.0, 94.0, 99.0],
    )
    engine = protected_engine(signals, breakeven_trigger_r=1.0)

    engine.run(data)
    trade = engine.trade_history[0]

    assert trade["protective_exit_type"] == "STOP_GAP"
    assert trade["protective_trigger_price"] == pytest.approx(100.0)
    assert trade["exit_market_price"] == pytest.approx(95.0)
    assert trade["realized_r"] == pytest.approx(-2.5)


def test_entry_price_break_even_can_still_have_negative_net_realized_r():
    signals = (1, 0, 0, 0)
    data = market(
        signals,
        opens=[100.0, 100.0, 101.0, 100.0],
        highs=[101.0, 102.5, 101.5, 101.0],
        lows=[99.0, 98.5, 99.5, 99.0],
    )
    engine = protected_engine(
        signals,
        breakeven_trigger_r=1.0,
        commission_rate=0.001,
        slippage_rate=0.001,
        spread_rate=0.002,
    )

    engine.run(data)
    trade = engine.trade_history[0]

    assert trade["protective_break_even_triggered"] is True
    assert trade["exit_market_price"] == pytest.approx(trade["entry_price"])
    assert trade["total_costs"] > 0.0
    assert trade["realized_r"] < 0.0


def test_static_policy_does_not_move_stop_after_one_r():
    signals = (1, 0, 0)
    data = market(
        signals,
        opens=[100.0, 100.0, 100.0],
        highs=[101.0, 102.5, 101.0],
        lows=[99.0, 98.5, 99.5],
    )
    engine = protected_engine(signals)

    engine.run(data)
    trade = engine.trade_history[0]

    assert trade["exit_reason"] == "TERMINAL_FORCE_CLOSE"
    assert trade["protective_break_even_enabled"] is False
    assert trade["protective_break_even_triggered"] is False


def test_final_completed_bar_cannot_activate_stop_without_a_following_open():
    signals = (1, 0)
    data = market(
        signals,
        opens=[100.0, 100.0],
        highs=[101.0, 102.5],
        lows=[99.0, 99.0],
    )
    engine = protected_engine(signals, breakeven_trigger_r=1.0)

    engine.run(data)
    trade = engine.trade_history[0]

    assert trade["exit_reason"] == "TERMINAL_FORCE_CLOSE"
    assert trade["protective_break_even_enabled"] is True
    assert trade["protective_break_even_triggered"] is False
    assert trade["protective_break_even_trigger_index"] is None


def test_trade_path_records_post_entry_excursions_r_and_holding_bars():
    signals = (1, 0, 0, 0)
    data = market(
        signals,
        opens=[100.0, 100.0, 100.0, 100.0],
        highs=[101.0, 101.0, 106.5, 101.0],
        lows=[99.0, 99.5, 99.0, 99.0],
    )
    engine = protected_engine(signals)

    engine.run(data)
    trade = engine.trade_history[0]

    assert trade["maximum_favorable_excursion_r"] == pytest.approx(3.0)
    assert trade["maximum_adverse_excursion_r"] == pytest.approx(0.25)
    assert trade["realized_r"] == pytest.approx(3.0)
    assert trade["holding_bars"] == 1
    assert trade["bars_to_maximum_favorable_excursion"] == 1
    assert trade["trade_path_observation_policy"] == (
        "SURVIVING_BAR_EXTREMA_EXIT_BAR_EXECUTABLE_PATH_ONLY"
    )


def test_stop_first_conflict_does_not_use_unreachable_exit_bar_high_for_mfe():
    signals = (1, 0, 0)
    data = market(
        signals,
        opens=[100.0, 100.0, 100.0],
        highs=[101.0, 107.0, 101.0],
        lows=[99.0, 97.0, 99.0],
    )
    engine = protected_engine(signals)

    engine.run(data)
    trade = engine.trade_history[0]

    assert trade["protective_same_bar_conflict"] is True
    assert trade["maximum_favorable_excursion_r"] == pytest.approx(0.0)
    assert trade["maximum_adverse_excursion_r"] == pytest.approx(1.0)
    assert trade["holding_bars"] == 0
    assert trade["bars_to_maximum_favorable_excursion"] == 0
