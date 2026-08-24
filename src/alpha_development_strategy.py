"""Causal joint ADX, market-regime and volume mechanisms for alpha research."""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

try:
    from market_regime import MarketRegimeDetector
    from volume_research import (
        VolumeResearchConfig,
        generate_volume_research_features,
    )
except ImportError:  # package import when src is not placed directly on sys.path
    from src.market_regime import MarketRegimeDetector
    from src.volume_research import (
        VolumeResearchConfig,
        generate_volume_research_features,
    )


@dataclass(frozen=True)
class AlphaDevelopmentVariant:
    """One pre-declared ablation in the joint-condition hypothesis chain."""

    variant_id: str
    required_market_regime: str | None = None
    required_obv_direction: str | None = None

    def __post_init__(self):
        if not isinstance(self.variant_id, str) or not self.variant_id.strip():
            raise ValueError("Variant ID is required.")
        if self.required_market_regime not in (None, "BULLISH_NORMAL"):
            raise ValueError("Only BULLISH_NORMAL may be frozen as a market gate.")
        if self.required_obv_direction not in (None, "RISING"):
            raise ValueError("Only RISING may be frozen as an OBV gate.")

    def as_dict(self):
        result = asdict(self)
        result.update(
            {
                "direction_gate": "ADX_14>=25_AND_PLUS_DI_14>MINUS_DI_14",
                "volume_entry_gate": "VOLUME_REGIME_20=HIGH",
                "volume_exit_gate": "NONE_ENTRY_CONFIRMATION_ONLY",
                "exit_gate": "ADX_14<20_OR_PLUS_DI_14<=MINUS_DI_14",
                "cooldown_bars": 4,
                "atr_risk_distance_multiple": 2.0,
                "reward_risk_ratio": 3.0,
            }
        )
        return result


ALPHA_DEVELOPMENT_VARIANTS = (
    AlphaDevelopmentVariant("adx_high_relative_volume"),
    AlphaDevelopmentVariant(
        "adx_bullish_normal_high_relative_volume",
        required_market_regime="BULLISH_NORMAL",
    ),
    AlphaDevelopmentVariant(
        "adx_bullish_normal_high_relative_volume_obv_rising",
        required_market_regime="BULLISH_NORMAL",
        required_obv_direction="RISING",
    ),
)


