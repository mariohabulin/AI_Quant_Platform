"""Read-only closure and offline feedback for locked Round 1 evidence."""

import argparse
import json
from numbers import Real

try:
    from kraken_ai_driven_v2_round_1_discovery_runner import (
        BASELINE_COST_PROFILE_ID,
        ROUTE_ORDER,
        STRESS_COST_PROFILE_ID,
        KrakenAIDrivenV2Round1DiscoveryEvidenceLock,
    )
    from kraken_ai_driven_v2_round_1_discovery_runner_review import (
        review_declaration as runner_review_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_round_1_discovery_runner import (
        BASELINE_COST_PROFILE_ID,
        ROUTE_ORDER,
        STRESS_COST_PROFILE_ID,
        KrakenAIDrivenV2Round1DiscoveryEvidenceLock,
    )
    from .kraken_ai_driven_v2_round_1_discovery_runner_review import (
        review_declaration as runner_review_declaration,
    )


SCHEMA_VERSION = 1
EXECUTION_COMMIT = "98a72181e9bd216dbe049a938fe7de56c6659a8f"
RECORDED_REPORT_SHA256 = (
    "3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b"
)
CLOSURE_PROTOCOL_ID = "kraken-ai-v2-round-1-development-closure-v1"
CLOSURE_STATUS = "KRAKEN_AI_V2_ROUND_1_CLOSED_NO_ELIGIBLE_ROUTE_HOLD_CASH"
RECORDED_ROUND_STATUS = "KRAKEN_AI_V2_ROUND_1_DEVELOPMENT_NO_INTEREST_HOLD_CASH"
SINGLE_FAILED_GATE_ROUTES = {
    "BTC-USD|VOLATILITY_BREAKOUT": "maximum_largest_trade_net_profit_share",
    "ETH-USD|VOLATILITY_BREAKOUT": "minimum_nonnegative_slices",
}
NO_CLOSED_TRADE_ROUTES = (
    "BTC-USD|RANGE_MEAN_REVERSION",
    "ETH-USD|RANGE_MEAN_REVERSION",
    "XRP-USD|RANGE_MEAN_REVERSION",
)
NEGATIVE_EXPECTANCY_BOTH_PROFILES_ROUTES = (
    "XRP-USD|TREND_PULLBACK_CONTINUATION",
    "XRP-USD|VOLATILITY_BREAKOUT",
)
PROFILE_FIELDS = (
    "signal_count",
    "approved_entry_count",
    "rejected_entry_count",
    "closed_trade_count",
    "net_expectancy_r",
    "profit_factor",
    "profit_factor_is_infinite",
    "maximum_marked_drawdown_fraction",
    "slices_with_trade",
    "nonnegative_slices",
    "largest_trade_net_profit_share",
    "unresolved_position_count",
    "entry_rejection_reason_counts",
    "entry_cancellation_reason_counts",
)


def closure_contract_declaration():
    """Declare the exact closure boundary without opening external evidence."""

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "KRAKEN_AI_V2_ROUND_1_CLOSURE_IMPLEMENTED_EXTERNAL_EVIDENCE_REQUIRED",
        "closure_protocol_id": CLOSURE_PROTOCOL_ID,
        "execution_commit": EXECUTION_COMMIT,
        "recorded_report_sha256": RECORDED_REPORT_SHA256,
        "expected_closure_status": CLOSURE_STATUS,
        "expected_round_status": RECORDED_ROUND_STATUS,
        "single_failed_gate_routes": dict(SINGLE_FAILED_GATE_ROUTES),
        "no_closed_trade_routes": list(NO_CLOSED_TRADE_ROUTES),
        "negative_expectancy_both_profiles_routes": list(
            NEGATIVE_EXPECTANCY_BOTH_PROFILES_ROUTES
        ),
        "round_1_closure_implemented": True,
        "offline_feedback_attribution_implemented": True,
        "round_2_manifest_registered": False,
        "round_1_evidence_opened": False,
        "round_1_rerun_authorized": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "runtime_learning_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
    }


