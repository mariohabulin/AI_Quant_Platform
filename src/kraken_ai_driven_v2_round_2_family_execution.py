"""Synthetic family execution adapters for Kraken AI-driven V2 Round 2."""

import copy
from dataclasses import asdict, dataclass, replace
import math
from numbers import Real

import numpy as np
import pandas as pd

try:
    from kraken_ai_driven_v2_hybrid_discovery_round_2 import (
        COST_PROFILES,
        ROUND_2_CONFIGURATION_LOCK,
        ROUND_2_HYPOTHESES,
    )
    from kraken_ai_driven_v2_risk_execution import (
        KrakenV2ExecutionCostProfile,
    )
    from kraken_ai_driven_v2_round_2_causal_signals import (
        ACTION_INTENT_COLUMN,
        ENTER_NEXT_OPEN,
        FAMILY_COLUMN,
        FAMILY_ORDER,
        FEATURES_AVAILABLE_COLUMN,
        HYPOTHESIS_COLUMN,
        SETUP_LOW_COLUMN,
        SETUP_TIMESTAMP_COLUMN,
        SIGNAL_ATR_COLUMN,
        SIGNAL_CONDITION_COLUMN,
        STATE_AFTER_COLUMN,
        STATE_FLAT,
        TARGET_ANCHOR_COLUMN,
        TRANSITION_COLUMN,
    )
    from kraken_ai_driven_v2_strategy_discovery import (
        ASSET_ORDER,
        SHARED_SAFETY_ENVELOPE,
    )
    from protective_exit import ProtectiveExitPolicy
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_hybrid_discovery_round_2 import (
        COST_PROFILES,
        ROUND_2_CONFIGURATION_LOCK,
        ROUND_2_HYPOTHESES,
    )
    from .kraken_ai_driven_v2_risk_execution import (
        KrakenV2ExecutionCostProfile,
    )
    from .kraken_ai_driven_v2_round_2_causal_signals import (
        ACTION_INTENT_COLUMN,
        ENTER_NEXT_OPEN,
        FAMILY_COLUMN,
        FAMILY_ORDER,
        FEATURES_AVAILABLE_COLUMN,
        HYPOTHESIS_COLUMN,
        SETUP_LOW_COLUMN,
        SETUP_TIMESTAMP_COLUMN,
        SIGNAL_ATR_COLUMN,
        SIGNAL_CONDITION_COLUMN,
        STATE_AFTER_COLUMN,
        STATE_FLAT,
        TARGET_ANCHOR_COLUMN,
        TRANSITION_COLUMN,
    )
    from .kraken_ai_driven_v2_strategy_discovery import (
        ASSET_ORDER,
        SHARED_SAFETY_ENVELOPE,
    )
    from .protective_exit import ProtectiveExitPolicy


FAMILY_EXECUTION_COMPONENT_ID = "kraken-ai-v2-round-2-family-execution-v1"
BASELINE_COST_PROFILE_ID = COST_PROFILES["baseline"]["cost_profile_id"]
STRESS_COST_PROFILE_ID = COST_PROFILES["stress"]["cost_profile_id"]
PENDING_STRUCTURAL_EXIT = "FAMILY_STRUCTURAL_EXIT"
PENDING_MAXIMUM_HOLD_EXIT = "MAXIMUM_HOLD_EXIT"
PENDING_STRUCTURAL_AND_MAXIMUM_HOLD_EXIT = (
    "FAMILY_STRUCTURAL_AND_MAXIMUM_HOLD_EXIT"
)
VALID_PENDING_EXITS = (
    PENDING_STRUCTURAL_EXIT,
    PENDING_MAXIMUM_HOLD_EXIT,
    PENDING_STRUCTURAL_AND_MAXIMUM_HOLD_EXIT,
)
PRIOR_CLOSE_LOW_10_COLUMN = "KRAKEN_AI_V2_R2_PRIOR_CLOSE_LOW_10"
EMA_50_PRIOR_COLUMN = "KRAKEN_AI_V2_R2_EMA_50_PRIOR"
CONFIRMATION_TRANSITIONS = {
    "CAPITULATION_RECOVERY": "CAPITULATION_CONFIRMATION",
    "VOLATILITY_BREAKOUT": "BREAKOUT_RETEST_CONFIRMATION",
    "TREND_PULLBACK_CONTINUATION": "TREND_MACD_RESUMPTION_CONFIRMATION",
}
TARGET_MODE_FIXED_R = "COST_ADJUSTED_FIXED_3R"
REWARD_RISK_REL_TOLERANCE = 1e-12


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


