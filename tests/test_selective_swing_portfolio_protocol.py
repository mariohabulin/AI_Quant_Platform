import json
import os
from pathlib import Path
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from selective_swing_portfolio_protocol import (
    CRYPTO_ASSET_ORDER,
    DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256,
    PORTFOLIO_PROTOCOL_ID,
    SELECTIVE_SWING_MANDATE_NORMALIZED_SHA256,
    STOCK_FUTURE_MAX_POSITIONS,
    STOCK_INITIAL_MAX_POSITIONS,
    SelectiveSwingPortfolioProtocol,
    equal_weight_envelopes,
    load_daily_crypto_protocol,
    load_selective_swing_mandate,
    main,
    normalized_text_sha256,
    portfolio_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
MANDATE = ROOT / "SELECTIVE_SWING_TRADING_RESEARCH_MANDATE_V1.md"
CRYPTO_PROTOCOL = ROOT / "BTC_ETH_XRP_DAILY_DATA_AND_BLINDED_REPLAY_PROTOCOL_V1.md"


def test_declaration_freezes_identity_and_cash_first_operating_style():
    declaration = portfolio_declaration()

    assert declaration["schema_version"] == 1
    assert declaration["status"] == "SELECTIVE_SWING_PORTFOLIO_PROTOCOL_DECLARED_NOT_EXECUTED"
    assert declaration["protocol_id"] == PORTFOLIO_PROTOCOL_ID
    assert declaration["cash_is_default"] is True
    assert declaration["trading_frequency_is_target"] is False
    assert declaration["capital_allocation_rule"] == "EQUAL_WEIGHT_ELIGIBLE_1_OVER_N_ENVELOPE"
    assert declaration["actual_position_size_rule"] == (
        "MINIMUM_OF_1_OVER_N_CAPITAL_ENVELOPE_AND_RISK_BASED_LIMITS"
    )
    assert declaration["forced_full_investment"] is False


def test_stock_portfolio_starts_with_three_and_cannot_silently_expand_to_five():
    stocks = portfolio_declaration()["listed_equity_sleeve"]

    assert STOCK_INITIAL_MAX_POSITIONS == 3
    assert STOCK_FUTURE_MAX_POSITIONS == 5
    assert stocks["initial_max_concurrent_positions"] == 3
    assert stocks["future_research_ceiling"] == 5
    assert stocks["expansion_requires_separate_review"] is True
    assert stocks["selection_framework"] == "POINT_IN_TIME_CAN_SLIM_RESEARCH"
    assert stocks["candidate_selection_executed"] is False


def test_crypto_portfolio_keeps_three_independent_asset_sleeves():
    crypto = portfolio_declaration()["crypto_sleeve"]

    assert CRYPTO_ASSET_ORDER == ("BTC-USD", "ETH-USD", "XRP-USD")
    assert crypto["asset_order"] == list(CRYPTO_ASSET_ORDER)
    assert crypto["signal_independence"] == "ONE_CAUSAL_SIGNAL_STATE_PER_ASSET"
    assert crypto["cross_asset_relationship_is_entry_rule"] is False
    assert crypto["one_over_n_allocation_executed"] is False


@pytest.mark.parametrize(
    "eligible, expected_weights, expected_cash",
    [
        ([], {}, 1.0),
        (["BTC-USD"], {"BTC-USD": 1.0}, 0.0),
        (["BTC-USD", "ETH-USD"], {"BTC-USD": 0.5, "ETH-USD": 0.5}, 0.0),
        (
            ["BTC-USD", "ETH-USD", "XRP-USD"],
            {"BTC-USD": 1 / 3, "ETH-USD": 1 / 3, "XRP-USD": 1 / 3},
            0.0,
        ),
    ],
)
def test_equal_weight_envelopes_implement_one_over_n_without_orders(
    eligible, expected_weights, expected_cash
):
    result = equal_weight_envelopes(eligible, max_positions=3)

    assert result["eligible_count"] == len(eligible)
    assert result["target_capital_envelopes"] == expected_weights
    assert result["unallocated_cash_envelope"] == expected_cash
    assert result["orders_generated"] is False
    assert result["risk_sizing_executed"] is False


@pytest.mark.parametrize(
    "eligible, max_positions, error",
    [
        (["BTC-USD", "BTC-USD"], 3, "unique"),
        ([""], 3, "nonempty"),
        ([1], 3, "strings"),
        (["A", "B"], 1, "max_positions"),
        (["A"], 0, "positive integer"),
        (["A"], True, "positive integer"),
    ],
)
def test_equal_weight_envelopes_fail_closed_on_invalid_membership(
    eligible, max_positions, error
):
    with pytest.raises((TypeError, ValueError), match=error):
        equal_weight_envelopes(eligible, max_positions=max_positions)


def test_one_over_n_is_a_capital_envelope_not_permission_to_risk_the_account():
    allocation = portfolio_declaration()["allocation_and_risk"]

    assert allocation["one_over_n_is_capital_envelope"] is True
    assert allocation["one_over_n_is_risk_budget"] is False
    assert allocation["risk_based_sizing_may_leave_cash"] is True
    assert allocation["single_eligible_asset_forces_full_notional"] is False
    assert allocation["unused_capital_default"] == "CASH"
    assert allocation["provisional_standard_swing_risk_range_percent"] == [0.25, 0.50]
    assert allocation["provisional_total_open_risk_range_percent"] == [1.00, 1.50]
    assert allocation["provisional_values_authorized_for_execution"] is False
    assert allocation["gap_and_execution_risk_required"] is True


def test_three_strategy_books_cannot_borrow_alpha_or_authorization():
    books = portfolio_declaration()["strategy_books"]

    assert books["daily_crypto_swing"] == "INDEPENDENT_EVIDENCE_REQUIRED"
    assert books["point_in_time_can_slim_swing"] == "INDEPENDENT_EVIDENCE_REQUIRED"
    assert books["exceptional_intraday_breakout_contingency"] == (
        "SEPARATE_UNIMPLEMENTED_EVIDENCE_BOOK"
    )
    assert books["cross_book_alpha_claims_allowed"] is False
    assert books["combined_evaluation_requires_independent_evidence"] is True


def test_no_trade_is_a_first_class_cash_outcome_and_ai_cannot_weaken_it():
    policy = portfolio_declaration()["no_trade_policy"]

    assert policy["status"] == "NO_TRADE_HOLD_CASH"
    assert policy["first_class_outcome"] is True
    assert policy["failed_market_regime_blocks_entry"] is True
    assert policy["missing_or_stale_data_blocks_entry"] is True
    assert policy["missing_or_non_executable_stop_blocks_entry"] is True
    assert policy["portfolio_risk_capacity_blocks_entry"] is True
    assert policy["liquidity_or_cost_budget_blocks_entry"] is True
    assert policy["insufficient_causal_reward_room_blocks_entry"] is True
    assert policy["safety_stop_blocks_entry"] is True
    assert policy["ai_may_weaken_gate_for_activity"] is False


def test_three_r_is_an_entry_quality_screen_not_a_promised_or_forced_exit():
    policy = portfolio_declaration()["reward_and_exit_policy"]

    assert policy["minimum_opportunity_screen_r_multiple"] == 3.0
    assert policy["three_r_is_guaranteed"] is False
    assert policy["mandatory_full_exit_at_three_r"] is False
    assert policy["partial_or_trailing_exit_requires_strategy_protocol"] is True
    assert policy["risk_may_be_widened_after_entry"] is False
    assert policy["signal_failure_exit_required"] is True
    assert policy["maximum_holding_rule_required"] is True


def test_freed_capital_cannot_chase_survivors_without_fresh_add_on_evidence():
    reallocation = portfolio_declaration()["membership_change_policy"]

    assert reallocation["exit_reduces_removed_member"] is True
    assert reallocation["automatic_redistribution_to_past_winners"] is False
    assert reallocation["survivor_increase_requires_fresh_add_on_signal"] is True
    assert reallocation["otherwise"] == "HOLD_FREED_CAPITAL_AS_CASH"
    assert reallocation["next_executable_boundary_required"] is True


def test_pyramiding_is_winner_only_smaller_and_never_average_down():
    policy = portfolio_declaration()["pyramiding_policy"]

    assert policy["authorized_now"] is False
    assert policy["winning_position_required"] is True
    assert policy["fresh_causal_add_on_signal_required"] is True
    assert policy["each_addition_smaller_than_prior"] is True
    assert policy["average_down"] == "PROHIBITED"
    assert policy["vertical_extension_alone_is_add_on_signal"] is False
    assert policy["total_position_risk_recomputed"] is True


def test_rare_intraday_contingency_is_not_general_day_trading():
    contingency = portfolio_declaration()["rare_intraday_equity_contingency"]

    assert contingency["status"] == "SEPARATE_RESEARCH_HYPOTHESIS_NOT_IMPLEMENTED"
    assert contingency["name"] == "Exceptional Sideways Breakout Contingency v1"
    assert contingency["general_day_trading_authorized"] is False
    assert contingency["scalping_authorized"] is False
    assert contingency["event_scope"] == "RARE_EXPLOSIVE_UPSIDE_BREAKOUT_FROM_CAUSAL_SIDEWAYS_BASE"
    assert contingency["observed_move_reference"] == "APPROXIMATELY_20_TO_30_PERCENT_OR_MORE"
    assert contingency["observed_move_is_frozen_entry_threshold"] is False


def test_rare_intraday_contingency_requires_its_own_data_risk_and_exit_review():
    contingency = portfolio_declaration()["rare_intraday_equity_contingency"]

    assert contingency["max_concurrent_positions"] == 1
    assert contingency["risk_budget_relation"] == "STRICTLY_SMALLER_THAN_STANDARD_SWING_TRADE"
    assert contingency["initial_vertical_move_market_chase"] == "PROHIBITED"
    assert contingency["predefined_stop_required"] is True
    assert contingency["same_session_flat_required"] is True
    assert contingency["pyramiding_authorized"] is False
    assert contingency["intraday_point_in_time_data_audit_required"] is True
    assert contingency["halt_spread_slippage_liquidity_review_required"] is True
    assert contingency["separate_protocol_and_unseen_validation_required"] is True


def test_ai_may_rank_only_eligible_candidates_and_cannot_mutate_rules_live():
    ai = portfolio_declaration()["ai_governance"]

    assert ai["may_rank_point_in_time_eligible_candidates"] is True
    assert ai["may_create_eligibility"] is False
    assert ai["may_silently_mutate_rules"] is False
    assert ai["may_use_future_outcomes"] is False
    assert ai["candidate_ranking_executed"] is False
    assert ai["portfolio_execution_authorized"] is False
    assert ai["live_self_learning_authorized"] is False
    assert ai["offline_versioned_learning_required"] is True
    assert ai["unseen_validation_required_before_promotion"] is True
    assert ai["production_drift_may_silently_retrain"] is False


def test_crypto_setup_is_reconstructed_causally_and_xrp_is_not_rotation_rule():
    crypto = portfolio_declaration()["crypto_sleeve"]

    assert crypto["risk_family"] == "CRYPTO_CORRELATION_CLUSTER"
    assert crypto["xrp_inverse_or_decoupling_is_entry_rule"] is False
    assert crypto["xrp_relationship_requires_locked_diagnostic_evidence"] is True
    assert crypto["setup_reconstruction_sequence"] == [
        "EXCEPTIONAL_DECLINE",
        "RELATIVE_VOLUME_EVENT",
        "STABILIZATION_OR_ABSORPTION",
        "RECOVERY_CONFIRMATION",
        "STRUCTURAL_INVALIDATION_AND_CAUSAL_ENTRY",
        "PREDEFINED_EXIT_EVIDENCE",
    ]


def test_execution_model_must_cover_real_fills_gaps_halts_and_outages():
    execution = portfolio_declaration()["execution_realism"]

    assert execution["commissions_spread_slippage_required"] is True
    assert execution["gap_through_stop_required"] is True
    assert execution["partial_rejected_fill_policy_required"] is True
    assert execution["minimum_notional_and_venue_outage_required"] is True
    assert execution["intraday_quotes_halts_and_event_timestamps_required"] is True
    assert execution["daily_ohlcv_proves_intraday_executability"] is False


def test_normalized_upstream_hashes_are_line_ending_stable(tmp_path):
    mandate_copy = tmp_path / "mandate.md"
    crypto_copy = tmp_path / "crypto.md"
    mandate_copy.write_bytes(
        MANDATE.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8")
    )
    crypto_copy.write_bytes(
        CRYPTO_PROTOCOL.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8")
    )

    assert normalized_text_sha256(mandate_copy) == (
        SELECTIVE_SWING_MANDATE_NORMALIZED_SHA256
    )
    assert normalized_text_sha256(crypto_copy) == (
        DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256
    )
    assert load_selective_swing_mandate(mandate_copy)[1] == (
        SELECTIVE_SWING_MANDATE_NORMALIZED_SHA256
    )
    assert load_daily_crypto_protocol(crypto_copy)[1] == (
        DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256
    )


@pytest.mark.parametrize("loader, source", [(load_selective_swing_mandate, MANDATE), (load_daily_crypto_protocol, CRYPTO_PROTOCOL)])
def test_upstream_tamper_is_rejected(tmp_path, loader, source):
    changed = tmp_path / source.name
    changed.write_text(source.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        loader(changed)


def test_review_binds_upstream_protocols_but_executes_nothing():
    review = SelectiveSwingPortfolioProtocol().review(MANDATE, CRYPTO_PROTOCOL)

    assert review["status"] == "SELECTIVE_SWING_PORTFOLIO_PROTOCOL_REVIEWED_NOT_EXECUTED"
    assert review["mandate_sha256_match"] is True
    assert review["daily_crypto_protocol_sha256_match"] is True
    assert review["portfolio_policy_reviewed"] is True
    assert review["portfolio_allocation_executed"] is False
    assert review["pyramiding_executed"] is False
    assert review["rare_intraday_strategy_implemented"] is False
    assert review["performance_evaluation_executed"] is False
    assert review["candidate_v2_authorized"] is False
    assert review["bounded_forward_paper_authorized"] is False
    assert review["cloud_execution_authorized"] is False
    assert review["live_execution_authorized"] is False


def test_cli_emits_review_without_portfolio_or_market_execution(capsys):
    exit_code = main(
        ["--mandate", str(MANDATE), "--daily-crypto-protocol", str(CRYPTO_PROTOCOL)]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"].endswith("REVIEWED_NOT_EXECUTED")
    assert payload["portfolio_allocation_executed"] is False
    assert payload["rare_intraday_strategy_implemented"] is False
    assert payload["live_execution_authorized"] is False
