import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from strategy_engine import StrategyEngine
from strategy_library import StrategyLibrary
from trend_pullback_state import CausalTrendPullbackStateMachine
from trend_pullback_volume_protocol import (
    TREND_PULLBACK_PARAMETER_CATALOG,
    TREND_PULLBACK_PARAMETER_ORDER,
)
from trend_pullback_volume_strategy import (
    TrendPullbackVolumeStrategy,
    trend_pullback_volume_strategy_engines,
)
from volume_research import VolumeResearchConfig


def setup_frame(rows=20):
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="6h")
    close = np.full(rows, 110.0)
    high = np.full(rows, 111.0)
    relative_volume = np.full(rows, 0.8)
    adx = np.full(rows, 30.0)

    close[9] = 100.5
    high[9] = 101.0
    close[10] = 102.0
    high[10] = 103.0
    relative_volume[10] = 1.3
    adx[10] = 22.0

    return pd.DataFrame(
        {
            "Open": close,
            "High": high,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.full(rows, 100.0),
            "ADX_14": adx,
            "PLUS_DI_14": np.full(rows, 25.0),
            "MINUS_DI_14": np.full(rows, 10.0),
            "ATR_14": np.full(rows, 2.0),
            "ALPHA_DISCOVERY_EMA_50": np.full(rows, 100.0),
            "ALPHA_DISCOVERY_EMA_200": np.full(rows, 90.0),
            "ALPHA_DISCOVERY_EMA_50_SLOPE_4": np.full(rows, 1.0),
            "ALPHA_DISCOVERY_TREND_STRUCTURE": np.full(rows, True),
            "RELATIVE_VOLUME_20": relative_volume,
        },
        index=index,
    )


class FixedTrendStructure:
    def generate(self, data):
        result = data.copy(deep=True)
        result["ALPHA_DISCOVERY_EMA_50"] = 100.0
        result["ALPHA_DISCOVERY_EMA_200"] = 90.0
        result["ALPHA_DISCOVERY_EMA_50_SLOPE_4"] = 1.0
        result["ALPHA_DISCOVERY_TREND_STRUCTURE"] = result.get(
            "TEST_TREND", pd.Series(True, index=result.index)
        ).astype(bool)
        return result

    def configuration(self):
        return {
            "fast_period": 50,
            "slow_period": 200,
            "slope_lookback": 4,
            "causal": True,
        }


def fixed_volume(data, configuration):
    result = data.copy(deep=True)
    relative = result.get(
        "TEST_RELATIVE_VOLUME", pd.Series(0.8, index=result.index)
    ).astype(float)
    result[f"RELATIVE_VOLUME_{configuration.lookback}"] = relative
    result[f"VOLUME_REGIME_{configuration.lookback}"] = "NORMAL"
    result[f"ON_BALANCE_VOLUME_DIRECTION_{configuration.lookback}"] = "UNKNOWN"
    return result


def raw_strategy_frame(rows=20):
    frame = setup_frame(rows).drop(
        columns=[
            "ALPHA_DISCOVERY_EMA_50",
            "ALPHA_DISCOVERY_EMA_200",
            "ALPHA_DISCOVERY_EMA_50_SLOPE_4",
            "ALPHA_DISCOVERY_TREND_STRUCTURE",
            "RELATIVE_VOLUME_20",
        ]
    )
    frame["TEST_RELATIVE_VOLUME"] = 0.8
    frame.loc[frame.index[10], "TEST_RELATIVE_VOLUME"] = 1.3
    frame["TEST_TREND"] = True
    return frame


def strategy(parameter_index=0, **kwargs):
    return TrendPullbackVolumeStrategy(
        TREND_PULLBACK_PARAMETER_CATALOG[parameter_index],
        volume_feature_generator=kwargs.pop(
            "volume_feature_generator", fixed_volume
        ),
        trend_structure=kwargs.pop(
            "trend_structure", FixedTrendStructure()
        ),
        **kwargs,
    )


