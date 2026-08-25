"""Causal setup state for trend-pullback and volume re-expansion research."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

try:
    from trend_pullback_volume_protocol import TrendPullbackVolumeParameterSet
except ImportError:  # package import when src is not placed directly on sys.path
    from src.trend_pullback_volume_protocol import (
        TrendPullbackVolumeParameterSet,
    )


@dataclass(frozen=True)
class TrendPullbackSetupState:
    """Minimal state carried only across completed bars inside one window."""

    armed: bool = False
    age: int = -1

    def __post_init__(self):
        if not isinstance(self.armed, bool):
            raise TypeError("Setup armed state must be boolean.")
        if not isinstance(self.age, int) or isinstance(self.age, bool):
            raise TypeError("Setup age must be an integer.")
        if self.armed and self.age < 0:
            raise ValueError("An armed setup must have a nonnegative age.")
        if not self.armed and self.age != -1:
            raise ValueError("An inactive setup must use age -1.")


class CausalTrendPullbackStateMachine:
    """Recognize an ordered pullback then recovery without same-bar entry."""

    def __init__(self, parameter_set):
        if not isinstance(parameter_set, TrendPullbackVolumeParameterSet):
            raise TypeError(
                "Parameter set must be a TrendPullbackVolumeParameterSet."
            )
        self.parameter_set = parameter_set

    def configuration(self):
        parameter = self.parameter_set
        return {
            "parameter_set_id": parameter.parameter_set_id,
            "prior_strength_lookback_bars": parameter.setup_lookback_bars,
            "prior_adx_confirmation": parameter.prior_adx_confirmation,
            "pullback_distance_atr": parameter.pullback_distance_atr,
            "pullback_relative_volume_ceiling": (
                parameter.pullback_relative_volume_ceiling
            ),
            "trigger_relative_volume": parameter.trigger_relative_volume,
            "current_adx_floor": parameter.current_adx_floor,
            "setup_expiry_bars": parameter.setup_lookback_bars,
            "observation_timing": "COMPLETED_BAR_CLOSE",
            "same_bar_pullback_and_trigger": False,
            "future_bar_access": False,
        }

    @staticmethod
    def initial_state():
        return TrendPullbackSetupState()

    def _validate_data(self, data, evaluation_start_position):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")
        if data.empty:
            raise ValueError("Input data cannot be empty.")
        if not data.index.is_monotonic_increasing or data.index.has_duplicates:
            raise ValueError("Input data must have a unique chronological index.")
        if (
            not isinstance(evaluation_start_position, int)
            or isinstance(evaluation_start_position, bool)
        ):
            raise TypeError("Evaluation start must be an integer position.")
        if not 0 <= evaluation_start_position < len(data):
            raise ValueError("Evaluation start is outside the supplied data.")

        parameter = self.parameter_set
        required = (
            "High",
            "Close",
            f"ADX_{parameter.adx_period}",
            f"PLUS_DI_{parameter.adx_period}",
            f"MINUS_DI_{parameter.adx_period}",
            f"ATR_{parameter.atr_period}",
            f"ALPHA_DISCOVERY_EMA_{parameter.ema_fast_period}",
            "ALPHA_DISCOVERY_TREND_STRUCTURE",
            f"RELATIVE_VOLUME_{parameter.volume_lookback}",
        )
        missing = [column for column in required if column not in data.columns]
        if missing:
            raise ValueError(f"Missing pullback-state columns: {missing}")

    def conditions(self, data, evaluation_start_position=0):
        """Return prefix-causal conditions without carrying setup state."""

        self._validate_data(data, evaluation_start_position)
        parameter = self.parameter_set
        result = data.copy(deep=True)
        close = pd.to_numeric(result["Close"], errors="coerce")
        previous_high = pd.to_numeric(result["High"], errors="coerce").shift(1)
        adx = pd.to_numeric(
            result[f"ADX_{parameter.adx_period}"], errors="coerce"
        )
        plus_di = pd.to_numeric(
            result[f"PLUS_DI_{parameter.adx_period}"], errors="coerce"
        )
        minus_di = pd.to_numeric(
            result[f"MINUS_DI_{parameter.adx_period}"], errors="coerce"
        )
        atr = pd.to_numeric(
            result[f"ATR_{parameter.atr_period}"], errors="coerce"
        )
        ema_fast = pd.to_numeric(
            result[f"ALPHA_DISCOVERY_EMA_{parameter.ema_fast_period}"],
            errors="coerce",
        )
        relative_volume = pd.to_numeric(
            result[f"RELATIVE_VOLUME_{parameter.volume_lookback}"],
            errors="coerce",
        )
        trend = result["ALPHA_DISCOVERY_TREND_STRUCTURE"].eq(True)

        finite_atr = atr.notna() & np.isfinite(atr) & atr.gt(0.0)
        finite_relative_volume = (
            relative_volume.notna()
            & np.isfinite(relative_volume)
            & relative_volume.ge(0.0)
        )
        prior_strength = (
            adx.shift(1)
            .rolling(
                window=parameter.setup_lookback_bars,
                min_periods=parameter.setup_lookback_bars,
            )
            .max()
            .ge(parameter.prior_adx_confirmation)
        )
        pullback = (
            trend
            & prior_strength
            & finite_atr
            & finite_relative_volume
            & close.notna()
            & ema_fast.notna()
            & close.sub(ema_fast).abs().le(
                atr * parameter.pullback_distance_atr
            )
            & relative_volume.le(parameter.pullback_relative_volume_ceiling)
        )
        recovery = (
            trend
            & finite_atr
            & finite_relative_volume
            & adx.ge(parameter.current_adx_floor)
            & plus_di.gt(minus_di)
            & close.gt(ema_fast)
            & close.gt(previous_high)
            & relative_volume.ge(parameter.trigger_relative_volume)
        )

        result["TREND_PULLBACK_PRIOR_STRENGTH"] = prior_strength.astype(bool)
        result["TREND_PULLBACK_PULLBACK_CONDITION"] = pullback.astype(bool)
        result["TREND_PULLBACK_RECOVERY_CONDITION"] = recovery.astype(bool)
        result["TREND_PULLBACK_EVALUATION_START_POSITION"] = (
            evaluation_start_position
        )
        return result

    def advance(
        self,
        state,
        *,
        pullback,
        recovery,
        trend_valid,
        allow_setup=True,
    ):
        """Advance one completed bar and return state, trigger and observed age."""

        if not isinstance(state, TrendPullbackSetupState):
            raise TypeError("State must be a TrendPullbackSetupState.")
        for value, name in (
            (pullback, "Pullback condition"),
            (recovery, "Recovery condition"),
            (trend_valid, "Trend-valid condition"),
            (allow_setup, "Allow-setup condition"),
        ):
            if not isinstance(value, (bool, np.bool_)):
                raise TypeError(f"{name} must be boolean.")

        if not bool(allow_setup) or not bool(trend_valid):
            return self.initial_state(), False, -1
        if state.armed:
            age = state.age + 1
            if age <= self.parameter_set.setup_lookback_bars and bool(recovery):
                return self.initial_state(), True, age
            if bool(pullback):
                return TrendPullbackSetupState(True, 0), False, 0
            if age >= self.parameter_set.setup_lookback_bars:
                return self.initial_state(), False, age
            return TrendPullbackSetupState(True, age), False, age
        if bool(pullback):
            return TrendPullbackSetupState(True, 0), False, 0
        return self.initial_state(), False, -1

    def generate(self, data, evaluation_start_position=0):
        """Generate diagnostic setup state, resetting at the evaluation boundary."""

        result = self.conditions(data, evaluation_start_position)
        state = self.initial_state()
        active = np.zeros(len(result), dtype=bool)
        ages = np.full(len(result), -1, dtype=int)
        triggers = np.zeros(len(result), dtype=bool)
        for position in range(evaluation_start_position, len(result)):
            state, triggered, observed_age = self.advance(
                state,
                pullback=bool(
                    result.iloc[position][
                        "TREND_PULLBACK_PULLBACK_CONDITION"
                    ]
                ),
                recovery=bool(
                    result.iloc[position][
                        "TREND_PULLBACK_RECOVERY_CONDITION"
                    ]
                ),
                trend_valid=bool(
                    result.iloc[position][
                        "ALPHA_DISCOVERY_TREND_STRUCTURE"
                    ]
                ),
            )
            active[position] = state.armed
            ages[position] = observed_age
            triggers[position] = triggered

        result["TREND_PULLBACK_SETUP_ACTIVE"] = active
        result["TREND_PULLBACK_SETUP_AGE"] = ages
        result["TREND_PULLBACK_TRIGGER"] = triggers
        result["TREND_PULLBACK_PARAMETER_SET_ID"] = (
            self.parameter_set.parameter_set_id
        )
        return result