class ADXRegimeVolumeStrategy:
    """Long-only causal development strategy with entry-only volume filters.

    The strategy records an ATR risk distance derived on the completed signal
    bar. A separately reviewed execution component must translate that distance
    into position size and active stop/target orders at the following bar open.
    This class deliberately does not pretend that advisory Stop/Target columns
    are protective fills.
    """

    def __init__(
        self,
        variant,
        adx_period=14,
        entry_threshold=25.0,
        exit_threshold=20.0,
        atr_period=14,
        atr_risk_distance_multiple=2.0,
        reward_risk_ratio=3.0,
        cooldown_bars=4,
        volume_configuration=None,
        regime_detector=None,
        volume_feature_generator=generate_volume_research_features,
    ):
        if not isinstance(variant, AlphaDevelopmentVariant):
            raise TypeError("Variant must be an AlphaDevelopmentVariant.")
        for value, name in (
            (adx_period, "ADX period"),
            (atr_period, "ATR period"),
            (cooldown_bars, "Cooldown bars"),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer.")
            if value < (0 if name == "Cooldown bars" else 1):
                raise ValueError(f"{name} is outside the permitted range.")
        for value, name in (
            (entry_threshold, "Entry threshold"),
            (exit_threshold, "Exit threshold"),
            (atr_risk_distance_multiple, "ATR risk-distance multiple"),
            (reward_risk_ratio, "Reward/risk ratio"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be numeric.")
            if not np.isfinite(float(value)) or float(value) <= 0.0:
                raise ValueError(f"{name} must be positive and finite.")
        if float(exit_threshold) >= float(entry_threshold):
            raise ValueError("Exit threshold must be below entry threshold.")
        if volume_configuration is None:
            volume_configuration = VolumeResearchConfig()
        if not isinstance(volume_configuration, VolumeResearchConfig):
            raise TypeError("Volume configuration must be a VolumeResearchConfig.")
        if regime_detector is None:
            regime_detector = MarketRegimeDetector()
        if not callable(getattr(regime_detector, "detect", None)):
            raise TypeError("Regime detector must implement detect().")
        if not callable(volume_feature_generator):
            raise TypeError("Volume feature generator must be callable.")

        self.variant = variant
        self.name = f"alpha_v2_{variant.variant_id}"
        self.adx_period = adx_period
        self.entry_threshold = float(entry_threshold)
        self.exit_threshold = float(exit_threshold)
        self.atr_period = atr_period
        self.atr_risk_distance_multiple = float(atr_risk_distance_multiple)
        self.reward_risk_ratio = float(reward_risk_ratio)
        self.cooldown_bars = cooldown_bars
        self.volume_configuration = volume_configuration
        self.regime_detector = regime_detector
        self.volume_feature_generator = volume_feature_generator

    @property
    def required_features(self):
        return [
            {"name": "ADX", "parameters": {"period": self.adx_period}},
            {"name": "ATR", "parameters": {"period": self.atr_period}},
        ]

    def configuration(self):
        return {
            **self.variant.as_dict(),
            "strategy_name": self.name,
            "adx_period": self.adx_period,
            "entry_threshold": self.entry_threshold,
            "exit_threshold": self.exit_threshold,
            "atr_period": self.atr_period,
            "atr_risk_distance_multiple": self.atr_risk_distance_multiple,
            "reward_risk_ratio": self.reward_risk_ratio,
            "cooldown_bars": self.cooldown_bars,
            "volume": self.volume_configuration.as_dict(),
            "signal_observation": "COMPLETED_BAR_CLOSE",
            "execution_timing": "NEXT_BAR_OPEN",
        }

    def _validate_columns(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")
        required = (
            "Close",
            "Volume",
            f"ADX_{self.adx_period}",
            f"PLUS_DI_{self.adx_period}",
            f"MINUS_DI_{self.adx_period}",
            f"ATR_{self.atr_period}",
        )
        missing = [column for column in required if column not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        if data.empty:
            raise ValueError("Input data cannot be empty.")
        if not data.index.is_monotonic_increasing or data.index.has_duplicates:
            raise ValueError("Input data must have a unique chronological index.")

    def generate_signals(self, data):
        self._validate_columns(data)
        result = self.volume_feature_generator(
            data, self.volume_configuration
        ).copy(deep=True)
        regimes = self.regime_detector.detect(data)
        for column in regimes.columns:
            result[column] = regimes[column]

        suffix = self.volume_configuration.lookback
        volume_regime_column = f"VOLUME_REGIME_{suffix}"
        obv_direction_column = f"ON_BALANCE_VOLUME_DIRECTION_{suffix}"
        adx = result[f"ADX_{self.adx_period}"].astype(float)
        plus_di = result[f"PLUS_DI_{self.adx_period}"].astype(float)
        minus_di = result[f"MINUS_DI_{self.adx_period}"].astype(float)
        atr = result[f"ATR_{self.atr_period}"].astype(float)

        entry = (
            (adx >= self.entry_threshold)
            & (plus_di > minus_di)
            & (result[volume_regime_column] == "HIGH")
            & atr.notna()
            & (atr > 0.0)
        )
        if self.variant.required_market_regime is not None:
            entry &= result["market_regime"].eq(
                self.variant.required_market_regime
            )
        if self.variant.required_obv_direction is not None:
            entry &= result[obv_direction_column].eq(
                self.variant.required_obv_direction
            )

        exit_condition = (adx < self.exit_threshold) | (plus_di <= minus_di)
        signals = np.zeros(len(result), dtype=int)
        in_position = False
        cooldown_remaining = 0
        for position in range(len(result)):
            if in_position:
                if bool(exit_condition.iloc[position]):
                    signals[position] = -1
                    in_position = False
                    cooldown_remaining = self.cooldown_bars
                continue
            if cooldown_remaining > 0:
                cooldown_remaining -= 1
                continue
            if bool(entry.iloc[position]):
                signals[position] = 1
                in_position = True

        result["Signal"] = signals
        result["ALPHA_V2_ENTRY_CONDITION"] = entry.astype(bool)
        result["ALPHA_V2_ATR_RISK_DISTANCE"] = (
            atr * self.atr_risk_distance_multiple
        )
        result["ALPHA_V2_REWARD_RISK_RATIO"] = self.reward_risk_ratio
        result["ALPHA_V2_VARIANT"] = self.variant.variant_id
        return result


def alpha_development_strategies():
    """Construct the exact ordered, non-ranked v2 ablation chain."""

    return tuple(ADXRegimeVolumeStrategy(variant) for variant in ALPHA_DEVELOPMENT_VARIANTS)
