"""Cost-aware synthetic risk and execution adapter for Kraken AI-driven v2."""

from dataclasses import asdict, dataclass, replace
import math
from numbers import Real

import pandas as pd

try:
    from kraken_ai_driven_v2_features import FEATURE_COLUMNS
    from kraken_ai_driven_v2_state_machine import (
        ACTION_INTENT_COLUMN,
        INTENT_ENTER_NEXT_OPEN,
        INTENT_EXIT_NEXT_OPEN,
        INTENT_NONE,
        SETUP_LOW_COLUMN,
        STATE_AFTER_COLUMN,
        STATE_LONG,
        TRANSITION_COLUMN,
    )
    from protective_exit import ProtectiveExitPolicy
    from risk_engine import RiskEngine
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_features import FEATURE_COLUMNS
    from .kraken_ai_driven_v2_state_machine import (
        ACTION_INTENT_COLUMN,
        INTENT_ENTER_NEXT_OPEN,
        INTENT_EXIT_NEXT_OPEN,
        INTENT_NONE,
        SETUP_LOW_COLUMN,
        STATE_AFTER_COLUMN,
        STATE_LONG,
        TRANSITION_COLUMN,
    )
    from .protective_exit import ProtectiveExitPolicy
    from .risk_engine import RiskEngine


RISK_EXECUTION_POLICY_ID = "kraken-ai-v2-risk-execution-reference-a-v1"
COST_PROFILE_ID = "kraken-tier1-taker-adverse-20260829-v1"
PENDING_STATE_EXIT = "STATE_SIGNAL_EXIT"
PENDING_MAX_HOLD_EXIT = "MAXIMUM_HOLD_EXIT"
PENDING_STATE_AND_MAX_HOLD_EXIT = "STATE_AND_MAXIMUM_HOLD_EXIT"
VALID_PENDING_EXITS = (
    PENDING_STATE_EXIT,
    PENDING_MAX_HOLD_EXIT,
    PENDING_STATE_AND_MAX_HOLD_EXIT,
)


