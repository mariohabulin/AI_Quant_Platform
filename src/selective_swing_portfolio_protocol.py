"""Cross-sleeve selective-swing portfolio construction declaration."""

import argparse
import hashlib
import json
from pathlib import Path


PORTFOLIO_PROTOCOL_SCHEMA_VERSION = 1
PORTFOLIO_PROTOCOL_ID = "selective-swing-portfolio-construction-v1"
SELECTIVE_SWING_MANDATE_NORMALIZED_SHA256 = (
    "7c4e6405f8b09c138748644bb51abcc69d06c5c45cfcd7c2df450dfd1efe0c98"
)
DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256 = (
    "4a195360d58f6c86d7eaae61b39300bf2cac00d947c5c9b2d7615df421e686ea"
)
CRYPTO_ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
STOCK_INITIAL_MAX_POSITIONS = 3
STOCK_FUTURE_MAX_POSITIONS = 5
DEFAULT_MANDATE_PATH = Path("SELECTIVE_SWING_TRADING_RESEARCH_MANDATE_V1.md")
DEFAULT_DAILY_CRYPTO_PROTOCOL_PATH = Path(
    "BTC_ETH_XRP_DAILY_DATA_AND_BLINDED_REPLAY_PROTOCOL_V1.md"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read protocol prerequisite: {path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _load_text_contract(path, expected_sha256, required_text, label):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(f"{label} SHA256 mismatch: {digest} != {expected_sha256}.")
    text = raw.decode("utf-8")
    if any(value not in text for value in required_text):
        raise RuntimeError(f"{label} required contract text is missing.")
    return text, digest


def load_selective_swing_mandate(
    path, expected_sha256=SELECTIVE_SWING_MANDATE_NORMALIZED_SHA256
):
    return _load_text_contract(
        path,
        expected_sha256,
        (
            "Selective Swing Trading Research Mandate v1",
            "`DECLARED_NOT_EXECUTED`",
            "cash is an explicit valid portfolio state",
            "CAN SLIM / O'Neil",
            "Crypto Capitulation-Volume Reversal v1",
        ),
        "Selective swing mandate",
    )


def load_daily_crypto_protocol(
    path, expected_sha256=DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256
):
    return _load_text_contract(
        path,
        expected_sha256,
        (
            "BTC/ETH/XRP Daily Data and Blinded Replay Protocol v1",
            "PROTOCOL_AND_REPLAY_COMPONENT_REVIEWED_PROVIDER_AUDIT_REQUIRED",
            "BTC-USD`, `ETH-USD`, `XRP-USD",
            "default portfolio state: cash",
            "real chart replay executed: `false`",
        ),
        "Daily crypto replay protocol",
    )


def equal_weight_envelopes(eligible_assets, max_positions):
    """Return non-executable 1/n capital envelopes for currently eligible assets."""

    if not isinstance(max_positions, int) or isinstance(max_positions, bool) or max_positions <= 0:
        raise ValueError("max_positions must be a positive integer.")
    if isinstance(eligible_assets, (str, bytes)) or not isinstance(
        eligible_assets, (list, tuple)
    ):
        raise TypeError("eligible_assets must be an ordered list or tuple of strings.")
    if any(not isinstance(asset, str) for asset in eligible_assets):
        raise TypeError("Eligible asset identifiers must be strings.")
    if any(not asset.strip() for asset in eligible_assets):
        raise ValueError("Eligible asset identifiers must be nonempty.")
    normalized = [asset.strip() for asset in eligible_assets]
    if len(set(normalized)) != len(normalized):
        raise ValueError("Eligible asset identifiers must be unique.")
    if len(normalized) > max_positions:
        raise ValueError("Eligible membership exceeds max_positions.")

    if not normalized:
        envelopes = {}
        cash = 1.0
    else:
        weight = 1.0 / len(normalized)
        envelopes = {asset: weight for asset in normalized}
        cash = 0.0
    return {
        "eligible_count": len(normalized),
        "target_capital_envelopes": envelopes,
        "unallocated_cash_envelope": cash,
        "orders_generated": False,
        "risk_sizing_executed": False,
    }


def portfolio_declaration():
    return {
        "schema_version": PORTFOLIO_PROTOCOL_SCHEMA_VERSION,
        "status": "SELECTIVE_SWING_PORTFOLIO_PROTOCOL_DECLARED_NOT_EXECUTED",
        "protocol_id": PORTFOLIO_PROTOCOL_ID,
        "mandate_normalized_sha256": SELECTIVE_SWING_MANDATE_NORMALIZED_SHA256,
        "daily_crypto_protocol_normalized_sha256": (
            DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256
        ),
        "cash_is_default": True,
        "trading_frequency_is_target": False,
        "capital_allocation_rule": "EQUAL_WEIGHT_ELIGIBLE_1_OVER_N_ENVELOPE",
        "actual_position_size_rule": (
            "MINIMUM_OF_1_OVER_N_CAPITAL_ENVELOPE_AND_RISK_BASED_LIMITS"
        ),
        "forced_full_investment": False,
        "strategy_books": {
            "daily_crypto_swing": "INDEPENDENT_EVIDENCE_REQUIRED",
            "point_in_time_can_slim_swing": "INDEPENDENT_EVIDENCE_REQUIRED",
            "exceptional_intraday_breakout_contingency": (
                "SEPARATE_UNIMPLEMENTED_EVIDENCE_BOOK"
            ),
            "cross_book_alpha_claims_allowed": False,
            "combined_evaluation_requires_independent_evidence": True,
        },
        "listed_equity_sleeve": {
            "selection_framework": "POINT_IN_TIME_CAN_SLIM_RESEARCH",
            "initial_max_concurrent_positions": STOCK_INITIAL_MAX_POSITIONS,
            "future_research_ceiling": STOCK_FUTURE_MAX_POSITIONS,
            "expansion_requires_separate_review": True,
            "candidate_selection_executed": False,
            "signal_and_portfolio_evidence_separate": True,
            "sector_and_correlation_limits_required": True,
        },
        "crypto_sleeve": {
            "asset_order": list(CRYPTO_ASSET_ORDER),
            "signal_independence": "ONE_CAUSAL_SIGNAL_STATE_PER_ASSET",
            "cross_asset_relationship_is_entry_rule": False,
            "cross_asset_relationship_diagnostic_allowed_after_data_lock": True,
            "one_over_n_allocation_executed": False,
            "risk_family": "CRYPTO_CORRELATION_CLUSTER",
            "xrp_inverse_or_decoupling_is_entry_rule": False,
            "xrp_relationship_requires_locked_diagnostic_evidence": True,
            "setup_reconstruction_sequence": [
                "EXCEPTIONAL_DECLINE",
                "RELATIVE_VOLUME_EVENT",
                "STABILIZATION_OR_ABSORPTION",
                "RECOVERY_CONFIRMATION",
                "STRUCTURAL_INVALIDATION_AND_CAUSAL_ENTRY",
                "PREDEFINED_EXIT_EVIDENCE",
            ],
        },
        "allocation_and_risk": {
            "one_over_n_is_capital_envelope": True,
            "one_over_n_is_risk_budget": False,
            "risk_based_sizing_may_leave_cash": True,
            "single_eligible_asset_forces_full_notional": False,
            "unused_capital_default": "CASH",
            "per_position_risk_limit_required": True,
            "portfolio_open_risk_limit_required": True,
            "correlation_cluster_limit_required": True,
            "provisional_standard_swing_risk_range_percent": [0.25, 0.50],
            "provisional_total_open_risk_range_percent": [1.00, 1.50],
            "provisional_values_authorized_for_execution": False,
            "gap_and_execution_risk_required": True,
            "minimum_executable_size_may_force_zero_position": True,
        },
        "no_trade_policy": {
            "status": "NO_TRADE_HOLD_CASH",
            "first_class_outcome": True,
            "failed_market_regime_blocks_entry": True,
            "missing_or_stale_data_blocks_entry": True,
            "missing_or_non_executable_stop_blocks_entry": True,
            "portfolio_risk_capacity_blocks_entry": True,
            "liquidity_or_cost_budget_blocks_entry": True,
            "insufficient_causal_reward_room_blocks_entry": True,
            "safety_stop_blocks_entry": True,
            "ai_may_weaken_gate_for_activity": False,
        },
        "reward_and_exit_policy": {
            "minimum_opportunity_screen_r_multiple": 3.0,
            "three_r_is_guaranteed": False,
            "mandatory_full_exit_at_three_r": False,
            "partial_or_trailing_exit_requires_strategy_protocol": True,
            "risk_may_be_widened_after_entry": False,
            "signal_failure_exit_required": True,
            "maximum_holding_rule_required": True,
        },
        "membership_change_policy": {
            "exit_reduces_removed_member": True,
            "automatic_redistribution_to_past_winners": False,
            "survivor_increase_requires_fresh_add_on_signal": True,
            "otherwise": "HOLD_FREED_CAPITAL_AS_CASH",
            "next_executable_boundary_required": True,
            "transaction_costs_required": True,
        },
        "pyramiding_policy": {
            "authorized_now": False,
            "winning_position_required": True,
            "fresh_causal_add_on_signal_required": True,
            "each_addition_smaller_than_prior": True,
            "average_down": "PROHIBITED",
            "vertical_extension_alone_is_add_on_signal": False,
            "total_position_risk_recomputed": True,
            "sector_correlation_exposure_rechecked": True,
            "separate_protocol_required": True,
        },
        "rare_intraday_equity_contingency": {
            "status": "SEPARATE_RESEARCH_HYPOTHESIS_NOT_IMPLEMENTED",
            "name": "Exceptional Sideways Breakout Contingency v1",
            "general_day_trading_authorized": False,
            "scalping_authorized": False,
            "event_scope": "RARE_EXPLOSIVE_UPSIDE_BREAKOUT_FROM_CAUSAL_SIDEWAYS_BASE",
            "observed_move_reference": "APPROXIMATELY_20_TO_30_PERCENT_OR_MORE",
            "observed_move_is_frozen_entry_threshold": False,
            "max_concurrent_positions": 1,
            "risk_budget_relation": "STRICTLY_SMALLER_THAN_STANDARD_SWING_TRADE",
            "initial_vertical_move_market_chase": "PROHIBITED",
            "predefined_stop_required": True,
            "same_session_flat_required": True,
            "pyramiding_authorized": False,
            "intraday_point_in_time_data_audit_required": True,
            "halt_spread_slippage_liquidity_review_required": True,
            "separate_protocol_and_unseen_validation_required": True,
            "strategy_implemented": False,
            "performance_evaluation_executed": False,
        },
        "ai_governance": {
            "may_rank_point_in_time_eligible_candidates": True,
            "may_create_eligibility": False,
            "may_silently_mutate_rules": False,
            "may_use_future_outcomes": False,
            "candidate_ranking_executed": False,
            "portfolio_execution_authorized": False,
            "live_self_learning_authorized": False,
            "offline_versioned_learning_required": True,
            "unseen_validation_required_before_promotion": True,
            "production_drift_may_silently_retrain": False,
        },
        "execution_realism": {
            "commissions_spread_slippage_required": True,
            "gap_through_stop_required": True,
            "partial_rejected_fill_policy_required": True,
            "minimum_notional_and_venue_outage_required": True,
            "intraday_quotes_halts_and_event_timestamps_required": True,
            "daily_ohlcv_proves_intraday_executability": False,
        },
        "portfolio_allocation_executed": False,
        "pyramiding_executed": False,
        "rare_intraday_strategy_implemented": False,
        "performance_evaluation_executed": False,
        "optimization_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
    }


class SelectiveSwingPortfolioProtocol:
    """Review cross-sleeve allocation declarations without market execution."""

    def review(
        self,
        mandate_path=DEFAULT_MANDATE_PATH,
        daily_crypto_protocol_path=DEFAULT_DAILY_CRYPTO_PROTOCOL_PATH,
    ):
        _, mandate_digest = load_selective_swing_mandate(mandate_path)
        _, crypto_digest = load_daily_crypto_protocol(daily_crypto_protocol_path)
        return {
            "schema_version": PORTFOLIO_PROTOCOL_SCHEMA_VERSION,
            "status": "SELECTIVE_SWING_PORTFOLIO_PROTOCOL_REVIEWED_NOT_EXECUTED",
            "protocol_id": PORTFOLIO_PROTOCOL_ID,
            "mandate_sha256_match": (
                mandate_digest == SELECTIVE_SWING_MANDATE_NORMALIZED_SHA256
            ),
            "daily_crypto_protocol_sha256_match": (
                crypto_digest == DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256
            ),
            "portfolio_policy_reviewed": True,
            "portfolio_allocation_executed": False,
            "pyramiding_executed": False,
            "rare_intraday_strategy_implemented": False,
            "performance_evaluation_executed": False,
            "optimization_authorized": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
        }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review the selective swing portfolio construction protocol."
    )
    parser.add_argument("--mandate", default=str(DEFAULT_MANDATE_PATH))
    parser.add_argument(
        "--daily-crypto-protocol",
        default=str(DEFAULT_DAILY_CRYPTO_PROTOCOL_PATH),
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    result = SelectiveSwingPortfolioProtocol().review(
        args.mandate, args.daily_crypto_protocol
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
