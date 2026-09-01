"""Frozen, nonexecuting contract for the real Kraken AI-driven V2 learner."""

import copy
from dataclasses import dataclass
import hashlib
import json

try:
    from kraken_ai_driven_v2_round_2_closure import (
        CLOSURE_STATUS as ROUND_2_CLOSURE_STATUS,
        RECORDED_REPORT_SHA256 as ROUND_2_REPORT_SHA256,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_round_2_closure import (
        CLOSURE_STATUS as ROUND_2_CLOSURE_STATUS,
        RECORDED_REPORT_SHA256 as ROUND_2_REPORT_SHA256,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-true-learning-contract-v1"
CONTRACT_ID = "kraken-ai-v2-true-learning-contract-v1"
STATUS = "KRAKEN_AI_V2_TRUE_LEARNING_CONTRACT_FROZEN_STAGE_2_AUDIT_REQUIRED"
STAGE_0_COMMIT = "70e7bca"
ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")

PARTITION_CONTRACT = {
    "training_partition": "DEVELOPMENT",
    "development_start_utc": "2019-01-01T00:00:00Z",
    "development_end_exclusive_utc": "2024-04-01T00:00:00Z",
    "calibration_start_utc": "2024-04-01T00:00:00Z",
    "calibration_end_exclusive_utc": "2025-04-01T00:00:00Z",
    "evaluation_start_utc": "2025-04-01T00:00:00Z",
    "evaluation_end_exclusive_utc": "2026-04-01T00:00:00Z",
    "calibration_opened": False,
    "evaluation_opened": False,
    "nondevelopment_rows_permitted_in_training": False,
    "partition_state_carry_permitted": False,
}

RESOLUTION_CONTRACT = {
    "selected_resolution": None,
    "selection_stage": "STAGE_2_NONPERFORMANCE_DATA_SUFFICIENCY_AUDIT",
    "selection_uses_strategy_performance": False,
    "selection_uses_prior_strategy_timeframe": False,
    "official_source_native_only": True,
    "minimum_distinct_candidate_resolutions": 2,
    "exact_resolution_required_before_label_generation": True,
    "candidate_dataset_requires_separate_lock": True,
    "selection_inputs": [
        "OBSERVED_ROW_COUNT",
        "CONTINUOUS_SEGMENT_LENGTHS",
        "KNOWN_GAP_COUNT",
        "FEATURE_WARMUP_LOSS",
        "HORIZON_RIGHT_CENSORING_COUNT",
        "PURGED_WALK_FORWARD_FOLD_CAPACITY",
    ],
    "prohibited_selection_inputs": [
        "RETURNS",
        "EXPECTANCY",
        "PROFIT_FACTOR",
        "WIN_RATE",
        "MODEL_SCORE",
        "ROUND_1_OR_ROUND_2_ROUTE_PERFORMANCE",
    ],
}

LABEL_CONTRACT = {
    "label_id": "kraken-ai-v2-next-open-triple-barrier-3r-1r-30d-v1",
    "decision_timestamp": "AFTER_COMPLETED_SOURCE_BAR_T",
    "entry_timestamp": "NEXT_OBSERVED_SOURCE_BAR_OPEN_T_PLUS_1",
    "entry_cost_profile": "kraken-tier1-taker-adverse-20260829-v1",
    "risk_unit": "1_5_X_SIGNAL_TIME_ATR_14",
    "target_barrier_net_r": 3.0,
    "stop_barrier_net_r": -1.0,
    "maximum_horizon_utc_days": 30,
    "class_order": [
        "TARGET_3R_FIRST",
        "STOP_1R_FIRST",
        "TIMEOUT_NO_BARRIER",
    ],
    "same_bar_barrier_policy": "STOP_FIRST_CONSERVATIVE",
    "gap_open_barrier_policy": "ADVERSE_EXECUTABLE_OPEN_FILL",
    "known_gap_policy": "INVALID_GAP_CENSORED_REPORTED_NOT_FIT",
    "right_edge_policy": "INVALID_RIGHT_CENSORED_REPORTED_NOT_FIT",
    "timeout_exit_policy": (
        "FIRST_OBSERVED_OPEN_AT_OR_AFTER_HORIZON_WITHIN_CONTINUOUS_SEGMENT"
    ),
    "primary_outputs": [
        "P_TARGET_3R_FIRST",
        "P_STOP_1R_FIRST",
        "P_TIMEOUT_NO_BARRIER",
    ],
}

FEATURE_CONTRACT = {
    "causal_cutoff": "COMPLETED_BAR_T_ONLY",
    "shared_model_with_asset_identity": True,
    "asset_order": list(ASSET_ORDER),
    "allowed_groups": [
        "PRICE_RETURNS_AND_MOMENTUM",
        "TREND_AND_MARKET_STRUCTURE",
        "VOLATILITY_AND_ATR_NORMALIZATION",
        "RELATIVE_VOLUME_AND_LIQUIDITY",
        "CAUSAL_SUPPORT_RESISTANCE",
        "MARKET_REGIME_CONTEXT",
        "CROSS_ASSET_CAUSAL_CONTEXT",
        "ASSET_IDENTITY",
        "CALENDAR_CONTEXT_AVAILABLE_AT_T",
    ],
    "prohibited_inputs": [
        "FUTURE_OHLCV_OR_FUTURE_DERIVED_VALUES",
        "CENTERED_OR_FORWARD_WINDOWS",
        "LABEL_OR_BARRIER_OUTCOME_FIELDS",
        "FULL_SAMPLE_SCALERS_OR_IMPUTERS",
        "CALIBRATION_ROWS",
        "EVALUATION_ROWS",
        "ROUND_1_OR_ROUND_2_PERFORMANCE_OUTCOMES_AS_FEATURES",
        "POST_DECISION_EXECUTION_OR_PNL_FIELDS",
    ],
    "fold_local_preprocessing_fit_required": True,
    "missing_value_indicator_required": True,
    "rolling_windows_exclude_future": True,
    "cross_asset_features_require_common_available_timestamp": True,
    "feature_schema_must_be_frozen_before_training": True,
}

MODEL_BUDGET = {
    "model_family_order": [
        "MULTINOMIAL_LOGISTIC_REGRESSION_BASELINE",
        "HISTOGRAM_GRADIENT_BOOSTED_TREES_CHALLENGER",
    ],
    "maximum_model_families": 2,
    "maximum_total_variants": 12,
    "maximum_random_seeds": 1,
    "fixed_random_seed": 1729,
    "parameters_learned_from_labels": True,
    "logistic_variant_budget": 6,
    "gradient_boosted_tree_variant_budget": 6,
    "fold_local_probability_calibration": (
        "MULTICLASS_TEMPERATURE_SCALING_ON_TRAINING_TAIL"
    ),
    "unlimited_automl_authorized": False,
    "unbounded_hyperparameter_search_authorized": False,
    "runtime_training_authorized": False,
    "automatic_challenger_promotion_authorized": False,
    "global_performance_leaderboard_authorized": False,
}

MODEL_VARIANTS = []
for c_value in (0.1, 1.0, 10.0):
    for class_weight in ("NONE", "BALANCED"):
        MODEL_VARIANTS.append(
            {
                "variant_id": (
                    f"logistic-c-{str(c_value).replace('.', '_')}-"
                    f"{class_weight.lower()}-v1"
                ),
                "family_id": "MULTINOMIAL_LOGISTIC_REGRESSION_BASELINE",
                "parameters": {
                    "c": c_value,
                    "class_weight": class_weight,
                    "solver": "LBFGS",
                    "maximum_iterations": 2000,
                    "random_seed": 1729,
                },
            }
        )
for learning_rate in (0.03, 0.08):
    for max_leaf_nodes in (7, 15, 31):
        MODEL_VARIANTS.append(
            {
                "variant_id": (
                    f"hist-gbt-lr-{str(learning_rate).replace('.', '_')}-"
                    f"leaves-{max_leaf_nodes}-v1"
                ),
                "family_id": "HISTOGRAM_GRADIENT_BOOSTED_TREES_CHALLENGER",
                "parameters": {
                    "learning_rate": learning_rate,
                    "max_leaf_nodes": max_leaf_nodes,
                    "maximum_iterations": 300,
                    "minimum_samples_leaf": 20,
                    "l2_regularization": 1.0,
                    "early_stopping": False,
                    "random_seed": 1729,
                },
            }
        )

DECISION_POLICY_CONTRACT = {
    "utility_formula": "3_X_P_TARGET_MINUS_1_X_P_STOP",
    "target_probability_threshold_candidates": [
        0.35,
        0.40,
        0.45,
        0.50,
        0.55,
        0.60,
        0.65,
        0.70,
    ],
    "minimum_predicted_utility_r": 0.10,
    "threshold_fit_scope": "TRAINING_FOLD_ONLY",
    "threshold_objective": (
        "MAXIMIZE_TRAINING_NET_EXPECTANCY_SUBJECT_TO_STAGE_2_SUPPORT_GATES"
    ),
    "tie_break_policy": "HIGHEST_TARGET_PROBABILITY_THRESHOLD",
    "no_threshold_pass_action": "HOLD_CASH",
    "abstention_is_valid": True,
    "threshold_frozen_inside_model_artifact": True,
}

WALK_FORWARD_CONTRACT = {
    "mode": "EXPANDING_TRAIN_THEN_LATER_VALIDATE",
    "minimum_fold_count": 3,
    "training_precedes_validation": True,
    "global_timestamp_boundaries_across_assets": True,
    "purge_utc_days": 30,
    "embargo_utc_days": 30,
    "overlap_control": "PURGED_SPLITS_PLUS_EVENT_UNIQUENESS_WEIGHT",
    "event_interval_overlap_purge_required": True,
    "preprocessing_fit_on_training_only": True,
    "probability_calibration_fit_on_training_only": True,
    "decision_threshold_fit_on_training_only": True,
    "validation_rows_used_for_refit": False,
    "fold_boundaries_selected_from_performance": False,
    "exact_fold_plan_status": "REQUIRED_AFTER_STAGE_2_BEFORE_TRAINING",
}

METRIC_AND_REJECTION_CONTRACT = {
    "predictive_metrics": [
        "MULTICLASS_LOG_LOSS_VS_FOLD_LOCAL_PRIOR",
        "TARGET_CLASS_BRIER_SCORE_VS_FOLD_LOCAL_PRIOR",
        "TARGET_CLASS_PRECISION_RECALL_AUC",
        "EXPECTED_CALIBRATION_ERROR",
        "PER_ASSET_PER_REGIME_CLASS_SUPPORT",
    ],
    "economic_metrics": [
        "BASELINE_AND_STRESS_NET_EXPECTANCY_R",
        "BASELINE_AND_STRESS_PROFIT_FACTOR",
        "BASELINE_AND_STRESS_MARKED_DRAWDOWN",
        "CHRONOLOGICAL_SLICE_STABILITY",
        "LARGEST_TRADE_NET_PROFIT_SHARE",
    ],
    "economic_simulation_uses_shared_safety_envelope": True,
    "minimum_net_reward_r": 3.0,
    "absolute_gates_required": True,
    "numeric_support_gates_status": (
        "FREEZE_AFTER_STAGE_2_NONPERFORMANCE_AUDIT_BEFORE_LABEL_GENERATION"
    ),
    "required_failure_action": "HOLD_CASH",
    "no_model_pass_is_valid_outcome": True,
    "validation_failure_can_open_calibration": False,
}

ARTIFACT_REQUIREMENTS = {
    "learned_model_bytes_sha256": True,
    "canonical_manifest_sha256": True,
    "training_code_sha256": True,
    "dataset_manifest_sha256": True,
    "feature_schema_sha256": True,
    "label_contract_sha256": True,
    "fold_plan_sha256": True,
    "training_row_identity_sha256": True,
    "out_of_fold_prediction_sha256": True,
    "environment_lock_sha256": True,
    "fitted_preprocessor_sha256": True,
    "probability_calibrator_sha256": True,
    "decision_policy_sha256": True,
    "identical_environment_reproduction_required": True,
    "runtime_model_immutable": True,
    "artifact_must_include_rejected_variants": True,
}

ACCEPTANCE_INVARIANTS = [
    "PARAMETERS_LEARNED_FROM_LABELED_DEVELOPMENT_EXAMPLES",
    "CAUSAL_CHRONOLOGICAL_REPRODUCIBLE_TRAINING",
    "DETERMINISTIC_MODEL_AND_METADATA_HASHES",
    "PREDICTIONS_ON_ROWS_NOT_USED_TO_FIT_MODEL_INSTANCE",
    "VERSIONED_CHALLENGER_REPRODUCIBLE_FROM_RECORDED_FEEDBACK",
    "NO_FUTURE_CALIBRATION_OR_EVALUATION_LEAKAGE",
    "IMMUTABLE_RUNTIME_MODEL",
    "EXPLICIT_SEPARATELY_AUTHORIZED_CANDIDATE_PROMOTION",
]


def _reference_contract():
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "protocol_id": PROTOCOL_ID,
        "contract_id": CONTRACT_ID,
        "stage_0_commit": STAGE_0_COMMIT,
        "round_2_closure_status": ROUND_2_CLOSURE_STATUS,
        "round_2_report_sha256": ROUND_2_REPORT_SHA256,
        "asset_order": list(ASSET_ORDER),
        "architecture_mode": (
            "SHARED_OFFLINE_CONTEXT_MODEL_WITH_ASSET_IDENTITY_AND_IMMUTABLE_RUNTIME"
        ),
        "partition_contract": copy.deepcopy(PARTITION_CONTRACT),
        "resolution_contract": copy.deepcopy(RESOLUTION_CONTRACT),
        "label_contract": copy.deepcopy(LABEL_CONTRACT),
        "feature_contract": copy.deepcopy(FEATURE_CONTRACT),
        "model_budget": copy.deepcopy(MODEL_BUDGET),
        "model_variants": copy.deepcopy(MODEL_VARIANTS),
        "decision_policy_contract": copy.deepcopy(DECISION_POLICY_CONTRACT),
        "walk_forward_contract": copy.deepcopy(WALK_FORWARD_CONTRACT),
        "metric_and_rejection_contract": copy.deepcopy(
            METRIC_AND_REJECTION_CONTRACT
        ),
        "artifact_requirements": copy.deepcopy(ARTIFACT_REQUIREMENTS),
        "acceptance_invariants": list(ACCEPTANCE_INVARIANTS),
        "learning_mode": "OFFLINE_VERSIONED_CHALLENGER_ONLY",
        "runtime_mode": "IMMUTABLE_APPROVED_ARTIFACT_INFERENCE_ONLY",
        "candidate_promotion_mode": "SEPARATE_EXPLICIT_OPERATOR_AUTHORIZATION",
    }


_REFERENCE_CONTRACT = _reference_contract()


@dataclass(frozen=True)
class LockedTrueLearningContract:
    payload: dict
    sha256: str


def _canonical_json_bytes(value):
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("True Learning Contract must be canonical JSON data.") from exc


def lock_true_learning_contract(contract=None):
    """Lock the exact learning contract without opening data or training."""

    candidate = copy.deepcopy(
        _REFERENCE_CONTRACT if contract is None else contract
    )
    if candidate != _REFERENCE_CONTRACT:
        raise ValueError("True Learning Contract mismatch after registration.")
    digest = hashlib.sha256(_canonical_json_bytes(candidate)).hexdigest()
    return LockedTrueLearningContract(payload=candidate, sha256=digest)


TRUE_LEARNING_CONTRACT_LOCK = lock_true_learning_contract()


def learning_contract_declaration():
    """Return the frozen contract and every explicit nonauthorization."""

    declaration = copy.deepcopy(TRUE_LEARNING_CONTRACT_LOCK.payload)
    declaration.update(
        {
            "contract_sha256": TRUE_LEARNING_CONTRACT_LOCK.sha256,
            "round_2_closed": True,
            "round_2_rerun_authorized": False,
            "rule_discovery_foundation_complete": True,
            "true_learning_contract_frozen": True,
            "data_sufficiency_audit_implemented": False,
            "resolution_selected": False,
            "feature_component_implemented": False,
            "label_component_implemented": False,
            "learning_engine_implemented": False,
            "learned_model_artifact_created": False,
            "dataset_opened": False,
            "development_data_opened": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "labels_generated": False,
            "model_training_authorized": False,
            "model_training_executed": False,
            "walk_forward_executed": False,
            "parameter_sweep_executed": False,
            "automatic_model_selection_executed": False,
            "runtime_learning_authorized": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
            "next_stage": (
                "IMPLEMENT_STAGE_2_NONPERFORMANCE_DATA_SUFFICIENCY_AND_RESOLUTION_AUDIT"
            ),
        }
    )
    return declaration
