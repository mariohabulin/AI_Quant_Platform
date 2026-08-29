import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_features import FEATURE_COLUMNS
from kraken_ai_driven_v2_state_machine import (
    ACTION_INTENT_COLUMN,
    BEARISH_EXIT_COLUMN,
    CAPITULATION_COLUMN,
    CONFIRMATION_COLUMN,
    EVENT_TIMESTAMP_COLUMN,
    INTENT_ENTER_NEXT_OPEN,
    INTENT_EXIT_NEXT_OPEN,
    INTENT_NONE,
    LONG_AGE_COLUMN,
    PARAMETER_SET_COLUMN,
    PARAMETER_SET_ID,
    REFERENCE_PARAMETERS,
    SETUP_AGE_COLUMN,
    SETUP_LOW_COLUMN,
    STATE_AFTER_COLUMN,
    STATE_ARMED,
    STATE_BEFORE_COLUMN,
    STATE_FLAT,
    STATE_LONG,
    STRUCTURAL_FAILURE_COLUMN,
    TRANSITION_COLUMN,
    KrakenAIDrivenV2SignalState,
    KrakenAIDrivenV2StateMachine,
    KrakenAIDrivenV2StateParameters,
)


def base_rows(count=30):
    return [
        {"Open": 100.0, "High": 102.0, "Low": 98.0, "Close": 100.0, "Volume": 100.0}
        for _ in range(count)
    ]


def frame(rows):
    return pd.DataFrame(
        rows,
        index=pd.date_range("2026-01-01", periods=len(rows), freq="D", tz="UTC"),
    )[["Open", "High", "Low", "Close", "Volume"]]


def event_row(close=80.0, low=78.0, volume=300.0):
    return {"Open": 100.0, "High": 101.0, "Low": low, "Close": close, "Volume": volume}


def stabilization_row(low=79.0):
    return {"Open": 80.0, "High": 83.0, "Low": low, "Close": 82.0, "Volume": 90.0}


def confirmation_row():
    return {"Open": 82.0, "High": 88.0, "Low": 81.0, "Close": 87.0, "Volume": 130.0}


def reference_path():
    return frame(
        [
            *base_rows(),
            event_row(),
            stabilization_row(),
            confirmation_row(),
            {"Open": 87.0, "High": 90.0, "Low": 86.0, "Close": 89.0, "Volume": 100.0},
            {"Open": 89.0, "High": 90.0, "Low": 84.0, "Close": 85.0, "Volume": 200.0},
        ]
    )