def _utc_midnight(value, name):
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


def _exact_true(value):
    return isinstance(value, (bool, np.bool_)) and bool(value)


def _cost_profile(profile_name):
    configuration = COST_PROFILES[profile_name]
    return KrakenV2ExecutionCostProfile(
        profile_id=configuration["cost_profile_id"],
        commission_rate=configuration["commission_per_side_fraction"],
        slippage_rate=configuration["slippage_per_side_fraction"],
        full_spread_rate=configuration["full_spread_fraction"],
    )


ROUND_2_BASELINE_COST_PROFILE = _cost_profile("baseline")
ROUND_2_STRESS_COST_PROFILE = _cost_profile("stress")
_COST_PROFILES_BY_ID = {
    BASELINE_COST_PROFILE_ID: ROUND_2_BASELINE_COST_PROFILE,
    STRESS_COST_PROFILE_ID: ROUND_2_STRESS_COST_PROFILE,
}
_HYPOTHESES_BY_FAMILY = {
    item["family_id"]: copy.deepcopy(item) for item in ROUND_2_HYPOTHESES
}

if tuple(_HYPOTHESES_BY_FAMILY) != FAMILY_ORDER:
    raise RuntimeError("Round 2 family execution order mismatch.")


@dataclass(frozen=True)
class Round2FamilyEntryPlan:
    status: str
    reason: str
    family_id: str
    hypothesis_id: str
    execution_contract_id: str
    cost_profile_id: str
    asset: str | None = None
    signal_timestamp: str | None = None
    execution_timestamp: str | None = None
    raw_open_price: float | None = None
    entry_fill_price: float | None = None
    stop_mode: str | None = None
    stop_trigger_price: float | None = None
    stop_fill_assumption: float | None = None
    target_mode: str | None = None
    target_trigger_price: float | None = None
    required_target_for_minimum_r: float | None = None
    net_risk_per_unit: float | None = None
    net_reward_per_unit: float | None = None
    net_reward_risk_ratio: float | None = None
    risk_budget: float = 0.0
    remaining_asset_notional_capacity: float = 0.0
    position_size: float = 0.0
    position_notional: float = 0.0
    cash_required: float = 0.0
    planned_monetary_risk: float = 0.0
    planned_net_reward: float = 0.0
    planned_entry_commission: float = 0.0
    planned_stop_commission: float = 0.0
    maximum_holding_completed_bars: int | None = None
    structural_exit_mode: str | None = None
    real_order_submitted: bool = False
    performance_evaluation_executed: bool = False

    def __post_init__(self):
        if self.status not in (
            "APPROVED_SYNTHETIC_FAMILY_ENTRY_PLAN",
            "NO_TRADE_HOLD_CASH",
        ):
            raise ValueError("Round 2 family entry-plan status is invalid.")
        for value, name in (
            (self.reason, "Entry-plan reason"),
            (self.family_id, "Family ID"),
            (self.hypothesis_id, "Hypothesis ID"),
            (self.execution_contract_id, "Execution contract ID"),
            (self.cost_profile_id, "Cost-profile ID"),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} is required.")
        if self.real_order_submitted or self.performance_evaluation_executed:
            raise ValueError("Family entry plans cannot execute or evaluate.")

    @property
    def approved(self):
        return self.status == "APPROVED_SYNTHETIC_FAMILY_ENTRY_PLAN"

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Round2FamilySyntheticPosition:
    family_id: str
    hypothesis_id: str
    execution_contract_id: str
    cost_profile_id: str
    asset: str
    signal_timestamp: pd.Timestamp
    entry_timestamp: pd.Timestamp
    units: float
    entry_fill_price: float
    entry_commission: float
    stop_trigger_price: float
    target_trigger_price: float
    maximum_holding_completed_bars: int
    structural_exit_mode: str
    bars_held: int = 0

    def __post_init__(self):
        if self.family_id not in FAMILY_ORDER:
            raise ValueError("Synthetic position family identity mismatch.")
        hypothesis = _HYPOTHESES_BY_FAMILY[self.family_id]
        if self.hypothesis_id != hypothesis["hypothesis_id"]:
            raise ValueError("Synthetic position hypothesis identity mismatch.")
        if self.execution_contract_id != hypothesis["execution_contract_id"]:
            raise ValueError("Synthetic position execution identity mismatch.")
        if self.cost_profile_id not in _COST_PROFILES_BY_ID:
            raise ValueError("Synthetic position cost identity mismatch.")
        if self.asset not in ASSET_ORDER:
            raise ValueError("Synthetic position asset is invalid.")
        signal_timestamp = _utc_midnight(
            self.signal_timestamp, "Synthetic signal timestamp"
        )
        entry_timestamp = _utc_midnight(
            self.entry_timestamp, "Synthetic entry timestamp"
        )
        if entry_timestamp != signal_timestamp + pd.Timedelta(days=1):
            raise ValueError(
                "Synthetic entry must be immediately following signal day."
            )
        for value, name in (
            (self.units, "Synthetic position units"),
            (self.entry_fill_price, "Synthetic entry fill"),
            (self.stop_trigger_price, "Synthetic stop trigger"),
            (self.target_trigger_price, "Synthetic target trigger"),
        ):
            _positive_number(value, name)
        _nonnegative_number(self.entry_commission, "Synthetic entry commission")
        if not self.stop_trigger_price < self.entry_fill_price < self.target_trigger_price:
            raise ValueError("Synthetic family position levels are not ordered.")
        expected_holding = hypothesis["execution_parameters"]["maximum_hold_bars"]
        if self.maximum_holding_completed_bars != expected_holding:
            raise ValueError("Synthetic position maximum-hold identity mismatch.")
        if self.structural_exit_mode != hypothesis["execution_parameters"][
            "scheduled_exit"
        ]:
            raise ValueError("Synthetic position structural-exit identity mismatch.")
        if not isinstance(self.bars_held, int) or isinstance(self.bars_held, bool):
            raise TypeError("Synthetic bars held must be an integer.")
        if self.bars_held < 0 or self.bars_held > self.maximum_holding_completed_bars:
            raise ValueError("Synthetic bars held are outside the family limit.")

    def as_dict(self):
        payload = asdict(self)
        payload["signal_timestamp"] = self.signal_timestamp.isoformat()
        payload["entry_timestamp"] = self.entry_timestamp.isoformat()
        return payload


