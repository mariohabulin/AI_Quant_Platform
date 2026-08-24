"""Deterministic active stop/target decisions for long-only research fills."""

from dataclasses import asdict, dataclass
import math
from numbers import Real

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ProtectiveExitDecision:
    """One explicit hold or protective-exit decision for a known OHLC bar."""

    status: str
    exit_type: str | None = None
    market_price: float | None = None
    trigger_price: float | None = None
    fill_reference: str | None = None
    same_bar_conflict: bool = False

    def __post_init__(self):
        if self.status not in ("HOLD", "EXIT"):
            raise ValueError("Protective decision status must be HOLD or EXIT.")
        if self.status == "HOLD":
            if any(
                value is not None
                for value in (
                    self.exit_type,
                    self.market_price,
                    self.trigger_price,
                    self.fill_reference,
                )
            ):
                raise ValueError("HOLD decisions cannot contain exit evidence.")
            if self.same_bar_conflict:
                raise ValueError("HOLD decisions cannot contain a touch conflict.")
            return
        if self.exit_type not in (
            "STOP_GAP",
            "TARGET_GAP",
            "STOP_INTRABAR",
            "TARGET_INTRABAR",
        ):
            raise ValueError("Protective exit type is invalid.")
        for value, name in (
            (self.market_price, "Protective market price"),
            (self.trigger_price, "Protective trigger price"),
        ):
            if not isinstance(value, Real) or isinstance(value, bool):
                raise TypeError(f"{name} must be numeric.")
            if not math.isfinite(float(value)) or float(value) <= 0.0:
                raise ValueError(f"{name} must be positive and finite.")
        if not isinstance(self.fill_reference, str) or not self.fill_reference:
            raise ValueError("Protective fill reference is required.")

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ProtectiveExitPolicy:
    """Freeze conservative long stop/target semantics before evaluation."""

    risk_distance_column: str = "ALPHA_V2_ATR_RISK_DISTANCE"
    reward_risk_ratio: float = 3.0
    reward_risk_ratio_column: str = "ALPHA_V2_REWARD_RISK_RATIO"
    stop_and_target_same_bar: str = "STOP_FIRST"
    stop_gap_fill: str = "OPEN"
    target_gap_fill: str = "TARGET"
    entry_bar_protection: bool = True

    def __post_init__(self):
        for value, name in (
            (self.risk_distance_column, "Risk-distance column"),
            (self.reward_risk_ratio_column, "Reward/risk column"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")
        if not isinstance(self.reward_risk_ratio, Real) or isinstance(
            self.reward_risk_ratio, bool
        ):
            raise TypeError("Reward/risk ratio must be numeric.")
        if (
            not math.isfinite(float(self.reward_risk_ratio))
            or float(self.reward_risk_ratio) <= 0.0
        ):
            raise ValueError("Reward/risk ratio must be positive and finite.")
        if self.stop_and_target_same_bar != "STOP_FIRST":
            raise ValueError("Protocol v1 requires STOP_FIRST same-bar ordering.")
        if self.stop_gap_fill != "OPEN":
            raise ValueError("Protocol v1 requires OPEN stop-gap fills.")
        if self.target_gap_fill != "TARGET":
            raise ValueError("Protocol v1 requires conservative TARGET gap fills.")
        if self.entry_bar_protection is not True:
            raise ValueError("Protocol v1 requires entry-bar protection.")

    @staticmethod
    def _positive_finite(value, name):
        if not isinstance(value, Real) or isinstance(value, bool):
            raise TypeError(f"{name} must be numeric.")
        value = float(value)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be positive and finite.")
        return value

    def resolve_levels(self, entry_price, signal_row):
        """Resolve active levels from lagged signal evidence and current open."""

        entry_price = self._positive_finite(entry_price, "Entry price")
        if self.risk_distance_column not in signal_row:
            raise ValueError(
                "Protective exits require signal-bar column "
                f"'{self.risk_distance_column}'."
            )
        if self.reward_risk_ratio_column not in signal_row:
            raise ValueError(
                "Protective exits require signal-bar column "
                f"'{self.reward_risk_ratio_column}'."
            )
        risk_distance = self._positive_finite(
            signal_row[self.risk_distance_column], "Signal-bar risk distance"
        )
        observed_ratio = self._positive_finite(
            signal_row[self.reward_risk_ratio_column],
            "Signal-bar reward/risk ratio",
        )
        if not math.isclose(
            observed_ratio,
            float(self.reward_risk_ratio),
            rel_tol=1e-12,
            abs_tol=0.0,
        ):
            raise ValueError("Signal-bar reward/risk ratio changed from policy.")
        stop_price = entry_price - risk_distance
        if stop_price <= 0.0:
            raise ValueError("Resolved protective stop must be positive.")
        target_price = entry_price + risk_distance * observed_ratio
        return {
            "entry_price": entry_price,
            "risk_distance": risk_distance,
            "stop_price": stop_price,
            "target_price": target_price,
            "reward_risk_ratio": observed_ratio,
            "source": "SIGNAL_BAR_DISTANCE_EXECUTION_OPEN_LEVELS",
        }

    @classmethod
    def validate_market_data(cls, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Protective-exit market data must be a DataFrame.")
        required = ("Open", "High", "Low", "Close")
        missing = [column for column in required if column not in data.columns]
        if missing:
            raise ValueError(f"Protective exits require OHLC columns: {missing}")
        numeric = data[list(required)].apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any() or not np.isfinite(
            numeric.to_numpy(dtype=float)
        ).all():
            raise ValueError("Protective-exit OHLC values must be finite numeric data.")
        if (numeric <= 0.0).any().any():
            raise ValueError("Protective-exit OHLC values must be positive.")
        maximum = numeric[["Open", "Low", "Close"]].max(axis=1)
        minimum = numeric[["Open", "High", "Close"]].min(axis=1)
        if (numeric["High"] < maximum).any() or (numeric["Low"] > minimum).any():
            raise ValueError("Protective-exit OHLC geometry is invalid.")

    def evaluate_long_open(self, open_price, stop_price, target_price):
        """Resolve only gaps that already exist at the current bar open."""

        open_price = self._positive_finite(open_price, "Open price")
        stop_price = self._positive_finite(stop_price, "Stop price")
        target_price = self._positive_finite(target_price, "Target price")
        if stop_price >= target_price:
            raise ValueError("Protective stop must be below target.")
        if open_price <= stop_price:
            return ProtectiveExitDecision(
                status="EXIT",
                exit_type="STOP_GAP",
                market_price=open_price,
                trigger_price=stop_price,
                fill_reference="FIRST_AVAILABLE_OPEN",
            )
        if open_price >= target_price:
            return ProtectiveExitDecision(
                status="EXIT",
                exit_type="TARGET_GAP",
                market_price=target_price,
                trigger_price=target_price,
                fill_reference="CONSERVATIVE_TARGET_PRICE",
            )
        return ProtectiveExitDecision(status="HOLD")

    def evaluate_long_intrabar(self, high_price, low_price, stop_price, target_price):
        """Resolve touches after open; ambiguous bars always stop first."""

        high_price = self._positive_finite(high_price, "High price")
        low_price = self._positive_finite(low_price, "Low price")
        stop_price = self._positive_finite(stop_price, "Stop price")
        target_price = self._positive_finite(target_price, "Target price")
        if high_price < low_price:
            raise ValueError("High price must not be below Low price.")
        if stop_price >= target_price:
            raise ValueError("Protective stop must be below target.")
        stop_hit = low_price <= stop_price
        target_hit = high_price >= target_price
        if stop_hit:
            return ProtectiveExitDecision(
                status="EXIT",
                exit_type="STOP_INTRABAR",
                market_price=stop_price,
                trigger_price=stop_price,
                fill_reference="STOP_TRIGGER_PRICE",
                same_bar_conflict=bool(target_hit),
            )
        if target_hit:
            return ProtectiveExitDecision(
                status="EXIT",
                exit_type="TARGET_INTRABAR",
                market_price=target_price,
                trigger_price=target_price,
                fill_reference="TARGET_TRIGGER_PRICE",
            )
        return ProtectiveExitDecision(status="HOLD")

    def as_dict(self):
        return {
            **asdict(self),
            "signal_observation": "COMPLETED_BAR_CLOSE",
            "entry_execution": "FOLLOWING_BAR_OPEN",
            "level_resolution": "SIGNAL_BAR_DISTANCE_FROM_EXECUTION_OPEN",
            "protective_costs": "NORMAL_SELL_COMMISSION_SLIPPAGE_SPREAD",
        }