def test_reference_parameter_set_is_exact_and_nonexecuting():
    configuration = KrakenAIDrivenV2StateMachine().configuration()

    assert configuration == {
        "parameter_set_id": PARAMETER_SET_ID,
        "decline_lookback_bars": 30,
        "volume_lookback_bars": 30,
        "atr_lookback_bars": 14,
        "minimum_drawdown_fraction": 0.15,
        "maximum_capitulation_return": -0.05,
        "minimum_capitulation_relative_volume": 2.0,
        "minimum_capitulation_range_expansion": 1.5,
        "maximum_capitulation_close_location": 0.35,
        "maximum_confirmation_delay_bars": 5,
        "minimum_confirmation_return": 0.0,
        "minimum_confirmation_relative_volume": 1.2,
        "minimum_confirmation_close_location": 0.60,
        "maximum_bearish_exit_return": -0.03,
        "minimum_bearish_exit_relative_volume": 1.5,
        "maximum_bearish_exit_close_location": 0.35,
        "observation_timing": "COMPLETED_DAILY_BAR_CLOSE",
        "state_role": "SIGNAL_STATE_NOT_EXECUTED_POSITION",
        "confirmation_price_rule": "CLOSE_STRICTLY_ABOVE_PREVIOUS_HIGH",
        "armed_priority": [
            "CAPITULATION_REARM",
            "STRUCTURAL_INVALIDATION",
            "EXPIRY",
            "CONFIRMATION",
            "WAIT",
        ],
        "long_priority": [
            "STRUCTURAL_AND_BEARISH_EXIT",
            "STRUCTURAL_EXIT",
            "BEARISH_VOLUME_EXIT",
            "HOLD",
        ],
        "entry_intent": INTENT_ENTER_NEXT_OPEN,
        "exit_intent": INTENT_EXIT_NEXT_OPEN,
        "fill_execution": False,
        "position_sizing": False,
        "performance_evaluation": False,
        "future_bar_access": False,
    }
    assert REFERENCE_PARAMETERS.feature_config.configuration()["future_bar_access"] is False


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("decline_lookback_bars", 0, "positive integer"),
        ("volume_lookback_bars", True, "positive integer"),
        ("atr_lookback_bars", 1.5, "positive integer"),
        ("maximum_confirmation_delay_bars", -1, "positive integer"),
        ("minimum_drawdown_fraction", -0.1, "between"),
        ("minimum_drawdown_fraction", 1.1, "between"),
        ("maximum_capitulation_return", 0.0, "strictly between"),
        ("maximum_bearish_exit_return", -1.0, "strictly between"),
        ("minimum_confirmation_return", -0.01, "nonnegative"),
        ("minimum_capitulation_relative_volume", 0.0, "positive"),
        ("minimum_capitulation_range_expansion", np.inf, "finite"),
        ("minimum_confirmation_relative_volume", True, "numeric"),
        ("minimum_bearish_exit_relative_volume", -1.0, "positive"),
        ("maximum_capitulation_close_location", 1.1, "between"),
        ("minimum_confirmation_close_location", -0.1, "between"),
        ("maximum_bearish_exit_close_location", np.nan, "finite"),
    ],
)
def test_state_parameters_fail_closed(field, value, error):
    values = REFERENCE_PARAMETERS.__dict__.copy()
    values[field] = value
    with pytest.raises((TypeError, ValueError), match=error):
        KrakenAIDrivenV2StateParameters(**values)


def test_state_machine_requires_exact_parameter_type():
    with pytest.raises(TypeError, match="StateParameters"):
        KrakenAIDrivenV2StateMachine({})


def test_reference_identity_cannot_hide_changed_valid_parameters():
    with pytest.raises(ValueError, match="Reference parameter-set values are immutable"):
        KrakenAIDrivenV2StateParameters(minimum_drawdown_fraction=0.20)

    alternative = KrakenAIDrivenV2StateParameters(
        parameter_set_id="synthetic-alternative-not-authorized-v1",
        minimum_drawdown_fraction=0.20,
    )
    assert alternative.parameter_set_id == "synthetic-alternative-not-authorized-v1"
    assert alternative.minimum_drawdown_fraction == pytest.approx(0.20)


def test_signal_state_invariants_are_strict():
    timestamp = pd.Timestamp("2026-01-01T00:00:00Z")

    assert KrakenAIDrivenV2SignalState.flat().name == STATE_FLAT
    with pytest.raises(ValueError, match="cannot retain"):
        KrakenAIDrivenV2SignalState(name=STATE_FLAT, setup_age=0)
    with pytest.raises(ValueError, match="ARMED"):
        KrakenAIDrivenV2SignalState(
            name=STATE_ARMED,
            setup_age=-1,
            event_timestamp=timestamp,
            setup_low=80.0,
        )
    with pytest.raises(ValueError, match="LONG"):
        KrakenAIDrivenV2SignalState(
            name=STATE_LONG,
            setup_age=0,
            long_age=0,
            event_timestamp=timestamp,
            setup_low=80.0,
        )


