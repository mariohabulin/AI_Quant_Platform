import copy
import os
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_round_1_causal_signals import (
    ACTION_INTENT_COLUMN,
    ENTER_NEXT_OPEN,
    FAMILY_COLUMN,
    FEATURE_COLUMNS,
    FEATURES_AVAILABLE_COLUMN,
    HYPOTHESIS_COLUMN,
    REGIME_CONDITION_COLUMN,
    SETUP_CONDITION_COLUMN,
    SETUP_LOW_COLUMN,
    SETUP_TIMESTAMP_COLUMN,
    SIGNAL_ATR_COLUMN,
    SIGNAL_CONDITION_COLUMN,
    STATE_AFTER_COLUMN,
    STATE_BEFORE_COLUMN,
    TARGET_ANCHOR_COLUMN,
    TRANSITION_COLUMN,
    KrakenAIDrivenV2Round1CausalFeatureEngine,
    KrakenAIDrivenV2Round1SignalEngine,
)
from kraken_ai_driven_v2_hybrid_discovery_round_1 import (
    HYPOTHESIS_ORDER,
    ROUND_1_CONFIGURATION_LOCK,
)


def continuous_frame(rows=280):
    positions = np.arange(rows, dtype=float)
    close = 100.0 + 0.08 * positions + 2.0 * np.sin(positions / 9.0)
    open_price = close - 0.2 * np.cos(positions / 5.0)
    high = np.maximum(open_price, close) + 1.0 + 0.1 * np.sin(positions / 4.0)
    low = np.minimum(open_price, close) - 1.0 - 0.1 * np.cos(positions / 6.0)
    volume = 100.0 + np.mod(positions, 17.0)
    return pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=pd.date_range("2020-01-01T00:00:00Z", periods=rows, freq="D"),
    )


def feature_fixture(rows=5):
    frame = pd.DataFrame(
        {
            "Open": np.full(rows, 100.0),
            "High": np.full(rows, 102.0),
            "Low": np.full(rows, 98.0),
            "Close": np.full(rows, 100.0),
            "Volume": np.full(rows, 100.0),
        },
        index=pd.date_range("2026-01-01T00:00:00Z", periods=rows, freq="D"),
    )
    for column in FEATURE_COLUMNS:
        frame[column] = np.nan
    return frame


def feature_name(suffix):
    return f"KRAKEN_AI_V2_R1_{suffix}"


def test_feature_engine_configuration_is_exactly_round_1_and_nonexecuting():
    configuration = KrakenAIDrivenV2Round1CausalFeatureEngine().configuration()

    assert configuration["component_id"] == (
        "kraken-ai-v2-round-1-causal-features-v1"
    )
    assert configuration["round_1_configuration_sha256"] == (
        ROUND_1_CONFIGURATION_LOCK.sha256
    )
    assert configuration["completed_daily_bar_only"] is True
    assert configuration["rolling_baseline_current_bar_included"] is False
    assert configuration["gap_policy"] == "SPLIT_BEFORE_GENERATION"
    assert configuration["signal_emitted"] is False
    assert configuration["execution_implemented"] is False
    assert configuration["dataset_opened"] is False


def test_feature_engine_preserves_input_and_generates_exact_prior_baselines():
    source = continuous_frame()
    original = source.copy(deep=True)
    result = KrakenAIDrivenV2Round1CausalFeatureEngine().generate(source)
    position = 250

    pd.testing.assert_frame_equal(source, original)
    assert result.iloc[position][feature_name("PREVIOUS_CLOSE")] == pytest.approx(
        source["Close"].iloc[position - 1]
    )
    assert result.iloc[position][feature_name("PRIOR_CLOSE_MAX_60")] == pytest.approx(
        source["Close"].iloc[position - 60 : position].max()
    )
    expected_drawdown = (
        source["Close"].iloc[position]
        / source["Close"].iloc[position - 60 : position].max()
        - 1.0
    )
    assert result.iloc[position][feature_name("DRAWDOWN_60")] == pytest.approx(
        expected_drawdown
    )
    assert result.iloc[position][feature_name("PRIOR_VOLUME_MEDIAN_30")] == pytest.approx(
        source["Volume"].iloc[position - 30 : position].median()
    )
    assert result.iloc[position][feature_name("DONCHIAN_PRIOR_CLOSE_HIGH_55")] == pytest.approx(
        source["Close"].iloc[position - 55 : position].max()
    )
    assert result.iloc[position][feature_name("BOLLINGER_MID_20_PRIOR")] == pytest.approx(
        source["Close"].iloc[position - 20 : position].mean()
    )


