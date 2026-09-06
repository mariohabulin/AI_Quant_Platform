"""Frozen bidirectional Development hypothesis with synthetic-only labels."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real

import pandas as pd

try:
    from kraken_ai_driven_v2_derivatives_context_hypothesis import (
        CONTEXT_FEATURE_COLUMNS,
        FOLD_PLAN,
        MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        MINIMUM_POSITIVE_ASSETS,
        MINIMUM_RAW_SELECTIONS_PER_FOLD,
        REGRESSOR_PARAMETERS,
        fold_plan_is_causal,
    )
    from kraken_ai_driven_v2_learning_core import (
        ASSET_ORDER,
        BAR_INTERVAL,
        BASELINE_COST_PROFILE,
        FEATURE_COLUMNS as SPOT_FEATURE_COLUMNS,
        LearningCostProfile,
        triple_barrier_label,
    )
except ImportError:  # pragma: no cover
    from .kraken_ai_driven_v2_derivatives_context_hypothesis import (
        CONTEXT_FEATURE_COLUMNS,
        FOLD_PLAN,
        MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        MINIMUM_POSITIVE_ASSETS,
        MINIMUM_RAW_SELECTIONS_PER_FOLD,
        REGRESSOR_PARAMETERS,
        fold_plan_is_causal,
    )
    from .kraken_ai_driven_v2_learning_core import (
        ASSET_ORDER,
        BAR_INTERVAL,
        BASELINE_COST_PROFILE,
        FEATURE_COLUMNS as SPOT_FEATURE_COLUMNS,
        LearningCostProfile,
        triple_barrier_label,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-v2-bidirectional-development-hypothesis-v1"
COMPONENT_ID = "kraken-ai-v2-bidirectional-development-hypothesis-v1"
PARENT_COMMIT = "bde314d47e30804a7380493f959f61e8f3a40212"
CONTEXT_LEARNING_REPORT_SHA256 = (
    "bddb6f7c0a9b056dcf8a4ca79fc3b8128dbf4ded4aac47e19022a84222215fb4"
)
CONTEXT_FORENSIC_REPORT_SHA256 = (
    "ed4ee096a9d45eee4d1ee0970dbb062473e74c9caad3597f20eda17cb4dba91f"
)
LONG_ONLY_CLOSURE_STATUS = "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_LONG_ONLY_CLOSED_HOLD_CASH"
DIRECTION_ORDER = ("LONG", "SHORT")
ACTION_ORDER = ("LONG", "SHORT", "HOLD_CASH")
HORIZON_BARS = 60
RISK_ATR_MULTIPLIER = 1.5
TARGET_R = 3.0
STOP_R = 1.0
POSITIVE_SCORE_THRESHOLD_NET_R = 0.0
MINIMUM_CONTEXT_FOLD_WINS = 2

ALL_NUMERIC_FEATURE_COLUMNS = (*SPOT_FEATURE_COLUMNS, *CONTEXT_FEATURE_COLUMNS)

VARIANT_SPECS = {
    "SPOT_ONLY_BIDIRECTIONAL_HIST_GBT_NET_R_CONTROL": {
        "objective": "BIDIRECTIONAL_DIRECT_EXPECTED_NET_R",
        "feature_set": "SPOT_ONLY",
        "numeric_feature_count": len(SPOT_FEATURE_COLUMNS),
        "model_family": "HISTOGRAM_GRADIENT_BOOSTING_REGRESSOR",
        "parameters": REGRESSOR_PARAMETERS,
        "absolute_gate_eligible": True,
        "incremental_context_gate_required": False,
    },
    "SPOT_CONTEXT_BIDIRECTIONAL_HIST_GBT_NET_R": {
        "objective": "BIDIRECTIONAL_DIRECT_EXPECTED_NET_R",
        "feature_set": "SPOT_PLUS_DERIVATIVES_CONTEXT",
        "numeric_feature_count": len(ALL_NUMERIC_FEATURE_COLUMNS),
        "model_family": "HISTOGRAM_GRADIENT_BOOSTING_REGRESSOR",
        "parameters": REGRESSOR_PARAMETERS,
        "absolute_gate_eligible": True,
        "incremental_context_gate_required": True,
    },
}

MATCHED_CONTROL = {
    "SPOT_CONTEXT_BIDIRECTIONAL_HIST_GBT_NET_R": (
        "SPOT_ONLY_BIDIRECTIONAL_HIST_GBT_NET_R_CONTROL"
    )
}


@dataclass(frozen=True)
class DirectionalLabelOutcome:
    valid: bool
    direction: str
    label: str | None
    invalid_reason: str | None
    decision_timestamp: pd.Timestamp
    entry_timestamp: pd.Timestamp | None = None
    event_end_timestamp: pd.Timestamp | None = None
    entry_cashflow_per_unit: float | None = None
    stop_trigger_price: float | None = None
    target_trigger_price: float | None = None
    exit_cashflow_per_unit: float | None = None
    outcome_net_r: float | None = None


def _positive(value, name):
    if not isinstance(value, Real) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric.")
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and positive.")
    return value


def _validate_label_request(frame, direction, decision_position, signal_atr, horizon_bars, cost_profile):
    if direction not in DIRECTION_ORDER:
        raise ValueError(f"Direction must be one of {DIRECTION_ORDER}.")
    if not isinstance(frame, pd.DataFrame) or not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("Label frame must use a DatetimeIndex.")
    if frame.index.tz is None:
        raise ValueError("Label timestamps must be timezone-aware.")
    if any(column not in frame for column in ("Open", "High", "Low", "Close")):
        raise ValueError("Label frame must contain Open, High, Low and Close.")
    if not isinstance(decision_position, Integral) or isinstance(decision_position, bool):
        raise TypeError("Decision position must be an integer.")
    decision_position = int(decision_position)
    if not 0 <= decision_position < len(frame):
        raise IndexError("Decision position is outside the frame.")
    if not isinstance(horizon_bars, Integral) or isinstance(horizon_bars, bool) or horizon_bars < 2:
        raise ValueError("Label horizon must contain at least two bars.")
    if not isinstance(cost_profile, LearningCostProfile):
        raise TypeError("Learning cost profile is invalid.")
    return decision_position, _positive(signal_atr, "Signal ATR"), int(horizon_bars)


def _invalid(frame, decision_position, direction, reason):
    return DirectionalLabelOutcome(
        valid=False,
        direction=direction,
        label=None,
        invalid_reason=reason,
        decision_timestamp=frame.index[decision_position],
    )


def directional_triple_barrier_label(
    frame,
    *,
    direction,
    decision_position,
    signal_atr,
    horizon_bars=HORIZON_BARS,
    cost_profile=BASELINE_COST_PROFILE,
):
    """Create one cost-aware LONG or SHORT outcome from an already supplied frame."""

    decision_position, signal_atr, horizon_bars = _validate_label_request(
        frame, direction, decision_position, signal_atr, horizon_bars, cost_profile
    )
    if direction == "LONG":
        legacy = triple_barrier_label(
            frame,
            decision_position=decision_position,
            signal_atr=signal_atr,
            horizon_bars=horizon_bars,
            cost_profile=cost_profile,
        )
        if not legacy.valid:
            return _invalid(frame, decision_position, direction, legacy.invalid_reason)
        return DirectionalLabelOutcome(
            valid=True,
            direction=direction,
            label=legacy.label,
            invalid_reason=None,
            decision_timestamp=legacy.decision_timestamp,
            entry_timestamp=legacy.entry_timestamp,
            event_end_timestamp=legacy.event_end_timestamp,
            entry_cashflow_per_unit=-legacy.entry_cash_per_unit,
            stop_trigger_price=legacy.stop_trigger_price,
            target_trigger_price=legacy.target_trigger_price,
            exit_cashflow_per_unit=legacy.exit_cash_per_unit,
            outcome_net_r=legacy.outcome_net_r,
        )

    boundary_position = decision_position + horizon_bars
    if boundary_position >= len(frame):
        return _invalid(frame, decision_position, direction, "RIGHT_EDGE_CENSORED")
    path_index = frame.index[decision_position : boundary_position + 1].tz_convert("UTC")
    if not (path_index.to_series().diff().dropna() == BAR_INTERVAL).all():
        return _invalid(frame, decision_position, direction, "PROVIDER_GAP_CENSORED")

    entry_position = decision_position + 1
    entry_open = _positive(frame.iloc[entry_position]["Open"], "Entry open")
    entry_proceeds = cost_profile.sell_cash_per_unit(entry_open)
    risk_unit = RISK_ATR_MULTIPLIER * signal_atr
    adverse_buy_multiplier = (1.0 + cost_profile.adverse_price_rate) * (
        1.0 + cost_profile.commission_rate
    )
    stop_trigger = (entry_proceeds + STOP_R * risk_unit) / adverse_buy_multiplier
    target_cash = entry_proceeds - TARGET_R * risk_unit
    if target_cash <= 0.0:
        return _invalid(frame, decision_position, direction, "NONPOSITIVE_TARGET_BARRIER")
    target_trigger = target_cash / adverse_buy_multiplier

    label = None
    event_position = None
    cover_cash = None
    for position in range(entry_position, boundary_position):
        row = frame.iloc[position]
        open_price = _positive(row["Open"], "Path open")
        high_price = _positive(row["High"], "Path high")
        low_price = _positive(row["Low"], "Path low")
        if open_price >= stop_trigger:
            label = "STOP_1R_FIRST"
            event_position = position
            cover_cash = cost_profile.buy_cash_per_unit(open_price)
            break
        if open_price <= target_trigger:
            label = "TARGET_3R_FIRST"
            event_position = position
            cover_cash = cost_profile.buy_cash_per_unit(open_price)
            break
        if high_price >= stop_trigger:
            label = "STOP_1R_FIRST"
            event_position = position
            cover_cash = cost_profile.buy_cash_per_unit(stop_trigger)
            break
        if low_price <= target_trigger:
            label = "TARGET_3R_FIRST"
            event_position = position
            cover_cash = cost_profile.buy_cash_per_unit(target_trigger)
            break

    if label is None:
        label = "TIMEOUT_NO_BARRIER"
        event_position = boundary_position
        cover_cash = cost_profile.buy_cash_per_unit(frame.iloc[event_position]["Open"])

    return DirectionalLabelOutcome(
        valid=True,
        direction=direction,
        label=label,
        invalid_reason=None,
        decision_timestamp=frame.index[decision_position],
        entry_timestamp=frame.index[entry_position],
        event_end_timestamp=frame.index[event_position],
        entry_cashflow_per_unit=entry_proceeds,
        stop_trigger_price=stop_trigger,
        target_trigger_price=target_trigger,
        exit_cashflow_per_unit=-cover_cash,
        outcome_net_r=(entry_proceeds - cover_cash) / risk_unit,
    )


def build_directional_outcome_pair(frame, *, decision_position, signal_atr, cost_profile=BASELINE_COST_PROFILE):
    return {
        direction: directional_triple_barrier_label(
            frame,
            direction=direction,
            decision_position=decision_position,
            signal_atr=signal_atr,
            cost_profile=cost_profile,
        )
        for direction in DIRECTION_ORDER
    }


def select_bidirectional_action(long_expected_net_r, short_expected_net_r):
    values = {}
    for direction, value in (("LONG", long_expected_net_r), ("SHORT", short_expected_net_r)):
        if not isinstance(value, Real) or isinstance(value, bool):
            raise TypeError(f"{direction} expected net R must be numeric.")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"{direction} expected net R must be finite.")
        values[direction] = value
    if values["LONG"] <= POSITIVE_SCORE_THRESHOLD_NET_R and values["SHORT"] <= POSITIVE_SCORE_THRESHOLD_NET_R:
        return "HOLD_CASH"
    if values["LONG"] == values["SHORT"]:
        return "HOLD_CASH"
    return "LONG" if values["LONG"] > values["SHORT"] else "SHORT"


def bidirectional_hypothesis_declaration():
    if not fold_plan_is_causal():
        raise RuntimeError("Frozen bidirectional fold plan is not causal.")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "context_learning_report_sha256": CONTEXT_LEARNING_REPORT_SHA256,
        "context_forensic_report_sha256": CONTEXT_FORENSIC_REPORT_SHA256,
        "long_only_closure_status": LONG_ONLY_CLOSURE_STATUS,
        "active_resolution": "12h",
        "partition": "DEVELOPMENT",
        "asset_order": list(ASSET_ORDER),
        "direction_order": list(DIRECTION_ORDER),
        "action_order": list(ACTION_ORDER),
        "spot_feature_order": list(SPOT_FEATURE_COLUMNS),
        "context_feature_order": list(CONTEXT_FEATURE_COLUMNS),
        "spot_feature_count": len(SPOT_FEATURE_COLUMNS),
        "context_feature_count": len(CONTEXT_FEATURE_COLUMNS),
        "maximum_numeric_feature_count": len(ALL_NUMERIC_FEATURE_COLUMNS),
        "new_indicator_count": 0,
        "horizon_bars": HORIZON_BARS,
        "horizon_days": 30,
        "risk_atr_multiplier": RISK_ATR_MULTIPLIER,
        "target_r": TARGET_R,
        "stop_r": STOP_R,
        "positive_score_threshold_net_r": POSITIVE_SCORE_THRESHOLD_NET_R,
        "same_bar_ambiguity": "STOP_FIRST",
        "exact_positive_direction_tie_action": "HOLD_CASH",
        "fold_plan": [dict(fold) for fold in FOLD_PLAN],
        "variant_order": list(VARIANT_SPECS),
        "matched_control": dict(MATCHED_CONTROL),
        "directional_model_count_per_fold": len(VARIANT_SPECS) * len(DIRECTION_ORDER),
        "maximum_fold_model_fits": len(VARIANT_SPECS) * len(DIRECTION_ORDER) * len(FOLD_PLAN),
        "minimum_raw_selections_per_fold": MINIMUM_RAW_SELECTIONS_PER_FOLD,
        "minimum_nonoverlapping_selections_per_fold": MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        "minimum_positive_assets": MINIMUM_POSITIVE_ASSETS,
        "minimum_context_fold_wins": MINIMUM_CONTEXT_FOLD_WINS,
        "market_values_opened": False,
        "labels_generated": False,
        "model_training_executed": False,
        "feature_search_authorized": False,
        "hyperparameter_sweep_authorized": False,
        "threshold_sweep_authorized": False,
        "automatic_model_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": "KRAKEN_AI_V2_BIDIRECTIONAL_DEVELOPMENT_HYPOTHESIS_FROZEN_REVIEW_REQUIRED",
        "next_stage": "STATIC_REVIEW_THEN_IMPLEMENT_HASH_BOUND_BIDIRECTIONAL_DEVELOPMENT_RUNNER",
    }
