"""Causal, per-asset volume evidence for controlled alpha research."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

try:
    from feature_engine import validate_input
except ImportError:  # package import when src is not placed directly on sys.path
    from src.feature_engine import validate_input


@dataclass(frozen=True)
class VolumeResearchConfig:
    """Freeze scale-independent volume features before inspecting results."""

    lookback: int = 20
    low_relative_volume: float = 0.75
    high_relative_volume: float = 1.50
    baseline_lag: int = 1

    def __post_init__(self):
        if isinstance(self.lookback, bool) or not isinstance(self.lookback, int):
            raise TypeError("Volume lookback must be an integer.")
        if self.lookback < 2:
            raise ValueError("Volume lookback must be at least 2.")
        if isinstance(self.baseline_lag, bool) or not isinstance(
            self.baseline_lag, int
        ):
            raise TypeError("Volume baseline lag must be an integer.")
        if self.baseline_lag < 1:
            raise ValueError("Volume baseline lag must be at least 1.")
        for value, name in (
            (self.low_relative_volume, "Low relative-volume threshold"),
            (self.high_relative_volume, "High relative-volume threshold"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be numeric.")
            if not np.isfinite(float(value)) or float(value) <= 0.0:
                raise ValueError(f"{name} must be a positive finite threshold.")
        if self.low_relative_volume >= self.high_relative_volume:
            raise ValueError(
                "Low relative-volume threshold must be less than the high threshold."
            )

    def as_dict(self):
        return {
            "lookback": self.lookback,
            "baseline_statistic": "TRAILING_MEDIAN",
            "baseline_lag": self.baseline_lag,
            "low_relative_volume": float(self.low_relative_volume),
            "high_relative_volume": float(self.high_relative_volume),
            "cross_asset_normalization": "PER_ASSET_RELATIVE_NOT_RAW_VOLUME",
            "signal_observation": "COMPLETED_BAR_ONLY",
        }


def _validated_market_data(data):
    validate_input(data)
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("Volume research data must use a DatetimeIndex.")
    if not data.index.is_monotonic_increasing or data.index.has_duplicates:
        raise ValueError("Volume research data must have a unique chronological index.")
    values = data[["Close", "Volume"]].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Volume research Close and Volume values must be finite.")
    if (data["Close"].astype(float) <= 0.0).any():
        raise ValueError("Volume research Close values must be positive.")
    if (data["Volume"].astype(float) < 0.0).any():
        raise ValueError("Volume research Volume values cannot be negative.")


def _prior_trailing_median(series, configuration):
    return series.shift(configuration.baseline_lag).rolling(
        window=configuration.lookback,
        min_periods=configuration.lookback,
    ).median()


def generate_volume_research_features(data, configuration=None):
    """Add causal volume features without changing the supplied market frame."""

    if configuration is None:
        configuration = VolumeResearchConfig()
    if not isinstance(configuration, VolumeResearchConfig):
        raise TypeError("Configuration must be a VolumeResearchConfig.")
    _validated_market_data(data)

    result = data.copy(deep=True)
    volume = result["Volume"].astype(float)
    close = result["Close"].astype(float)
    dollar_volume = close * volume
    volume_baseline = _prior_trailing_median(volume, configuration)
    dollar_volume_baseline = _prior_trailing_median(
        dollar_volume, configuration
    )
    relative_volume = volume / volume_baseline.where(volume_baseline > 0.0)
    relative_dollar_volume = dollar_volume / dollar_volume_baseline.where(
        dollar_volume_baseline > 0.0
    )

    change = close.diff()
    signed_volume = pd.Series(0.0, index=result.index, dtype=float)
    signed_volume.loc[change > 0.0] = volume.loc[change > 0.0]
    signed_volume.loc[change < 0.0] = -volume.loc[change < 0.0]
    on_balance_volume = signed_volume.cumsum()
    obv_change = on_balance_volume - on_balance_volume.shift(
        configuration.lookback
    )
    obv_direction = pd.Series("UNKNOWN", index=result.index, dtype=object)
    obv_ready = obv_change.notna()
    obv_direction.loc[obv_ready & (obv_change > 0.0)] = "RISING"
    obv_direction.loc[obv_ready & (obv_change < 0.0)] = "FALLING"
    obv_direction.loc[obv_ready & (obv_change == 0.0)] = "FLAT"

    regime = pd.Series("UNKNOWN", index=result.index, dtype=object)
    ready = relative_volume.notna()
    regime.loc[
        ready & (relative_volume < configuration.low_relative_volume)
    ] = "LOW"
    regime.loc[
        ready & (relative_volume > configuration.high_relative_volume)
    ] = "HIGH"
    regime.loc[
        ready
        & (relative_volume >= configuration.low_relative_volume)
        & (relative_volume <= configuration.high_relative_volume)
    ] = "NORMAL"

    suffix = configuration.lookback
    result[f"VOLUME_BASELINE_{suffix}"] = volume_baseline
    result[f"RELATIVE_VOLUME_{suffix}"] = relative_volume
    result["DOLLAR_VOLUME"] = dollar_volume
    result[f"DOLLAR_VOLUME_BASELINE_{suffix}"] = dollar_volume_baseline
    result[f"RELATIVE_DOLLAR_VOLUME_{suffix}"] = relative_dollar_volume
    result["ON_BALANCE_VOLUME"] = on_balance_volume
    result[f"ON_BALANCE_VOLUME_CHANGE_{suffix}"] = obv_change
    result[f"ON_BALANCE_VOLUME_DIRECTION_{suffix}"] = obv_direction
    result[f"VOLUME_REGIME_{suffix}"] = regime
    return result


class VolumeConditionedAnalyzer:
    """Attribute unseen trades to the volume regime on their signal bar."""

    def __init__(self, configuration=None):
        if configuration is None:
            configuration = VolumeResearchConfig()
        if not isinstance(configuration, VolumeResearchConfig):
            raise TypeError("Configuration must be a VolumeResearchConfig.")
        self.configuration = configuration

    @staticmethod
    def _trade_value(trade, key):
        try:
            value = float(trade[key])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Trade evidence is missing numeric {key}.") from exc
        if not np.isfinite(value):
            raise ValueError(f"Trade evidence {key} must be finite.")
        return value

    @classmethod
    def _summarize(cls, trades):
        gross = [cls._trade_value(trade, "gross_profit_loss") for trade in trades]
        costs = [cls._trade_value(trade, "total_costs") for trade in trades]
        net = [cls._trade_value(trade, "profit_loss") for trade in trades]
        net_total = sum(net)
        return {
            "trade_count": len(trades),
            "gross_profit_loss": sum(gross),
            "total_costs": sum(costs),
            "net_profit_loss": net_total,
            "average_net_profit_loss": (
                net_total / len(trades) if trades else 0.0
            ),
            "win_rate": (
                sum(value > 0.0 for value in net) / len(net) if net else 0.0
            ),
        }

    def analyze(self, data, validation_result):
        if not isinstance(validation_result, dict):
            raise TypeError("Validation result must be a dictionary.")
        try:
            trades = validation_result["out_of_sample"]["out_of_sample"][
                "trade_history"
            ]
        except (KeyError, TypeError) as exc:
            raise ValueError(
                "Validation result does not contain OOS trade history."
            ) from exc
        if not isinstance(trades, list):
            raise ValueError("Validation result OOS trade history must be a list.")

        features = generate_volume_research_features(data, self.configuration)
        regime_column = f"VOLUME_REGIME_{self.configuration.lookback}"
        relative_volume_column = (
            f"RELATIVE_VOLUME_{self.configuration.lookback}"
        )
        relative_dollar_volume_column = (
            f"RELATIVE_DOLLAR_VOLUME_{self.configuration.lookback}"
        )
        obv_direction_column = (
            f"ON_BALANCE_VOLUME_DIRECTION_{self.configuration.lookback}"
        )
        grouped = {}
        obv_grouped = {}
        relative_volume_values = []
        relative_dollar_volume_values = []
        unattributed = 0
        for trade in trades:
            if not isinstance(trade, dict):
                raise ValueError("Every trade-history item must be a dictionary.")
            signal_index = trade.get("entry_signal_index")
            if signal_index not in features.index:
                unattributed += 1
                continue
            label = features.at[signal_index, regime_column]
            if label == "UNKNOWN":
                unattributed += 1
                continue
            grouped.setdefault(label, []).append(trade)
            obv_label = features.at[signal_index, obv_direction_column]
            if obv_label != "UNKNOWN":
                obv_grouped.setdefault(obv_label, []).append(trade)
            relative_volume_values.append(
                float(features.at[signal_index, relative_volume_column])
            )
            relative_dollar_volume_values.append(
                float(features.at[signal_index, relative_dollar_volume_column])
            )

        summaries = {
            label: self._summarize(grouped[label]) for label in sorted(grouped)
        }
        obv_summaries = {
            label: self._summarize(obv_grouped[label])
            for label in sorted(obv_grouped)
        }
        return {
            "configuration": self.configuration.as_dict(),
            "signal_bar_attribution": True,
            "volume_regimes": summaries,
            "obv_directions": obv_summaries,
            "entry_context": {
                "mean_relative_volume": (
                    float(np.mean(relative_volume_values))
                    if relative_volume_values
                    else None
                ),
                "median_relative_volume": (
                    float(np.median(relative_volume_values))
                    if relative_volume_values
                    else None
                ),
                "mean_relative_dollar_volume": (
                    float(np.mean(relative_dollar_volume_values))
                    if relative_dollar_volume_values
                    else None
                ),
                "median_relative_dollar_volume": (
                    float(np.median(relative_dollar_volume_values))
                    if relative_dollar_volume_values
                    else None
                ),
            },
            "attributed_trade_count": sum(
                item["trade_count"] for item in summaries.values()
            ),
            "unattributed_trade_count": unattributed,
            "observed_volume_regime_count": len(summaries),
        }
