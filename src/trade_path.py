"""Causal, compact post-entry trade-path evidence for long positions."""

from dataclasses import dataclass, field
import math
from numbers import Real


@dataclass
class LongTradePathTracker:
    """Track only price evidence observable while a long position is active."""

    entry_bar_position: int
    entry_index: object
    entry_price: float
    risk_distance: float
    shares: float
    maximum_favorable_excursion: float = field(init=False, default=0.0)
    maximum_adverse_excursion: float = field(init=False, default=0.0)
    maximum_favorable_bar_position: int = field(init=False)
    maximum_favorable_index: object = field(init=False)

    def __post_init__(self):
        if (
            not isinstance(self.entry_bar_position, int)
            or isinstance(self.entry_bar_position, bool)
            or self.entry_bar_position < 0
        ):
            raise ValueError("Entry bar position must be a nonnegative integer.")
        self.entry_price = self._positive(self.entry_price, "Entry price")
        self.risk_distance = self._positive(
            self.risk_distance, "Initial risk distance"
        )
        self.shares = self._positive(self.shares, "Shares")
        self.maximum_favorable_bar_position = self.entry_bar_position
        self.maximum_favorable_index = self.entry_index

    @staticmethod
    def _positive(value, name):
        if not isinstance(value, Real) or isinstance(value, bool):
            raise TypeError(f"{name} must be numeric.")
        value = float(value)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be positive and finite.")
        return value

    def _validated_position(self, bar_position):
        if (
            not isinstance(bar_position, int)
            or isinstance(bar_position, bool)
            or bar_position < self.entry_bar_position
        ):
            raise ValueError("Observed bar cannot precede the entry bar.")
        return bar_position

    def observe_price(self, price, bar_position, index):
        price = self._positive(price, "Observed price")
        bar_position = self._validated_position(bar_position)
        favorable = max(0.0, price - self.entry_price)
        adverse = max(0.0, self.entry_price - price)
        if favorable > self.maximum_favorable_excursion:
            self.maximum_favorable_excursion = favorable
            self.maximum_favorable_bar_position = bar_position
            self.maximum_favorable_index = index
        self.maximum_adverse_excursion = max(
            self.maximum_adverse_excursion, adverse
        )

    def observe_surviving_bar(self, high_price, low_price, bar_position, index):
        high_price = self._positive(high_price, "Observed High")
        low_price = self._positive(low_price, "Observed Low")
        if high_price < low_price:
            raise ValueError("Observed High must not be below Low.")
        self.observe_price(high_price, bar_position, index)
        self.observe_price(low_price, bar_position, index)

    def close(self, exit_bar_position, gross_profit_loss, net_profit_loss):
        exit_bar_position = self._validated_position(exit_bar_position)
        for value, name in (
            (gross_profit_loss, "Gross profit/loss"),
            (net_profit_loss, "Net profit/loss"),
        ):
            if not isinstance(value, Real) or isinstance(value, bool):
                raise TypeError(f"{name} must be numeric.")
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")
        initial_monetary_risk = self.shares * self.risk_distance
        return {
            "maximum_favorable_excursion_r": (
                self.maximum_favorable_excursion / self.risk_distance
            ),
            "maximum_adverse_excursion_r": (
                self.maximum_adverse_excursion / self.risk_distance
            ),
            "realized_r": float(net_profit_loss) / initial_monetary_risk,
            "gross_realized_r": (
                float(gross_profit_loss) / initial_monetary_risk
            ),
            "holding_bars": exit_bar_position - self.entry_bar_position,
            "bars_to_maximum_favorable_excursion": (
                self.maximum_favorable_bar_position - self.entry_bar_position
            ),
            "maximum_favorable_excursion_index": self.maximum_favorable_index,
            "initial_risk_distance": self.risk_distance,
            "initial_monetary_risk": initial_monetary_risk,
            "trade_path_observation_policy": (
                "SURVIVING_BAR_EXTREMA_EXIT_BAR_EXECUTABLE_PATH_ONLY"
            ),
        }