@dataclass(frozen=True)
class Round2FamilyExitDecision:
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
            raise ValueError("Family exit-decision status is invalid.")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("Family exit-decision reason is required.")
        if self.real_order_submitted or self.performance_evaluation_executed:
            raise ValueError("Family exits cannot execute or evaluate.")
        if self.status == "HOLD" and any(
            value is not None
            for value in (
                self.exit_type,
                self.market_reference_price,
                self.trigger_price,
                self.fill_price,
            )
        ):
            raise ValueError("HOLD cannot contain family exit evidence.")

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Round2CompletedBarExitSchedule:
    status: str
    reason: str
    pending_exit_reason: str | None
    updated_position: Round2FamilySyntheticPosition
    real_order_submitted: bool = False
    performance_evaluation_executed: bool = False

    def __post_init__(self):
        if self.status not in ("HOLD", "SCHEDULE_EXIT_NEXT_OPEN"):
            raise ValueError("Family completed-bar schedule status is invalid.")
        if self.real_order_submitted or self.performance_evaluation_executed:
            raise ValueError("Family completed-bar schedules cannot execute.")
        if not isinstance(self.updated_position, Round2FamilySyntheticPosition):
            raise TypeError("Family schedule requires a synthetic position.")

    def as_dict(self):
        payload = asdict(self)
        payload["updated_position"] = self.updated_position.as_dict()
        return payload


