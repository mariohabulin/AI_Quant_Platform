from dataclasses import dataclass


@dataclass(frozen=True)
class RiskDecision:
    status: str
    position_size: float
    monetary_risk: float
    risk_budget: float
    position_notional: float
    reason: str


class RiskEngine:
    """Deterministic long-position sizing from equity, risk and stop distance."""

    def __init__(self, risk_per_trade=0.01, max_position_fraction=1.0):
        self.risk_per_trade = self._validate_fraction(
            risk_per_trade, "Risk per trade", allow_zero=False
        )
        self.max_position_fraction = self._validate_fraction(
            max_position_fraction, "Max position fraction", allow_zero=False
        )

    @staticmethod
    def _validate_fraction(value, name, allow_zero):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be a number.")
        value = float(value)
        lower_invalid = value < 0 if allow_zero else value <= 0
        if lower_invalid or value > 1:
            raise ValueError(f"{name} must be greater than zero and at most 1.0.")
        return value

    @staticmethod
    def _positive(value, name):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be a number.")
        value = float(value)
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")
        return value

    def assess_long(self, equity, entry_price, stop_price):
        equity = self._positive(equity, "Equity")
        entry_price = self._positive(entry_price, "Entry price")
        stop_price = self._positive(stop_price, "Stop price")

        if stop_price >= entry_price:
            return RiskDecision("REJECT", 0.0, 0.0, equity * self.risk_per_trade,
                                0.0, "Long stop must be below entry price.")

        risk_budget = equity * self.risk_per_trade
        risk_per_unit = entry_price - stop_price
        risk_sized_units = risk_budget / risk_per_unit
        exposure_cap = equity * self.max_position_fraction
        exposure_sized_units = exposure_cap / entry_price
        position_size = min(risk_sized_units, exposure_sized_units)

        if position_size <= 0:
            return RiskDecision("REJECT", 0.0, 0.0, risk_budget, 0.0,
                                "No positive position size is available.")

        capped = exposure_sized_units < risk_sized_units
        status = "REDUCE" if capped else "ALLOW"
        reason = "Position reduced by exposure cap." if capped else "Risk sizing approved."
        monetary_risk = position_size * risk_per_unit
        notional = position_size * entry_price
        return RiskDecision(status, position_size, monetary_risk, risk_budget,
                            notional, reason)
