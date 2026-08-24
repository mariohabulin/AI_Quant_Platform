"""Executable catalog strategies for Alpha Discovery Protocol v1."""

import numpy as np
import pandas as pd

try:
    from alpha_discovery_features import CausalEMATrendStructure
    from alpha_discovery_protocol import (
        CALIBRATION_PARAMETER_CATALOG,
        PARAMETER_SET_ORDER,
        AlphaCalibrationParameterSet,
    )
    from market_regime import MarketRegimeDetector
    from strategy_engine import StrategyEngine
    from strategy_library import StrategyLibrary
    from volume_research import (
        VolumeResearchConfig,
        generate_volume_research_features,
    )
except ImportError:  # package import when src is not placed directly on sys.path
    from src.alpha_discovery_features import CausalEMATrendStructure
    from src.alpha_discovery_protocol import (
        CALIBRATION_PARAMETER_CATALOG,
        PARAMETER_SET_ORDER,
        AlphaCalibrationParameterSet,
    )
    from src.market_regime import MarketRegimeDetector
    from src.strategy_engine import StrategyEngine
    from src.strategy_library import StrategyLibrary
    from src.volume_research import (
        VolumeResearchConfig,
        generate_volume_research_features,
    )


class AlphaDiscoveryStrategy:
    """One exact catalog member with causal regime, volume and EMA gates."""

    def __init__(
        self,
        parameter_set,
        regime_detector=None,
        volume_configuration=None,
        volume_feature_generator=generate_volume_research_features,
        trend_structure=None,
    ):
        if not isinstance(parameter_set, AlphaCalibrationParameterSet):
            raise TypeError(
                "Parameter set must be an AlphaCalibrationParameterSet."
            )
        if regime_detector is None:
            regime_detector = MarketRegimeDetector()
        if not callable(getattr(regime_detector, "detect", None)):
            raise TypeError("Regime detector must implement detect().")
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

        self.parameter_set = parameter_set
        self.name = f"alpha_discovery_{parameter_set.parameter_set_id}"
        self.regime_detector = regime_detector
        self.volume_configuration = volume_configuration
        self.volume_feature_generator = volume_feature_generator
        self.trend_structure = trend_structure

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
        period = self.parameter_set.adx_period
        atr_period = self.parameter_set.atr_period
        required = (
            "Close",
            "Volume",
            f"ADX_{period}",
            f"PLUS_DI_{period}",
            f"MINUS_DI_{period}",
            f"ATR_{atr_period}",
        )
        missing = [column for column in required if column not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def generate_signals(self, data, evaluation_start_position=0):
        self._validate_data(data, evaluation_start_position)
        result = self.volume_feature_generator(
            data, self.volume_configuration
        ).copy(deep=True)
        regimes = self.regime_detector.detect(data)
        for column in regimes.columns:
            result[column] = regimes[column]
        result = self.trend_structure.generate(result)

        parameter = self.parameter_set
        adx = result[f"ADX_{parameter.adx_period}"].astype(float)
        plus_di = result[f"PLUS_DI_{parameter.adx_period}"].astype(float)
        minus_di = result[f"MINUS_DI_{parameter.adx_period}"].astype(float)
        atr = result[f"ATR_{parameter.atr_period}"].astype(float)
        volume_regime = result[
            f"VOLUME_REGIME_{parameter.volume_lookback}"
        ]

        entry = (
            (adx >= parameter.adx_entry_threshold)
            & (plus_di > minus_di)
            & volume_regime.eq(parameter.required_volume_regime)
            & result["market_regime"].eq(parameter.required_market_regime)
            & result["ALPHA_DISCOVERY_TREND_STRUCTURE"].eq(True)
            & atr.notna()
            & np.isfinite(atr)
            & atr.gt(0.0)
        )
        exit_condition = (
            (adx < parameter.adx_exit_threshold) | (plus_di <= minus_di)
        )

        signals = np.zeros(len(result), dtype=int)
        in_position = False
        cooldown_remaining = 0
        for position in range(evaluation_start_position, len(result)):
            if in_position:
                if bool(exit_condition.iloc[position]):
                    signals[position] = -1
                    in_position = False
                    cooldown_remaining = parameter.cooldown_bars
                continue
            if cooldown_remaining > 0:
                cooldown_remaining -= 1
                continue
            if bool(entry.iloc[position]):
                signals[position] = 1
                in_position = True

        result["Signal"] = signals
        result["ALPHA_DISCOVERY_ENTRY_CONDITION"] = entry.astype(bool)
        result["ALPHA_V2_ATR_RISK_DISTANCE"] = (
            atr * parameter.atr_risk_distance_multiple
        )
        result["ALPHA_V2_REWARD_RISK_RATIO"] = parameter.reward_risk_ratio
        result["ALPHA_DISCOVERY_PARAMETER_SET_ID"] = parameter.parameter_set_id
        result["ALPHA_DISCOVERY_EVALUATION_START_POSITION"] = (
            evaluation_start_position
        )
        return result


def alpha_discovery_strategy_engines():
    """Build the exact complete ordered strategy catalog."""

    engines = {}
    for parameter_set in CALIBRATION_PARAMETER_CATALOG:
        strategy = AlphaDiscoveryStrategy(parameter_set)
        library = StrategyLibrary()
        library.register(strategy)
        engines[parameter_set.parameter_set_id] = StrategyEngine(
            library, strategy.name
        )
    if tuple(engines) != PARAMETER_SET_ORDER:
        raise ValueError("Alpha Discovery strategy catalog order changed.")
    return engines
