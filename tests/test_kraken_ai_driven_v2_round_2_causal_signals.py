import os
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_hybrid_discovery_round_2 import (
    HYPOTHESIS_ORDER,
    ROUND_2_CONFIGURATION_LOCK,
)
from kraken_ai_driven_v2_round_2_causal_signals import (
    ACTION_INTENT_COLUMN,
    ENTER_NEXT_OPEN,
    FAMILY_COLUMN,
    FAMILY_ORDER,
    FEATURE_COLUMNS,
    FEATURES_AVAILABLE_COLUMN,
    HYPOTHESIS_COLUMN,
    MACD_NONPOSITIVE_SEEN_COLUMN,
    REGIME_CONDITION_COLUMN,
    RETEST_OBSERVED_COLUMN,
    SETUP_CONDITION_COLUMN,
    SETUP_LEVEL_COLUMN,
    SETUP_LOW_COLUMN,
    SETUP_TIMESTAMP_COLUMN,
    SIGNAL_ATR_COLUMN,
    SIGNAL_CONDITION_COLUMN,
    STATE_AFTER_COLUMN,
    STATE_AGE_COLUMN,
    STATE_BEFORE_COLUMN,
    TARGET_ANCHOR_COLUMN,
    TRANSITION_COLUMN,
    KrakenAIDrivenV2Round2CausalFeatureEngine,
    KrakenAIDrivenV2Round2SignalEngine,
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


def feature_fixture(rows=8):
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
    return f"KRAKEN_AI_V2_R2_{suffix}"


def set_ohlc(frame, row, *, open_price, high, low, close):
    frame.iloc[row, frame.columns.get_loc("Open")] = open_price
    frame.iloc[row, frame.columns.get_loc("High")] = high
    frame.iloc[row, frame.columns.get_loc("Low")] = low
    frame.iloc[row, frame.columns.get_loc("Close")] = close


def set_value(frame, row, suffix, value):
    frame.iloc[row, frame.columns.get_loc(feature_name(suffix))] = value


def set_capitulation_setup(frame, row=0):
    set_ohlc(frame, row, open_price=84.0, high=86.0, low=75.0, close=80.0)
    set_value(frame, row, "DRAWDOWN_FROM_PRIOR_HIGH_ATR", -6.5)
    set_value(frame, row, "ONE_BAR_PRICE_CHANGE_TO_PRIOR_ATR", -1.6)
    set_value(frame, row, "TR_TO_PRIOR_ATR", 1.8)
    set_value(frame, row, "VOLUME_RATIO", 1.6)
    set_value(frame, row, "CLOSE_LOCATION", 0.2)
    set_value(frame, row, "PRIOR_ATR_14", 2.0)


def set_capitulation_confirmation(frame, row, *, close, prior_high_2, low=78.0):
    set_ohlc(frame, row, open_price=close - 1.0, high=close + 1.0, low=low, close=close)
    set_value(frame, row, "VOLUME_RATIO", 0.9)
    set_value(frame, row, "CLOSE_LOCATION", 0.7)
    set_value(frame, row, "PRIOR_HIGH_2", prior_high_2)
    set_value(frame, row, "PRIOR_ATR_14", 2.2)


def set_breakout_setup(frame, row=0):
    set_ohlc(frame, row, open_price=109.0, high=111.0, low=108.0, close=110.0)
    set_value(frame, row, "ATR_TO_PRIOR_MEDIAN_60", 1.2)
    set_value(frame, row, "ADX_14_PRIOR", 25.0)
    set_value(frame, row, "DONCHIAN_PRIOR_CLOSE_HIGH_55", 105.0)
    set_value(frame, row, "VOLUME_RATIO", 1.3)
    set_value(frame, row, "CLOSE_LOCATION", 0.8)
    set_value(frame, row, "PRIOR_ATR_14", 2.0)


def set_trend_regime(frame, row):
    set_value(frame, row, "EMA_20_PRIOR", 100.0)
    set_value(frame, row, "EMA_50_PRIOR", 95.0)
    set_value(frame, row, "EMA_200_PRIOR", 90.0)
    set_value(frame, row, "EMA_50_SLOPE_20", 0.03)
    set_value(frame, row, "ADX_14_PRIOR", 25.0)
    set_value(frame, row, "PRIOR_ATR_14", 2.0)


def test_feature_engine_configuration_is_round_2_and_nonexecuting():
    configuration = KrakenAIDrivenV2Round2CausalFeatureEngine().configuration()

    assert configuration["component_id"] == (
        "kraken-ai-v2-round-2-causal-features-v1"
    )
    assert configuration["round_2_configuration_sha256"] == (
        ROUND_2_CONFIGURATION_LOCK.sha256
    )
    assert configuration["completed_daily_bar_only"] is True
    assert configuration["rolling_baseline_current_bar_included"] is False
    assert configuration["macd_decision_value"] == "CURRENT_COMPLETED_BAR"
    assert configuration["gap_policy"] == "SPLIT_BEFORE_GENERATION"
    assert configuration["signal_emitted"] is False
    assert configuration["execution_implemented"] is False
    assert configuration["dataset_opened"] is False


def test_feature_engine_preserves_input_and_generates_exact_prior_measurements():
    source = continuous_frame()
    original = source.copy(deep=True)
    result = KrakenAIDrivenV2Round2CausalFeatureEngine().generate(source)
    position = 250
    prior_atr = result.iloc[position][feature_name("PRIOR_ATR_14")]

    pd.testing.assert_frame_equal(source, original)
    assert result.iloc[position][feature_name("PREVIOUS_CLOSE")] == pytest.approx(
        source["Close"].iloc[position - 1]
    )
    assert result.iloc[position][feature_name("PRIOR_CLOSE_MAX_40")] == pytest.approx(
        source["Close"].iloc[position - 40 : position].max()
    )
    assert result.iloc[position][feature_name("PRIOR_HIGH_2")] == pytest.approx(
        source["High"].iloc[position - 2 : position].max()
    )
    assert result.iloc[position][feature_name("PRIOR_HIGH_3")] == pytest.approx(
        source["High"].iloc[position - 3 : position].max()
    )
    expected_drawdown_atr = (
        source["Close"].iloc[position]
        - source["Close"].iloc[position - 40 : position].max()
    ) / prior_atr
    expected_change_atr = (
        source["Close"].iloc[position] - source["Close"].iloc[position - 1]
    ) / prior_atr
    assert result.iloc[position][
        feature_name("DRAWDOWN_FROM_PRIOR_HIGH_ATR")
    ] == pytest.approx(expected_drawdown_atr)
    assert result.iloc[position][
        feature_name("ONE_BAR_PRICE_CHANGE_TO_PRIOR_ATR")
    ] == pytest.approx(expected_change_atr)
    assert result.iloc[position][feature_name("PRIOR_VOLUME_MEDIAN_30")] == pytest.approx(
        source["Volume"].iloc[position - 30 : position].median()
    )
    assert result.iloc[position][
        feature_name("DONCHIAN_PRIOR_CLOSE_HIGH_55")
    ] == pytest.approx(source["Close"].iloc[position - 55 : position].max())


def test_macd_histogram_uses_current_completed_close_and_prior_is_shifted():
    source = continuous_frame()
    result = KrakenAIDrivenV2Round2CausalFeatureEngine().generate(source)
    fast = source["Close"].ewm(span=12, adjust=False, min_periods=12).mean()
    slow = source["Close"].ewm(span=26, adjust=False, min_periods=26).mean()
    line = fast - slow
    signal = line.ewm(span=9, adjust=False, min_periods=9).mean()
    histogram = line - signal

    assert result.iloc[-1][feature_name("MACD_HISTOGRAM")] == pytest.approx(
        histogram.iloc[-1]
    )
    assert result.iloc[-1][feature_name("MACD_HISTOGRAM_PRIOR")] == pytest.approx(
        histogram.iloc[-2]
    )


def test_current_bar_mutation_cannot_change_its_prior_only_baselines():
    source = continuous_frame()
    changed = source.copy(deep=True)
    changed.iloc[-1, changed.columns.get_loc("Open")] *= 1.2
    changed.iloc[-1, changed.columns.get_loc("High")] *= 1.5
    changed.iloc[-1, changed.columns.get_loc("Low")] *= 0.8
    changed.iloc[-1, changed.columns.get_loc("Close")] *= 1.3
    changed.iloc[-1, changed.columns.get_loc("Volume")] *= 10.0
    first = KrakenAIDrivenV2Round2CausalFeatureEngine().generate(source)
    second = KrakenAIDrivenV2Round2CausalFeatureEngine().generate(changed)

    for suffix in (
        "PREVIOUS_CLOSE",
        "PRIOR_CLOSE_MAX_40",
        "PRIOR_HIGH_2",
        "PRIOR_HIGH_3",
        "PRIOR_VOLUME_MEDIAN_30",
        "PRIOR_ATR_14",
        "EMA_20_PRIOR",
        "EMA_50_PRIOR",
        "EMA_200_PRIOR",
        "ADX_14_PRIOR",
        "MACD_HISTOGRAM_PRIOR",
        "DONCHIAN_PRIOR_CLOSE_HIGH_55",
    ):
        assert first.iloc[-1][feature_name(suffix)] == pytest.approx(
            second.iloc[-1][feature_name(suffix)]
        )


def test_feature_generation_is_prefix_causal_under_future_mutation():
    source = continuous_frame()
    cutoff = 250
    prefix = KrakenAIDrivenV2Round2CausalFeatureEngine().generate(
        source.iloc[:cutoff]
    )
    changed = source.copy(deep=True)
    changed.iloc[cutoff:, changed.columns.get_loc("Close")] *= 1.8
    changed.iloc[cutoff:, changed.columns.get_loc("High")] *= 1.9
    changed.iloc[cutoff:, changed.columns.get_loc("Low")] *= 0.6
    full = KrakenAIDrivenV2Round2CausalFeatureEngine().generate(changed)

    pd.testing.assert_frame_equal(prefix, full.iloc[:cutoff], check_exact=True)


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
        KrakenAIDrivenV2Round2CausalFeatureEngine().generate(
            mutator(continuous_frame())
        )


def test_feature_engine_rejects_crossing_a_recorded_gap():
    source = continuous_frame()
    source = source.drop(source.index[100])

    with pytest.raises(ValueError, match="continuous daily"):
        KrakenAIDrivenV2Round2CausalFeatureEngine().generate(source)


def test_capitulation_requires_two_post_setup_bars_before_confirmation():
    frame = feature_fixture(3)
    set_capitulation_setup(frame)
    set_capitulation_confirmation(frame, 1, close=83.0, prior_high_2=82.0)
    set_capitulation_confirmation(frame, 2, close=86.0, prior_high_2=85.0)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "CAPITULATION_RECOVERY", frame
    )

    assert result.iloc[0][TRANSITION_COLUMN] == "CAPITULATION_ARMED"
    assert result.iloc[1][SIGNAL_CONDITION_COLUMN] == False
    assert result.iloc[1][TRANSITION_COLUMN] == "CAPITULATION_STABILIZING"
    assert result.iloc[1][STATE_AGE_COLUMN] == 1
    assert result.iloc[2][SIGNAL_CONDITION_COLUMN] == True
    assert result.iloc[2][TRANSITION_COLUMN] == "CAPITULATION_CONFIRMATION"
    assert result.iloc[2][ACTION_INTENT_COLUMN] == ENTER_NEXT_OPEN
    assert result.iloc[2][SETUP_LOW_COLUMN] == pytest.approx(75.0)
    assert result.iloc[2][SIGNAL_ATR_COLUMN] == pytest.approx(2.2)
    assert np.isnan(result.iloc[2][TARGET_ANCHOR_COLUMN])
    assert result.iloc[2][STATE_AFTER_COLUMN] == "FLAT"