def _finite_number(value, name):
    if not isinstance(value, Real) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric.")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def _positive_number(value, name):
    value = _finite_number(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return value


def _nonnegative_number(value, name):
    value = _finite_number(value, name)
    if value < 0.0:
        raise ValueError(f"{name} must be nonnegative.")
    return value


def _fraction(value, name, *, allow_zero=False):
    value = _finite_number(value, name)
    invalid = value < 0.0 if allow_zero else value <= 0.0
    if invalid or value > 1.0:
        qualifier = "nonnegative" if allow_zero else "positive"
        raise ValueError(f"{name} must be {qualifier} and at most 1.0.")
    return value


def _utc_timestamp(value, name):
    try:
        timestamp = pd.Timestamp(value)
    except Exception as exc:
        raise TypeError(f"{name} must be datetime-like.") from exc
    if pd.isna(timestamp):
        raise ValueError(f"{name} must be a valid timestamp.")
    if timestamp.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware.")
    timestamp = timestamp.tz_convert("UTC")
    if any(
        (
            timestamp.hour,
            timestamp.minute,
            timestamp.second,
            timestamp.microsecond,
            timestamp.nanosecond,
        )
    ):
        raise ValueError(f"{name} must align to UTC midnight.")
    return timestamp


@dataclass(frozen=True)
class KrakenV2ExecutionCostProfile:
    """Frozen adverse Tier-1 taker assumptions for synthetic fills."""

    profile_id: str = COST_PROFILE_ID
    venue: str = "Kraken Pro Spot"
    order_role: str = "TAKER"
    commission_rate: float = 0.008
    slippage_rate: float = 0.0015
    full_spread_rate: float = 0.0030
    official_fee_source: str = "https://www.kraken.com/features/fee-schedule"
    official_fee_reviewed_utc: str = "2026-08-29"

    def __post_init__(self):
        for value, name in (
            (self.profile_id, "Cost-profile ID"),
            (self.venue, "Venue"),
            (self.order_role, "Order role"),
            (self.official_fee_source, "Official fee source"),
            (self.official_fee_reviewed_utc, "Official fee review date"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string.")
        if self.order_role != "TAKER":
            raise ValueError("Reference cost profile requires TAKER execution.")
        for value, name in (
            (self.commission_rate, "Commission rate"),
            (self.slippage_rate, "Slippage rate"),
            (self.full_spread_rate, "Full spread rate"),
        ):
            _fraction(value, name, allow_zero=True)
        if self.profile_id == COST_PROFILE_ID:
            expected = {
                "venue": "Kraken Pro Spot",
                "order_role": "TAKER",
                "commission_rate": 0.008,
                "slippage_rate": 0.0015,
                "full_spread_rate": 0.0030,
                "official_fee_source": (
                    "https://www.kraken.com/features/fee-schedule"
                ),
                "official_fee_reviewed_utc": "2026-08-29",
            }
            observed = asdict(self)
            observed.pop("profile_id")
            if observed != expected:
                raise ValueError(
                    "Reference cost-profile values are immutable; use a new "
                    "profile ID for another reviewed assumption."
                )

    @property
    def adverse_price_rate(self):
        return float(self.slippage_rate) + float(self.full_spread_rate) / 2.0

    def buy_fill(self, market_reference):
        market_reference = _positive_number(market_reference, "Buy reference")
        return market_reference * (1.0 + self.adverse_price_rate)

    def sell_fill(self, market_reference):
        market_reference = _positive_number(market_reference, "Sell reference")
        return market_reference * (1.0 - self.adverse_price_rate)

    def commission(self, fill_price, units):
        fill_price = _positive_number(fill_price, "Commission fill price")
        units = _positive_number(units, "Commission units")
        return fill_price * units * float(self.commission_rate)

    def configuration(self):
        return {
            **asdict(self),
            "adverse_price_rate_per_side": self.adverse_price_rate,
            "maker_model_permitted": False,
            "account_fee_tier_verified": False,
            "spread_and_slippage_are_research_assumptions": True,
        }


REFERENCE_COST_PROFILE = KrakenV2ExecutionCostProfile()


@dataclass(frozen=True)
class KrakenV2RiskExecutionPolicy:
    """Frozen risk and timing gates for synthetic reference-A execution."""

    policy_id: str = RISK_EXECUTION_POLICY_ID
    risk_per_trade_fraction: float = 0.005
    maximum_total_open_risk_fraction: float = 0.015
    maximum_position_fraction: float = 1.0 / 3.0
    maximum_crypto_positions: int = 3
    minimum_net_reward_risk: float = 3.0
    maximum_entry_gap_up_atr: float = 0.5
    maximum_holding_completed_bars: int = 20
    cost_profile: KrakenV2ExecutionCostProfile = REFERENCE_COST_PROFILE

    def __post_init__(self):
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise ValueError("Risk/execution policy ID must be a nonempty string.")
        for value, name in (
            (self.risk_per_trade_fraction, "Risk per trade"),
            (self.maximum_total_open_risk_fraction, "Maximum total open risk"),
            (self.maximum_position_fraction, "Maximum position fraction"),
        ):
            _fraction(value, name)
        if self.risk_per_trade_fraction > self.maximum_total_open_risk_fraction:
            raise ValueError("Risk per trade cannot exceed total open-risk limit.")
        for value, name in (
            (self.maximum_crypto_positions, "Maximum crypto positions"),
            (self.maximum_holding_completed_bars, "Maximum holding bars"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
        _positive_number(self.minimum_net_reward_risk, "Minimum net reward/risk")
        _positive_number(self.maximum_entry_gap_up_atr, "Maximum entry gap ATR")
        if not isinstance(self.cost_profile, KrakenV2ExecutionCostProfile):
            raise TypeError("Policy cost profile is invalid.")
        if self.policy_id == RISK_EXECUTION_POLICY_ID:
            expected = {
                "risk_per_trade_fraction": 0.005,
                "maximum_total_open_risk_fraction": 0.015,
                "maximum_position_fraction": 1.0 / 3.0,
                "maximum_crypto_positions": 3,
                "minimum_net_reward_risk": 3.0,
                "maximum_entry_gap_up_atr": 0.5,
                "maximum_holding_completed_bars": 20,
                "cost_profile": REFERENCE_COST_PROFILE,
            }
            observed = {
                key: getattr(self, key)
                for key in expected
            }
            if observed != expected:
                raise ValueError(
                    "Reference risk/execution values are immutable; use a new "
                    "policy ID for another pre-registered hypothesis."
                )

    def configuration(self):
        return {
            "policy_id": self.policy_id,
            "risk_per_trade_fraction": self.risk_per_trade_fraction,
            "maximum_total_open_risk_fraction": (
                self.maximum_total_open_risk_fraction
            ),
            "maximum_position_fraction": self.maximum_position_fraction,
            "maximum_crypto_positions": self.maximum_crypto_positions,
            "minimum_net_reward_risk": self.minimum_net_reward_risk,
            "maximum_entry_gap_up_atr": self.maximum_entry_gap_up_atr,
            "maximum_holding_completed_bars": (
                self.maximum_holding_completed_bars
            ),
            "entry_execution": "FOLLOWING_DAILY_OPEN",
            "stop_trigger_source": "STATE_MACHINE_FIXED_SETUP_LOW",
            "target_trigger_source": "SIGNAL_BAR_PRIOR_CLOSE_HIGH",
            "protective_open_priority": [
                "STOP_GAP",
                "TARGET_GAP",
                "SCHEDULED_EXIT",
                "HOLD",
            ],
            "protective_intrabar_priority": [
                "STOP_TOUCH",
                "TARGET_TOUCH",
                "HOLD",
            ],
            "same_bar_stop_target": "STOP_FIRST",
            "entry_bar_protection": True,
            "break_even_stop": False,
            "trailing_stop": False,
            "partial_exit": False,
            "real_order_submission": False,
            "performance_evaluation": False,
            "cost_profile": self.cost_profile.configuration(),
        }


REFERENCE_RISK_EXECUTION_POLICY = KrakenV2RiskExecutionPolicy()


@dataclass(frozen=True)
class SyntheticEntryPlan:
    status: str
    reason: str
    policy_id: str
    cost_profile_id: str
    signal_timestamp: str | None = None
    execution_timestamp: str | None = None
    raw_open_price: float | None = None
    entry_fill_price: float | None = None
    stop_trigger_price: float | None = None
    stop_fill_assumption: float | None = None
    target_trigger_price: float | None = None
    required_target_for_minimum_r: float | None = None
    net_risk_per_unit: float | None = None
    net_reward_per_unit: float | None = None
    net_reward_risk_ratio: float | None = None
    risk_budget: float = 0.0
    position_size: float = 0.0
    position_notional: float = 0.0
    cash_required: float = 0.0
    planned_monetary_risk: float = 0.0
    planned_net_reward: float = 0.0
    planned_entry_commission: float = 0.0
    planned_stop_commission: float = 0.0
    risk_engine_status: str | None = None
    real_order_submitted: bool = False
    performance_evaluation_executed: bool = False

    def __post_init__(self):
        if self.status not in ("APPROVED_SYNTHETIC_ENTRY_PLAN", "NO_TRADE_HOLD_CASH"):
            raise ValueError("Synthetic entry-plan status is invalid.")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("Synthetic entry-plan reason is required.")
        if self.real_order_submitted or self.performance_evaluation_executed:
            raise ValueError("Synthetic entry plans cannot execute or evaluate.")

    @property
    def approved(self):
        return self.status == "APPROVED_SYNTHETIC_ENTRY_PLAN"

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SyntheticResearchPosition:
    policy_id: str
    cost_profile_id: str
    entry_timestamp: pd.Timestamp
    units: float
    entry_fill_price: float
    entry_commission: float
    stop_trigger_price: float
    target_trigger_price: float
    bars_held: int = 0

    def __post_init__(self):
        if self.policy_id != RISK_EXECUTION_POLICY_ID:
            raise ValueError("Synthetic position policy identity mismatch.")
        if self.cost_profile_id != COST_PROFILE_ID:
            raise ValueError("Synthetic position cost identity mismatch.")
        _utc_timestamp(self.entry_timestamp, "Synthetic entry timestamp")
        for value, name in (
            (self.units, "Synthetic position units"),
            (self.entry_fill_price, "Synthetic entry fill"),
            (self.stop_trigger_price, "Synthetic stop trigger"),
            (self.target_trigger_price, "Synthetic target trigger"),
        ):
            _positive_number(value, name)
        _nonnegative_number(self.entry_commission, "Synthetic entry commission")
        if not self.stop_trigger_price < self.entry_fill_price < self.target_trigger_price:
            raise ValueError("Synthetic position levels are not ordered.")
        if not isinstance(self.bars_held, int) or isinstance(self.bars_held, bool):
            raise TypeError("Synthetic bars held must be an integer.")
        if self.bars_held < 0:
            raise ValueError("Synthetic bars held cannot be negative.")

    def as_dict(self):
        payload = asdict(self)
        payload["entry_timestamp"] = self.entry_timestamp.isoformat()
        return payload


@dataclass(frozen=True)
class SyntheticExitDecision:
    status: str
    reason: str
    exit_type: str | None = None
    market_reference_price: float | None = None
    trigger_price: float | None = None
    fill_price: float | None = None
    commission: float = 0.0
    net_proceeds: float = 0.0
    same_bar_conflict: bool = False
    real_order_submitted: bool = False
    performance_evaluation_executed: bool = False

    def __post_init__(self):
        if self.status not in ("HOLD", "SYNTHETIC_EXIT"):
            raise ValueError("Synthetic exit status is invalid.")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("Synthetic exit reason is required.")
        if self.real_order_submitted or self.performance_evaluation_executed:
            raise ValueError("Synthetic exits cannot execute or evaluate.")
        if self.status == "HOLD" and any(
            value is not None
            for value in (
                self.exit_type,
                self.market_reference_price,
                self.trigger_price,
                self.fill_price,
            )
        ):
            raise ValueError("HOLD cannot contain exit evidence.")

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class CompletedBarExitSchedule:
    status: str
    reason: str
    pending_exit_reason: str | None
    updated_position: SyntheticResearchPosition
    real_order_submitted: bool = False

    def __post_init__(self):
        if self.status not in ("HOLD", "SCHEDULE_EXIT_NEXT_OPEN"):
            raise ValueError("Completed-bar schedule status is invalid.")
        if self.real_order_submitted:
            raise ValueError("Completed-bar schedule cannot submit an order.")

    def as_dict(self):
        result = asdict(self)
        result["updated_position"] = self.updated_position.as_dict()
        return result


class KrakenAIDrivenV2RiskExecutionAdapter:
    """Translate frozen state intents into cost-aware synthetic plans."""

    REWARD_RISK_REL_TOLERANCE = 1e-12

    def __init__(self, policy=REFERENCE_RISK_EXECUTION_POLICY):
        if not isinstance(policy, KrakenV2RiskExecutionPolicy):
            raise TypeError("Risk/execution adapter policy is invalid.")
        self.policy = policy
        self.costs = policy.cost_profile
        self.protective_policy = ProtectiveExitPolicy(
            reward_risk_ratio=policy.minimum_net_reward_risk,
            breakeven_trigger_r=None,
        )

    def configuration(self):
        return self.policy.configuration()

    def _no_trade(self, reason, **evidence):
        return SyntheticEntryPlan(
            status="NO_TRADE_HOLD_CASH",
            reason=reason,
            policy_id=self.policy.policy_id,
            cost_profile_id=self.costs.profile_id,
            **evidence,
        )

    @staticmethod
    def _required_signal_values(signal_row):
        if not isinstance(signal_row, pd.Series):
            raise TypeError("Entry signal evidence must be a pandas Series.")
        required = (
            ACTION_INTENT_COLUMN,
            STATE_AFTER_COLUMN,
            TRANSITION_COLUMN,
            SETUP_LOW_COLUMN,
            FEATURE_COLUMNS[2],
            FEATURE_COLUMNS[7],
            "Close",
        )
        missing = [column for column in required if column not in signal_row]
        if missing:
            raise ValueError(f"Entry signal evidence is missing columns: {missing}")
        signal_timestamp = _utc_timestamp(signal_row.name, "Signal timestamp")
        setup_low = _positive_number(signal_row[SETUP_LOW_COLUMN], "Setup low")
        resistance = _positive_number(
            signal_row[FEATURE_COLUMNS[2]], "Causal prior-close resistance"
        )
        prior_atr = _positive_number(signal_row[FEATURE_COLUMNS[7]], "Prior ATR")
        signal_close = _positive_number(signal_row["Close"], "Signal close")
        return signal_timestamp, setup_low, resistance, prior_atr, signal_close

    def plan_entry(
        self,
        signal_row,
        *,
        execution_timestamp,
        next_open_price,
        equity,
        available_cash,
        current_open_risk_amount,
        open_crypto_positions,
    ):
        signal_timestamp, setup_low, resistance, prior_atr, signal_close = (
            self._required_signal_values(signal_row)
        )
        execution_timestamp = _utc_timestamp(
            execution_timestamp, "Entry execution timestamp"
        )
        if execution_timestamp != signal_timestamp + pd.Timedelta(days=1):
            raise ValueError("Entry execution must use the immediately following day.")
        raw_open = _positive_number(next_open_price, "Next open price")
        equity = _positive_number(equity, "Current equity")
        available_cash = _nonnegative_number(available_cash, "Available cash")
        current_open_risk = _nonnegative_number(
            current_open_risk_amount, "Current open risk"
        )
        if (
            not isinstance(open_crypto_positions, int)
            or isinstance(open_crypto_positions, bool)
            or open_crypto_positions < 0
        ):
            raise ValueError("Open crypto-position count must be a nonnegative integer.")

        common = {
            "signal_timestamp": signal_timestamp.isoformat(),
            "execution_timestamp": execution_timestamp.isoformat(),
            "raw_open_price": raw_open,
        }
        if (
            signal_row[ACTION_INTENT_COLUMN] != INTENT_ENTER_NEXT_OPEN
            or signal_row[STATE_AFTER_COLUMN] != STATE_LONG
            or signal_row[TRANSITION_COLUMN] != "CONFIRMATION_LONG"
        ):
            return self._no_trade("SIGNAL_INTENT_NOT_ENTRY_ELIGIBLE", **common)
        if open_crypto_positions >= self.policy.maximum_crypto_positions:
            return self._no_trade("CRYPTO_POSITION_CAPACITY_EXHAUSTED", **common)

        total_risk_limit = equity * self.policy.maximum_total_open_risk_fraction
        remaining_risk_capacity = total_risk_limit - current_open_risk
        if remaining_risk_capacity <= 0.0:
            return self._no_trade("TOTAL_OPEN_RISK_CAPACITY_EXHAUSTED", **common)
        risk_budget = min(
            equity * self.policy.risk_per_trade_fraction,
            remaining_risk_capacity,
        )
        if raw_open <= setup_low:
            return self._no_trade(
                "ENTRY_OPEN_AT_OR_BELOW_STRUCTURAL_STOP",
                risk_budget=risk_budget,
                stop_trigger_price=setup_low,
                **common,
            )
        if raw_open > signal_close + prior_atr * self.policy.maximum_entry_gap_up_atr:
            return self._no_trade(
                "ENTRY_UPWARD_GAP_EXCEEDS_ATR_LIMIT",
                risk_budget=risk_budget,
                stop_trigger_price=setup_low,
                target_trigger_price=resistance,
                **common,
            )

        entry_fill = self.costs.buy_fill(raw_open)
        if entry_fill <= setup_low:
            return self._no_trade(
                "COST_ADJUSTED_ENTRY_NOT_ABOVE_STOP",
                risk_budget=risk_budget,
                entry_fill_price=entry_fill,
                stop_trigger_price=setup_low,
                **common,
            )
        if resistance <= entry_fill:
            return self._no_trade(
                "CAUSAL_RESISTANCE_NOT_ABOVE_ENTRY",
                risk_budget=risk_budget,
                entry_fill_price=entry_fill,
                stop_trigger_price=setup_low,
                target_trigger_price=resistance,
                **common,
            )

        entry_cash_per_unit = entry_fill * (1.0 + self.costs.commission_rate)
        stop_fill = self.costs.sell_fill(setup_low)
        stop_proceeds_per_unit = stop_fill * (1.0 - self.costs.commission_rate)
        net_risk_per_unit = entry_cash_per_unit - stop_proceeds_per_unit
        if net_risk_per_unit <= 0.0:
            return self._no_trade(
                "NO_POSITIVE_COST_AWARE_RISK_DISTANCE",
                risk_budget=risk_budget,
                entry_fill_price=entry_fill,
                stop_trigger_price=setup_low,
                stop_fill_assumption=stop_fill,
                target_trigger_price=resistance,
                **common,
            )

        target_fill = self.costs.sell_fill(resistance)
        target_proceeds_per_unit = target_fill * (1.0 - self.costs.commission_rate)
        net_reward_per_unit = target_proceeds_per_unit - entry_cash_per_unit
        net_reward_risk = net_reward_per_unit / net_risk_per_unit
        required_target = (
            entry_cash_per_unit
            + self.policy.minimum_net_reward_risk * net_risk_per_unit
        ) / (
            (1.0 - self.costs.adverse_price_rate)
            * (1.0 - self.costs.commission_rate)
        )
        meets_reward_risk = (
            net_reward_risk >= self.policy.minimum_net_reward_risk
            or math.isclose(
                net_reward_risk,
                self.policy.minimum_net_reward_risk,
                rel_tol=self.REWARD_RISK_REL_TOLERANCE,
                abs_tol=0.0,
            )
        )
        calculated = {
            "risk_budget": risk_budget,
            "entry_fill_price": entry_fill,
            "stop_trigger_price": setup_low,
            "stop_fill_assumption": stop_fill,
            "target_trigger_price": resistance,
            "required_target_for_minimum_r": required_target,
            "net_risk_per_unit": net_risk_per_unit,
            "net_reward_per_unit": net_reward_per_unit,
            "net_reward_risk_ratio": net_reward_risk,
            **common,
        }
        if not meets_reward_risk:
            return self._no_trade("NET_THREE_R_CAUSAL_ROOM_NOT_AVAILABLE", **calculated)

        effective_stop = entry_fill - net_risk_per_unit
        if effective_stop <= 0.0:
            return self._no_trade("EFFECTIVE_COST_STOP_NOT_POSITIVE", **calculated)
        dynamic_risk_fraction = risk_budget / equity
        risk_decision = RiskEngine(
            risk_per_trade=dynamic_risk_fraction,
            max_position_fraction=self.policy.maximum_position_fraction,
        ).assess_long(equity, entry_fill, effective_stop)
        cash_sized_units = available_cash / entry_cash_per_unit
        position_size = min(risk_decision.position_size, cash_sized_units)
        if position_size <= 0.0:
            return self._no_trade(
                "NO_POSITIVE_SIZE_AFTER_RISK_EXPOSURE_AND_CASH_CAPS",
                risk_engine_status=risk_decision.status,
                **calculated,
            )

        position_notional = position_size * entry_fill
        cash_required = position_size * entry_cash_per_unit
        planned_risk = position_size * net_risk_per_unit
        planned_reward = position_size * net_reward_per_unit
        return SyntheticEntryPlan(
            status="APPROVED_SYNTHETIC_ENTRY_PLAN",
            reason="ALL_ENTRY_RISK_EXECUTION_GATES_PASS",
            policy_id=self.policy.policy_id,
            cost_profile_id=self.costs.profile_id,
            position_size=position_size,
            position_notional=position_notional,
            cash_required=cash_required,
            planned_monetary_risk=planned_risk,
            planned_net_reward=planned_reward,
            planned_entry_commission=(
                position_size * entry_fill * self.costs.commission_rate
            ),
            planned_stop_commission=(
                position_size * stop_fill * self.costs.commission_rate
            ),
            risk_engine_status=risk_decision.status,
            **calculated,
        )

    @staticmethod
    def position_from_plan(plan):
        if not isinstance(plan, SyntheticEntryPlan):
            raise TypeError("Synthetic position requires a SyntheticEntryPlan.")
        if not plan.approved:
            raise ValueError("Rejected entry plan cannot create a position.")
        return SyntheticResearchPosition(
            policy_id=plan.policy_id,
            cost_profile_id=plan.cost_profile_id,
            entry_timestamp=pd.Timestamp(plan.execution_timestamp),
            units=plan.position_size,
            entry_fill_price=plan.entry_fill_price,
            entry_commission=plan.planned_entry_commission,
            stop_trigger_price=plan.stop_trigger_price,
            target_trigger_price=plan.target_trigger_price,
        )

    def _synthetic_exit(
        self,
        position,
        *,
        reason,
        exit_type,
        market_reference_price,
        trigger_price,
        same_bar_conflict=False,
    ):
        fill_price = self.costs.sell_fill(market_reference_price)
        commission = self.costs.commission(fill_price, position.units)
        return SyntheticExitDecision(
            status="SYNTHETIC_EXIT",
            reason=reason,
            exit_type=exit_type,
            market_reference_price=float(market_reference_price),
            trigger_price=(None if trigger_price is None else float(trigger_price)),
            fill_price=fill_price,
            commission=commission,
            net_proceeds=fill_price * position.units - commission,
            same_bar_conflict=bool(same_bar_conflict),
        )

    @staticmethod
    def _validated_position(position):
        if not isinstance(position, SyntheticResearchPosition):
            raise TypeError("Protective evaluation requires a synthetic position.")
        return position

    def evaluate_open(self, position, open_price, pending_exit_reason=None):
        position = self._validated_position(position)
        open_price = _positive_number(open_price, "Protective open price")
        if pending_exit_reason is not None and pending_exit_reason not in VALID_PENDING_EXITS:
            raise ValueError("Pending exit reason is invalid.")
        protective = self.protective_policy.evaluate_long_open(
            open_price,
            position.stop_trigger_price,
            position.target_trigger_price,
        )
        if protective.status == "EXIT":
            return self._synthetic_exit(
                position,
                reason=f"PROTECTIVE_{protective.exit_type}",
                exit_type=protective.exit_type,
                market_reference_price=protective.market_price,
                trigger_price=protective.trigger_price,
                same_bar_conflict=protective.same_bar_conflict,
            )
        if pending_exit_reason is not None:
            return self._synthetic_exit(
                position,
                reason=pending_exit_reason,
                exit_type="SCHEDULED_NEXT_OPEN",
                market_reference_price=open_price,
                trigger_price=None,
            )
        return SyntheticExitDecision(status="HOLD", reason="OPEN_PROTECTION_HOLD")

    def evaluate_intrabar(self, position, high_price, low_price):
        position = self._validated_position(position)
        decision = self.protective_policy.evaluate_long_intrabar(
            high_price,
            low_price,
            position.stop_trigger_price,
            position.target_trigger_price,
        )
        if decision.status == "HOLD":
            return SyntheticExitDecision(
                status="HOLD", reason="INTRABAR_PROTECTION_HOLD"
            )
        return self._synthetic_exit(
            position,
            reason=f"PROTECTIVE_{decision.exit_type}",
            exit_type=decision.exit_type,
            market_reference_price=decision.market_price,
            trigger_price=decision.trigger_price,
            same_bar_conflict=decision.same_bar_conflict,
        )

    def complete_bar(self, position, action_intent):
        position = self._validated_position(position)
        if action_intent not in (INTENT_NONE, INTENT_EXIT_NEXT_OPEN):
            raise ValueError("Open synthetic position received an invalid action intent.")
        updated = replace(position, bars_held=position.bars_held + 1)
        maximum_hold_due = (
            updated.bars_held >= self.policy.maximum_holding_completed_bars
        )
        state_exit_due = action_intent == INTENT_EXIT_NEXT_OPEN
        if state_exit_due and maximum_hold_due:
            return CompletedBarExitSchedule(
                status="SCHEDULE_EXIT_NEXT_OPEN",
                reason="STATE_AND_MAXIMUM_HOLD_EXIT_SCHEDULED",
                pending_exit_reason=PENDING_STATE_AND_MAX_HOLD_EXIT,
                updated_position=updated,
            )
        if state_exit_due:
            return CompletedBarExitSchedule(
                status="SCHEDULE_EXIT_NEXT_OPEN",
                reason="STATE_SIGNAL_EXIT_SCHEDULED",
                pending_exit_reason=PENDING_STATE_EXIT,
                updated_position=updated,
            )
        if maximum_hold_due:
            return CompletedBarExitSchedule(
                status="SCHEDULE_EXIT_NEXT_OPEN",
                reason="MAXIMUM_HOLD_EXIT_SCHEDULED",
                pending_exit_reason=PENDING_MAX_HOLD_EXIT,
                updated_position=updated,
            )
        return CompletedBarExitSchedule(
            status="HOLD",
            reason="COMPLETED_BAR_HOLD",
            pending_exit_reason=None,
            updated_position=updated,
        )
