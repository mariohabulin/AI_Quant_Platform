import copy
import math
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_true_learning_contract import (
    ACCEPTANCE_INVARIANTS,
    ARTIFACT_REQUIREMENTS,
    ASSET_ORDER,
    CONTRACT_ID,
    DECISION_POLICY_CONTRACT,
    FEATURE_CONTRACT,
    LABEL_CONTRACT,
    MODEL_BUDGET,
    MODEL_VARIANTS,
    PARTITION_CONTRACT,
    PROTOCOL_ID,
    RESOLUTION_CONTRACT,
    STAGE_0_COMMIT,
    STATUS,
    TRUE_LEARNING_CONTRACT_LOCK,
    WALK_FORWARD_CONTRACT,
    learning_contract_declaration,
    lock_true_learning_contract,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_TRUE_LEARNING_CONTRACT_V1.md"


def test_contract_identity_records_scope_correction_and_stage_zero_lineage():
    declaration = learning_contract_declaration()

    assert declaration["status"] == STATUS
    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["contract_id"] == CONTRACT_ID
    assert declaration["stage_0_commit"] == STAGE_0_COMMIT == "70e7bca"
    assert declaration["round_2_closed"] is True
    assert declaration["round_2_rerun_authorized"] is False
    assert declaration["round_2_report_sha256"] == (
        "5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01"
    )
    assert declaration["rule_discovery_foundation_complete"] is True
    assert declaration["true_learning_contract_frozen"] is True


def test_label_is_causal_next_open_three_class_three_r_before_one_r_target():
    assert LABEL_CONTRACT == {
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
        "timeout_exit_policy": "FIRST_OBSERVED_OPEN_AT_OR_AFTER_HORIZON_WITHIN_CONTINUOUS_SEGMENT",
        "primary_outputs": [
            "P_TARGET_3R_FIRST",
            "P_STOP_1R_FIRST",
            "P_TIMEOUT_NO_BARRIER",
        ],
    }


def test_resolution_is_deliberately_unselected_until_nonperformance_audit():
    assert RESOLUTION_CONTRACT["selected_resolution"] is None
    assert RESOLUTION_CONTRACT["selection_stage"] == (
        "STAGE_2_NONPERFORMANCE_DATA_SUFFICIENCY_AUDIT"
    )
    assert RESOLUTION_CONTRACT["selection_uses_strategy_performance"] is False
    assert RESOLUTION_CONTRACT["selection_uses_prior_strategy_timeframe"] is False
    assert RESOLUTION_CONTRACT["official_source_native_only"] is True
    assert RESOLUTION_CONTRACT["minimum_distinct_candidate_resolutions"] == 2
    assert RESOLUTION_CONTRACT["exact_resolution_required_before_label_generation"] is True


def test_feature_contract_allows_context_but_forbids_future_and_partition_leakage():
    assert FEATURE_CONTRACT["causal_cutoff"] == "COMPLETED_BAR_T_ONLY"
    assert FEATURE_CONTRACT["shared_model_with_asset_identity"] is True
    assert FEATURE_CONTRACT["allowed_groups"] == [
        "PRICE_RETURNS_AND_MOMENTUM",
        "TREND_AND_MARKET_STRUCTURE",
        "VOLATILITY_AND_ATR_NORMALIZATION",
        "RELATIVE_VOLUME_AND_LIQUIDITY",
        "CAUSAL_SUPPORT_RESISTANCE",
        "MARKET_REGIME_CONTEXT",
        "CROSS_ASSET_CAUSAL_CONTEXT",
        "ASSET_IDENTITY",
        "CALENDAR_CONTEXT_AVAILABLE_AT_T",
    ]
    assert set(FEATURE_CONTRACT["prohibited_inputs"]) == {
        "FUTURE_OHLCV_OR_FUTURE_DERIVED_VALUES",
        "CENTERED_OR_FORWARD_WINDOWS",
        "LABEL_OR_BARRIER_OUTCOME_FIELDS",
        "FULL_SAMPLE_SCALERS_OR_IMPUTERS",
        "CALIBRATION_ROWS",
        "EVALUATION_ROWS",
        "ROUND_1_OR_ROUND_2_PERFORMANCE_OUTCOMES_AS_FEATURES",
        "POST_DECISION_EXECUTION_OR_PNL_FIELDS",
    }
    assert FEATURE_CONTRACT["fold_local_preprocessing_fit_required"] is True
    assert FEATURE_CONTRACT["missing_value_indicator_required"] is True


def test_model_budget_is_bounded_offline_and_learns_parameters():
    assert MODEL_BUDGET["model_family_order"] == [
        "MULTINOMIAL_LOGISTIC_REGRESSION_BASELINE",
        "HISTOGRAM_GRADIENT_BOOSTED_TREES_CHALLENGER",
    ]
    assert MODEL_BUDGET["maximum_model_families"] == 2
    assert MODEL_BUDGET["maximum_total_variants"] == 12
    assert MODEL_BUDGET["maximum_random_seeds"] == 1
    assert MODEL_BUDGET["fixed_random_seed"] == 1729
    assert MODEL_BUDGET["parameters_learned_from_labels"] is True
    assert MODEL_BUDGET["unlimited_automl_authorized"] is False
    assert MODEL_BUDGET["unbounded_hyperparameter_search_authorized"] is False
    assert MODEL_BUDGET["runtime_training_authorized"] is False
    assert MODEL_BUDGET["automatic_challenger_promotion_authorized"] is False


def test_model_variant_grid_is_exact_and_exhaustive_before_training():
    assert len(MODEL_VARIANTS) == 12
    assert len({item["variant_id"] for item in MODEL_VARIANTS}) == 12
    logistic = [
        item
        for item in MODEL_VARIANTS
        if item["family_id"] == "MULTINOMIAL_LOGISTIC_REGRESSION_BASELINE"
    ]
    boosted = [
        item
        for item in MODEL_VARIANTS
        if item["family_id"] == "HISTOGRAM_GRADIENT_BOOSTED_TREES_CHALLENGER"
    ]
    assert len(logistic) == len(boosted) == 6
    assert {(item["parameters"]["c"], item["parameters"]["class_weight"]) for item in logistic} == {
        (0.1, "NONE"),
        (0.1, "BALANCED"),
        (1.0, "NONE"),
        (1.0, "BALANCED"),
        (10.0, "NONE"),
        (10.0, "BALANCED"),
    }
    assert {
        (
            item["parameters"]["learning_rate"],
            item["parameters"]["max_leaf_nodes"],
        )
        for item in boosted
    } == {
        (0.03, 7),
        (0.03, 15),
        (0.03, 31),
        (0.08, 7),
        (0.08, 15),
        (0.08, 31),
    }
    assert all(item["parameters"]["early_stopping"] is False for item in boosted)


def test_decision_policy_is_bounded_fold_local_and_can_abstain():
    assert DECISION_POLICY_CONTRACT == {
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
        "threshold_objective": "MAXIMIZE_TRAINING_NET_EXPECTANCY_SUBJECT_TO_STAGE_2_SUPPORT_GATES",
        "tie_break_policy": "HIGHEST_TARGET_PROBABILITY_THRESHOLD",
        "no_threshold_pass_action": "HOLD_CASH",
        "abstention_is_valid": True,
        "threshold_frozen_inside_model_artifact": True,
    }


def test_walk_forward_is_development_only_chronological_purged_and_embargoed():
    assert PARTITION_CONTRACT["training_partition"] == "DEVELOPMENT"
    assert PARTITION_CONTRACT["development_start_utc"] == "2019-01-01T00:00:00Z"
    assert PARTITION_CONTRACT["development_end_exclusive_utc"] == (
        "2024-04-01T00:00:00Z"
    )
    assert PARTITION_CONTRACT["calibration_opened"] is False
    assert PARTITION_CONTRACT["evaluation_opened"] is False
    assert WALK_FORWARD_CONTRACT["mode"] == "EXPANDING_TRAIN_THEN_LATER_VALIDATE"
    assert WALK_FORWARD_CONTRACT["minimum_fold_count"] == 3
    assert WALK_FORWARD_CONTRACT["training_precedes_validation"] is True
    assert WALK_FORWARD_CONTRACT["purge_utc_days"] == 30
    assert WALK_FORWARD_CONTRACT["embargo_utc_days"] == 30
    assert WALK_FORWARD_CONTRACT["overlap_control"] == (
        "PURGED_SPLITS_PLUS_EVENT_UNIQUENESS_WEIGHT"
    )
    assert WALK_FORWARD_CONTRACT["event_interval_overlap_purge_required"] is True
    assert WALK_FORWARD_CONTRACT["fold_boundaries_selected_from_performance"] is False
    assert WALK_FORWARD_CONTRACT["exact_fold_plan_status"] == (
        "REQUIRED_AFTER_STAGE_2_BEFORE_TRAINING"
    )


def test_artifact_contract_requires_reproducible_model_and_prediction_identity():
    assert ARTIFACT_REQUIREMENTS["learned_model_bytes_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["canonical_manifest_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["training_code_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["dataset_manifest_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["feature_schema_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["label_contract_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["fold_plan_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["training_row_identity_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["out_of_fold_prediction_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["environment_lock_sha256"] is True
    assert ARTIFACT_REQUIREMENTS["identical_environment_reproduction_required"] is True
    assert ARTIFACT_REQUIREMENTS["runtime_model_immutable"] is True


def test_acceptance_invariants_define_when_true_learning_claim_becomes_valid():
    assert ACCEPTANCE_INVARIANTS == [
        "PARAMETERS_LEARNED_FROM_LABELED_DEVELOPMENT_EXAMPLES",
        "CAUSAL_CHRONOLOGICAL_REPRODUCIBLE_TRAINING",
        "DETERMINISTIC_MODEL_AND_METADATA_HASHES",
        "PREDICTIONS_ON_ROWS_NOT_USED_TO_FIT_MODEL_INSTANCE",
        "VERSIONED_CHALLENGER_REPRODUCIBLE_FROM_RECORDED_FEEDBACK",
        "NO_FUTURE_CALIBRATION_OR_EVALUATION_LEAKAGE",
        "IMMUTABLE_RUNTIME_MODEL",
        "EXPLICIT_SEPARATELY_AUTHORIZED_CANDIDATE_PROMOTION",
    ]


def test_contract_lock_is_canonical_stable_and_returns_deep_copies():
    first = lock_true_learning_contract()
    second = lock_true_learning_contract()

    assert first.sha256 == second.sha256 == TRUE_LEARNING_CONTRACT_LOCK.sha256
    assert len(first.sha256) == 64
    first.payload["label_contract"]["target_barrier_net_r"] = 99.0
    assert second.payload["label_contract"]["target_barrier_net_r"] == 3.0


@pytest.mark.parametrize(
    "path,value",
    [
        (("label_contract", "target_barrier_net_r"), 2.0),
        (("resolution_contract", "selected_resolution"), "6h"),
        (("model_budget", "runtime_training_authorized"), True),
        (("walk_forward_contract", "fold_boundaries_selected_from_performance"), True),
    ],
)
def test_post_registration_contract_mutation_is_rejected(path, value):
    changed = copy.deepcopy(TRUE_LEARNING_CONTRACT_LOCK.payload)
    changed[path[0]][path[1]] = value

    with pytest.raises(ValueError, match="True Learning Contract mismatch"):
        lock_true_learning_contract(changed)


def test_noncanonical_nan_is_rejected():
    changed = copy.deepcopy(TRUE_LEARNING_CONTRACT_LOCK.payload)
    changed["model_budget"]["invalid"] = math.nan

    with pytest.raises(ValueError, match="True Learning Contract mismatch"):
        lock_true_learning_contract(changed)


def test_declaration_opens_no_data_and_authorizes_no_training_or_candidate():
    declaration = learning_contract_declaration()

    for field in (
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "labels_generated",
        "model_training_executed",
        "walk_forward_executed",
        "parameter_sweep_executed",
        "automatic_model_selection_executed",
        "runtime_learning_authorized",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        assert declaration[field] is False
    assert declaration["next_stage"] == (
        "IMPLEMENT_STAGE_2_NONPERFORMANCE_DATA_SUFFICIENCY_AND_RESOLUTION_AUDIT"
    )


def test_protocol_explains_learning_boundary_in_plain_language():
    text = PROTOCOL.read_text(encoding="utf-8")

    for phrase in (
        STATUS,
        PROTOCOL_ID,
        "What one training example means",
        "TARGET_3R_FIRST",
        "STOP_1R_FIRST",
        "TIMEOUT_NO_BARRIER",
        "Resolution is not selected in Stage 1",
        "The model learns parameters; we do not write the decision rules",
        "Calibration and Evaluation remain unopened",
        "Candidate v2 remains unauthorized",
        "learned model artifact",
    ):
        assert phrase in text
