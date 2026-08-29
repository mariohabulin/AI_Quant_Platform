"""Causal completed-bar features for the Kraken AI-driven v2 research path.

This module deliberately contains no trading action, strategy threshold,
position state, performance calculation or parameter search.  It converts one
continuous daily OHLCV availability segment into auditable measurements that a
separately pre-registered state machine may consume later.
"""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


REQUIRED_OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
DAILY_STEP = pd.Timedelta(days=1)
FEATURE_PREFIX = "KRAKEN_AI_V2_"
FEATURE_COLUMNS = (
    f"{FEATURE_PREFIX}PREVIOUS_CLOSE",
    f"{FEATURE_PREFIX}CLOSE_RETURN_1",
    f"{FEATURE_PREFIX}PRIOR_CLOSE_HIGH",
    f"{FEATURE_PREFIX}DRAWDOWN_FROM_PRIOR_HIGH",
    f"{FEATURE_PREFIX}PRIOR_VOLUME_MEDIAN",
    f"{FEATURE_PREFIX}RELATIVE_VOLUME",
    f"{FEATURE_PREFIX}TRUE_RANGE",
    f"{FEATURE_PREFIX}PRIOR_ATR_MEAN",
    f"{FEATURE_PREFIX}RANGE_EXPANSION",
    f"{FEATURE_PREFIX}CLOSE_LOCATION",
)