def execution_component_declaration():
    return {
        "schema_version": 1,
        "component_id": FAMILY_EXECUTION_COMPONENT_ID,
        "round_2_configuration_sha256": ROUND_2_CONFIGURATION_LOCK.sha256,
        "family_order": list(FAMILY_ORDER),
        "family_count": len(FAMILY_ORDER),
        "execution_contract_ids": [
            _HYPOTHESES_BY_FAMILY[family]["execution_contract_id"]
            for family in FAMILY_ORDER
        ],
        "asset_scopes": {
            family: list(_HYPOTHESES_BY_FAMILY[family]["asset_scope"])
            for family in FAMILY_ORDER
        },
        "cost_profile_ids": [BASELINE_COST_PROFILE_ID, STRESS_COST_PROFILE_ID],
        "family_execution_components_implemented": True,
        "baseline_cost_profile_implemented": True,
        "stress_cost_profile_implemented": True,
        "shared_safety_envelope_implemented": True,
        "protective_execution_implemented": True,
        "entry_bar_protection_implemented": True,
        "stop_first_same_bar_ordering_implemented": True,
        "discovery_runner_implemented": False,
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_run_authorized": False,
        "performance_evaluation_executed": False,
        "parameter_sweep_authorized": False,
        "automatic_ranking_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
    }