def test_capitulation_confirmation_pattern_without_setup_never_signals():
    frame = feature_fixture(1)
    set_capitulation_confirmation(frame, 0, close=103.0, prior_high_2=102.0)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "CAPITULATION_RECOVERY", frame
    )

    assert result.iloc[0][STATE_BEFORE_COLUMN] == "FLAT"
    assert result.iloc[0][SIGNAL_CONDITION_COLUMN] == False
    assert result.iloc[0][ACTION_INTENT_COLUMN] == "NONE"


def test_capitulation_expires_after_seven_following_bars():
    frame = feature_fixture(9)
    set_capitulation_setup(frame)
    for row in range(1, 9):
        set_capitulation_confirmation(frame, row, close=80.0, prior_high_2=90.0)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "CAPITULATION_RECOVERY", frame
    )

    assert result.iloc[7][STATE_AFTER_COLUMN] == "ARMED"
    assert result.iloc[8][TRANSITION_COLUMN] == "CAPITULATION_EXPIRED"
    assert result.iloc[8][STATE_AFTER_COLUMN] == "FLAT"
    assert not result[SIGNAL_CONDITION_COLUMN].any()


def test_capitulation_close_below_running_setup_low_invalidates():
    frame = feature_fixture(3)
    set_capitulation_setup(frame)
    set_capitulation_confirmation(frame, 1, close=78.0, prior_high_2=90.0, low=74.0)
    set_capitulation_confirmation(frame, 2, close=73.0, prior_high_2=90.0, low=72.0)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "CAPITULATION_RECOVERY", frame
    )

    assert result.iloc[1][SETUP_LOW_COLUMN] == pytest.approx(74.0)
    assert result.iloc[2][TRANSITION_COLUMN] == (
        "CAPITULATION_STRUCTURAL_INVALIDATION"
    )
    assert result.iloc[2][ACTION_INTENT_COLUMN] == "NONE"