def test_reference_path_arms_confirms_holds_and_exits_without_fills():
    result = KrakenAIDrivenV2StateMachine().generate(reference_path())
    event = result.iloc[30]
    stabilization = result.iloc[31]
    confirmation = result.iloc[32]
    hold = result.iloc[33]
    exit_row = result.iloc[34]

    assert event[CAPITULATION_COLUMN] == True
    assert event[STATE_BEFORE_COLUMN] == STATE_FLAT
    assert event[STATE_AFTER_COLUMN] == STATE_ARMED
    assert event[TRANSITION_COLUMN] == "CAPITULATION_ARMED"
    assert event[ACTION_INTENT_COLUMN] == INTENT_NONE
    assert event[SETUP_AGE_COLUMN] == 0
    assert event[SETUP_LOW_COLUMN] == pytest.approx(78.0)

    assert stabilization[STATE_AFTER_COLUMN] == STATE_ARMED
    assert stabilization[TRANSITION_COLUMN] == "ARMED_WAIT"
    assert stabilization[SETUP_AGE_COLUMN] == 1

    assert confirmation[CONFIRMATION_COLUMN] == True
    assert confirmation[STATE_BEFORE_COLUMN] == STATE_ARMED
    assert confirmation[STATE_AFTER_COLUMN] == STATE_LONG
    assert confirmation[TRANSITION_COLUMN] == "CONFIRMATION_LONG"
    assert confirmation[ACTION_INTENT_COLUMN] == INTENT_ENTER_NEXT_OPEN
    assert confirmation[SETUP_AGE_COLUMN] == 2
    assert confirmation[LONG_AGE_COLUMN] == 0

    assert hold[STATE_AFTER_COLUMN] == STATE_LONG
    assert hold[TRANSITION_COLUMN] == "LONG_HOLD"
    assert hold[LONG_AGE_COLUMN] == 1
    assert hold[ACTION_INTENT_COLUMN] == INTENT_NONE

    assert exit_row[BEARISH_EXIT_COLUMN] == True
    assert exit_row[STRUCTURAL_FAILURE_COLUMN] == False
    assert exit_row[STATE_BEFORE_COLUMN] == STATE_LONG
    assert exit_row[STATE_AFTER_COLUMN] == STATE_FLAT
    assert exit_row[TRANSITION_COLUMN] == "LONG_BEARISH_VOLUME_EXIT"
    assert exit_row[ACTION_INTENT_COLUMN] == INTENT_EXIT_NEXT_OPEN
    assert exit_row[LONG_AGE_COLUMN] == 2
    assert set(result[PARAMETER_SET_COLUMN]) == {PARAMETER_SET_ID}


def test_event_bar_cannot_confirm_on_the_same_bar():
    result = KrakenAIDrivenV2StateMachine().generate(reference_path().iloc[:31])
    event = result.iloc[-1]

    assert event[CAPITULATION_COLUMN] == True
    assert event[STATE_AFTER_COLUMN] == STATE_ARMED
    assert event[ACTION_INTENT_COLUMN] == INTENT_NONE


def test_new_capitulation_rearms_before_structural_invalidation():
    rows = [
        *base_rows(),
        event_row(),
        {"Open": 80.0, "High": 81.0, "Low": 68.0, "Close": 70.0, "Volume": 400.0},
    ]
    result = KrakenAIDrivenV2StateMachine().generate(frame(rows))
    second_event = result.iloc[-1]

    assert second_event[CAPITULATION_COLUMN] == True
    assert second_event[STRUCTURAL_FAILURE_COLUMN] == True
    assert second_event[TRANSITION_COLUMN] == "CAPITULATION_REARMED"
    assert second_event[STATE_AFTER_COLUMN] == STATE_ARMED
    assert second_event[SETUP_AGE_COLUMN] == 0
    assert second_event[SETUP_LOW_COLUMN] == pytest.approx(68.0)
    assert second_event[EVENT_TIMESTAMP_COLUMN] == second_event.name