class _Round2FamilyExecutionAdapter:
    FAMILY_ID = None

    def __init__(self, *, cost_profile_id=BASELINE_COST_PROFILE_ID):
        if self.FAMILY_ID not in FAMILY_ORDER:
            raise RuntimeError("Round 2 family adapter identity is invalid.")
        if cost_profile_id not in _COST_PROFILES_BY_ID:
            raise ValueError("Round 2 family cost-profile identity is invalid.")
        self.hypothesis = copy.deepcopy(_HYPOTHESES_BY_FAMILY[self.FAMILY_ID])
        self.execution = copy.deepcopy(self.hypothesis["execution_parameters"])
        self.costs = _COST_PROFILES_BY_ID[cost_profile_id]
        self.protective_policy = ProtectiveExitPolicy(
            reward_risk_ratio=self.execution["minimum_net_reward_r"],
            breakeven_trigger_r=None,
        )

    def configuration(self):
        return {
            "component_id": FAMILY_EXECUTION_COMPONENT_ID,
            "round_2_configuration_sha256": ROUND_2_CONFIGURATION_LOCK.sha256,
            "family_id": self.FAMILY_ID,
            "hypothesis_id": self.hypothesis["hypothesis_id"],
            "execution_contract_id": self.hypothesis["execution_contract_id"],
            "execution_parameters": copy.deepcopy(self.execution),
            "asset_scope": list(self.hypothesis["asset_scope"]),
            "shared_safety_envelope": copy.deepcopy(SHARED_SAFETY_ENVELOPE),
            "cost_profile": self.costs.configuration(),
            "entry_execution": "IMMEDIATELY_FOLLOWING_DAILY_OPEN",
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
            "real_order_submission": False,
            "performance_evaluation": False,
            "dataset_opened": False,
        }

    def _no_trade(self, reason, **evidence):
        return Round2FamilyEntryPlan(
            status="NO_TRADE_HOLD_CASH",
            reason=reason,
            family_id=self.FAMILY_ID,
            hypothesis_id=self.hypothesis["hypothesis_id"],
            execution_contract_id=self.hypothesis["execution_contract_id"],
            cost_profile_id=self.costs.profile_id,
            maximum_holding_completed_bars=self.execution["maximum_hold_bars"],
            structural_exit_mode=self.execution["scheduled_exit"],
            **evidence,
        )

    @staticmethod
    def _signal_values(signal_row):
        if not isinstance(signal_row, pd.Series):
            raise TypeError("Family entry evidence must be a pandas Series.")
        required = (
            FAMILY_COLUMN,
            HYPOTHESIS_COLUMN,
            FEATURES_AVAILABLE_COLUMN,
            SIGNAL_CONDITION_COLUMN,
            ACTION_INTENT_COLUMN,
            STATE_AFTER_COLUMN,
            TRANSITION_COLUMN,
            SETUP_TIMESTAMP_COLUMN,
            SETUP_LOW_COLUMN,
            SIGNAL_ATR_COLUMN,
            TARGET_ANCHOR_COLUMN,
            "Close",
        )
        missing = [column for column in required if column not in signal_row]
        if missing:
            raise ValueError(f"Family entry evidence is missing columns: {missing}")
        return {
            "signal_timestamp": _utc_midnight(
                signal_row.name, "Family signal timestamp"
            ),
            "setup_timestamp": _utc_midnight(
                signal_row[SETUP_TIMESTAMP_COLUMN], "Family setup timestamp"
            ),
            "setup_low": _positive_number(
                signal_row[SETUP_LOW_COLUMN], "Family setup low"
            ),
            "prior_atr": _positive_number(
                signal_row[SIGNAL_ATR_COLUMN], "Family signal prior ATR"
            ),
            "signal_close": _positive_number(
                signal_row["Close"], "Family signal close"
            ),
            "target_anchor": signal_row[TARGET_ANCHOR_COLUMN],
        }

    def _signal_is_eligible(self, signal_row):
        return (
            signal_row[FAMILY_COLUMN] == self.FAMILY_ID
            and signal_row[HYPOTHESIS_COLUMN] == self.hypothesis["hypothesis_id"]
            and _exact_true(signal_row[FEATURES_AVAILABLE_COLUMN])
            and _exact_true(signal_row[SIGNAL_CONDITION_COLUMN])
            and signal_row[ACTION_INTENT_COLUMN] == ENTER_NEXT_OPEN
            and signal_row[STATE_AFTER_COLUMN] == STATE_FLAT
            and signal_row[TRANSITION_COLUMN]
            == CONFIRMATION_TRANSITIONS[self.FAMILY_ID]
        )

    def _setup_timing_is_eligible(self, signal_timestamp, setup_timestamp):
        age = (signal_timestamp - setup_timestamp) / pd.Timedelta(days=1)
        if self.FAMILY_ID == "CAPITULATION_RECOVERY":
            return 2 <= age <= 7
        return 2 <= age <= 5

    def _resolved_stop(self, raw_open, setup_low, prior_atr):
        del raw_open
        return setup_low - 0.25 * prior_atr

    def _target_and_mode(self, signal_values, required_target):
        del signal_values
        return required_target, TARGET_MODE_FIXED_R

    def plan_entry(
        self,
        signal_row,
        *,
        asset,
        execution_timestamp,
        next_open_price,
        equity,
        available_cash,
        current_open_risk_amount,
        current_asset_notional,
        open_crypto_positions,
    ):
        values = self._signal_values(signal_row)
        execution_timestamp = _utc_midnight(
            execution_timestamp, "Family execution timestamp"
        )
        if execution_timestamp != values["signal_timestamp"] + pd.Timedelta(days=1):
            raise ValueError(
                "Family entry execution must use the immediately following day."
            )
        if asset not in ASSET_ORDER:
            raise ValueError("Family execution asset is invalid.")
        raw_open = _positive_number(next_open_price, "Family next open price")
        equity = _positive_number(equity, "Family current equity")
        available_cash = _nonnegative_number(
            available_cash, "Family available cash"
        )
        current_open_risk = _nonnegative_number(
            current_open_risk_amount, "Family current open risk"
        )
        current_asset_notional = _nonnegative_number(
            current_asset_notional, "Family current asset notional"
        )
        if (
            not isinstance(open_crypto_positions, int)
            or isinstance(open_crypto_positions, bool)
            or open_crypto_positions < 0
        ):
            raise ValueError(
                "Family open crypto-position count must be a nonnegative integer."
            )

        common = {
            "asset": asset,
            "signal_timestamp": values["signal_timestamp"].isoformat(),
            "execution_timestamp": execution_timestamp.isoformat(),
            "raw_open_price": raw_open,
        }
        if not self._signal_is_eligible(signal_row):
            return self._no_trade(
                "SIGNAL_EVIDENCE_NOT_ENTRY_ELIGIBLE", **common
            )
        if not self._setup_timing_is_eligible(
            values["signal_timestamp"], values["setup_timestamp"]
        ):
            return self._no_trade("FAMILY_SETUP_TIMING_NOT_ELIGIBLE", **common)
        if asset not in self.hypothesis["asset_scope"]:
            return self._no_trade(
                "ASSET_NOT_IN_REGISTERED_FAMILY_SCOPE", **common
            )
        maximum_positions = SHARED_SAFETY_ENVELOPE["maximum_concurrent_positions"]
        if open_crypto_positions >= maximum_positions:
            return self._no_trade(
                "CRYPTO_POSITION_CAPACITY_EXHAUSTED", **common
            )

        total_risk_limit = (
            equity
            * SHARED_SAFETY_ENVELOPE["total_open_risk_fraction_ceiling"]
        )
        remaining_risk = total_risk_limit - current_open_risk
        if remaining_risk <= 0.0:
            return self._no_trade(
                "TOTAL_OPEN_RISK_CAPACITY_EXHAUSTED", **common
            )
        risk_budget = min(
            equity * SHARED_SAFETY_ENVELOPE["position_risk_fraction_ceiling"],
            remaining_risk,
        )
        asset_notional_limit = (
            equity
            * SHARED_SAFETY_ENVELOPE["per_asset_notional_fraction_ceiling"]
        )
        remaining_asset_notional = asset_notional_limit - current_asset_notional
        if remaining_asset_notional <= 0.0:
            return self._no_trade(
                "ASSET_NOTIONAL_CAPACITY_EXHAUSTED",
                risk_budget=risk_budget,
                **common,
            )

        stop = self._resolved_stop(
            raw_open, values["setup_low"], values["prior_atr"]
        )
        stop_mode = self.execution["stop_mode"]
        level_evidence = {
            "risk_budget": risk_budget,
            "remaining_asset_notional_capacity": remaining_asset_notional,
            "stop_mode": stop_mode,
            "stop_trigger_price": stop,
            **common,
        }
        if stop <= 0.0:
            return self._no_trade("RESOLVED_STOP_NOT_POSITIVE", **level_evidence)
        if raw_open <= stop:
            return self._no_trade(
                "ENTRY_OPEN_AT_OR_BELOW_RESOLVED_STOP", **level_evidence
            )
        gap_limit = self.execution["maximum_upward_gap_atr"]
        if raw_open > values["signal_close"] + values["prior_atr"] * gap_limit:
            return self._no_trade(
                "ENTRY_UPWARD_GAP_EXCEEDS_ATR_LIMIT", **level_evidence
            )

        entry_fill = self.costs.buy_fill(raw_open)
        entry_cash_per_unit = entry_fill * (1.0 + self.costs.commission_rate)
        stop_fill = self.costs.sell_fill(stop)
        stop_proceeds_per_unit = stop_fill * (1.0 - self.costs.commission_rate)
        net_risk_per_unit = entry_cash_per_unit - stop_proceeds_per_unit
        calculated = {
            "entry_fill_price": entry_fill,
            "stop_fill_assumption": stop_fill,
            "net_risk_per_unit": net_risk_per_unit,
            **level_evidence,
        }
        if net_risk_per_unit <= 0.0:
            return self._no_trade(
                "NO_POSITIVE_COST_AWARE_RISK_DISTANCE", **calculated
            )
        minimum_r = self.execution["minimum_net_reward_r"]
        required_target = (
            entry_cash_per_unit + minimum_r * net_risk_per_unit
        ) / (
            (1.0 - self.costs.adverse_price_rate)
            * (1.0 - self.costs.commission_rate)
        )
        target, target_mode = self._target_and_mode(values, required_target)
        target_fill = self.costs.sell_fill(target)
        target_proceeds_per_unit = target_fill * (
            1.0 - self.costs.commission_rate
        )
        net_reward_per_unit = target_proceeds_per_unit - entry_cash_per_unit
        net_reward_risk = net_reward_per_unit / net_risk_per_unit
        calculated.update(
            {
                "target_mode": target_mode,
                "target_trigger_price": target,
                "required_target_for_minimum_r": required_target,
                "net_reward_per_unit": net_reward_per_unit,
                "net_reward_risk_ratio": net_reward_risk,
            }
        )
        if target <= entry_fill:
            return self._no_trade(
                "SIGNAL_TARGET_NOT_ABOVE_COST_ADJUSTED_ENTRY", **calculated
            )
        meets_minimum = net_reward_risk >= minimum_r or math.isclose(
            net_reward_risk,
            minimum_r,
            rel_tol=REWARD_RISK_REL_TOLERANCE,
            abs_tol=0.0,
        )
        if not meets_minimum:
            return self._no_trade(
                "NET_THREE_R_SIGNAL_TARGET_ROOM_NOT_AVAILABLE", **calculated
            )

        risk_sized_units = risk_budget / net_risk_per_unit
        asset_sized_units = remaining_asset_notional / entry_fill
        cash_sized_units = available_cash / entry_cash_per_unit
        units = min(risk_sized_units, asset_sized_units, cash_sized_units)
        if units <= 0.0:
            return self._no_trade(
                "NO_POSITIVE_SIZE_AFTER_SHARED_SAFETY_CAPS", **calculated
            )
        position_notional = units * entry_fill
        cash_required = units * entry_cash_per_unit
        planned_risk = units * net_risk_per_unit
        planned_reward = units * net_reward_per_unit
        return Round2FamilyEntryPlan(
            status="APPROVED_SYNTHETIC_FAMILY_ENTRY_PLAN",
            reason="ALL_FAMILY_ENTRY_GATES_PASS",
            family_id=self.FAMILY_ID,
            hypothesis_id=self.hypothesis["hypothesis_id"],
            execution_contract_id=self.hypothesis["execution_contract_id"],
            cost_profile_id=self.costs.profile_id,
            position_size=units,
            position_notional=position_notional,
            cash_required=cash_required,
            planned_monetary_risk=planned_risk,
            planned_net_reward=planned_reward,
            planned_entry_commission=(
                units * entry_fill * self.costs.commission_rate
            ),
            planned_stop_commission=(
                units * stop_fill * self.costs.commission_rate
            ),
            maximum_holding_completed_bars=self.execution["maximum_hold_bars"],
            structural_exit_mode=self.execution["scheduled_exit"],
            **calculated,
        )

    def position_from_plan(self, plan):
        if not isinstance(plan, Round2FamilyEntryPlan):
            raise TypeError("Synthetic position requires a Round2FamilyEntryPlan.")
        if not plan.approved:
            raise ValueError("Rejected family entry plan cannot create a position.")
        if plan.family_id != self.FAMILY_ID:
            raise ValueError("Entry plan family identity does not match adapter.")
        return Round2FamilySyntheticPosition(
            family_id=plan.family_id,
            hypothesis_id=plan.hypothesis_id,
            execution_contract_id=plan.execution_contract_id,
            cost_profile_id=plan.cost_profile_id,
            asset=plan.asset,
            signal_timestamp=pd.Timestamp(plan.signal_timestamp),
            entry_timestamp=pd.Timestamp(plan.execution_timestamp),
            units=plan.position_size,
            entry_fill_price=plan.entry_fill_price,
            entry_commission=plan.planned_entry_commission,
            stop_trigger_price=plan.stop_trigger_price,
            target_trigger_price=plan.target_trigger_price,
            maximum_holding_completed_bars=(
                plan.maximum_holding_completed_bars
            ),
            structural_exit_mode=plan.structural_exit_mode,
        )

    def _validated_position(self, position):
        if not isinstance(position, Round2FamilySyntheticPosition):
            raise TypeError("Family protection requires a synthetic position.")
        if position.family_id != self.FAMILY_ID:
            raise ValueError("Synthetic position family does not match adapter.")
        if position.cost_profile_id != self.costs.profile_id:
            raise ValueError("Synthetic position cost profile does not match adapter.")
        return position

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
        return Round2FamilyExitDecision(
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

    def evaluate_open(self, position, open_price, pending_exit_reason=None):
        position = self._validated_position(position)
        open_price = _positive_number(open_price, "Family protective open price")
        if pending_exit_reason is not None and pending_exit_reason not in (
            VALID_PENDING_EXITS
        ):
            raise ValueError("Family pending exit reason is invalid.")
        decision = self.protective_policy.evaluate_long_open(
            open_price,
            position.stop_trigger_price,
            position.target_trigger_price,
        )
        if decision.status == "EXIT":
            return self._synthetic_exit(
                position,
                reason=f"PROTECTIVE_{decision.exit_type}",
                exit_type=decision.exit_type,
                market_reference_price=decision.market_price,
                trigger_price=decision.trigger_price,
                same_bar_conflict=decision.same_bar_conflict,
            )
        if pending_exit_reason is not None:
            return self._synthetic_exit(
                position,
                reason=pending_exit_reason,
                exit_type="SCHEDULED_NEXT_OPEN",
                market_reference_price=open_price,
                trigger_price=None,
            )
        return Round2FamilyExitDecision(
            status="HOLD", reason="OPEN_PROTECTION_HOLD"
        )

    def evaluate_intrabar(self, position, high_price, low_price):
        position = self._validated_position(position)
        decision = self.protective_policy.evaluate_long_intrabar(
            high_price,
            low_price,
            position.stop_trigger_price,
            position.target_trigger_price,
        )
        if decision.status == "HOLD":
            return Round2FamilyExitDecision(
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

    def _structural_exit_due(self, completed_row):
        if not isinstance(completed_row, pd.Series):
            raise TypeError("Family completed-bar evidence must be a pandas Series.")
        close = _positive_number(completed_row.get("Close"), "Family completed close")
        if self.FAMILY_ID in (
            "CAPITULATION_RECOVERY",
            "VOLATILITY_BREAKOUT",
        ):
            if PRIOR_CLOSE_LOW_10_COLUMN not in completed_row:
                raise ValueError(
                    "Family completed-bar evidence is missing prior close low."
                )
            prior_low = _positive_number(
                completed_row[PRIOR_CLOSE_LOW_10_COLUMN],
                "Family prior 10-close low",
            )
            return close < prior_low
        if self.FAMILY_ID == "TREND_PULLBACK_CONTINUATION":
            if EMA_50_PRIOR_COLUMN not in completed_row:
                raise ValueError(
                    "Family completed-bar evidence is missing prior EMA-50."
                )
            ema_50 = _positive_number(
                completed_row[EMA_50_PRIOR_COLUMN], "Family prior EMA-50"
            )
            return close < ema_50
        return False

    def complete_bar(self, position, completed_row):
        position = self._validated_position(position)
        if not isinstance(completed_row, pd.Series):
            raise TypeError("Family completed-bar evidence must be a pandas Series.")
        timestamp = _utc_midnight(
            completed_row.name, "Family completed-bar timestamp"
        )
        expected = position.entry_timestamp + pd.Timedelta(days=position.bars_held)
        if timestamp != expected:
            raise ValueError(
                "Family completed bar must preserve a continuous daily position path."
            )
        structural_due = self._structural_exit_due(completed_row)
        updated = replace(position, bars_held=position.bars_held + 1)
        maximum_due = (
            updated.bars_held >= position.maximum_holding_completed_bars
        )
        if structural_due and maximum_due:
            return Round2CompletedBarExitSchedule(
                status="SCHEDULE_EXIT_NEXT_OPEN",
                reason="STRUCTURAL_AND_MAXIMUM_HOLD_EXIT_SCHEDULED",
                pending_exit_reason=PENDING_STRUCTURAL_AND_MAXIMUM_HOLD_EXIT,
                updated_position=updated,
            )
        if structural_due:
            return Round2CompletedBarExitSchedule(
                status="SCHEDULE_EXIT_NEXT_OPEN",
                reason="FAMILY_STRUCTURAL_EXIT_SCHEDULED",
                pending_exit_reason=PENDING_STRUCTURAL_EXIT,
                updated_position=updated,
            )
        if maximum_due:
            return Round2CompletedBarExitSchedule(
                status="SCHEDULE_EXIT_NEXT_OPEN",
                reason="MAXIMUM_HOLD_EXIT_SCHEDULED",
                pending_exit_reason=PENDING_MAXIMUM_HOLD_EXIT,
                updated_position=updated,
            )
        return Round2CompletedBarExitSchedule(
            status="HOLD",
            reason="COMPLETED_BAR_HOLD",
            pending_exit_reason=None,
            updated_position=updated,
        )


class KrakenAIDrivenV2Round2CapitulationExecutionAdapter(
    _Round2FamilyExecutionAdapter
):
    FAMILY_ID = "CAPITULATION_RECOVERY"


class KrakenAIDrivenV2Round2VolatilityBreakoutExecutionAdapter(
    _Round2FamilyExecutionAdapter
):
    FAMILY_ID = "VOLATILITY_BREAKOUT"


class KrakenAIDrivenV2Round2TrendPullbackExecutionAdapter(
    _Round2FamilyExecutionAdapter
):
    FAMILY_ID = "TREND_PULLBACK_CONTINUATION"


def family_execution_adapters(*, cost_profile_id=BASELINE_COST_PROFILE_ID):
    return {
        "CAPITULATION_RECOVERY": (
            KrakenAIDrivenV2Round2CapitulationExecutionAdapter(
                cost_profile_id=cost_profile_id
            )
        ),
        "VOLATILITY_BREAKOUT": (
            KrakenAIDrivenV2Round2VolatilityBreakoutExecutionAdapter(
                cost_profile_id=cost_profile_id
            )
        ),
        "TREND_PULLBACK_CONTINUATION": (
            KrakenAIDrivenV2Round2TrendPullbackExecutionAdapter(
                cost_profile_id=cost_profile_id
            )
        ),
    }