@dataclass(frozen=True)
class KrakenAIDrivenV2FeatureConfig:
    """Explicit research windows; no production defaults are implied."""

    decline_lookback_bars: int
    volume_lookback_bars: int
    atr_lookback_bars: int

    def __post_init__(self):
        for value, name in (
            (self.decline_lookback_bars, "Decline lookback"),
            (self.volume_lookback_bars, "Volume lookback"),
            (self.atr_lookback_bars, "ATR lookback"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")

    def configuration(self):
        return {
            **asdict(self),
            "observation_timing": "COMPLETED_DAILY_BAR_CLOSE",
            "execution_timing": "NOT_DEFINED_BY_FEATURE_CONTRACT",
            "baseline_current_bar_included": False,
            "future_bar_access": False,
            "signal_thresholds_frozen": False,
            "trading_actions_emitted": False,
        }


def _validated_continuous_daily_frame(data):
    if not isinstance(data, pd.DataFrame):
        raise TypeError("AI-driven v2 feature data must be a pandas DataFrame.")
    if data.empty:
        raise ValueError("AI-driven v2 feature data cannot be empty.")
    if tuple(data.columns) != REQUIRED_OHLCV_COLUMNS:
        raise ValueError(
            "AI-driven v2 feature data must contain exact ordered OHLCV "
            f"columns: {REQUIRED_OHLCV_COLUMNS}."
        )
    if not isinstance(data.index, pd.DatetimeIndex):
        raise TypeError("AI-driven v2 feature data must use a DatetimeIndex.")
    if data.index.tz is None:
        raise ValueError("AI-driven v2 feature timestamps must be timezone-aware.")
    if not data.index.is_monotonic_increasing:
        raise ValueError("AI-driven v2 feature timestamps must increase.")
    if data.index.has_duplicates:
        raise ValueError("AI-driven v2 feature timestamps must be unique.")

    frame = data.copy(deep=True)
    frame.index = frame.index.tz_convert("UTC")
    if any(
        timestamp.hour
        or timestamp.minute
        or timestamp.second
        or timestamp.microsecond
        or timestamp.nanosecond
        for timestamp in frame.index
    ):
        raise ValueError("AI-driven v2 feature timestamps must align to UTC midnight.")
    if len(frame.index) > 1:
        deltas = frame.index[1:] - frame.index[:-1]
        if any(delta != DAILY_STEP for delta in deltas):
            raise ValueError(
                "AI-driven v2 features require one continuous daily availability "
                "segment; split at every recorded gap before generation."
            )

    numeric = frame.loc[:, REQUIRED_OHLCV_COLUMNS].apply(
        pd.to_numeric, errors="coerce"
    )
    values = numeric.to_numpy(dtype=float)
    if numeric.isna().any().any() or not np.isfinite(values).all():
        raise ValueError("AI-driven v2 OHLCV values must be finite numeric data.")
    if (values[:, :4] <= 0.0).any() or (values[:, 4] < 0.0).any():
        raise ValueError(
            "AI-driven v2 prices must be positive and volume nonnegative."
        )

    open_values = values[:, 0]
    high_values = values[:, 1]
    low_values = values[:, 2]
    close_values = values[:, 3]
    if (
        (high_values < open_values).any()
        or (high_values < close_values).any()
        or (low_values > open_values).any()
        or (low_values > close_values).any()
        or (high_values < low_values).any()
    ):
        raise ValueError("AI-driven v2 OHLC price geometry is invalid.")
    return frame, numeric


class KrakenAIDrivenV2FeatureEngine:
    """Generate prefix-stable measurements from one completed daily segment."""

    def __init__(self, config):
        if not isinstance(config, KrakenAIDrivenV2FeatureConfig):
            raise TypeError(
                "AI-driven v2 features require KrakenAIDrivenV2FeatureConfig."
            )
        self.config = config

    def configuration(self):
        return {
            "feature_contract": "KRAKEN_AI_DRIVEN_V2_CAUSAL_FEATURES_V1",
            **self.config.configuration(),
            "feature_columns": list(FEATURE_COLUMNS),
            "prior_close_high_formula": "MAX(CLOSE.shift(1), decline_window)",
            "prior_volume_formula": "MEDIAN(VOLUME.shift(1), volume_window)",
            "prior_atr_formula": "MEAN(TRUE_RANGE.shift(1), atr_window)",
            "zero_volume_baseline_policy": "RELATIVE_VOLUME_UNAVAILABLE",
            "zero_range_policy": "CLOSE_LOCATION_UNAVAILABLE",
            "gap_policy": "SPLIT_BEFORE_FEATURE_GENERATION",
        }

    def generate(self, data):
        frame, numeric = _validated_continuous_daily_frame(data)
        config = self.config
        high = numeric["High"]
        low = numeric["Low"]
        close = numeric["Close"]
        volume = numeric["Volume"]

        previous_close = close.shift(1)
        close_return = close.div(previous_close).sub(1.0)
        prior_close_high = previous_close.rolling(
            window=config.decline_lookback_bars,
            min_periods=config.decline_lookback_bars,
        ).max()
        drawdown = prior_close_high.sub(close).div(prior_close_high).clip(lower=0.0)

        prior_volume_median = volume.shift(1).rolling(
            window=config.volume_lookback_bars,
            min_periods=config.volume_lookback_bars,
        ).median()
        usable_volume_baseline = prior_volume_median.where(prior_volume_median > 0.0)
        relative_volume = volume.div(usable_volume_baseline)

        true_range = pd.concat(
            (
                high.sub(low),
                high.sub(previous_close).abs(),
                low.sub(previous_close).abs(),
            ),
            axis=1,
        ).max(axis=1, skipna=True)
        prior_atr_mean = true_range.shift(1).rolling(
            window=config.atr_lookback_bars,
            min_periods=config.atr_lookback_bars,
        ).mean()
        usable_atr_baseline = prior_atr_mean.where(prior_atr_mean > 0.0)
        range_expansion = true_range.div(usable_atr_baseline)

        completed_range = high.sub(low)
        close_location = close.sub(low).div(completed_range.where(completed_range > 0.0))

        result = frame.copy(deep=True)
        result[FEATURE_COLUMNS[0]] = previous_close
        result[FEATURE_COLUMNS[1]] = close_return
        result[FEATURE_COLUMNS[2]] = prior_close_high
        result[FEATURE_COLUMNS[3]] = drawdown
        result[FEATURE_COLUMNS[4]] = prior_volume_median
        result[FEATURE_COLUMNS[5]] = relative_volume
        result[FEATURE_COLUMNS[6]] = true_range
        result[FEATURE_COLUMNS[7]] = prior_atr_mean
        result[FEATURE_COLUMNS[8]] = range_expansion
        result[FEATURE_COLUMNS[9]] = close_location

        return result
