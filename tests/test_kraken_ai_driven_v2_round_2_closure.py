import json
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_round_2_closure import (
    CLOSURE_STATUS,
    EXECUTION_COMMIT,
    EXPECTED_FAILED_GATES_BY_ROUTE,
    FEEDBACK_CLASS_BY_ROUTE,
    RECORDED_REPORT_SHA256,
    closure_contract_declaration,
    closure_declaration,
    main,
)
from kraken_ai_driven_v2_round_2_discovery_runner import (
    BASELINE_COST_PROFILE_ID,
    ROUTE_ORDER,
    STRESS_COST_PROFILE_ID,
)
from kraken_ai_driven_v2_round_2_discovery_runner_review import review_declaration


ROOT = Path(__file__).resolve().parents[1]
CLOSURE_DOCUMENT = ROOT / "KRAKEN_AI_DRIVEN_V2_ROUND_2_CLOSURE.md"
SCOPE_CORRECTION_DOCUMENT = ROOT / "KRAKEN_AI_DRIVEN_V2_SCOPE_GAP_CORRECTION_V1.md"


def profile(*, trades, expectancy, slices, nonnegative, largest_share):
    return {
        "signal_count": trades,
        "approved_entry_count": trades,
        "rejected_entry_count": 0,
        "closed_trade_count": trades,
        "net_expectancy_r": expectancy,
        "profit_factor": 2.0 if trades > 1 else None,
        "profit_factor_is_infinite": trades == 1,
        "maximum_marked_drawdown_fraction": 0.05,
        "slices_with_trade": slices,
        "nonnegative_slices": nonnegative,
        "largest_trade_net_profit_share": largest_share,
        "unresolved_position_count": 0,
        "entry_rejection_reason_counts": {},
        "entry_cancellation_reason_counts": {},
    }


def recorded_report():
    metrics = {
        "BTC-USD|CAPITULATION_RECOVERY": (1, 0.208, 0.191, 1, 1, 1.0),
        "BTC-USD|VOLATILITY_BREAKOUT": (5, 0.432, 0.408, 4, 2, 0.6),
        "BTC-USD|TREND_PULLBACK_CONTINUATION": (1, 3.0, 3.0, 1, 1, 1.0),
        "ETH-USD|CAPITULATION_RECOVERY": (3, 1.538, 1.503, 3, 3, 0.5),
        "ETH-USD|VOLATILITY_BREAKOUT": (6, 1.092, 1.088, 4, 2, 0.5),
        "ETH-USD|TREND_PULLBACK_CONTINUATION": (2, 1.0, 1.0, 1, 1, 0.7),
        "XRP-USD|CAPITULATION_RECOVERY": (2, 0.093, 0.070, 2, 1, 0.7),
    }
    routes = []
    for route_id in ROUTE_ORDER:
        asset, family = route_id.split("|")
        trades, baseline_r, stress_r, slices, nonnegative, largest = metrics[route_id]
        baseline = profile(
            trades=trades,
            expectancy=baseline_r,
            slices=slices,
            nonnegative=nonnegative,
            largest_share=largest,
        )
        stress = profile(
            trades=trades,
            expectancy=stress_r,
            slices=slices,
            nonnegative=nonnegative,
            largest_share=largest,
        )
        failed = EXPECTED_FAILED_GATES_BY_ROUTE[route_id]
        checks = {"placeholder_pass": True, **{name: False for name in failed}}
        routes.append(
            {
                "route_id": route_id,
                "asset": asset,
                "family_id": family,
                "profiles": {
                    BASELINE_COST_PROFILE_ID: baseline,
                    STRESS_COST_PROFILE_ID: stress,
                },
                "interest_gate": {
                    "eligible": False,
                    "checks": checks,
                    "action": "HOLD_CASH",
                },
            }
        )
    return {
        "status": "KRAKEN_AI_V2_ROUND_2_DEVELOPMENT_NO_INTEREST_HOLD_CASH",
        "route_order": list(ROUTE_ORDER),
        "route_results": routes,
        "round_interest": {
            "status": "KRAKEN_AI_V2_ROUND_2_DEVELOPMENT_NO_INTEREST_HOLD_CASH",
            "round_interest_gate_passed": False,
            "eligible_route_count": 0,
            "eligible_asset_count": 0,
            "eligible_route_ids": [],
            "eligible_assets": [],
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "candidate_v2_authorized": False,
        },
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


class FakeLockedEvidence:
    def __init__(self, report=None, digest=RECORDED_REPORT_SHA256):
        self.report = recorded_report() if report is None else report
        self.report_sha256 = digest
        self.status = "KRAKEN_AI_V2_ROUND_2_DISCOVERY_EVIDENCE_LOCK_PASS"


class FakeEvidenceLock:
    def __init__(self, locked=None):
        self.locked = locked or FakeLockedEvidence()

    def lock(self, evidence_directory):
        assert str(evidence_directory) == "evidence"
        return self.locked


def test_contract_declares_closure_without_opening_evidence_or_claiming_learning():
    result = closure_contract_declaration()

    assert result["execution_commit"] == EXECUTION_COMMIT
    assert result["recorded_report_sha256"] == RECORDED_REPORT_SHA256
    assert result["round_2_closure_implemented"] is True
    assert result["round_2_evidence_opened"] is False
    assert result["round_2_rerun_authorized"] is False
    assert result["true_learning_engine_implemented"] is False
    assert result["candidate_v2_authorized"] is False


def test_exact_locked_evidence_closes_round_2_as_hold_cash_with_offline_feedback():
    result = closure_declaration(
        "evidence",
        evidence_lock=FakeEvidenceLock(),
        dependency_reviewer=review_declaration,
    )

    assert result["status"] == CLOSURE_STATUS
    assert result["execution_commit"] == EXECUTION_COMMIT
    assert result["round_2_report_sha256"] == RECORDED_REPORT_SHA256
    assert result["route_count"] == 7
    assert result["eligible_route_count"] == 0
    assert result["eligible_asset_count"] == 0
    assert result["action"] == "HOLD_CASH"
    assert result["round_2_closed"] is True
    assert result["round_2_rerun_authorized"] is False
    assert result["true_learning_engine_implemented"] is False
    assert result["offline_feedback_recorded"] is True
    assert result["automatic_ranking_generated"] is False
    assert result["candidate_v2_authorized"] is False
    assert result["next_stage"] == "IMPLEMENT_TRUE_LEARNING_CONTRACT_V1"


def test_feedback_classes_are_descriptive_not_a_ranking():
    result = closure_declaration(
        "evidence",
        evidence_lock=FakeEvidenceLock(),
        dependency_reviewer=review_declaration,
    )
    by_route = {item["route_id"]: item for item in result["route_feedback"]}

    for route_id, feedback_class in FEEDBACK_CLASS_BY_ROUTE.items():
        assert by_route[route_id]["feedback_class"] == feedback_class
        assert by_route[route_id]["failed_gates"] == list(
            EXPECTED_FAILED_GATES_BY_ROUTE[route_id]
        )
    assert all(item["eligible"] is False for item in result["route_feedback"])
    assert all(item["action"] == "HOLD_CASH" for item in result["route_feedback"])


def test_changed_report_hash_is_rejected_before_interpretation():
    lock = FakeEvidenceLock(FakeLockedEvidence(digest="a" * 64))

    with pytest.raises(ValueError, match="report SHA-256"):
        closure_declaration(
            "evidence", evidence_lock=lock, dependency_reviewer=review_declaration
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "CHANGED"),
        ("route_order", list(reversed(ROUTE_ORDER))),
        ("calibration_data_opened", True),
        ("evaluation_data_opened", True),
        ("automatic_ranking_generated", True),
        ("candidate_v2_authorized", True),
        ("real_orders_submitted", True),
    ],
)
def test_changed_recorded_top_level_outcome_is_rejected(field, value):
    report = recorded_report()
    report[field] = value

    with pytest.raises(ValueError, match="recorded outcome mismatch"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(FakeLockedEvidence(report=report)),
            dependency_reviewer=review_declaration,
        )