def test_breakout_requires_later_retest_then_later_confirmation():
    frame = feature_fixture(3)
    set_breakout_setup(frame)
    set_ohlc(frame, 1, open_price=107.0, high=109.0, low=105.2, close=105.5)
    set_value(frame, 1, "PRIOR_ATR_14", 2.0)
    set_value(frame, 1, "PRIOR_HIGH_1", 110.0)
    set_value(frame, 1, "VOLUME_RATIO", 0.9)
    set_ohlc(frame, 2, open_price=109.0, high=113.0, low=107.0, close=112.0)
    set_value(frame, 2, "PRIOR_ATR_14", 2.2)
    set_value(frame, 2, "PRIOR_HIGH_1", 111.0)
    set_value(frame, 2, "VOLUME_RATIO", 1.1)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "VOLATILITY_BREAKOUT", frame
    )

    assert result.iloc[0][TRANSITION_COLUMN] == "BREAKOUT_SETUP_ARMED"
    assert result.iloc[0][ACTION_INTENT_COLUMN] == "NONE"
    assert result.iloc[0][SETUP_LEVEL_COLUMN] == pytest.approx(105.0)
    assert result.iloc[1][TRANSITION_COLUMN] == "BREAKOUT_RETEST_OBSERVED"
    assert result.iloc[1][RETEST_OBSERVED_COLUMN] == True
    assert result.iloc[1][ACTION_INTENT_COLUMN] == "NONE"
    assert result.iloc[2][TRANSITION_COLUMN] == "BREAKOUT_RETEST_CONFIRMATION"
    assert result.iloc[2][ACTION_INTENT_COLUMN] == ENTER_NEXT_OPEN
    assert result.iloc[2][SETUP_LOW_COLUMN] == pytest.approx(105.2)
    assert result.iloc[2][SIGNAL_ATR_COLUMN] == pytest.approx(2.2)


