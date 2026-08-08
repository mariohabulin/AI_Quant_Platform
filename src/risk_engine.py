from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class RiskDecision:
    status: str
    position_size: float
    monetary_risk: float
    risk_budget: float
    position_notional: float
    reason: str


@dataclass(frozen=True)
class ProtectionDecision:
    status: str
    reason: str
    drawdown: float
    daily_loss: float
    weekly_loss: float
    kill_switch_active: bool


class RiskEngine:
    """Deterministic long-position sizing from equity, risk and stop distance."""

    def __init__(
        self, risk_per_trade=0.01, max_position_fraction=1.0,
        max_drawdown_fraction=None, daily_loss_limit=None, weekly_loss_limit=None,
    ):
        self.risk_per_trade = self._validate_fraction(
            risk_per_trade, "Risk per trade", allow_zero=False
        )
        self.max_position_fraction = self._validate_fraction(
            max_position_fraction, "Max position fraction", allow_zero=False
        )
        self.max_drawdown_fraction = self._optional_fraction(max_drawdown_fraction, "Max drawdown fraction")
        self.daily_loss_limit = self._optional_fraction(daily_loss_limit, "Daily loss limit")
        self.weekly_loss_limit = self._optional_fraction(weekly_loss_limit, "Weekly loss limit")
        self.reset_protection_state()

    @staticmethod
    def _validate_fraction(value, name, allow_zero):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be a number.")
        value = float(value)
        lower_invalid = value < 0 if allow_zero else value <= 0
        if lower_invalid or value > 1:
            raise ValueError(f"{name} must be greater than zero and at most 1.0.")
        return value


    @classmethod
    def _optional_fraction(cls, value, name):
        if value is None:
            return None
        return cls._validate_fraction(value, name, allow_zero=False)

    def reset_protection_state(self):
        self.peak_equity = None
        self.day_key = None
        self.day_start_equity = None
        self.week_key = None
        self.week_start_equity = None
        self.kill_switch_active = False
        self.kill_switch_reason = None

    @staticmethod
    def _period_keys(index):
        try:
            ts = pd.Timestamp(index)
        except Exception as exc:
            raise TypeError("Protection guards require a datetime-like index.") from exc
        if pd.isna(ts):
            raise ValueError("Protection guards require a valid datetime-like index.")
        iso = ts.isocalendar()
        return ts.date(), (int(iso.year), int(iso.week))

    def protection_enabled(self):
        return any(v is not None for v in (
            self.max_drawdown_fraction, self.daily_loss_limit, self.weekly_loss_limit
        ))

    def observe_equity(self, equity, index):
        equity = self._positive(equity, "Equity")
        if not self.protection_enabled():
            return ProtectionDecision("ALLOW", "Protection guards disabled.", 0.0, 0.0, 0.0, False)

        day_key, week_key = self._period_keys(index)
        if self.peak_equity is None:
            self.peak_equity = equity
        self.peak_equity = max(self.peak_equity, equity)

        if self.day_key != day_key:
            self.day_key, self.day_start_equity = day_key, equity
        if self.week_key != week_key:
            self.week_key, self.week_start_equity = week_key, equity

        drawdown = max(0.0, (self.peak_equity - equity) / self.peak_equity)
        daily_loss = max(0.0, (self.day_start_equity - equity) / self.day_start_equity)
        weekly_loss = max(0.0, (self.week_start_equity - equity) / self.week_start_equity)

        if self.max_drawdown_fraction is not None and drawdown >= self.max_drawdown_fraction:
            self.kill_switch_active = True
            self.kill_switch_reason = "Maximum drawdown limit reached."

        if self.kill_switch_active:
            return ProtectionDecision("REJECT", self.kill_switch_reason, drawdown, daily_loss, weekly_loss, True)
        if self.daily_loss_limit is not None and daily_loss >= self.daily_loss_limit:
            return ProtectionDecision("REJECT", "Daily loss limit reached.", drawdown, daily_loss, weekly_loss, False)
        if self.weekly_loss_limit is not None and weekly_loss >= self.weekly_loss_limit:
            return ProtectionDecision("REJECT", "Weekly loss limit reached.", drawdown, daily_loss, weekly_loss, False)
        return ProtectionDecision("ALLOW", "Protection guards allow new risk.", drawdown, daily_loss, weekly_loss, False)

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