def test_current_bar_mutation_cannot_change_its_prior_baselines():
    source = continuous_frame()
    changed = source.copy(deep=True)
    changed.iloc[-1, changed.columns.get_loc("Open")] *= 1.2
    changed.iloc[-1, changed.columns.get_loc("High")] *= 1.5
    changed.iloc[-1, changed.columns.get_loc("Low")] *= 0.8
    changed.iloc[-1, changed.columns.get_loc("Close")] *= 1.3
    changed.iloc[-1, changed.columns.get_loc("Volume")] *= 10.0
    first = KrakenAIDrivenV2Round1CausalFeatureEngine().generate(source)
    second = KrakenAIDrivenV2Round1CausalFeatureEngine().generate(changed)

    for suffix in (
        "PREVIOUS_CLOSE",
        "PRIOR_CLOSE_MAX_60",
        "PRIOR_VOLUME_MEDIAN_30",
        "PRIOR_ATR_14",
        "EMA_20_PRIOR",
        "EMA_50_PRIOR",
        "EMA_200_PRIOR",
        "ADX_14_PRIOR",
        "BOLLINGER_MID_20_PRIOR",
        "BOLLINGER_LOWER_20_PRIOR",
        "DONCHIAN_PRIOR_CLOSE_HIGH_55",
    ):
        column = feature_name(suffix)
        assert first.iloc[-1][column] == pytest.approx(second.iloc[-1][column])


def test_feature_generation_is_prefix_causal_under_future_mutation():
    source = continuous_frame()
    cutoff = 250
    prefix = KrakenAIDrivenV2Round1CausalFeatureEngine().generate(
        source.iloc[:cutoff]
    )
    changed = source.copy(deep=True)
    changed.iloc[cutoff:, changed.columns.get_loc("Close")] *= 1.8
    changed.iloc[cutoff:, changed.columns.get_loc("High")] *= 1.9
    changed.iloc[cutoff:, changed.columns.get_loc("Low")] *= 0.6
    full = KrakenAIDrivenV2Round1CausalFeatureEngine().generate(changed)

    pd.testing.assert_frame_equal(
        prefix,
        full.iloc[:cutoff],
        check_dtype=True,
        check_exact=True,
    )


@pytest.mark.parametrize(
    "mutator,error",
    [
        (lambda frame: frame.iloc[0:0], "cannot be empty"),
        (lambda frame: frame.drop(columns=["Volume"]), "exact ordered OHLCV"),
        (lambda frame: frame.rename_axis(None).reset_index(drop=True), "DatetimeIndex"),
        (lambda frame: frame.assign(Close=np.nan), "finite numeric"),
    ],
)
def test_feature_input_validation_fails_closed(mutator, error):
    with pytest.raises((TypeError, ValueError), match=error):
        KrakenAIDrivenV2Round1CausalFeatureEngine().generate(
            mutator(continuous_frame())
        )


def test_feature_engine_rejects_crossing_a_recorded_gap():
    source = continuous_frame().drop(continuous_frame().index[100])

    with pytest.raises(ValueError, match="continuous daily"):
        KrakenAIDrivenV2Round1CausalFeatureEngine().generate(source)