def test_armed_completed_close_below_prior_setup_low_invalidates():
    rows = [
        *base_rows(),
        event_row(),
        {"Open": 80.0, "High": 81.0, "Low": 76.0, "Close": 77.0, "Volume": 100.0},
    ]
    result = KrakenAIDrivenV2StateMachine().generate(frame(rows))
    invalidation = result.iloc[-1]

    assert invalidation[CAPITULATION_COLUMN] == False
    assert invalidation[STRUCTURAL_FAILURE_COLUMN] == True
    assert invalidation[TRANSITION_COLUMN] == "ARMED_STRUCTURAL_INVALIDATION"
    assert invalidation[STATE_AFTER_COLUMN] == STATE_FLAT
    assert invalidation[ACTION_INTENT_COLUMN] == INTENT_NONE


def wait_row():
    return {"Open": 80.0, "High": 82.0, "Low": 79.0, "Close": 80.0, "Volume": 100.0}


def late_confirmation_row():
    return {"Open": 80.0, "High": 87.0, "Low": 79.0, "Close": 86.0, "Volume": 130.0}


def test_confirmation_is_accepted_at_age_five():
    rows = [*base_rows(), event_row(), *[wait_row() for _ in range(4)], late_confirmation_row()]
    result = KrakenAIDrivenV2StateMachine().generate(frame(rows))
    confirmation = result.iloc[-1]

    assert confirmation[CONFIRMATION_COLUMN] == True
    assert confirmation[SETUP_AGE_COLUMN] == 5
    assert confirmation[TRANSITION_COLUMN] == "CONFIRMATION_LONG"
    assert confirmation[STATE_AFTER_COLUMN] == STATE_LONG


def test_confirmation_is_rejected_when_age_six_expires_first():
    rows = [*base_rows(), event_row(), *[wait_row() for _ in range(5)], late_confirmation_row()]
    result = KrakenAIDrivenV2StateMachine().generate(frame(rows))
    expired = result.iloc[-1]

    assert expired[CONFIRMATION_COLUMN] == True
    assert expired[SETUP_AGE_COLUMN] == 6
    assert expired[TRANSITION_COLUMN] == "ARMED_EXPIRED"
    assert expired[STATE_AFTER_COLUMN] == STATE_FLAT
    assert expired[ACTION_INTENT_COLUMN] == INTENT_NONE


def test_setup_low_includes_intrabar_undercut_that_closed_above_prior_low():
    rows = [
        *base_rows(),
        event_row(),
        stabilization_row(low=77.0),
        confirmation_row(),
    ]
    result = KrakenAIDrivenV2StateMachine().generate(frame(rows))

    assert result.iloc[31][STATE_AFTER_COLUMN] == STATE_ARMED
    assert result.iloc[31][STRUCTURAL_FAILURE_COLUMN] == False
    assert result.iloc[31][SETUP_LOW_COLUMN] == pytest.approx(77.0)
    assert result.iloc[32][STATE_AFTER_COLUMN] == STATE_LONG
    assert result.iloc[32][SETUP_LOW_COLUMN] == pytest.approx(77.0)


def test_combined_long_exit_records_both_conditions():
    rows = [
        *base_rows(),
        event_row(),
        stabilization_row(),
        confirmation_row(),
        {"Open": 87.0, "High": 88.0, "Low": 69.0, "Close": 70.0, "Volume": 250.0},
    ]
    result = KrakenAIDrivenV2StateMachine().generate(frame(rows))
    exit_row = result.iloc[-1]

    assert exit_row[STRUCTURAL_FAILURE_COLUMN] == True
    assert exit_row[BEARISH_EXIT_COLUMN] == True
    assert exit_row[TRANSITION_COLUMN] == "LONG_STRUCTURAL_AND_BEARISH_EXIT"
    assert exit_row[ACTION_INTENT_COLUMN] == INTENT_EXIT_NEXT_OPEN
    assert exit_row[STATE_AFTER_COLUMN] == STATE_FLAT