def test_breakout_retest_bar_cannot_also_confirm():
    frame = feature_fixture(2)
    set_breakout_setup(frame)
    set_ohlc(frame, 1, open_price=106.0, high=113.0, low=105.2, close=112.0)
    set_value(frame, 1, "PRIOR_ATR_14", 2.0)
    set_value(frame, 1, "PRIOR_HIGH_1", 111.0)
    set_value(frame, 1, "VOLUME_RATIO", 1.2)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "VOLATILITY_BREAKOUT", frame
    )

    assert result.iloc[1][TRANSITION_COLUMN] == "BREAKOUT_RETEST_OBSERVED"
    assert result.iloc[1][SIGNAL_CONDITION_COLUMN] == False
    assert result.iloc[1][ACTION_INTENT_COLUMN] == "NONE"


def test_breakout_close_below_frozen_level_invalidates():
    frame = feature_fixture(2)
    set_breakout_setup(frame)
    set_ohlc(frame, 1, open_price=105.0, high=106.0, low=103.0, close=104.0)
    set_value(frame, 1, "PRIOR_ATR_14", 2.0)
    set_value(frame, 1, "PRIOR_HIGH_1", 110.0)
    set_value(frame, 1, "VOLUME_RATIO", 1.0)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "VOLATILITY_BREAKOUT", frame
    )

    assert result.iloc[1][TRANSITION_COLUMN] == "BREAKOUT_LEVEL_FAILED"
    assert result.iloc[1][STATE_AFTER_COLUMN] == "FLAT"
    assert result.iloc[1][ACTION_INTENT_COLUMN] == "NONE"


