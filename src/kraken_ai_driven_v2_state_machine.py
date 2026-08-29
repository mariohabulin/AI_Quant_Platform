"""Deterministic causal signal state for Kraken AI-driven v2 research."""

from dataclasses import asdict, dataclass
import math
from numbers import Real

import numpy as np
import pandas as pd

try:
    from kraken_ai_driven_v2_features import (
        FEATURE_COLUMNS,
        KrakenAIDrivenV2FeatureConfig,
        KrakenAIDrivenV2FeatureEngine,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_features import (
        FEATURE_COLUMNS,
        KrakenAIDrivenV2FeatureConfig,
        KrakenAIDrivenV2FeatureEngine,
    )


STATE_FLAT = "FLAT"
STATE_ARMED = "ARMED"
STATE_LONG = "LONG"
VALID_STATES = (STATE_FLAT, STATE_ARMED, STATE_LONG)
INTENT_NONE = "NONE"
INTENT_ENTER_NEXT_OPEN = "ENTER_NEXT_OPEN"
INTENT_EXIT_NEXT_OPEN = "EXIT_NEXT_OPEN"
PARAMETER_SET_ID = "kraken-ai-v2-ccvr-reference-a-v1"

CAPITULATION_COLUMN = "KRAKEN_AI_V2_CAPITULATION_CONDITION"
CONFIRMATION_COLUMN = "KRAKEN_AI_V2_CONFIRMATION_CONDITION"
BEARISH_EXIT_COLUMN = "KRAKEN_AI_V2_BEARISH_VOLUME_EXIT_CONDITION"
STATE_BEFORE_COLUMN = "KRAKEN_AI_V2_STATE_BEFORE"
STATE_AFTER_COLUMN = "KRAKEN_AI_V2_STATE_AFTER"
TRANSITION_COLUMN = "KRAKEN_AI_V2_TRANSITION"
ACTION_INTENT_COLUMN = "KRAKEN_AI_V2_ACTION_INTENT"
STRUCTURAL_FAILURE_COLUMN = "KRAKEN_AI_V2_STRUCTURAL_FAILURE"
SETUP_AGE_COLUMN = "KRAKEN_AI_V2_SETUP_AGE"
LONG_AGE_COLUMN = "KRAKEN_AI_V2_LONG_AGE"
EVENT_TIMESTAMP_COLUMN = "KRAKEN_AI_V2_EVENT_TIMESTAMP"
SETUP_LOW_COLUMN = "KRAKEN_AI_V2_SETUP_LOW"
PARAMETER_SET_COLUMN = "KRAKEN_AI_V2_PARAMETER_SET_ID"
STATE_COLUMNS = (
    CAPITULATION_COLUMN,
    CONFIRMATION_COLUMN,
    BEARISH_EXIT_COLUMN,
    STATE_BEFORE_COLUMN,
    STATE_AFTER_COLUMN,
    TRANSITION_COLUMN,
    ACTION_INTENT_COLUMN,
    STRUCTURAL_FAILURE_COLUMN,
    SETUP_AGE_COLUMN,
    LONG_AGE_COLUMN,
    EVENT_TIMESTAMP_COLUMN,
    SETUP_LOW_COLUMN,
    PARAMETER_SET_COLUMN,
)


def _finite_number(value, name):
    if not isinstance(value, Real) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric.")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def _positive_number(value, name):
    value = _finite_number(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return value


def _fraction(value, name, *, minimum=0.0, maximum=1.0):
    value = _finite_number(value, name)
    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return value


@dataclass(frozen=True)
class KrakenAIDrivenV2StateParameters:
    """Frozen reference-A state thresholds; no performance claim is implied."""

    parameter_set_id: str = PARAMETER_SET_ID
    decline_lookback_bars: int = 30
    volume_lookback_bars: int = 30
    atr_lookback_bars: int = 14
    minimum_drawdown_fraction: float = 0.15
    maximum_capitulation_return: float = -0.05
    minimum_capitulation_relative_volume: float = 2.0
    minimum_capitulation_range_expansion: float = 1.5
    maximum_capitulation_close_location: float = 0.35
    maximum_confirmation_delay_bars: int = 5
    minimum_confirmation_return: float = 0.0
    minimum_confirmation_relative_volume: float = 1.2
    minimum_confirmation_close_location: float = 0.60
    maximum_bearish_exit_return: float = -0.03
    minimum_bearish_exit_relative_volume: float = 1.5
    maximum_bearish_exit_close_location: float = 0.35

    def __post_init__(self):
        if not isinstance(self.parameter_set_id, str) or not self.parameter_set_id.strip():
            raise ValueError("Parameter-set ID must be a nonempty string.")
        for value, name in (
            (self.decline_lookback_bars, "Decline lookback"),
            (self.volume_lookback_bars, "Volume lookback"),
            (self.atr_lookback_bars, "ATR lookback"),
            (self.maximum_confirmation_delay_bars, "Confirmation delay"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")

        _fraction(
            self.minimum_drawdown_fraction,
            "Minimum drawdown fraction",
            minimum=0.0,
            maximum=1.0,
        )
        for value, name in (
            (self.maximum_capitulation_return, "Maximum capitulation return"),
            (self.maximum_bearish_exit_return, "Maximum bearish exit return"),
        ):
            value = _finite_number(value, name)
            if not -1.0 < value < 0.0:
                raise ValueError(f"{name} must be strictly between -1 and 0.")
        confirmation_return = _finite_number(
            self.minimum_confirmation_return, "Minimum confirmation return"
        )
        if confirmation_return < 0.0:
            raise ValueError("Minimum confirmation return must be nonnegative.")
        for value, name in (
            (
                self.minimum_capitulation_relative_volume,
                "Minimum capitulation relative volume",
            ),
            (
                self.minimum_capitulation_range_expansion,
                "Minimum capitulation range expansion",
            ),
            (
                self.minimum_confirmation_relative_volume,
                "Minimum confirmation relative volume",
            ),
            (
                self.minimum_bearish_exit_relative_volume,
                "Minimum bearish exit relative volume",
            ),
        ):
            _positive_number(value, name)
        for value, name in (
            (
                self.maximum_capitulation_close_location,
                "Maximum capitulation close location",
            ),
            (
                self.minimum_confirmation_close_location,
                "Minimum confirmation close location",
            ),
            (
                self.maximum_bearish_exit_close_location,
                "Maximum bearish exit close location",
            ),
        ):
            _fraction(value, name)

        if self.parameter_set_id == PARAMETER_SET_ID:
            expected = {
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
            }
            observed = asdict(self)
            observed.pop("parameter_set_id")
            if observed != expected:
                raise ValueError(
                    "Reference parameter-set values are immutable; use a new "
                    "parameter-set ID for another pre-registered hypothesis."
                )

    @property
    def feature_config(self):
        return KrakenAIDrivenV2FeatureConfig(
            decline_lookback_bars=self.decline_lookback_bars,
            volume_lookback_bars=self.volume_lookback_bars,
            atr_lookback_bars=self.atr_lookback_bars,
        )

    def configuration(self):
        return {
            **asdict(self),
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


REFERENCE_PARAMETERS = KrakenAIDrivenV2StateParameters()


@dataclass(frozen=True)
class KrakenAIDrivenV2SignalState:
    """Minimal completed-bar state; it is not an executed brokerage position."""

    name: str = STATE_FLAT
    setup_age: int = -1
    long_age: int = -1
    event_timestamp: pd.Timestamp | None = None
    setup_low: float | None = None

    def __post_init__(self):
        if self.name not in VALID_STATES:
            raise ValueError("AI-driven v2 signal state is invalid.")
        for value, label in (
            (self.setup_age, "Setup age"),
            (self.long_age, "Long age"),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{label} must be an integer.")

        if self.name == STATE_FLAT:
            if (
                self.setup_age != -1
                or self.long_age != -1
                or self.event_timestamp is not None
                or self.setup_low is not None
            ):
                raise ValueError("FLAT state cannot retain an active setup.")
            return

        if not isinstance(self.event_timestamp, pd.Timestamp):
            raise TypeError("Active signal state requires a pandas Timestamp.")
        if self.event_timestamp.tzinfo is None:
            raise ValueError("Active signal event timestamp must be timezone-aware.")
        _positive_number(self.setup_low, "Active setup low")

        if self.name == STATE_ARMED:
            if self.setup_age < 0 or self.long_age != -1:
                raise ValueError("ARMED state requires setup age and no long age.")
        if self.name == STATE_LONG:
            if self.setup_age != -1 or self.long_age < 0:
                raise ValueError("LONG state requires long age and no setup age.")

    @classmethod
    def flat(cls):
        return cls()


class KrakenAIDrivenV2StateMachine:
    """Generate deterministic signal states from causal feature rows."""

    def __init__(self, parameters=REFERENCE_PARAMETERS):
        if not isinstance(parameters, KrakenAIDrivenV2StateParameters):
            raise TypeError(
                "State machine requires KrakenAIDrivenV2StateParameters."
            )
        self.parameters = parameters
        self.feature_engine = KrakenAIDrivenV2FeatureEngine(
            parameters.feature_config
        )

    def configuration(self):
        return self.parameters.configuration()

    @staticmethod
    def initial_state():
        return KrakenAIDrivenV2SignalState.flat()

    def conditions(self, data):
        result = self.feature_engine.generate(data)
        parameters = self.parameters
        close = pd.to_numeric(result["Close"], errors="coerce")
        previous_high = pd.to_numeric(result["High"], errors="coerce").shift(1)
        close_return = pd.to_numeric(result[FEATURE_COLUMNS[1]], errors="coerce")
        drawdown = pd.to_numeric(result[FEATURE_COLUMNS[3]], errors="coerce")
        relative_volume = pd.to_numeric(result[FEATURE_COLUMNS[5]], errors="coerce")
        range_expansion = pd.to_numeric(result[FEATURE_COLUMNS[8]], errors="coerce")
        close_location = pd.to_numeric(result[FEATURE_COLUMNS[9]], errors="coerce")

        capitulation_inputs = pd.concat(
            (drawdown, close_return, relative_volume, range_expansion, close_location),
            axis=1,
        )
        capitulation_available = capitulation_inputs.notna().all(axis=1) & np.isfinite(
            capitulation_inputs.to_numpy(dtype=float)
        ).all(axis=1)
        capitulation = (
            capitulation_available
            & drawdown.ge(parameters.minimum_drawdown_fraction)
            & close_return.le(parameters.maximum_capitulation_return)
            & relative_volume.ge(parameters.minimum_capitulation_relative_volume)
            & range_expansion.ge(parameters.minimum_capitulation_range_expansion)
            & close_location.le(parameters.maximum_capitulation_close_location)
        )

        confirmation_inputs = pd.concat(
            (close, previous_high, close_return, relative_volume, close_location),
            axis=1,
        )
        confirmation_available = confirmation_inputs.notna().all(axis=1) & np.isfinite(
            confirmation_inputs.to_numpy(dtype=float)
        ).all(axis=1)
        confirmation = (
            confirmation_available
            & close_return.gt(parameters.minimum_confirmation_return)
            & relative_volume.ge(parameters.minimum_confirmation_relative_volume)
            & close_location.ge(parameters.minimum_confirmation_close_location)
            & close.gt(previous_high)
        )

        bearish_inputs = pd.concat(
            (close_return, relative_volume, close_location), axis=1
        )
        bearish_available = bearish_inputs.notna().all(axis=1) & np.isfinite(
            bearish_inputs.to_numpy(dtype=float)
        ).all(axis=1)
        bearish_exit = (
            bearish_available
            & close_return.le(parameters.maximum_bearish_exit_return)
            & relative_volume.ge(parameters.minimum_bearish_exit_relative_volume)
            & close_location.le(parameters.maximum_bearish_exit_close_location)
        )

        result[CAPITULATION_COLUMN] = capitulation.astype(bool)
        result[CONFIRMATION_COLUMN] = confirmation.astype(bool)
        result[BEARISH_EXIT_COLUMN] = bearish_exit.astype(bool)
        result["KRAKEN_AI_V2_CAPITULATION_FEATURES_AVAILABLE"] = (
            capitulation_available.astype(bool)
        )
        result["KRAKEN_AI_V2_CONFIRMATION_FEATURES_AVAILABLE"] = (
            confirmation_available.astype(bool)
        )
        result["KRAKEN_AI_V2_BEARISH_EXIT_FEATURES_AVAILABLE"] = (
            bearish_available.astype(bool)
        )
        return result

    def generate(self, data):
        result = self.conditions(data)
        parameters = self.parameters
        state = self.initial_state()
        state_before = []
        state_after = []
        transitions = []
        intents = []
        structural_failures = []
        setup_ages = []
        long_ages = []
        event_timestamps = []
        setup_lows = []

        for timestamp, row in result.iterrows():
            before = state
            capitulation = bool(row[CAPITULATION_COLUMN])
            confirmation = bool(row[CONFIRMATION_COLUMN])
            bearish_exit = bool(row[BEARISH_EXIT_COLUMN])
            close = float(row["Close"])
            low = float(row["Low"])
            structural_failure = False
            transition = "FLAT_WAIT"
            intent = INTENT_NONE
            observed_setup_age = -1
            observed_long_age = -1
            evidence_event_timestamp = None
            evidence_setup_low = np.nan

            if before.name == STATE_FLAT:
                if capitulation:
                    state = KrakenAIDrivenV2SignalState(
                        name=STATE_ARMED,
                        setup_age=0,
                        event_timestamp=timestamp,
                        setup_low=low,
                    )
                    transition = "CAPITULATION_ARMED"
                    observed_setup_age = 0
                    evidence_event_timestamp = timestamp
                    evidence_setup_low = low
                elif not bool(
                    row["KRAKEN_AI_V2_CAPITULATION_FEATURES_AVAILABLE"]
                ):
                    state = before
                    transition = "FLAT_FEATURES_UNAVAILABLE"
                else:
                    state = before

            elif before.name == STATE_ARMED:
                candidate_age = before.setup_age + 1
                structural_failure = close < float(before.setup_low)
                observed_setup_age = candidate_age
                evidence_event_timestamp = before.event_timestamp
                evidence_setup_low = float(before.setup_low)
                if capitulation:
                    state = KrakenAIDrivenV2SignalState(
                        name=STATE_ARMED,
                        setup_age=0,
                        event_timestamp=timestamp,
                        setup_low=low,
                    )
                    transition = "CAPITULATION_REARMED"
                    observed_setup_age = 0
                    evidence_event_timestamp = timestamp
                    evidence_setup_low = low
                elif structural_failure:
                    state = self.initial_state()
                    transition = "ARMED_STRUCTURAL_INVALIDATION"
                elif candidate_age > parameters.maximum_confirmation_delay_bars:
                    evidence_setup_low = min(float(before.setup_low), low)
                    state = self.initial_state()
                    transition = "ARMED_EXPIRED"
                elif confirmation:
                    confirmed_low = min(float(before.setup_low), low)
                    state = KrakenAIDrivenV2SignalState(
                        name=STATE_LONG,
                        long_age=0,
                        event_timestamp=before.event_timestamp,
                        setup_low=confirmed_low,
                    )
                    transition = "CONFIRMATION_LONG"
                    intent = INTENT_ENTER_NEXT_OPEN
                    observed_long_age = 0
                    evidence_setup_low = confirmed_low
                else:
                    continued_low = min(float(before.setup_low), low)
                    state = KrakenAIDrivenV2SignalState(
                        name=STATE_ARMED,
                        setup_age=candidate_age,
                        event_timestamp=before.event_timestamp,
                        setup_low=continued_low,
                    )
                    transition = (
                        "ARMED_WAIT"
                        if bool(
                            row["KRAKEN_AI_V2_CONFIRMATION_FEATURES_AVAILABLE"]
                        )
                        else "ARMED_FEATURES_UNAVAILABLE"
                    )
                    evidence_setup_low = continued_low

            else:
                observed_long_age = before.long_age + 1
                evidence_event_timestamp = before.event_timestamp
                evidence_setup_low = float(before.setup_low)
                structural_failure = close < float(before.setup_low)
                if structural_failure and bearish_exit:
                    state = self.initial_state()
                    transition = "LONG_STRUCTURAL_AND_BEARISH_EXIT"
                    intent = INTENT_EXIT_NEXT_OPEN
                elif structural_failure:
                    state = self.initial_state()
                    transition = "LONG_STRUCTURAL_EXIT"
                    intent = INTENT_EXIT_NEXT_OPEN
                elif bearish_exit:
                    state = self.initial_state()
                    transition = "LONG_BEARISH_VOLUME_EXIT"
                    intent = INTENT_EXIT_NEXT_OPEN
                else:
                    state = KrakenAIDrivenV2SignalState(
                        name=STATE_LONG,
                        long_age=observed_long_age,
                        event_timestamp=before.event_timestamp,
                        setup_low=before.setup_low,
                    )
                    transition = (
                        "LONG_HOLD"
                        if bool(
                            row["KRAKEN_AI_V2_BEARISH_EXIT_FEATURES_AVAILABLE"]
                        )
                        else "LONG_FEATURES_UNAVAILABLE"
                    )

            state_before.append(before.name)
            state_after.append(state.name)
            transitions.append(transition)
            intents.append(intent)
            structural_failures.append(bool(structural_failure))
            setup_ages.append(observed_setup_age)
            long_ages.append(observed_long_age)
            event_timestamps.append(evidence_event_timestamp)
            setup_lows.append(evidence_setup_low)

        result[STATE_BEFORE_COLUMN] = state_before
        result[STATE_AFTER_COLUMN] = state_after
        result[TRANSITION_COLUMN] = transitions
        result[ACTION_INTENT_COLUMN] = intents
        result[STRUCTURAL_FAILURE_COLUMN] = structural_failures
        result[SETUP_AGE_COLUMN] = setup_ages
        result[LONG_AGE_COLUMN] = long_ages
        result[EVENT_TIMESTAMP_COLUMN] = event_timestamps
        result[SETUP_LOW_COLUMN] = setup_lows
        result[PARAMETER_SET_COLUMN] = self.parameters.parameter_set_id
        return result