def test_state_machine_freezes_exact_causal_configuration():
    machine = CausalTrendPullbackStateMachine(
        TREND_PULLBACK_PARAMETER_CATALOG[0]
    )
    assert machine.configuration() == {
        "parameter_set_id": "pb0p5-rv1p2-2atr-static3r",
        "prior_strength_lookback_bars": 8,
        "prior_adx_confirmation": 25.0,
        "pullback_distance_atr": 0.5,
        "pullback_relative_volume_ceiling": 1.0,
        "trigger_relative_volume": 1.2,
        "current_adx_floor": 20.0,
        "setup_expiry_bars": 8,
        "observation_timing": "COMPLETED_BAR_CLOSE",
        "same_bar_pullback_and_trigger": False,
        "future_bar_access": False,
    }


def test_state_machine_requires_prior_strength_then_pullback_then_later_recovery():
    result = CausalTrendPullbackStateMachine(
        TREND_PULLBACK_PARAMETER_CATALOG[0]
    ).generate(setup_frame())

    assert result.iloc[9]["TREND_PULLBACK_PRIOR_STRENGTH"]
    assert result.iloc[9]["TREND_PULLBACK_PULLBACK_CONDITION"]
    assert result.iloc[9]["TREND_PULLBACK_SETUP_ACTIVE"]
    assert not result.iloc[9]["TREND_PULLBACK_TRIGGER"]
    assert result.iloc[10]["TREND_PULLBACK_RECOVERY_CONDITION"]
    assert result.iloc[10]["TREND_PULLBACK_TRIGGER"]
    assert not result.iloc[10]["TREND_PULLBACK_SETUP_ACTIVE"]


def test_state_machine_does_not_carry_a_setup_across_evaluation_boundary():
    result = CausalTrendPullbackStateMachine(
        TREND_PULLBACK_PARAMETER_CATALOG[0]
    ).generate(setup_frame(), evaluation_start_position=10)

    assert result["TREND_PULLBACK_TRIGGER"].eq(False).all()
    assert result.iloc[10]["TREND_PULLBACK_RECOVERY_CONDITION"]
    assert result.iloc[:10]["TREND_PULLBACK_SETUP_AGE"].eq(-1).all()


def test_state_machine_expires_after_eight_subsequent_completed_bars():
    data = setup_frame(22)
    data.loc[data.index[10], "RELATIVE_VOLUME_20"] = 0.8
    data.loc[data.index[18], "Close"] = 102.0
    data.loc[data.index[17], "High"] = 101.0
    data.loc[data.index[18], "RELATIVE_VOLUME_20"] = 1.3
    data.loc[data.index[18], "ADX_14"] = 22.0

    result = CausalTrendPullbackStateMachine(
        TREND_PULLBACK_PARAMETER_CATALOG[0]
    ).generate(data)

    assert not result["TREND_PULLBACK_TRIGGER"].any()
    assert result.iloc[17]["TREND_PULLBACK_SETUP_AGE"] == 8
    assert not result.iloc[17]["TREND_PULLBACK_SETUP_ACTIVE"]


def test_state_machine_allows_recovery_on_exact_eighth_subsequent_bar():
    data = setup_frame(22)
    data.loc[data.index[10], "RELATIVE_VOLUME_20"] = 0.8
    data.loc[data.index[17], "Close"] = 102.0
    data.loc[data.index[16], "High"] = 101.0
    data.loc[data.index[17], "RELATIVE_VOLUME_20"] = 1.3
    data.loc[data.index[17], "ADX_14"] = 22.0

    result = CausalTrendPullbackStateMachine(
        TREND_PULLBACK_PARAMETER_CATALOG[0]
    ).generate(data)
    assert result.iloc[17]["TREND_PULLBACK_TRIGGER"]
    assert result.iloc[17]["TREND_PULLBACK_SETUP_AGE"] == 8


def test_state_machine_never_triggers_on_the_bar_that_arms_a_setup():
    machine = CausalTrendPullbackStateMachine(
        TREND_PULLBACK_PARAMETER_CATALOG[0]
    )
    state, triggered, age = machine.advance(
        machine.initial_state(),
        pullback=True,
        recovery=True,
        trend_valid=True,
    )
    assert state.armed
    assert age == 0
    assert triggered is False