def test_breakout_expires_after_five_post_setup_bars():
    frame = feature_fixture(7)
    set_breakout_setup(frame)
    for row in range(1, 7):
        set_ohlc(frame, row, open_price=108.0, high=110.0, low=106.0, close=108.0)
        set_value(frame, row, "PRIOR_ATR_14", 2.0)
        set_value(frame, row, "PRIOR_HIGH_1", 110.0)
        set_value(frame, row, "VOLUME_RATIO", 0.9)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "VOLATILITY_BREAKOUT", frame
    )

    assert result.iloc[5][STATE_AFTER_COLUMN] == "BREAKOUT_ARMED"
    assert result.iloc[6][TRANSITION_COLUMN] == "BREAKOUT_RETEST_EXPIRED"
    assert result.iloc[6][STATE_AFTER_COLUMN] == "FLAT"


def test_trend_requires_multibar_pullback_and_real_macd_zero_cross():
    frame = feature_fixture(3)
    for row in range(3):
        set_trend_regime(frame, row)
    set_ohlc(frame, 0, open_price=101.0, high=102.0, low=99.5, close=101.0)
    set_value(frame, 0, "VOLUME_RATIO", 0.8)
    set_value(frame, 0, "MACD_HISTOGRAM", -0.2)
    set_value(frame, 0, "MACD_HISTOGRAM_PRIOR", 0.1)
    set_value(frame, 0, "PRIOR_HIGH_3", 103.0)
    set_ohlc(frame, 1, open_price=100.5, high=102.0, low=99.3, close=101.0)
    set_value(frame, 1, "VOLUME_RATIO", 0.9)
    set_value(frame, 1, "MACD_HISTOGRAM", -0.1)
    set_value(frame, 1, "MACD_HISTOGRAM_PRIOR", -0.2)
    set_value(frame, 1, "PRIOR_HIGH_3", 103.0)
    set_ohlc(frame, 2, open_price=102.0, high=105.0, low=100.0, close=104.0)
    set_value(frame, 2, "VOLUME_RATIO", 1.1)
    set_value(frame, 2, "MACD_HISTOGRAM", 0.2)
    set_value(frame, 2, "MACD_HISTOGRAM_PRIOR", -0.1)
    set_value(frame, 2, "PRIOR_HIGH_3", 103.0)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "TREND_PULLBACK_CONTINUATION", frame
    )

    assert result.iloc[0][TRANSITION_COLUMN] == "TREND_PULLBACK_ARMED"
    assert result.iloc[0][MACD_NONPOSITIVE_SEEN_COLUMN] == True
    assert result.iloc[1][TRANSITION_COLUMN] == "TREND_PULLBACK_BUILDING"
    assert result.iloc[1][STATE_AGE_COLUMN] == 1
    assert result.iloc[2][SIGNAL_CONDITION_COLUMN] == True
    assert result.iloc[2][TRANSITION_COLUMN] == "TREND_MACD_RESUMPTION_CONFIRMATION"
    assert result.iloc[2][ACTION_INTENT_COLUMN] == ENTER_NEXT_OPEN
    assert result.iloc[2][SETUP_LOW_COLUMN] == pytest.approx(99.3)


def test_trend_macd_cross_before_minimum_age_cannot_confirm_later_without_new_cross():
    frame = feature_fixture(3)
    for row in range(3):
        set_trend_regime(frame, row)
        set_value(frame, row, "PRIOR_HIGH_3", 103.0)
    set_ohlc(frame, 0, open_price=101.0, high=102.0, low=99.5, close=101.0)
    set_value(frame, 0, "VOLUME_RATIO", 0.8)
    set_value(frame, 0, "MACD_HISTOGRAM", -0.2)
    set_value(frame, 0, "MACD_HISTOGRAM_PRIOR", 0.1)
    set_ohlc(frame, 1, open_price=102.0, high=105.0, low=100.0, close=104.0)
    set_value(frame, 1, "VOLUME_RATIO", 1.1)
    set_value(frame, 1, "MACD_HISTOGRAM", 0.2)
    set_value(frame, 1, "MACD_HISTOGRAM_PRIOR", -0.2)
    set_ohlc(frame, 2, open_price=103.0, high=106.0, low=101.0, close=105.0)
    set_value(frame, 2, "VOLUME_RATIO", 1.1)
    set_value(frame, 2, "MACD_HISTOGRAM", 0.3)
    set_value(frame, 2, "MACD_HISTOGRAM_PRIOR", 0.2)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "TREND_PULLBACK_CONTINUATION", frame
    )

    assert result.iloc[1][SIGNAL_CONDITION_COLUMN] == False
    assert result.iloc[2][SIGNAL_CONDITION_COLUMN] == False
    assert set(result[ACTION_INTENT_COLUMN]) == {"NONE"}