def test_structural_long_exit_does_not_require_bearish_volume():
    rows = [
        *base_rows(),
        event_row(),
        stabilization_row(),
        confirmation_row(),
        {"Open": 77.0, "High": 79.0, "Low": 74.0, "Close": 77.0, "Volume": 80.0},
    ]
    result = KrakenAIDrivenV2StateMachine().generate(frame(rows))
    exit_row = result.iloc[-1]

    assert exit_row[STRUCTURAL_FAILURE_COLUMN] == True
    assert exit_row[BEARISH_EXIT_COLUMN] == False
    assert exit_row[TRANSITION_COLUMN] == "LONG_STRUCTURAL_EXIT"
    assert exit_row[ACTION_INTENT_COLUMN] == INTENT_EXIT_NEXT_OPEN
    assert exit_row[STATE_AFTER_COLUMN] == STATE_FLAT


def test_unavailable_confirmation_and_exit_features_fail_closed():
    armed_rows = [
        *base_rows(),
        event_row(),
        {"Open": 80.0, "High": 80.0, "Low": 80.0, "Close": 80.0, "Volume": 100.0},
    ]
    armed_result = KrakenAIDrivenV2StateMachine().generate(frame(armed_rows))
    unavailable_armed = armed_result.iloc[-1]

    assert unavailable_armed[TRANSITION_COLUMN] == "ARMED_FEATURES_UNAVAILABLE"
    assert unavailable_armed[STATE_AFTER_COLUMN] == STATE_ARMED
    assert unavailable_armed[ACTION_INTENT_COLUMN] == INTENT_NONE

    long_rows = [
        *base_rows(),
        event_row(),
        stabilization_row(),
        confirmation_row(),
        {"Open": 87.0, "High": 87.0, "Low": 87.0, "Close": 87.0, "Volume": 100.0},
    ]
    long_result = KrakenAIDrivenV2StateMachine().generate(frame(long_rows))
    unavailable_long = long_result.iloc[-1]

    assert unavailable_long[TRANSITION_COLUMN] == "LONG_FEATURES_UNAVAILABLE"
    assert unavailable_long[STATE_AFTER_COLUMN] == STATE_LONG
    assert unavailable_long[ACTION_INTENT_COLUMN] == INTENT_NONE


def test_feature_to_state_path_is_prefix_causal_and_future_stable():
    data = reference_path()
    full = KrakenAIDrivenV2StateMachine().generate(data)
    prefix = KrakenAIDrivenV2StateMachine().generate(data.iloc[:33])
    pd.testing.assert_frame_equal(full.iloc[:33], prefix)

    changed_future = data.copy(deep=True)
    changed_future.loc[changed_future.index[33]:, ["Open", "High", "Low", "Close", "Volume"]] *= 20.0
    changed = KrakenAIDrivenV2StateMachine().generate(changed_future)
    pd.testing.assert_frame_equal(full.iloc[:33], changed.iloc[:33])


def test_state_generation_does_not_mutate_input_or_emit_performance_fields():
    data = reference_path()
    before = data.copy(deep=True)

    result = KrakenAIDrivenV2StateMachine().generate(data)

    pd.testing.assert_frame_equal(data, before)
    assert all(column in result.columns for column in FEATURE_COLUMNS)
    forbidden = {
        "fill_price",
        "position_size",
        "pnl",
        "equity",
        "trade_return",
        "optimizer_score",
    }
    assert forbidden.isdisjoint({str(column).lower() for column in result.columns})
    assert set(result[ACTION_INTENT_COLUMN]).issubset(
        {INTENT_NONE, INTENT_ENTER_NEXT_OPEN, INTENT_EXIT_NEXT_OPEN}
    )


def test_daily_gap_is_rejected_before_state_generation():
    data = reference_path().drop(reference_path().index[10])
    with pytest.raises(ValueError, match="continuous daily"):
        KrakenAIDrivenV2StateMachine().generate(data)
