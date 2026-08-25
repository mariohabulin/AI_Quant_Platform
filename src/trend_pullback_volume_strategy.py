"""Executable four-member trend-pullback and volume re-expansion catalog."""

import numpy as np
import pandas as pd

try:
    from alpha_discovery_features import CausalEMATrendStructure
    from strategy_engine import StrategyEngine
    from strategy_library import StrategyLibrary
    from trend_pullback_state import CausalTrendPullbackStateMachine
    from trend_pullback_volume_protocol import (
        TREND_PULLBACK_PARAMETER_CATALOG,
        TREND_PULLBACK_PARAMETER_ORDER,
        TrendPullbackVolumeParameterSet,
    )
    from volume_research import (
        VolumeResearchConfig,
        generate_volume_research_features,
    )
except ImportError:  # package import when src is not placed directly on sys.path
    from src.alpha_discovery_features import CausalEMATrendStructure
    from src.strategy_engine import StrategyEngine
    from src.strategy_library import StrategyLibrary
    from src.trend_pullback_state import CausalTrendPullbackStateMachine
    from src.trend_pullback_volume_protocol import (
        TREND_PULLBACK_PARAMETER_CATALOG,
        TREND_PULLBACK_PARAMETER_ORDER,
        TrendPullbackVolumeParameterSet,
    )
    from src.volume_research import (
        VolumeResearchConfig,
        generate_volume_research_features,
    )