def test_route_cannot_be_relabelled_eligible_after_inspection():
    report = recorded_report()
    report["route_results"][0]["interest_gate"]["eligible"] = True

    with pytest.raises(ValueError, match="route eligibility"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(FakeLockedEvidence(report=report)),
            dependency_reviewer=review_declaration,
        )


def test_exact_failed_gate_set_cannot_be_post_hoc_reinterpreted():
    report = recorded_report()
    route = next(
        item
        for item in report["route_results"]
        if item["route_id"] == "ETH-USD|CAPITULATION_RECOVERY"
    )
    route["interest_gate"]["checks"]["extra_failure"] = False

    with pytest.raises(ValueError, match="failed-gate attribution"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(FakeLockedEvidence(report=report)),
            dependency_reviewer=review_declaration,
        )


def test_xrp_baseline_expectancy_attribution_fails_closed():
    report = recorded_report()
    xrp = next(
        item
        for item in report["route_results"]
        if item["route_id"] == "XRP-USD|CAPITULATION_RECOVERY"
    )
    xrp["profiles"][BASELINE_COST_PROFILE_ID]["net_expectancy_r"] = 0.1

    with pytest.raises(ValueError, match="XRP baseline expectancy"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(FakeLockedEvidence(report=report)),
            dependency_reviewer=review_declaration,
        )


def test_unresolved_position_prevents_clean_round_closure():
    report = recorded_report()
    report["route_results"][0]["profiles"][BASELINE_COST_PROFILE_ID][
        "unresolved_position_count"
    ] = 1

    with pytest.raises(ValueError, match="zero unresolved"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(FakeLockedEvidence(report=report)),
            dependency_reviewer=review_declaration,
        )


def test_changed_dependency_binding_is_rejected():
    changed = review_declaration()
    changed["parent_source_binding_matches"][
        "AI-driven v2 Round 2 family execution component"
    ] = False

    with pytest.raises(ValueError, match="dependency binding"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(),
            dependency_reviewer=lambda: changed,
        )


def test_closure_cli_prints_only_declaration(monkeypatch, capsys):
    expected = {"status": CLOSURE_STATUS}
    monkeypatch.setattr(
        "kraken_ai_driven_v2_round_2_closure.closure_declaration",
        lambda evidence_directory: expected,
    )

    result = main(["--evidence-directory", "evidence"])

    assert result == expected
    assert json.loads(capsys.readouterr().out) == expected


def test_closure_document_and_project_sources_record_exact_boundary():
    closure = CLOSURE_DOCUMENT.read_text(encoding="utf-8")
    scope = SCOPE_CORRECTION_DOCUMENT.read_text(encoding="utf-8")
    assert CLOSURE_STATUS in closure
    assert RECORDED_REPORT_SHA256 in closure
    assert EXECUTION_COMMIT in closure
    assert "7" in closure
    assert "HOLD_CASH" in closure
    assert "Rule Discovery Foundation is not a Learning Engine" in closure
    assert "True Learning Engine is not implemented" in scope
    assert "learned model artifact" in scope

    for name in ("VISION.md", "ARCHITECTURE.md", "ROADMAP.md", "CURRENT_MISSION.md", "LOG.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Round 2 Closure" in text
        assert RECORDED_REPORT_SHA256 in text
        assert "Rule Discovery Foundation" in text
        assert "True Learning Engine" in text
        assert "Candidate v2" in text