def test_state_machine_lost_trend_invalidates_armed_setup():
    data = setup_frame()
    data.loc[data.index[10], "ALPHA_DISCOVERY_TREND_STRUCTURE"] = False
    data.loc[data.index[11], "Close"] = 104.0
    data.loc[data.index[10], "High"] = 103.0
    data.loc[data.index[11], "RELATIVE_VOLUME_20"] = 1.3

    result = CausalTrendPullbackStateMachine(
        TREND_PULLBACK_PARAMETER_CATALOG[0]
    ).generate(data)
    assert not result["TREND_PULLBACK_TRIGGER"].any()


@pytest.mark.parametrize(
    "change",
    [
        "NO_PRIOR_STRENGTH",
        "PULLBACK_TOO_FAR",
        "PULLBACK_VOLUME_TOO_HIGH",
        "TREND_NOT_BULLISH",
        "RECOVERY_BELOW_PREVIOUS_HIGH",
        "RECOVERY_VOLUME_TOO_LOW",
        "RECOVERY_ADX_TOO_LOW",
        "RECOVERY_DIRECTION_WRONG",
    ],
)
def test_strategy_entry_fails_when_one_frozen_sequence_gate_is_missing(change):
    data = raw_strategy_frame()
    if change == "NO_PRIOR_STRENGTH":
        data.loc[data.index[1:10], "ADX_14"] = 24.0
    elif change == "PULLBACK_TOO_FAR":
        data.loc[data.index[9], "Close"] = 102.0
    elif change == "PULLBACK_VOLUME_TOO_HIGH":
        data.loc[data.index[9], "TEST_RELATIVE_VOLUME"] = 1.01
    elif change == "TREND_NOT_BULLISH":
        data.loc[data.index[9], "TEST_TREND"] = False
    elif change == "RECOVERY_BELOW_PREVIOUS_HIGH":
        data.loc[data.index[10], "Close"] = 101.0
    elif change == "RECOVERY_VOLUME_TOO_LOW":
        data.loc[data.index[10], "TEST_RELATIVE_VOLUME"] = 1.19
    elif change == "RECOVERY_ADX_TOO_LOW":
        data.loc[data.index[10], "ADX_14"] = 19.0
    elif change == "RECOVERY_DIRECTION_WRONG":
        data.loc[data.index[10], "PLUS_DI_14"] = 9.0

    result = strategy().generate_signals(data)
    assert not result["Signal"].eq(1).any()


def test_strategy_enters_on_recovery_and_exposes_exact_risk_evidence():
    data = raw_strategy_frame()
    data.loc[data.index[13], "ADX_14"] = 14.0
    result = strategy().generate_signals(data)

    assert result["Signal"].tolist() == [0] * 10 + [1, 0, 0, -1] + [0] * 6
    assert result.iloc[10]["TREND_PULLBACK_ENTRY_CONDITION"]
    assert result.iloc[10]["ALPHA_V2_ATR_RISK_DISTANCE"] == pytest.approx(4.0)
    assert result.iloc[10]["ALPHA_V2_REWARD_RISK_RATIO"] == pytest.approx(3.0)
    assert result.iloc[10]["TREND_PULLBACK_PARAMETER_SET_ID"] == (
        "pb0p5-rv1p2-2atr-static3r"
    )


@pytest.mark.parametrize("exit_gate", ["EMA", "ADX", "DIRECTION"])
def test_strategy_uses_each_frozen_completed_bar_signal_exit(exit_gate):
    data = raw_strategy_frame()
    if exit_gate == "EMA":
        data.loc[data.index[13], "Close"] = 99.0
    elif exit_gate == "ADX":
        data.loc[data.index[13], "ADX_14"] = 14.0
    else:
        data.loc[data.index[13], "PLUS_DI_14"] = 9.0

    result = strategy().generate_signals(data)
    assert result.iloc[10]["Signal"] == 1
    assert result.iloc[13]["Signal"] == -1