class TrendPullbackVolumeStrategy:
    """Long-only ordered setup with completed-bar observation and next-Open fill."""

    def __init__(
        self,
        parameter_set,
        volume_configuration=None,
        volume_feature_generator=generate_volume_research_features,
        trend_structure=None,
        state_machine=None,
    ):
        if not isinstance(parameter_set, TrendPullbackVolumeParameterSet):
            raise TypeError(
                "Parameter set must be a TrendPullbackVolumeParameterSet."
            )
        if volume_configuration is None:
            volume_configuration = VolumeResearchConfig(
                lookback=parameter_set.volume_lookback,
                baseline_lag=parameter_set.volume_baseline_lag,
            )
        if not isinstance(volume_configuration, VolumeResearchConfig):
            raise TypeError("Volume configuration must be a VolumeResearchConfig.")
        if (
            volume_configuration.lookback != parameter_set.volume_lookback
            or volume_configuration.baseline_lag
            != parameter_set.volume_baseline_lag
        ):
            raise ValueError("Volume configuration changed from the catalog.")
        if not callable(volume_feature_generator):
            raise TypeError("Volume feature generator must be callable.")

        if trend_structure is None:
            trend_structure = CausalEMATrendStructure(
                fast_period=parameter_set.ema_fast_period,
                slow_period=parameter_set.ema_slow_period,
                slope_lookback=parameter_set.ema_slope_lookback,
            )
        if not callable(getattr(trend_structure, "generate", None)) or not callable(
            getattr(trend_structure, "configuration", None)
        ):
            raise TypeError(
                "Trend structure must implement generate() and configuration()."
            )
        trend_configuration = trend_structure.configuration()
        if (
            trend_configuration.get("fast_period")
            != parameter_set.ema_fast_period
            or trend_configuration.get("slow_period")
            != parameter_set.ema_slow_period
            or trend_configuration.get("slope_lookback")
            != parameter_set.ema_slope_lookback
            or trend_configuration.get("causal") is not True
        ):
            raise ValueError("Trend structure changed from the catalog.")

        if state_machine is None:
            state_machine = CausalTrendPullbackStateMachine(parameter_set)
        if not isinstance(state_machine, CausalTrendPullbackStateMachine):
            raise TypeError(
                "State machine must be a CausalTrendPullbackStateMachine."
            )
        if state_machine.parameter_set != parameter_set:
            raise ValueError("State machine identity changed from the catalog.")

        self.parameter_set = parameter_set
        self.name = f"trend_pullback_volume_{parameter_set.parameter_set_id}"
        self.volume_configuration = volume_configuration
        self.volume_feature_generator = volume_feature_generator
        self.trend_structure = trend_structure
        self.state_machine = state_machine

    @property
    def required_features(self):
        return [
            {
                "name": "ADX",
                "parameters": {"period": self.parameter_set.adx_period},
            },
            {
                "name": "ATR",
                "parameters": {"period": self.parameter_set.atr_period},
            },
        ]

    def configuration(self):
        return {
            **self.parameter_set.as_dict(),
            "strategy_name": self.name,
            "volume": self.volume_configuration.as_dict(),
            "trend_structure_configuration": (
                self.trend_structure.configuration()
            ),
            "setup_state_machine": self.state_machine.configuration(),
            "market_regime_gate": "NONE",
            "signal_state_reset": "EVALUATION_WINDOW_START",
            "signal_observation": "COMPLETED_BAR_CLOSE",
            "execution_timing": "NEXT_BAR_OPEN",
        }

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
            "Volume",
            f"ADX_{parameter.adx_period}",
            f"PLUS_DI_{parameter.adx_period}",
            f"MINUS_DI_{parameter.adx_period}",
            f"ATR_{parameter.atr_period}",
        )
        missing = [column for column in required if column not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def generate_signals(self, data, evaluation_start_position=0):
        self._validate_data(data, evaluation_start_position)
        result = self.volume_feature_generator(
            data, self.volume_configuration
        ).copy(deep=True)
        result = self.trend_structure.generate(result)
        result = self.state_machine.conditions(
            result, evaluation_start_position=evaluation_start_position
        )

        parameter = self.parameter_set
        close = pd.to_numeric(result["Close"], errors="coerce")
        ema_fast = pd.to_numeric(
            result[f"ALPHA_DISCOVERY_EMA_{parameter.ema_fast_period}"],
            errors="coerce",
        )
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
        exit_condition = (
            close.lt(ema_fast)
            | adx.lt(parameter.adx_exit_threshold)
            | plus_di.le(minus_di)
        )

        signals = np.zeros(len(result), dtype=int)
        setup_active = np.zeros(len(result), dtype=bool)
        setup_age = np.full(len(result), -1, dtype=int)
        triggers = np.zeros(len(result), dtype=bool)
        state = self.state_machine.initial_state()
        in_position = False
        cooldown_remaining = 0
        for position in range(evaluation_start_position, len(result)):
            if in_position:
                state, _, _ = self.state_machine.advance(
                    state,
                    pullback=False,
                    recovery=False,
                    trend_valid=False,
                    allow_setup=False,
                )
                if bool(exit_condition.iloc[position]):
                    signals[position] = -1
                    in_position = False
                    cooldown_remaining = parameter.cooldown_bars
                continue
            if cooldown_remaining > 0:
                state, _, _ = self.state_machine.advance(
                    state,
                    pullback=False,
                    recovery=False,
                    trend_valid=False,
                    allow_setup=False,
                )
                cooldown_remaining -= 1
                continue

            state, triggered, observed_age = self.state_machine.advance(
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
            setup_active[position] = state.armed
            setup_age[position] = observed_age
            triggers[position] = triggered
            if triggered:
                signals[position] = 1
                in_position = True

        result["Signal"] = signals
        result["TREND_PULLBACK_SETUP_ACTIVE"] = setup_active
        result["TREND_PULLBACK_SETUP_AGE"] = setup_age
        result["TREND_PULLBACK_TRIGGER"] = triggers
        result["TREND_PULLBACK_ENTRY_CONDITION"] = triggers
        result["ALPHA_V2_ATR_RISK_DISTANCE"] = (
            atr * parameter.initial_stop_atr
        )
        result["ALPHA_V2_REWARD_RISK_RATIO"] = parameter.reward_risk_ratio
        result["TREND_PULLBACK_PARAMETER_SET_ID"] = parameter.parameter_set_id
        result["TREND_PULLBACK_EVALUATION_START_POSITION"] = (
            evaluation_start_position
        )
        return result


def trend_pullback_volume_strategy_engines():
    """Build the exact complete ordered strategy catalog without ranking."""

    engines = {}
    for parameter_set in TREND_PULLBACK_PARAMETER_CATALOG:
        strategy = TrendPullbackVolumeStrategy(parameter_set)
        library = StrategyLibrary()
        library.register(strategy)
        engines[parameter_set.parameter_set_id] = StrategyEngine(
            library, strategy.name
        )
    if tuple(engines) != TREND_PULLBACK_PARAMETER_ORDER:
        raise ValueError("Trend-pullback strategy catalog order changed.")
    return engines
