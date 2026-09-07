"""Frozen regime-gated selective Development hypothesis; no real fitting."""

from __future__ import annotations

import math
from numbers import Real

try:
    from kraken_ai_driven_v2_bidirectional_hypothesis import (
        CONTEXT_FEATURE_COLUMNS,
        DIRECTION_ORDER,
        FOLD_PLAN,
        HORIZON_BARS,
        RISK_ATR_MULTIPLIER,
        SPOT_FEATURE_COLUMNS,
        STOP_R,
        TARGET_R,
        fold_plan_is_causal,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_bidirectional_hypothesis import (
        CONTEXT_FEATURE_COLUMNS,
        DIRECTION_ORDER,
        FOLD_PLAN,
        HORIZON_BARS,
        RISK_ATR_MULTIPLIER,
        SPOT_FEATURE_COLUMNS,
        STOP_R,
        TARGET_R,
        fold_plan_is_causal,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-v2-regime-gated-selective-development-hypothesis-v1"
)
COMPONENT_ID = "kraken-ai-v2-regime-gated-selective-development-hypothesis-v1"
PARENT_COMMIT = "0511fe567c8da4afc436697771ac7d9d1d281f2b"
BIDIRECTIONAL_LEARNING_REPORT_SHA256 = (
    "7176ca3a005b7bdbfbdcbc2259fafd11c154ee45b0517eab26894e675aa26b3f"
)
BIDIRECTIONAL_FORENSIC_RESULT_SHA256 = (
    "eaad73eadeb83a19dad4031edb19c4e7ebeb0c50c3681394e41e41ded50a4920"
)
PRIOR_CLOSURE_STATUS = (
    "KRAKEN_AI_V2_BIDIRECTIONAL_NO_VIABLE_HYPOTHESIS_HOLD_CASH"
)
TERMINAL_FAILURE_STATUS = (
    "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_NO_VIABLE_HYPOTHESIS_"
    "STOP_KRAKEN_12H_RESEARCH"
)

REGIME_ORDER = ("LONG_REGIME", "SHORT_REGIME", "NEUTRAL")
ACTION_ORDER = ("LONG", "SHORT", "HOLD_CASH")
REGIME_FEATURE_COLUMNS = (
    "return_14",
    "ema_12_48_spread",
    "ema_180_distance",
)
CONTEXT_CONFIRMATION_FEATURE_COLUMNS = (
    "funding_rate_zscore_60",
    "open_interest_log_change_6",
    "basis_change_1",
)
FUNDING_CROWDING_Z_LIMIT = 1.0
PROBABILITY_SAFETY_BUFFER = 0.05
INNER_BASE_FIT_FRACTION = 0.75
MINIMUM_BASE_CLASS_COUNT = 20
MINIMUM_CALIBRATION_CLASS_COUNT = 10
MINIMUM_RAW_SELECTIONS_PER_FOLD = 30
MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD = 10
MINIMUM_POSITIVE_ASSETS = 2
MINIMUM_CONTEXT_FOLD_WINS = 2

LOGISTIC_PARAMETERS = {
    "C": 1.0,
    "class_weight": None,
    "solver": "lbfgs",
    "max_iter": 2000,
    "random_state": 1729,
}
CALIBRATOR_PARAMETERS = {"method": "sigmoid"}

VARIANT_SPECS = {
    "SPOT_REGIME_CALIBRATED_LOGISTIC_CONTROL": {
        "feature_set": "SPOT_ONLY",
        "numeric_feature_count": len(SPOT_FEATURE_COLUMNS),
        "objective": "CALIBRATED_BINARY_POSITIVE_NET_R_PROBABILITY",
        "model_family": "LOGISTIC_REGRESSION",
        "model_parameters": LOGISTIC_PARAMETERS,
        "derivatives_confirmation_required": False,
        "incremental_context_gate_required": False,
    },
    "SPOT_CONTEXT_REGIME_CALIBRATED_LOGISTIC": {
        "feature_set": "SPOT_PLUS_DERIVATIVES_CONTEXT",
        "numeric_feature_count": len(SPOT_FEATURE_COLUMNS)
        + len(CONTEXT_FEATURE_COLUMNS),
        "objective": "CALIBRATED_BINARY_POSITIVE_NET_R_PROBABILITY",
        "model_family": "LOGISTIC_REGRESSION",
        "model_parameters": LOGISTIC_PARAMETERS,
        "derivatives_confirmation_required": True,
        "incremental_context_gate_required": True,
    },
}
MATCHED_CONTROL = {
    "SPOT_CONTEXT_REGIME_CALIBRATED_LOGISTIC": (
        "SPOT_REGIME_CALIBRATED_LOGISTIC_CONTROL"
    )
}


def _finite(value, name):
    if not isinstance(value, Real) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric.")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def _feature(features, name):
    try:
        value = features[name]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Missing frozen feature: {name}.") from exc
    return _finite(value, name)


def classify_spot_regime(features):
    """Return one strict directional regime from three existing spot features."""

    values = tuple(_feature(features, name) for name in REGIME_FEATURE_COLUMNS)
    if all(value > 0.0 for value in values):
        return "LONG_REGIME"
    if all(value < 0.0 for value in values):
        return "SHORT_REGIME"
    return "NEUTRAL"


def context_confirms_direction(features, direction):
    """Apply the frozen participation, basis-direction and crowding checks."""

    if direction not in DIRECTION_ORDER:
        raise ValueError(f"Direction must be one of {DIRECTION_ORDER}.")
    funding_z = _feature(features, "funding_rate_zscore_60")
    open_interest_change = _feature(features, "open_interest_log_change_6")
    basis_change = _feature(features, "basis_change_1")
    if open_interest_change <= 0.0:
        return False
    if direction == "LONG":
        return basis_change > 0.0 and funding_z <= FUNDING_CROWDING_Z_LIMIT
    return basis_change < 0.0 and funding_z >= -FUNDING_CROWDING_Z_LIMIT


def break_even_positive_probability(mean_positive_net_r, mean_nonpositive_net_r):
    """Derive the probability that gives zero expected net R."""

    positive = _finite(mean_positive_net_r, "Mean positive net R")
    nonpositive = _finite(mean_nonpositive_net_r, "Mean nonpositive net R")
    if positive <= 0.0:
        raise ValueError("Mean positive net R must be strictly positive.")
    if nonpositive >= 0.0:
        raise ValueError("Mean nonpositive net R must be strictly negative.")
    return -nonpositive / (positive - nonpositive)


def required_positive_probability(mean_positive_net_r, mean_nonpositive_net_r):
    break_even = break_even_positive_probability(
        mean_positive_net_r, mean_nonpositive_net_r
    )
    return min(1.0, break_even + PROBABILITY_SAFETY_BUFFER)


def select_regime_gated_action(
    regime,
    *,
    long_probability,
    short_probability,
    long_required_probability,
    short_required_probability,
    context_confirmed=True,
):
    """Select only the regime direction above its frozen economic threshold."""

    if regime not in REGIME_ORDER:
        raise ValueError(f"Regime must be one of {REGIME_ORDER}.")
    if not isinstance(context_confirmed, bool):
        raise TypeError("Context confirmation must be Boolean.")
    values = {
        "LONG": _finite(long_probability, "LONG probability"),
        "SHORT": _finite(short_probability, "SHORT probability"),
    }
    required = {
        "LONG": _finite(long_required_probability, "LONG required probability"),
        "SHORT": _finite(short_required_probability, "SHORT required probability"),
    }
    if any(not 0.0 <= value <= 1.0 for value in (*values.values(), *required.values())):
        raise ValueError("Probabilities must remain inside [0, 1].")
    if regime == "NEUTRAL" or not context_confirmed:
        return "HOLD_CASH"
    direction = "LONG" if regime == "LONG_REGIME" else "SHORT"
    return direction if values[direction] > required[direction] else "HOLD_CASH"


def regime_gated_selective_hypothesis_declaration():
    if not fold_plan_is_causal():
        raise RuntimeError("Inherited Development fold plan is not causal.")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "bidirectional_learning_report_sha256": BIDIRECTIONAL_LEARNING_REPORT_SHA256,
        "bidirectional_forensic_result_sha256": BIDIRECTIONAL_FORENSIC_RESULT_SHA256,
        "prior_closure_status": PRIOR_CLOSURE_STATUS,
        "active_resolution": "12h",
        "partition": "DEVELOPMENT",
        "direction_order": list(DIRECTION_ORDER),
        "regime_order": list(REGIME_ORDER),
        "action_order": list(ACTION_ORDER),
        "spot_feature_order": list(SPOT_FEATURE_COLUMNS),
        "context_feature_order": list(CONTEXT_FEATURE_COLUMNS),
        "regime_feature_order": list(REGIME_FEATURE_COLUMNS),
        "context_confirmation_feature_order": list(
            CONTEXT_CONFIRMATION_FEATURE_COLUMNS
        ),
        "new_indicator_count": 0,
        "variant_order": list(VARIANT_SPECS),
        "matched_control": dict(MATCHED_CONTROL),
        "fold_plan": [dict(fold) for fold in FOLD_PLAN],
        "horizon_bars": HORIZON_BARS,
        "horizon_days": 30,
        "risk_atr_multiplier": RISK_ATR_MULTIPLIER,
        "target_r": TARGET_R,
        "stop_r": STOP_R,
        "target_definition": "OUTCOME_NET_R_STRICTLY_POSITIVE",
        "inner_base_fit_fraction": INNER_BASE_FIT_FRACTION,
        "calibration_method": "SIGMOID",
        "class_weight": None,
        "probability_safety_buffer": PROBABILITY_SAFETY_BUFFER,
        "funding_crowding_z_limit": FUNDING_CROWDING_Z_LIMIT,
        "minimum_base_class_count": MINIMUM_BASE_CLASS_COUNT,
        "minimum_calibration_class_count": MINIMUM_CALIBRATION_CLASS_COUNT,
        "maximum_base_model_fits": len(VARIANT_SPECS)
        * len(DIRECTION_ORDER)
        * len(FOLD_PLAN),
        "maximum_calibrator_fits": len(VARIANT_SPECS)
        * len(DIRECTION_ORDER)
        * len(FOLD_PLAN),
        "maximum_total_fits": 2
        * len(VARIANT_SPECS)
        * len(DIRECTION_ORDER)
        * len(FOLD_PLAN),
        "minimum_raw_selections_per_fold": MINIMUM_RAW_SELECTIONS_PER_FOLD,
        "minimum_nonoverlapping_selections_per_fold": (
            MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD
        ),
        "minimum_positive_assets": MINIMUM_POSITIVE_ASSETS,
        "minimum_context_fold_wins": MINIMUM_CONTEXT_FOLD_WINS,
        "brier_skill_required_every_supported_direction_fold": True,
        "one_economic_development_execution": True,
        "terminal_failure_status": TERMINAL_FAILURE_STATUS,
        "technical_recovery_must_preserve_identical_hypothesis": True,
        "source_values_opened": False,
        "labels_generated": False,
        "model_training_executed": False,
        "direct_net_r_regression_authorized": False,
        "feature_search_authorized": False,
        "hyperparameter_sweep_authorized": False,
        "threshold_sweep_authorized": False,
        "top_k_rule_authorized": False,
        "automatic_model_selection": False,
        "automatic_successor_authorized": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": (
            "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_HYPOTHESIS_"
            "FROZEN_IMPLEMENTATION_REVIEW_REQUIRED"
        ),
        "next_stage": (
            "STATIC_REVIEW_THEN_IMPLEMENT_HASH_BOUND_REGIME_GATED_"
            "SELECTIVE_DEVELOPMENT_RUNNER"
        ),
    }