def _validate_dependency_review(declaration):
    matches = declaration.get("parent_source_binding_matches")
    if not isinstance(matches, dict) or not matches or not all(matches.values()):
        raise ValueError("Round 1 closure dependency binding mismatch.")
    for field in (
        "runner_protocol_sha256_match",
        "runner_component_sha256_match",
        "parent_family_execution_review_passed",
        "development_only_reader_reused",
        "independent_evidence_lock_implemented",
        "one_shot_atomic_evidence_implemented",
        "absolute_route_gates_implemented",
        "round_interest_gate_implemented",
        "discovery_runner_implemented",
    ):
        if declaration.get(field) is not True:
            raise ValueError(f"Round 1 closure dependency mismatch for {field}.")
    for field in (
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "development_run_authorized",
        "development_run_executed",
        "performance_evaluation_executed",
        "automatic_ranking_generated",
        "automatic_strategy_selection",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise ValueError(f"Round 1 closure dependency safety mismatch for {field}.")
    return matches


def _number(value, label):
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ValueError(f"Round 1 closure {label} must be numeric.")
    return float(value)


def _profile_feedback(profile):
    missing = [field for field in PROFILE_FIELDS if field not in profile]
    if missing:
        raise ValueError(f"Round 1 closure profile fields are missing: {missing}.")
    for field in (
        "signal_count",
        "approved_entry_count",
        "rejected_entry_count",
        "closed_trade_count",
        "slices_with_trade",
        "nonnegative_slices",
        "unresolved_position_count",
    ):
        value = profile[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"Round 1 closure profile count is invalid: {field}.")
    for field in (
        "net_expectancy_r",
        "maximum_marked_drawdown_fraction",
        "largest_trade_net_profit_share",
    ):
        _number(profile[field], field)
    profit_factor = profile["profit_factor"]
    if profit_factor is not None:
        _number(profit_factor, "profit_factor")
    if not isinstance(profile["profit_factor_is_infinite"], bool):
        raise ValueError("Round 1 closure infinite profit-factor flag is invalid.")
    for field in (
        "entry_rejection_reason_counts",
        "entry_cancellation_reason_counts",
    ):
        if not isinstance(profile[field], dict):
            raise ValueError(f"Round 1 closure attribution is invalid: {field}.")
    return {field: profile[field] for field in PROFILE_FIELDS}


def _feedback_class(route_id, failed_gates, baseline, stress):
    if route_id in SINGLE_FAILED_GATE_ROUTES:
        expected = SINGLE_FAILED_GATE_ROUTES[route_id]
        if failed_gates != [expected]:
            raise ValueError("Round 1 single-gate feedback attribution mismatch.")
        return "SINGLE_FROZEN_GATE_FAILURE"
    if route_id in NO_CLOSED_TRADE_ROUTES:
        if baseline["closed_trade_count"] or stress["closed_trade_count"]:
            raise ValueError("Round 1 no-trade feedback attribution mismatch.")
        return "NO_EXECUTABLE_CLOSED_TRADE_EVIDENCE"
    if route_id in NEGATIVE_EXPECTANCY_BOTH_PROFILES_ROUTES:
        if baseline["net_expectancy_r"] >= 0.0 or stress["net_expectancy_r"] >= 0.0:
            raise ValueError("Round 1 negative-expectancy attribution mismatch.")
        return "NEGATIVE_EXPECTANCY_BOTH_COST_PROFILES"
    return "MULTIPLE_FROZEN_GATE_FAILURES"


def _validate_recorded_outcome(report):
    expected = {
        "status": RECORDED_ROUND_STATUS,
        "route_order": list(ROUTE_ORDER),
        "dataset_opened": True,
        "development_data_opened": True,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_run_authorized": True,
        "development_run_executed": True,
        "performance_evaluation_executed": True,
        "parameter_sweep_executed": False,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "candidate_v2_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
    }
    for field, value in expected.items():
        if report.get(field) != value:
            raise ValueError(f"Round 1 recorded outcome mismatch for {field}.")
    round_interest = report.get("round_interest")
    if not isinstance(round_interest, dict):
        raise ValueError("Round 1 recorded interest evidence is missing.")
    interest_expected = {
        "status": RECORDED_ROUND_STATUS,
        "round_interest_gate_passed": False,
        "eligible_route_count": 0,
        "eligible_asset_count": 0,
        "eligible_route_ids": [],
        "eligible_assets": [],
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "candidate_v2_authorized": False,
    }
    for field, value in interest_expected.items():
        if round_interest.get(field) != value:
            raise ValueError(f"Round 1 recorded interest mismatch for {field}.")

    routes = report.get("route_results")
    if not isinstance(routes, list) or len(routes) != len(ROUTE_ORDER):
        raise ValueError("Round 1 recorded route count mismatch.")
    if [route.get("route_id") for route in routes] != list(ROUTE_ORDER):
        raise ValueError("Round 1 recorded route order mismatch.")

    feedback = []
    total_unresolved = 0
    for route in routes:
        gate = route.get("interest_gate")
        if not isinstance(gate, dict) or gate.get("eligible") is not False:
            raise ValueError("Round 1 recorded route eligibility mismatch.")
        checks = gate.get("checks")
        if not isinstance(checks, dict) or not checks:
            raise ValueError("Round 1 recorded route checks are missing.")
        failed_gates = sorted(name for name, passed in checks.items() if passed is False)
        if not failed_gates or any(not isinstance(value, bool) for value in checks.values()):
            raise ValueError("Round 1 recorded route failure attribution mismatch.")
        profiles = route.get("profiles")
        if not isinstance(profiles, dict):
            raise ValueError("Round 1 recorded route profiles are missing.")
        if tuple(profiles) != (BASELINE_COST_PROFILE_ID, STRESS_COST_PROFILE_ID):
            raise ValueError("Round 1 recorded profile order mismatch.")
        baseline = _profile_feedback(profiles[BASELINE_COST_PROFILE_ID])
        stress = _profile_feedback(profiles[STRESS_COST_PROFILE_ID])
        total_unresolved += baseline["unresolved_position_count"]
        total_unresolved += stress["unresolved_position_count"]
        feedback.append(
            {
                "route_id": route["route_id"],
                "asset": route["asset"],
                "family_id": route["family_id"],
                "feedback_class": _feedback_class(
                    route["route_id"], failed_gates, baseline, stress
                ),
                "failed_gates": failed_gates,
                "baseline": baseline,
                "stress": stress,
                "eligible": False,
                "action": "HOLD_CASH",
            }
        )
    if total_unresolved != 0:
        raise ValueError("Round 1 closure requires zero unresolved positions.")
    return feedback


def closure_declaration(
    evidence_directory,
    *,
    evidence_lock=None,
    dependency_reviewer=None,
):
    lock = evidence_lock or KrakenAIDrivenV2Round1DiscoveryEvidenceLock()
    reviewer = dependency_reviewer or runner_review_declaration
    if not hasattr(lock, "lock"):
        raise TypeError("Round 1 closure evidence lock must provide lock().")
    if not callable(reviewer):
        raise TypeError("Round 1 closure dependency reviewer must be callable.")

    locked = lock.lock(evidence_directory)
    if locked.report_sha256 != RECORDED_REPORT_SHA256:
        raise ValueError("Round 1 closure report SHA-256 mismatch.")
    dependency_review = reviewer()
    binding_matches = _validate_dependency_review(dependency_review)
    route_feedback = _validate_recorded_outcome(locked.report)

    return {
        "schema_version": SCHEMA_VERSION,
        "status": CLOSURE_STATUS,
        "closure_protocol_id": CLOSURE_PROTOCOL_ID,
        "execution_commit": EXECUTION_COMMIT,
        "round_1_report_sha256": locked.report_sha256,
        "evidence_lock_status": locked.status,
        "source_binding_mode": (
            "EXECUTION_COMMIT_PLUS_HASH_BOUND_PREFLIGHT_PLUS_REPORT_SHA256"
        ),
        "parent_source_binding_matches": binding_matches,
        "runner_protocol_sha256_match": dependency_review[
            "runner_protocol_sha256_match"
        ],
        "runner_component_sha256_match": dependency_review[
            "runner_component_sha256_match"
        ],
        "round_status": locked.report["status"],
        "route_count": len(route_feedback),
        "eligible_route_count": 0,
        "eligible_asset_count": 0,
        "route_feedback": route_feedback,
        "single_failed_gate_routes": dict(SINGLE_FAILED_GATE_ROUTES),
        "no_closed_trade_routes": list(NO_CLOSED_TRADE_ROUTES),
        "negative_expectancy_both_profiles_routes": list(
            NEGATIVE_EXPECTANCY_BOTH_PROFILES_ROUTES
        ),
        "action": "HOLD_CASH",
        "round_1_closed": True,
        "round_1_rerun_authorized": False,
        "round_2_manifest_registered": False,
        "offline_feedback_recorded": True,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "runtime_learning_authorized": False,
        "calibration_authorized": False,
        "evaluation_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": "PRE_REGISTER_BOUNDED_ROUND_2_OR_STOP",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Close locked Kraken AI-driven v2 Round 1 evidence."
    )
    parser.add_argument("--evidence-directory", required=True)
    args = parser.parse_args(argv)
    declaration = closure_declaration(args.evidence_directory)
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
