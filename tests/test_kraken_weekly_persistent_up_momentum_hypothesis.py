import copy
import os
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_weekly_persistent_up_momentum_hypothesis import (
    ACTION_ORDER,
    ASSET_ORDER,
    COMPONENT_ID,
    CONTROL_ORDER,
    COST_PROFILES,
    DATASET_ID,
    DATASET_MANIFEST_SHA256,
    DECISION_RESOLUTION,
    DEVELOPMENT_GATES,
    DEVELOPMENT_SLICES,
    MOMENTUM_LOOKBACK_WEEKS,
    OUTCOME_ORDER,
    PARENT_COMMIT,
    PRIMARY_RULE_ID,
    PROTOCOL_ID,
    SAFETY_FLAGS,
    SOURCE_RESOLUTION,
    TERMINAL_12H_STATUS,
    WEEKLY_OBSERVATION_COUNT,
    WEEK_START,
    validate_weekly_persistent_up_momentum_hypothesis,
    weekly_persistent_up_momentum_hypothesis_declaration,
)


def test_declaration_freezes_identity_lineage_and_existing_daily_source():
    declaration = weekly_persistent_up_momentum_hypothesis_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["component_id"] == COMPONENT_ID
    assert declaration["parent_commit"] == PARENT_COMMIT
    assert declaration["parent_commit"].startswith("a9307df")
    assert declaration["dataset_id"] == DATASET_ID
    assert declaration["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert declaration["asset_order"] == list(ASSET_ORDER)
    assert declaration["terminal_12h_status"] == TERMINAL_12H_STATUS


def test_weekly_boundary_is_exact_complete_utc_week_with_no_fill():
    boundary = weekly_persistent_up_momentum_hypothesis_declaration()[
        "configuration"
    ]["weekly_boundary"]

    assert SOURCE_RESOLUTION == "1d"
    assert DECISION_RESOLUTION == "1w"
    assert WEEK_START == "MONDAY_00_00_UTC"
    assert WEEKLY_OBSERVATION_COUNT == 7
    assert boundary["timezone"] == "UTC"
    assert boundary["required_native_daily_observations"] == 7
    assert boundary["incomplete_week_policy"] == "INVALID_NO_FILL"
    assert boundary["provider_gap_policy"] == "INVALIDATE_WEEK_AND_RESET_LOOKBACK"
    assert boundary["market_proxy_requires_all_assets_complete"] is True


def test_primary_rule_is_one_four_week_persistent_up_momentum_hypothesis():
    declaration = weekly_persistent_up_momentum_hypothesis_declaration()
    signal = declaration["configuration"]["causal_signal"]

    assert declaration["primary_rule_id"] == PRIMARY_RULE_ID
    assert MOMENTUM_LOOKBACK_WEEKS == 4
    assert signal["persistent_up_rule"] == "STATE_T_MINUS_1_UP_AND_STATE_T_UP"
    assert signal["asset_momentum_rule"] == "ASSET_FOUR_WEEK_RETURN_STRICTLY_POSITIVE"
    assert signal["eligible_action"] == "LONG"
    assert signal["fallback_action"] == "HOLD_CASH"
    assert signal["future_information_permitted"] is False
    assert declaration["action_order"] == list(ACTION_ORDER)


def test_fixed_next_week_outcome_changes_the_closed_12h_target():
    outcome = weekly_persistent_up_momentum_hypothesis_declaration()[
        "configuration"
    ]["outcome"]

    assert outcome["forward_horizon_weeks"] == 1
    assert outcome["outcome_order"] == list(OUTCOME_ORDER)
    assert outcome["zero_net_return_class"] == "NEXT_WEEK_NET_NONPOSITIVE"
    assert outcome["signal_feasibility_only"] is True
    assert outcome["protective_stop_implemented"] is False
    assert outcome["position_sizing_implemented"] is False
    assert outcome["portfolio_simulation_authorized"] is False
    assert outcome["adverse_price_rate_formula"] == (
        "SLIPPAGE_PLUS_HALF_FULL_SPREAD"
    )
    assert outcome["entry_cash_formula"] == (
        "ENTRY_FILL_TIMES_ONE_PLUS_COMMISSION"
    )
    assert outcome["exit_proceeds_formula"] == (
        "EXIT_FILL_TIMES_ONE_MINUS_COMMISSION"
    )
    assert outcome["net_return_formula"] == (
        "EXIT_PROCEEDS_MINUS_ENTRY_CASH_DIVIDED_BY_ENTRY_CASH"
    )
    assert outcome["consecutive_event_policy"] == (
        "ADJACENT_NONOVERLAPPING_EVENTS_ALLOWED"
    )


def test_two_controls_are_fixed_non_promotable_mechanism_ablations():
    declaration = weekly_persistent_up_momentum_hypothesis_declaration()
    controls = declaration["configuration"]["controls"]

    assert declaration["control_order"] == list(CONTROL_ORDER)
    assert controls["control_order"] == list(CONTROL_ORDER)
    assert controls["candidate_eligible"] is False
    assert controls["ranking_authorized"] is False
    assert controls["purpose"] == "MECHANISM_ABLATION_ONLY"
    assert controls["shared_timing_outcome_and_cost_boundary"] is True
    assert controls["definitions"] == {
        "CURRENT_UP_ONLY_ASSET_MOMENTUM_CONTROL": (
            "STATE_T_UP_AND_ASSET_FOUR_WEEK_RETURN_STRICTLY_POSITIVE"
        ),
        "PERSISTENT_UP_MARKET_ONLY_CONTROL": "STATE_T_MINUS_1_UP_AND_STATE_T_UP",
    }


def test_costs_preserve_existing_adverse_baseline_and_stronger_stress():
    baseline = COST_PROFILES["KRAKEN_BASELINE_ADVERSE"]
    stress = COST_PROFILES["KRAKEN_STRESS_ADVERSE"]

    assert baseline["profile_id"] == "kraken-tier1-taker-adverse-20260829-v1"
    assert baseline["commission_rate_each_side"] == stress["commission_rate_each_side"] == 0.008
    assert baseline["slippage_rate_each_side"] == 0.0015
    assert stress["slippage_rate_each_side"] == 0.003
    assert baseline["full_spread_rate"] == 0.003
    assert stress["full_spread_rate"] == 0.006


def test_development_slices_and_gates_are_frozen_before_data_access():
    development = weekly_persistent_up_momentum_hypothesis_declaration()[
        "configuration"
    ]["development"]

    assert development["slices"] == [dict(item) for item in DEVELOPMENT_SLICES]
    assert development["gates"] == DEVELOPMENT_GATES
    assert development["model_family"] == "NONE_RULE_BASED_SIGNAL_BASELINE"
    assert development["model_fit_count"] == 0
    assert development["single_future_execution_ceiling"] == 1
    assert development["threshold_rescue_authorized"] is False


def test_novelty_boundary_does_not_reopen_daily_rules_or_12h_learning():
    novelty = weekly_persistent_up_momentum_hypothesis_declaration()[
        "configuration"
    ]["novelty"]

    assert novelty["prior_daily_rule_rounds_reopened"] is False
    assert novelty["prior_12h_learning_reopened"] is False
    assert novelty["decision_target"] == "FIXED_NEXT_WEEK_NET_RETURN"
    assert novelty["state_transition_required"] == "UP_TO_UP"
    assert novelty["literature_informed_derivative_not_replication"] is True


def test_every_data_learning_and_execution_flag_remains_false():
    declaration = weekly_persistent_up_momentum_hypothesis_declaration()

    assert all(declaration[name] is False for name in SAFETY_FLAGS)
    assert declaration["status"].endswith("FROZEN_NO_DATA_OR_RUN")
    assert declaration["next_stage"] == "SEPARATE_SYNTHETIC_ONLY_IMPLEMENTATION_DECISION"


def test_frozen_declaration_validates_and_return_is_independent_copy():
    declaration = weekly_persistent_up_momentum_hypothesis_declaration()
    validated = validate_weekly_persistent_up_momentum_hypothesis(declaration)

    assert validated == declaration
    validated["configuration"]["causal_signal"]["momentum_lookback_weeks"] = 99
    assert (
        weekly_persistent_up_momentum_hypothesis_declaration()["configuration"]
        ["causal_signal"]["momentum_lookback_weeks"]
        == 4
    )


def test_changed_parameter_or_open_authorization_fails_closed():
    for mutation in ("parameter", "authorization"):
        candidate = copy.deepcopy(weekly_persistent_up_momentum_hypothesis_declaration())
        if mutation == "parameter":
            candidate["configuration"]["causal_signal"]["momentum_lookback_weeks"] = 5
        else:
            candidate["development_run_authorized"] = True
        with pytest.raises(ValueError, match="differs|safety"):
            validate_weekly_persistent_up_momentum_hypothesis(candidate)


def test_unknown_missing_and_nonmapping_declarations_fail_closed():
    candidate = weekly_persistent_up_momentum_hypothesis_declaration()
    candidate["unknown"] = True
    with pytest.raises(ValueError, match="Unknown"):
        validate_weekly_persistent_up_momentum_hypothesis(candidate)

    candidate = weekly_persistent_up_momentum_hypothesis_declaration()
    del candidate["status"]
    with pytest.raises(ValueError, match="Missing"):
        validate_weekly_persistent_up_momentum_hypothesis(candidate)

    with pytest.raises(TypeError, match="dictionary"):
        validate_weekly_persistent_up_momentum_hypothesis([])
