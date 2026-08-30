"""Read-only closure for locked Kraken AI-driven v2 development evidence."""

import argparse
import json

try:
    from kraken_ai_driven_v2_development_review import review_declaration
    from kraken_ai_driven_v2_development_runner import (
        KrakenAIDrivenV2DevelopmentEvidenceLock,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_development_review import review_declaration
    from .kraken_ai_driven_v2_development_runner import (
        KrakenAIDrivenV2DevelopmentEvidenceLock,
    )


SCHEMA_VERSION = 1
EXECUTION_COMMIT = "1f040e2"
RECORDED_DEVELOPMENT_REPORT_SHA256 = (
    "f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594"
)
CLOSURE_STATUS = (
    "KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH"
)

RECORDED_STATE_TRANSITION_COUNTS = {
    "BTC-USD": {
        "ARMED_EXPIRED": 7,
        "ARMED_STRUCTURAL_INVALIDATION": 5,
        "ARMED_WAIT": 49,
        "CAPITULATION_ARMED": 15,
        "CAPITULATION_REARMED": 1,
        "CONFIRMATION_LONG": 3,
        "FLAT_FEATURES_UNAVAILABLE": 30,
        "FLAT_WAIT": 1788,
        "LONG_BEARISH_VOLUME_EXIT": 3,
        "LONG_HOLD": 15,
    },
    "ETH-USD": {
        "ARMED_EXPIRED": 5,
        "ARMED_STRUCTURAL_INVALIDATION": 5,
        "ARMED_WAIT": 39,
        "CAPITULATION_ARMED": 15,
        "CAPITULATION_REARMED": 5,
        "CONFIRMATION_LONG": 5,
        "FLAT_FEATURES_UNAVAILABLE": 30,
        "FLAT_WAIT": 1714,
        "LONG_BEARISH_VOLUME_EXIT": 4,
        "LONG_HOLD": 94,
        "LONG_STRUCTURAL_EXIT": 1,
    },
    "XRP-USD": {
        "ARMED_EXPIRED": 5,
        "ARMED_STRUCTURAL_INVALIDATION": 5,
        "ARMED_WAIT": 42,
        "CAPITULATION_ARMED": 16,
        "CAPITULATION_REARMED": 1,
        "CONFIRMATION_LONG": 5,
        "FLAT_FEATURES_UNAVAILABLE": 60,
        "FLAT_WAIT": 1697,
        "LONG_BEARISH_VOLUME_EXIT": 4,
        "LONG_HOLD": 79,
        "LONG_STRUCTURAL_AND_BEARISH_EXIT": 1,
    },
}

RECORDED_OUTCOME = {
    "status": "KRAKEN_AI_V2_DEVELOPMENT_COMPLETED_FLAT",
    "path_completed": True,
    "halt_timestamp": None,
    "halt_asset": None,
    "development_rows": {
        "BTC-USD": 1916,
        "ETH-USD": 1917,
        "XRP-USD": 1915,
    },
    "continuous_segment_rows": {
        "BTC-USD": [1916],
        "ETH-USD": [1917],
        "XRP-USD": [1226, 689],
    },
    "full_observed_rows": {
        "BTC-USD": 2646,
        "ETH-USD": 2647,
        "XRP-USD": 2645,
    },
    "opaque_non_development_rows": {
        "BTC-USD": 730,
        "ETH-USD": 730,
        "XRP-USD": 730,
    },
    "calibration_rows_parsed": 0,
    "evaluation_rows_parsed": 0,
    "state_transition_counts": RECORDED_STATE_TRANSITION_COUNTS,
    "approved_entry_count": 0,
    "rejected_entry_count": 13,
    "entry_rejection_reason_counts": {
        "CAUSAL_RESISTANCE_NOT_ABOVE_ENTRY": 2,
        "NET_THREE_R_CAUSAL_ROOM_NOT_AVAILABLE": 11,
    },
    "canceled_entry_intent_count": 0,
    "canceled_entry_intents": [],
    "entry_ledger": [],
    "closed_trade_count": 0,
    "closed_trade_ledger": [],
    "winning_trade_count": 0,
    "losing_trade_count": 0,
    "flat_trade_count": 0,
    "exit_reason_counts": {},
    "terminal_open_position_count": 0,
    "terminal_open_positions": [],
    "initial_capital": 5000.0,
    "realized_cash": 5000.0,
    "realized_net_pnl": 0,
    "terminal_marked_equity": 5000.0,
    "terminal_marked_return_fraction": 0.0,
    "maximum_marked_drawdown_fraction": 0.0,
    "total_modeled_commissions": 0,
    "maximum_concurrent_positions": 0,
    "maximum_planned_open_risk_fraction": 0.0,
    "full_asset_files_hashed_as_opaque_bytes": True,
    "dataset_opened": True,
    "development_data_opened": True,
    "calibration_data_opened": False,
    "evaluation_data_opened": False,
    "development_run_authorized": True,
    "development_run_executed": True,
    "performance_evaluation_executed": True,
    "real_orders_submitted": False,
    "synthetic_terminal_force_close_executed": False,
    "parameter_sweep_executed": False,
    "automatic_ranking_generated": False,
    "automatic_strategy_selection": False,
    "optimization_authorized": False,
    "candidate_v2_authorized": False,
    "bounded_forward_paper_authorized": False,
    "cloud_execution_authorized": False,
    "live_execution_authorized": False,
}


def _validate_dependency_review(declaration):
    matches = declaration.get("upstream_binding_matches")
    if not isinstance(matches, dict) or not matches or not all(matches.values()):
        raise ValueError("Development closure dependency binding mismatch.")
    if declaration.get("development_protocol_sha256_match") is not True:
        raise ValueError("Development closure protocol binding mismatch.")
    if declaration.get("development_runner_sha256_match") is not True:
        raise ValueError("Development closure runner binding mismatch.")
    return matches


def _validate_recorded_outcome(report):
    for field, expected in RECORDED_OUTCOME.items():
        if report.get(field) != expected:
            raise ValueError(
                f"Development recorded outcome mismatch for {field}."
            )
    confirmations = sum(
        transitions.get("CONFIRMATION_LONG", 0)
        for transitions in report["state_transition_counts"].values()
    )
    rejected_by_reason = sum(
        report["entry_rejection_reason_counts"].values()
    )
    if confirmations != 13 or rejected_by_reason != confirmations:
        raise ValueError("Development recorded outcome mismatch for confirmations.")
    return confirmations


def closure_declaration(
    evidence_directory,
    *,
    evidence_lock=None,
    dependency_reviewer=None,
):
    lock = evidence_lock or KrakenAIDrivenV2DevelopmentEvidenceLock()
    reviewer = dependency_reviewer or review_declaration
    if not hasattr(lock, "lock"):
        raise TypeError("Development closure evidence lock must provide lock().")
    if not callable(reviewer):
        raise TypeError("Development closure dependency reviewer must be callable.")

    locked = lock.lock(evidence_directory)
    if locked.report_sha256 != RECORDED_DEVELOPMENT_REPORT_SHA256:
        raise ValueError("Development closure report SHA-256 mismatch.")
    dependency_review = reviewer()
    binding_matches = _validate_dependency_review(dependency_review)
    confirmations = _validate_recorded_outcome(locked.report)

    return {
        "schema_version": SCHEMA_VERSION,
        "status": CLOSURE_STATUS,
        "execution_commit": EXECUTION_COMMIT,
        "development_report_sha256": locked.report_sha256,
        "evidence_lock_status": locked.status,
        "source_binding_mode": (
            "EXECUTION_COMMIT_PLUS_HASH_BOUND_PREFLIGHT_PLUS_REPORT_SHA256"
        ),
        "upstream_binding_matches": binding_matches,
        "development_protocol_sha256_match": dependency_review[
            "development_protocol_sha256_match"
        ],
        "development_runner_sha256_match": dependency_review[
            "development_runner_sha256_match"
        ],
        "development_status": locked.report["status"],
        "confirmation_long_count": confirmations,
        "approved_entry_count": locked.report["approved_entry_count"],
        "rejected_entry_count": locked.report["rejected_entry_count"],
        "entry_rejection_reason_counts": locked.report[
            "entry_rejection_reason_counts"
        ],
        "closed_trade_count": locked.report["closed_trade_count"],
        "initial_capital": locked.report["initial_capital"],
        "realized_cash": locked.report["realized_cash"],
        "realized_net_pnl": locked.report["realized_net_pnl"],
        "maximum_marked_drawdown_fraction": locked.report[
            "maximum_marked_drawdown_fraction"
        ],
        "action": "HOLD_CASH",
        "reference_a_closed": True,
        "reference_a_rerun_authorized": False,
        "calibration_authorized": False,
        "evaluation_authorized": False,
        "optimization_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
        "next_stage": "NEW_PRE_REGISTERED_DEVELOPMENT_HYPOTHESIS_OR_STOP",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Close locked Kraken AI v2 development Reference A."
    )
    parser.add_argument("--evidence-directory", required=True)
    args = parser.parse_args(argv)
    declaration = closure_declaration(args.evidence_directory)
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