def test_capitulation_path_arms_waits_and_confirms_without_reference_a_gate():
    frame = feature_fixture(3)
    frame.iloc[0, frame.columns.get_loc("Close")] = 80.0
    frame.iloc[0, frame.columns.get_loc("Low")] = 75.0
    frame.iloc[0, frame.columns.get_loc(feature_name("DRAWDOWN_60"))] = -0.20
    frame.iloc[0, frame.columns.get_loc(feature_name("CLOSE_RETURN_1"))] = -0.07
    frame.iloc[0, frame.columns.get_loc(feature_name("TR_TO_PRIOR_ATR"))] = 1.6
    frame.iloc[0, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 1.6
    frame.iloc[0, frame.columns.get_loc(feature_name("CLOSE_LOCATION"))] = 0.2
    frame.iloc[0, frame.columns.get_loc(feature_name("PRIOR_HIGH_1"))] = 100.0
    frame.iloc[0, frame.columns.get_loc(feature_name("PRIOR_ATR_14"))] = 2.0

    frame.iloc[1, frame.columns.get_loc("Close")] = 79.0
    frame.iloc[1, frame.columns.get_loc("Low")] = 74.0
    frame.iloc[1, frame.columns.get_loc(feature_name("CLOSE_RETURN_1"))] = -0.01
    frame.iloc[1, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 1.0
    frame.iloc[1, frame.columns.get_loc(feature_name("CLOSE_LOCATION"))] = 0.5
    frame.iloc[1, frame.columns.get_loc(feature_name("PRIOR_HIGH_1"))] = 82.0
    frame.iloc[1, frame.columns.get_loc(feature_name("PRIOR_ATR_14"))] = 2.0

    frame.iloc[2, frame.columns.get_loc("Close")] = 85.0
    frame.iloc[2, frame.columns.get_loc("Low")] = 78.0
    frame.iloc[2, frame.columns.get_loc(feature_name("CLOSE_RETURN_1"))] = 0.05
    frame.iloc[2, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 0.9
    frame.iloc[2, frame.columns.get_loc(feature_name("CLOSE_LOCATION"))] = 0.8
    frame.iloc[2, frame.columns.get_loc(feature_name("PRIOR_HIGH_1"))] = 84.0
    frame.iloc[2, frame.columns.get_loc(feature_name("PRIOR_ATR_14"))] = 2.2

    result = KrakenAIDrivenV2Round1SignalEngine().generate_from_features(
        "CAPITULATION_RECOVERY", frame
    )

    assert result.iloc[0][REGIME_CONDITION_COLUMN] == True
    assert result.iloc[0][TRANSITION_COLUMN] == "CAPITULATION_ARMED"
    assert result.iloc[0][ACTION_INTENT_COLUMN] == "NONE"
    assert result.iloc[1][TRANSITION_COLUMN] == "CAPITULATION_WAIT"
    assert result.iloc[2][SIGNAL_CONDITION_COLUMN] == True
    assert result.iloc[2][TRANSITION_COLUMN] == "CAPITULATION_CONFIRMATION"
    assert result.iloc[2][ACTION_INTENT_COLUMN] == ENTER_NEXT_OPEN
    assert result.iloc[2][SETUP_LOW_COLUMN] == pytest.approx(74.0)
    assert result.iloc[2][SIGNAL_ATR_COLUMN] == pytest.approx(2.2)
    assert np.isnan(result.iloc[2][TARGET_ANCHOR_COLUMN])
    assert result.iloc[2][STATE_AFTER_COLUMN] == "FLAT"


def test_capitulation_confirmation_pattern_is_not_a_signal_without_setup():
    frame = feature_fixture(1)
    frame.iloc[0, frame.columns.get_loc("Close")] = 101.0
    frame.iloc[0, frame.columns.get_loc(feature_name("CLOSE_RETURN_1"))] = 0.02
    frame.iloc[0, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 1.0
    frame.iloc[0, frame.columns.get_loc(feature_name("CLOSE_LOCATION"))] = 0.8
    frame.iloc[0, frame.columns.get_loc(feature_name("PRIOR_HIGH_1"))] = 100.0
    frame.iloc[0, frame.columns.get_loc(feature_name("PRIOR_ATR_14"))] = 2.0

    result = KrakenAIDrivenV2Round1SignalEngine().generate_from_features(
        "CAPITULATION_RECOVERY", frame
    )

    assert result.iloc[0][STATE_BEFORE_COLUMN] == "FLAT"
    assert result.iloc[0][SIGNAL_CONDITION_COLUMN] == False
    assert result.iloc[0][ACTION_INTENT_COLUMN] == "NONE"


def test_trend_pullback_requires_setup_then_immediate_confirmation():
    frame = feature_fixture(2)
    for row in range(2):
        frame.iloc[row, frame.columns.get_loc(feature_name("EMA_20_PRIOR"))] = 100.0
        frame.iloc[row, frame.columns.get_loc(feature_name("EMA_50_PRIOR"))] = 95.0
        frame.iloc[row, frame.columns.get_loc(feature_name("EMA_200_PRIOR"))] = 90.0
        frame.iloc[row, frame.columns.get_loc(feature_name("EMA_50_SLOPE_20"))] = 0.03
        frame.iloc[row, frame.columns.get_loc(feature_name("ADX_14_PRIOR"))] = 25.0
        frame.iloc[row, frame.columns.get_loc(feature_name("PRIOR_ATR_14"))] = 2.0
    frame.iloc[0, frame.columns.get_loc("Low")] = 99.8
    frame.iloc[0, frame.columns.get_loc("Close")] = 101.0
    frame.iloc[0, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 0.8
    frame.iloc[0, frame.columns.get_loc(feature_name("PRIOR_HIGH_1"))] = 101.5
    frame.iloc[1, frame.columns.get_loc("Close")] = 103.0
    frame.iloc[1, frame.columns.get_loc("High")] = 104.0
    frame.iloc[1, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 1.2
    frame.iloc[1, frame.columns.get_loc(feature_name("PRIOR_HIGH_1"))] = 102.0

    result = KrakenAIDrivenV2Round1SignalEngine().generate_from_features(
        "TREND_PULLBACK_CONTINUATION", frame
    )

    assert result.iloc[0][REGIME_CONDITION_COLUMN] == True
    assert result.iloc[0][SETUP_CONDITION_COLUMN] == True
    assert result.iloc[0][TRANSITION_COLUMN] == "TREND_PULLBACK_ARMED"
    assert result.iloc[1][SIGNAL_CONDITION_COLUMN] == True
    assert result.iloc[1][TRANSITION_COLUMN] == "TREND_PULLBACK_CONFIRMATION"
    assert result.iloc[1][ACTION_INTENT_COLUMN] == ENTER_NEXT_OPEN
    assert result.iloc[1][SETUP_LOW_COLUMN] == pytest.approx(99.8)


def test_trend_confirmation_pattern_requires_immediately_armed_setup():
    frame = feature_fixture(3)
    for row in range(3):
        frame.iloc[row, frame.columns.get_loc(feature_name("EMA_20_PRIOR"))] = 100.0
        frame.iloc[row, frame.columns.get_loc(feature_name("EMA_50_PRIOR"))] = 95.0
        frame.iloc[row, frame.columns.get_loc(feature_name("EMA_200_PRIOR"))] = 90.0
        frame.iloc[row, frame.columns.get_loc(feature_name("EMA_50_SLOPE_20"))] = 0.03
        frame.iloc[row, frame.columns.get_loc(feature_name("ADX_14_PRIOR"))] = 25.0
        frame.iloc[row, frame.columns.get_loc(feature_name("PRIOR_ATR_14"))] = 2.0
        frame.iloc[row, frame.columns.get_loc(feature_name("PRIOR_HIGH_1"))] = 102.0

    frame.iloc[0, frame.columns.get_loc("Low")] = 99.8
    frame.iloc[0, frame.columns.get_loc("Close")] = 101.0
    frame.iloc[0, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 0.8
    frame.iloc[1, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 1.0
    frame.iloc[2, frame.columns.get_loc("Close")] = 103.0
    frame.iloc[2, frame.columns.get_loc("High")] = 104.0
    frame.iloc[2, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 1.2

    result = KrakenAIDrivenV2Round1SignalEngine().generate_from_features(
        "TREND_PULLBACK_CONTINUATION", frame
    )

    assert result.iloc[0][TRANSITION_COLUMN] == "TREND_PULLBACK_ARMED"
    assert result.iloc[1][TRANSITION_COLUMN] == "TREND_PULLBACK_EXPIRED"
    assert result.iloc[2][STATE_BEFORE_COLUMN] == "FLAT"
    assert result.iloc[2][SIGNAL_CONDITION_COLUMN] == False
    assert result.iloc[2][ACTION_INTENT_COLUMN] == "NONE"


def test_range_reversion_freezes_signal_time_midline_as_target_anchor():
    frame = feature_fixture(2)
    for row in range(2):
        frame.iloc[row, frame.columns.get_loc(feature_name("BAND_WIDTH_TO_PRIOR_MEDIAN_120"))] = 1.0
        frame.iloc[row, frame.columns.get_loc(feature_name("ATR_TO_PRIOR_MEDIAN_120"))] = 1.0
        frame.iloc[row, frame.columns.get_loc(feature_name("PRIOR_ATR_14"))] = 2.0
        frame.iloc[row, frame.columns.get_loc(feature_name("BOLLINGER_LOWER_20_PRIOR"))] = 91.0
        frame.iloc[row, frame.columns.get_loc(feature_name("BOLLINGER_MID_20_PRIOR"))] = 100.0
    frame.iloc[0, frame.columns.get_loc("Close")] = 90.0
    frame.iloc[0, frame.columns.get_loc("Low")] = 89.0
    frame.iloc[0, frame.columns.get_loc(feature_name("RSI_14"))] = 20.0
    frame.iloc[0, frame.columns.get_loc(feature_name("STOCHASTIC_K_14"))] = 15.0
    frame.iloc[0, frame.columns.get_loc(feature_name("STOCHASTIC_D_14_3"))] = 18.0
    frame.iloc[1, frame.columns.get_loc("Close")] = 92.0
    frame.iloc[1, frame.columns.get_loc("Low")] = 90.0
    frame.iloc[1, frame.columns.get_loc(feature_name("RSI_14"))] = 30.0
    frame.iloc[1, frame.columns.get_loc(feature_name("STOCHASTIC_K_14"))] = 25.0
    frame.iloc[1, frame.columns.get_loc(feature_name("STOCHASTIC_D_14_3"))] = 20.0

    result = KrakenAIDrivenV2Round1SignalEngine().generate_from_features(
        "RANGE_MEAN_REVERSION", frame
    )

    assert result.iloc[0][SETUP_CONDITION_COLUMN] == True
    assert result.iloc[0][TRANSITION_COLUMN] == "RANGE_REVERSION_ARMED"
    assert result.iloc[1][SIGNAL_CONDITION_COLUMN] == True
    assert result.iloc[1][ACTION_INTENT_COLUMN] == ENTER_NEXT_OPEN
    assert result.iloc[1][TARGET_ANCHOR_COLUMN] == pytest.approx(100.0)
    assert result.iloc[1][SETUP_LOW_COLUMN] == pytest.approx(89.0)


def test_breakout_emits_same_completed_bar_intent_with_causal_anchors():
    frame = feature_fixture(1)
    frame.iloc[0, frame.columns.get_loc("Open")] = 109.0
    frame.iloc[0, frame.columns.get_loc("Close")] = 110.0
    frame.iloc[0, frame.columns.get_loc("High")] = 111.0
    frame.iloc[0, frame.columns.get_loc("Low")] = 108.0
    frame.iloc[0, frame.columns.get_loc(feature_name("ATR_TO_PRIOR_MEDIAN_60"))] = 1.2
    frame.iloc[0, frame.columns.get_loc(feature_name("ADX_14_PRIOR"))] = 25.0
    frame.iloc[0, frame.columns.get_loc(feature_name("DONCHIAN_PRIOR_CLOSE_HIGH_55"))] = 105.0
    frame.iloc[0, frame.columns.get_loc(feature_name("VOLUME_RATIO"))] = 1.3
    frame.iloc[0, frame.columns.get_loc(feature_name("CLOSE_LOCATION"))] = 0.8
    frame.iloc[0, frame.columns.get_loc(feature_name("PRIOR_ATR_14"))] = 2.0

    result = KrakenAIDrivenV2Round1SignalEngine().generate_from_features(
        "VOLATILITY_BREAKOUT", frame
    )

    assert result.iloc[0][REGIME_CONDITION_COLUMN] == True
    assert result.iloc[0][SIGNAL_CONDITION_COLUMN] == True
    assert result.iloc[0][TRANSITION_COLUMN] == "VOLATILITY_BREAKOUT_CONFIRMATION"
    assert result.iloc[0][ACTION_INTENT_COLUMN] == ENTER_NEXT_OPEN
    assert result.iloc[0][SETUP_LOW_COLUMN] == pytest.approx(108.0)
    assert result.iloc[0][SIGNAL_ATR_COLUMN] == pytest.approx(2.0)
    assert result.iloc[0][SETUP_TIMESTAMP_COLUMN] == frame.index[0]


def test_missing_family_features_fail_closed_without_an_intent():
    frame = feature_fixture(3)
    result = KrakenAIDrivenV2Round1SignalEngine().generate_from_features(
        "VOLATILITY_BREAKOUT", frame
    )

    assert not result[FEATURES_AVAILABLE_COLUMN].any()
    assert not result[REGIME_CONDITION_COLUMN].any()
    assert not result[SIGNAL_CONDITION_COLUMN].any()
    assert set(result[ACTION_INTENT_COLUMN]) == {"NONE"}
    assert set(result[TRANSITION_COLUMN]) == {"FEATURES_UNAVAILABLE"}


def test_generate_all_returns_four_independent_family_paths_without_execution():
    source = continuous_frame()
    original = source.copy(deep=True)
    engine = KrakenAIDrivenV2Round1SignalEngine()
    results = engine.generate_all(source)

    assert tuple(results) == (
        "CAPITULATION_RECOVERY",
        "TREND_PULLBACK_CONTINUATION",
        "RANGE_MEAN_REVERSION",
        "VOLATILITY_BREAKOUT",
    )
    for family, result in results.items():
        assert set(result[FAMILY_COLUMN]) == {family}
        assert set(result[HYPOTHESIS_COLUMN]) == {
            dict(
                zip(
                    results,
                    HYPOTHESIS_ORDER,
                )
            )[family]
        }
        assert "quantity" not in result.columns
        assert "pnl" not in {column.lower() for column in result.columns}
    pd.testing.assert_frame_equal(source, original)


def test_signal_generation_is_prefix_causal_under_future_mutation():
    source = continuous_frame()
    cutoff = 250
    engine = KrakenAIDrivenV2Round1SignalEngine()
    prefix_results = engine.generate_all(source.iloc[:cutoff])
    changed = source.copy(deep=True)
    changed.iloc[cutoff:, changed.columns.get_loc("Close")] *= 1.8
    changed.iloc[cutoff:, changed.columns.get_loc("High")] *= 1.9
    changed.iloc[cutoff:, changed.columns.get_loc("Low")] *= 0.6
    full_results = engine.generate_all(changed)

    for family in prefix_results:
        pd.testing.assert_frame_equal(
            prefix_results[family],
            full_results[family].iloc[:cutoff],
            check_dtype=True,
            check_exact=True,
        )


def test_unknown_family_and_nonfeature_frame_are_rejected():
    engine = KrakenAIDrivenV2Round1SignalEngine()
    with pytest.raises(ValueError, match="Unknown Round 1 family"):
        engine.generate("UNKNOWN", continuous_frame())
    with pytest.raises(ValueError, match="feature columns"):
        engine.generate_from_features(
            "VOLATILITY_BREAKOUT", continuous_frame()
        )
