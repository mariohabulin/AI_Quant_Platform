"""Read-only closure and scope-correct feedback for locked Round 2 evidence."""

import argparse
import json
from numbers import Real

try:
    from kraken_ai_driven_v2_round_2_discovery_runner import (
        BASELINE_COST_PROFILE_ID,
        ROUTE_ORDER,
        STRESS_COST_PROFILE_ID,
        KrakenAIDrivenV2Round2DiscoveryEvidenceLock,
    )
    from kraken_ai_driven_v2_round_2_discovery_runner_review import (
        review_declaration as runner_review_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_round_2_discovery_runner import (
        BASELINE_COST_PROFILE_ID,
        ROUTE_ORDER,
        STRESS_COST_PROFILE_ID,
        KrakenAIDrivenV2Round2DiscoveryEvidenceLock,
    )
    from .kraken_ai_driven_v2_round_2_discovery_runner_review import (
        review_declaration as runner_review_declaration,
    )


SCHEMA_VERSION = 1
EXECUTION_COMMIT = "a601a322b353179663a96423bc29d50adc28627e"
RECORDED_REPORT_SHA256 = (
    "5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01"
)
CLOSURE_PROTOCOL_ID = "kraken-ai-v2-round-2-development-closure-v1"
CLOSURE_STATUS = "KRAKEN_AI_V2_ROUND_2_CLOSED_NO_ELIGIBLE_ROUTE_HOLD_CASH"
RECORDED_ROUND_STATUS = "KRAKEN_AI_V2_ROUND_2_DEVELOPMENT_NO_INTEREST_HOLD_CASH"

EXPECTED_FAILED_GATES_BY_ROUTE = {
    "BTC-USD|CAPITULATION_RECOVERY": (
        "maximum_largest_trade_net_profit_share",
        "minimum_closed_trades",
        "minimum_nonnegative_slices",
        "minimum_slices_with_trade",
    ),
    "BTC-USD|VOLATILITY_BREAKOUT": (
        "maximum_largest_trade_net_profit_share",
        "minimum_closed_trades",
        "minimum_nonnegative_slices",
    ),
    "BTC-USD|TREND_PULLBACK_CONTINUATION": (
        "maximum_largest_trade_net_profit_share",
        "minimum_closed_trades",
        "minimum_nonnegative_slices",
        "minimum_slices_with_trade",
    ),
    "ETH-USD|CAPITULATION_RECOVERY": (
        "maximum_largest_trade_net_profit_share",
        "minimum_closed_trades",
    ),
    "ETH-USD|VOLATILITY_BREAKOUT": (
        "maximum_largest_trade_net_profit_share",
        "minimum_closed_trades",
        "minimum_nonnegative_slices",
    ),
    "ETH-USD|TREND_PULLBACK_CONTINUATION": (
        "maximum_largest_trade_net_profit_share",
        "minimum_closed_trades",
        "minimum_nonnegative_slices",
        "minimum_slices_with_trade",
    ),
    "XRP-USD|CAPITULATION_RECOVERY": (
        "maximum_largest_trade_net_profit_share",
        "minimum_baseline_net_expectancy_r",
        "minimum_closed_trades",
        "minimum_nonnegative_slices",
        "minimum_slices_with_trade",
    ),
}
FEEDBACK_CLASS_BY_ROUTE = {
    "BTC-USD|CAPITULATION_RECOVERY": (
        "SPARSE_CONCENTRATED_AND_CHRONOLOGICALLY_INSUFFICIENT"
    ),
    "BTC-USD|VOLATILITY_BREAKOUT": (
        "POSITIVE_EXPECTANCY_SPARSE_STABILITY_AND_CONCENTRATION_FAILURE"
    ),
    "BTC-USD|TREND_PULLBACK_CONTINUATION": (
        "SPARSE_CONCENTRATED_AND_CHRONOLOGICALLY_INSUFFICIENT"
    ),
    "ETH-USD|CAPITULATION_RECOVERY": (
        "INSUFFICIENT_SAMPLE_AND_PROFIT_CONCENTRATION"
    ),
    "ETH-USD|VOLATILITY_BREAKOUT": (
        "POSITIVE_EXPECTANCY_SPARSE_STABILITY_AND_CONCENTRATION_FAILURE"
    ),
    "ETH-USD|TREND_PULLBACK_CONTINUATION": (
        "SPARSE_CONCENTRATED_AND_CHRONOLOGICALLY_INSUFFICIENT"
    ),
    "XRP-USD|CAPITULATION_RECOVERY": (
        "SPARSE_BASELINE_EXPECTANCY_STABILITY_AND_CONCENTRATION_FAILURE"
    ),
}
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
    """Declare the closure boundary without opening external evidence."""

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "KRAKEN_AI_V2_ROUND_2_CLOSURE_IMPLEMENTED_EXTERNAL_EVIDENCE_REQUIRED",
        "closure_protocol_id": CLOSURE_PROTOCOL_ID,
        "execution_commit": EXECUTION_COMMIT,
        "recorded_report_sha256": RECORDED_REPORT_SHA256,
        "expected_closure_status": CLOSURE_STATUS,
        "expected_round_status": RECORDED_ROUND_STATUS,
        "expected_failed_gates_by_route": {
            route_id: list(gates)
            for route_id, gates in EXPECTED_FAILED_GATES_BY_ROUTE.items()
        },
        "round_2_closure_implemented": True,
        "offline_feedback_attribution_implemented": True,
        "scope_gap_correction_recorded": True,
        "true_learning_engine_implemented": False,
        "round_2_evidence_opened": False,
        "round_2_rerun_authorized": False,
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
        raise ValueError("Round 2 closure dependency binding mismatch.")
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
            raise ValueError(f"Round 2 closure dependency mismatch for {field}.")
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
            raise ValueError(f"Round 2 closure dependency safety mismatch for {field}.")
    return matches


def _number(value, label):
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ValueError(f"Round 2 closure {label} must be numeric.")
    return float(value)


def _profile_feedback(profile):
    missing = [field for field in PROFILE_FIELDS if field not in profile]
    if missing:
        raise ValueError(f"Round 2 closure profile fields are missing: {missing}.")
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
            raise ValueError(f"Round 2 closure profile count is invalid: {field}.")
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
        raise ValueError("Round 2 closure infinite profit-factor flag is invalid.")
    for field in (
        "entry_rejection_reason_counts",
        "entry_cancellation_reason_counts",
    ):
        if not isinstance(profile[field], dict):
            raise ValueError(f"Round 2 closure attribution is invalid: {field}.")
    return {field: profile[field] for field in PROFILE_FIELDS}


def _feedback_class(route_id, failed_gates, baseline, stress):
    expected = list(EXPECTED_FAILED_GATES_BY_ROUTE[route_id])
    if failed_gates != expected:
        raise ValueError("Round 2 failed-gate attribution mismatch.")
    if min(baseline["closed_trade_count"], stress["closed_trade_count"]) >= 8:
        raise ValueError("Round 2 sparse-sample attribution mismatch.")
    if max(
        baseline["largest_trade_net_profit_share"],
        stress["largest_trade_net_profit_share"],
    ) <= 0.4:
        raise ValueError("Round 2 concentration attribution mismatch.")
    if route_id == "XRP-USD|CAPITULATION_RECOVERY":
        if baseline["net_expectancy_r"] >= 0.1:
            raise ValueError("Round 2 XRP baseline expectancy attribution mismatch.")
    return FEEDBACK_CLASS_BY_ROUTE[route_id]


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
            raise ValueError(f"Round 2 recorded outcome mismatch for {field}.")

    round_interest = report.get("round_interest")
    if not isinstance(round_interest, dict):
        raise ValueError("Round 2 recorded interest evidence is missing.")
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
            raise ValueError(f"Round 2 recorded interest mismatch for {field}.")

    routes = report.get("route_results")
    if not isinstance(routes, list) or len(routes) != len(ROUTE_ORDER):
        raise ValueError("Round 2 recorded route count mismatch.")
    if [route.get("route_id") for route in routes] != list(ROUTE_ORDER):
        raise ValueError("Round 2 recorded route order mismatch.")

    feedback = []
    total_unresolved = 0
    for route in routes:
        route_id = route.get("route_id")
        gate = route.get("interest_gate")
        if not isinstance(gate, dict) or gate.get("eligible") is not False:
            raise ValueError("Round 2 recorded route eligibility mismatch.")
        if gate.get("action") != "HOLD_CASH":
            raise ValueError("Round 2 recorded route action mismatch.")
        checks = gate.get("checks")
        if not isinstance(checks, dict) or not checks:
            raise ValueError("Round 2 recorded route checks are missing.")
        if any(not isinstance(value, bool) for value in checks.values()):
            raise ValueError("Round 2 recorded route failure attribution mismatch.")
        failed_gates = sorted(name for name, passed in checks.items() if passed is False)
        profiles = route.get("profiles")
        if not isinstance(profiles, dict):
            raise ValueError("Round 2 recorded route profiles are missing.")
        if tuple(profiles) != (BASELINE_COST_PROFILE_ID, STRESS_COST_PROFILE_ID):
            raise ValueError("Round 2 recorded profile order mismatch.")
        baseline = _profile_feedback(profiles[BASELINE_COST_PROFILE_ID])
        stress = _profile_feedback(profiles[STRESS_COST_PROFILE_ID])
        total_unresolved += baseline["unresolved_position_count"]
        total_unresolved += stress["unresolved_position_count"]
        feedback.append(
            {
                "route_id": route_id,
                "asset": route.get("asset"),
                "family_id": route.get("family_id"),
                "feedback_class": _feedback_class(
                    route_id, failed_gates, baseline, stress
                ),
                "failed_gates": failed_gates,
                "baseline": baseline,
                "stress": stress,
                "eligible": False,
                "action": "HOLD_CASH",
            }
        )
    if total_unresolved != 0:
        raise ValueError("Round 2 closure requires zero unresolved positions.")
    return feedback


def closure_declaration(
    evidence_directory,
    *,
    evidence_lock=None,
    dependency_reviewer=None,
):
    lock = evidence_lock or KrakenAIDrivenV2Round2DiscoveryEvidenceLock()
    reviewer = dependency_reviewer or runner_review_declaration
    if not hasattr(lock, "lock"):
        raise TypeError("Round 2 closure evidence lock must provide lock().")
    if not callable(reviewer):
        raise TypeError("Round 2 closure dependency reviewer must be callable.")

    locked = lock.lock(evidence_directory)
    if locked.report_sha256 != RECORDED_REPORT_SHA256:
        raise ValueError("Round 2 closure report SHA-256 mismatch.")
    dependency_review = reviewer()
    binding_matches = _validate_dependency_review(dependency_review)
    route_feedback = _validate_recorded_outcome(locked.report)

    return {
        "schema_version": SCHEMA_VERSION,
        "status": CLOSURE_STATUS,
        "closure_protocol_id": CLOSURE_PROTOCOL_ID,
        "execution_commit": EXECUTION_COMMIT,
        "round_2_report_sha256": locked.report_sha256,
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
        "action": "HOLD_CASH",
        "round_2_closed": True,
        "round_2_rerun_authorized": False,
        "offline_feedback_recorded": True,
        "scope_gap_correction_recorded": True,
        "true_learning_engine_implemented": False,
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
        "next_stage": "IMPLEMENT_TRUE_LEARNING_CONTRACT_V1",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Close locked Kraken AI-driven v2 Round 2 evidence."
    )
    parser.add_argument("--evidence-directory", required=True)
    args = parser.parse_args(argv)
    declaration = closure_declaration(args.evidence_directory)
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