def test_trend_expires_after_five_post_setup_bars():
    frame = feature_fixture(7)
    for row in range(7):
        set_trend_regime(frame, row)
        set_value(frame, row, "PRIOR_HIGH_3", 110.0)
        set_value(frame, row, "VOLUME_RATIO", 0.9)
        set_value(frame, row, "MACD_HISTOGRAM", -0.1)
        set_value(frame, row, "MACD_HISTOGRAM_PRIOR", -0.1)
        set_ohlc(frame, row, open_price=100.0, high=102.0, low=99.5, close=101.0)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "TREND_PULLBACK_CONTINUATION", frame
    )

    assert result.iloc[5][STATE_AFTER_COLUMN] == "ARMED"
    assert result.iloc[6][TRANSITION_COLUMN] == "TREND_PULLBACK_EXPIRED"
    assert result.iloc[6][STATE_AFTER_COLUMN] == "FLAT"


def test_trend_close_below_ema50_invalidates_pullback():
    frame = feature_fixture(2)
    for row in range(2):
        set_trend_regime(frame, row)
        set_value(frame, row, "PRIOR_HIGH_3", 110.0)
        set_value(frame, row, "VOLUME_RATIO", 0.9)
        set_value(frame, row, "MACD_HISTOGRAM", -0.1)
        set_value(frame, row, "MACD_HISTOGRAM_PRIOR", -0.1)
    set_ohlc(frame, 0, open_price=100.0, high=102.0, low=99.5, close=101.0)
    set_ohlc(frame, 1, open_price=96.0, high=97.0, low=93.0, close=94.0)

    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "TREND_PULLBACK_CONTINUATION", frame
    )

    assert result.iloc[1][TRANSITION_COLUMN] == (
        "TREND_PULLBACK_STRUCTURAL_INVALIDATION"
    )
    assert result.iloc[1][STATE_AFTER_COLUMN] == "FLAT"


def test_missing_features_fail_closed_without_an_intent():
    frame = feature_fixture(3)
    result = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "VOLATILITY_BREAKOUT", frame
    )

    assert not result[FEATURES_AVAILABLE_COLUMN].any()
    assert not result[REGIME_CONDITION_COLUMN].any()
    assert not result[SIGNAL_CONDITION_COLUMN].any()
    assert set(result[ACTION_INTENT_COLUMN]) == {"NONE"}
    assert set(result[TRANSITION_COLUMN]) == {"FEATURES_UNAVAILABLE"}


def test_generate_all_returns_three_independent_paths_without_execution():
    source = continuous_frame()
    original = source.copy(deep=True)
    results = KrakenAIDrivenV2Round2SignalEngine().generate_all(source)

    assert tuple(results) == FAMILY_ORDER
    assert FAMILY_ORDER == (
        "CAPITULATION_RECOVERY",
        "VOLATILITY_BREAKOUT",
        "TREND_PULLBACK_CONTINUATION",
    )
    for family, result in results.items():
        assert set(result[FAMILY_COLUMN]) == {family}
        assert set(result[HYPOTHESIS_COLUMN]) == {
            dict(zip(FAMILY_ORDER, HYPOTHESIS_ORDER))[family]
        }
        assert "quantity" not in result.columns
        assert "pnl" not in {column.lower() for column in result.columns}
    pd.testing.assert_frame_equal(source, original)


def test_signal_generation_is_prefix_causal_under_future_mutation():
    source = continuous_frame()
    cutoff = 250
    engine = KrakenAIDrivenV2Round2SignalEngine()
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
            check_exact=True,
        )


def test_unknown_family_and_nonfeature_frame_are_rejected():
    engine = KrakenAIDrivenV2Round2SignalEngine()
    with pytest.raises(ValueError, match="Unknown Round 2 family"):
        engine.generate("UNKNOWN", continuous_frame())
    with pytest.raises(ValueError, match="feature columns"):
        engine.generate_from_features("VOLATILITY_BREAKOUT", continuous_frame())
