"""Causal price-trend features required by Alpha Discovery Protocol v1."""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CausalEMATrendStructure:
    """Completed-bar EMA structure with no centered or future observations."""

    fast_period: int = 50
    slow_period: int = 200
    slope_lookback: int = 4

    def __post_init__(self):
        for value, name in (
            (self.fast_period, "Fast EMA period"),
            (self.slow_period, "Slow EMA period"),
            (self.slope_lookback, "EMA slope lookback"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
        if self.fast_period >= self.slow_period:
            raise ValueError("Fast EMA period must be below slow EMA period.")

    def configuration(self):
        return {
            **asdict(self),
            "price_condition": f"CLOSE_ABOVE_EMA_{self.slow_period}",
            "slope_condition": (
                f"EMA_{self.fast_period}_ABOVE_VALUE_"
                f"{self.slope_lookback}_BARS_EARLIER"
            ),
            "observation_timing": "COMPLETED_BAR_CLOSE",
            "causal": True,
        }

    def generate(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")
        if "Close" not in data.columns:
            raise ValueError("Causal EMA trend structure requires Close.")
        if data.empty:
            raise ValueError("Input data cannot be empty.")
        if not data.index.is_monotonic_increasing or data.index.has_duplicates:
            raise ValueError("Input data must have a unique chronological index.")

        close = pd.to_numeric(data["Close"], errors="coerce")
        values = close.to_numpy(dtype=float)
        if close.isna().any() or not np.isfinite(values).all():
            raise ValueError("Close values must be finite numeric data.")
        if (close <= 0.0).any():
            raise ValueError("Close values must be positive.")

        fast = close.ewm(
            span=self.fast_period,
            adjust=False,
            min_periods=self.fast_period,
        ).mean()
        slow = close.ewm(
            span=self.slow_period,
            adjust=False,
            min_periods=self.slow_period,
        ).mean()
        slope = fast - fast.shift(self.slope_lookback)
        trend = slow.notna() & slope.notna() & close.gt(slow) & slope.gt(0.0)

        result = data.copy(deep=True)
        result[f"ALPHA_DISCOVERY_EMA_{self.fast_period}"] = fast
        result[f"ALPHA_DISCOVERY_EMA_{self.slow_period}"] = slow
        result[
            f"ALPHA_DISCOVERY_EMA_{self.fast_period}_SLOPE_"
            f"{self.slope_lookback}"
        ] = slope
        result["ALPHA_DISCOVERY_TREND_STRUCTURE"] = trend.astype(bool)
        return result