def test_strategy_does_not_arm_a_new_setup_while_position_or_cooldown_is_active():
    data = raw_strategy_frame(24)
    data.loc[data.index[13], "ADX_14"] = 14.0
    data.loc[data.index[12], "Close"] = 100.5
    data.loc[data.index[12], "TEST_RELATIVE_VOLUME"] = 0.8
    data.loc[data.index[15], "Close"] = 100.5
    data.loc[data.index[15], "TEST_RELATIVE_VOLUME"] = 0.8

    result = strategy().generate_signals(data)
    assert result.iloc[10]["Signal"] == 1
    assert result.iloc[13]["Signal"] == -1
    assert not result.iloc[12]["TREND_PULLBACK_SETUP_ACTIVE"]
    assert not result.iloc[15]["TREND_PULLBACK_SETUP_ACTIVE"]


def test_strategy_resets_setup_state_at_evaluation_start():
    result = strategy().generate_signals(
        raw_strategy_frame(), evaluation_start_position=10
    )
    assert not result["Signal"].eq(1).any()
    assert result.iloc[10]["TREND_PULLBACK_RECOVERY_CONDITION"]


def test_strategy_configuration_has_no_hidden_regime_or_obv_entry_gate():
    configuration = strategy().configuration()
    assert configuration["strategy_name"] == (
        "trend_pullback_volume_pb0p5-rv1p2-2atr-static3r"
    )
    assert configuration["market_regime_gate"] == "NONE"
    assert configuration["obv_role"] == "DIAGNOSTIC_ONLY_NOT_ENTRY_GATE"
    assert configuration["signal_observation"] == "COMPLETED_BAR_CLOSE"
    assert configuration["execution_timing"] == "NEXT_BAR_OPEN"
    assert configuration["signal_state_reset"] == "EVALUATION_WINDOW_START"
    assert configuration["protective_management"] == (
        "STATIC_2ATR_STOP_AND_3R_TARGET"
    )


def test_strategy_engines_cover_exact_four_member_catalog_order():
    engines = trend_pullback_volume_strategy_engines()
    assert tuple(engines) == TREND_PULLBACK_PARAMETER_ORDER
    assert tuple(
        engine.strategy.parameter_set.parameter_set_id
        for engine in engines.values()
    ) == TREND_PULLBACK_PARAMETER_ORDER
    assert len({engine.strategy_name for engine in engines.values()}) == 4


def test_strategy_rejects_volume_or_state_machine_identity_drift():
    with pytest.raises(ValueError, match="Volume configuration"):
        strategy(
            volume_configuration=VolumeResearchConfig(
                lookback=19,
                baseline_lag=1,
            )
        )
    wrong_machine = CausalTrendPullbackStateMachine(
        TREND_PULLBACK_PARAMETER_CATALOG[1]
    )
    with pytest.raises(ValueError, match="State machine"):
        strategy(state_machine=wrong_machine)


@pytest.mark.parametrize("value", [-1, True, 20])
def test_strategy_evaluation_start_fails_closed(value):
    with pytest.raises((TypeError, ValueError), match="Evaluation start"):
        strategy().generate_signals(raw_strategy_frame(), value)


def test_real_feature_and_strategy_path_is_prefix_causal():
    rows = 320
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="6h")
    close = 100.0 + np.linspace(0.0, 70.0, rows) + 2.0 * np.sin(
        np.arange(rows) / 7.0
    )
    data = pd.DataFrame(
        {
            "Open": close - 0.1,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 100.0 + (np.arange(rows) % 13) * 25.0,
        },
        index=index,
    )
    instance = TrendPullbackVolumeStrategy(
        TREND_PULLBACK_PARAMETER_CATALOG[0]
    )
    library = StrategyLibrary()
    library.register(instance)
    engine = StrategyEngine(library, instance.name)

    full = engine.run(data)
    prefix = engine.run(data.iloc[:280])
    for column in (
        "Signal",
        "TREND_PULLBACK_PULLBACK_CONDITION",
        "TREND_PULLBACK_RECOVERY_CONDITION",
        "TREND_PULLBACK_TRIGGER",
    ):
        pd.testing.assert_series_equal(
            full.iloc[:280][column], prefix[column], check_names=True
        )
