import json
import os
import sys
from copy import deepcopy
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_round_1_closure import (
    CLOSURE_STATUS,
    EXECUTION_COMMIT,
    NEGATIVE_EXPECTANCY_BOTH_PROFILES_ROUTES,
    NO_CLOSED_TRADE_ROUTES,
    RECORDED_REPORT_SHA256,
    SINGLE_FAILED_GATE_ROUTES,
    closure_contract_declaration,
    closure_declaration,
    main,
)
from kraken_ai_driven_v2_round_1_discovery_runner import (
    BASELINE_COST_PROFILE_ID,
    ROUTE_ORDER,
    STRESS_COST_PROFILE_ID,
)
from kraken_ai_driven_v2_round_1_discovery_runner_review import review_declaration


ROOT = Path(__file__).resolve().parents[1]
CLOSURE_DOCUMENT = ROOT / "KRAKEN_AI_DRIVEN_V2_ROUND_1_CLOSURE.md"


def profile(*, trades=8, expectancy=0.2):
    return {
        "signal_count": trades,
        "approved_entry_count": trades,
        "rejected_entry_count": 0,
        "closed_trade_count": trades,
        "net_expectancy_r": expectancy,
        "profit_factor": 1.5 if trades else None,
        "profit_factor_is_infinite": False,
        "maximum_marked_drawdown_fraction": 0.05,
        "slices_with_trade": 3 if trades else 0,
        "nonnegative_slices": 3 if trades else 0,
        "largest_trade_net_profit_share": 0.3 if trades else 1.0,
        "unresolved_position_count": 0,
        "entry_rejection_reason_counts": {},
        "entry_cancellation_reason_counts": {},
    }


def recorded_report():
    routes = []
    for route_id in ROUTE_ORDER:
        asset, family = route_id.split("|")
        baseline = profile()
        stress = profile(expectancy=0.1)
        if route_id in SINGLE_FAILED_GATE_ROUTES:
            failed = [SINGLE_FAILED_GATE_ROUTES[route_id]]
        elif route_id in NO_CLOSED_TRADE_ROUTES:
            baseline = profile(trades=0, expectancy=0.0)
            stress = profile(trades=0, expectancy=0.0)
            failed = ["minimum_closed_trades", "minimum_baseline_profit_factor"]
        elif route_id in NEGATIVE_EXPECTANCY_BOTH_PROFILES_ROUTES:
            baseline = profile(expectancy=-0.1)
            stress = profile(expectancy=-0.2)
            failed = ["minimum_baseline_net_expectancy_r", "minimum_stress_net_expectancy_r"]
        else:
            failed = ["minimum_closed_trades", "minimum_nonnegative_slices"]
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
        "status": "KRAKEN_AI_V2_ROUND_1_DEVELOPMENT_NO_INTEREST_HOLD_CASH",
        "route_order": list(ROUTE_ORDER),
        "route_results": routes,
        "round_interest": {
            "status": "KRAKEN_AI_V2_ROUND_1_DEVELOPMENT_NO_INTEREST_HOLD_CASH",
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
        self.status = "KRAKEN_AI_V2_ROUND_1_DISCOVERY_EVIDENCE_LOCK_PASS"


class FakeEvidenceLock:
    def __init__(self, locked=None):
        self.locked = locked or FakeLockedEvidence()

    def lock(self, evidence_directory):
        assert str(evidence_directory) == "evidence"
        return self.locked


def test_contract_declares_closure_without_opening_evidence_or_registering_round_2():
    result = closure_contract_declaration()

    assert result["execution_commit"] == EXECUTION_COMMIT
    assert result["recorded_report_sha256"] == RECORDED_REPORT_SHA256
    assert result["round_1_closure_implemented"] is True
    assert result["round_1_evidence_opened"] is False
    assert result["round_1_rerun_authorized"] is False
    assert result["round_2_manifest_registered"] is False
    assert result["candidate_v2_authorized"] is False


def test_exact_locked_evidence_closes_round_1_as_hold_cash_with_offline_feedback():
    result = closure_declaration(
        "evidence",
        evidence_lock=FakeEvidenceLock(),
        dependency_reviewer=review_declaration,
    )

    assert result["status"] == CLOSURE_STATUS
    assert result["execution_commit"] == EXECUTION_COMMIT
    assert result["round_1_report_sha256"] == RECORDED_REPORT_SHA256
    assert result["route_count"] == 12
    assert result["eligible_route_count"] == 0
    assert result["eligible_asset_count"] == 0
    assert result["action"] == "HOLD_CASH"
    assert result["round_1_closed"] is True
    assert result["round_1_rerun_authorized"] is False
    assert result["round_2_manifest_registered"] is False
    assert result["offline_feedback_recorded"] is True
    assert result["automatic_ranking_generated"] is False
    assert result["candidate_v2_authorized"] is False
    assert result["next_stage"] == "PRE_REGISTER_BOUNDED_ROUND_2_OR_STOP"


def test_feedback_classes_are_descriptive_not_a_ranking():
    result = closure_declaration(
        "evidence",
        evidence_lock=FakeEvidenceLock(),
        dependency_reviewer=review_declaration,
    )
    by_route = {item["route_id"]: item for item in result["route_feedback"]}

    for route_id in SINGLE_FAILED_GATE_ROUTES:
        assert by_route[route_id]["feedback_class"] == "SINGLE_FROZEN_GATE_FAILURE"
    for route_id in NO_CLOSED_TRADE_ROUTES:
        assert by_route[route_id]["feedback_class"] == "NO_EXECUTABLE_CLOSED_TRADE_EVIDENCE"
    for route_id in NEGATIVE_EXPECTANCY_BOTH_PROFILES_ROUTES:
        assert by_route[route_id]["feedback_class"] == "NEGATIVE_EXPECTANCY_BOTH_COST_PROFILES"
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


def test_single_failed_gate_route_cannot_be_post_hoc_reinterpreted():
    report = recorded_report()
    route = next(
        item
        for item in report["route_results"]
        if item["route_id"] == "ETH-USD|VOLATILITY_BREAKOUT"
    )
    route["interest_gate"]["checks"]["extra_failure"] = False

    with pytest.raises(ValueError, match="single-gate feedback"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(FakeLockedEvidence(report=report)),
            dependency_reviewer=review_declaration,
        )


def test_no_trade_and_negative_expectancy_attributions_fail_closed():
    report = recorded_report()
    no_trade = next(
        item for item in report["route_results"] if item["route_id"] == NO_CLOSED_TRADE_ROUTES[0]
    )
    no_trade["profiles"][BASELINE_COST_PROFILE_ID]["closed_trade_count"] = 1

    with pytest.raises(ValueError, match="no-trade feedback"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(FakeLockedEvidence(report=report)),
            dependency_reviewer=review_declaration,
        )

    report = recorded_report()
    negative = next(
        item
        for item in report["route_results"]
        if item["route_id"] == NEGATIVE_EXPECTANCY_BOTH_PROFILES_ROUTES[0]
    )
    negative["profiles"][STRESS_COST_PROFILE_ID]["net_expectancy_r"] = 0.0

    with pytest.raises(ValueError, match="negative-expectancy"):
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
        "AI-driven v2 Round 1 family execution component"
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
        "kraken_ai_driven_v2_round_1_closure.closure_declaration",
        lambda evidence_directory: expected,
    )

    result = main(["--evidence-directory", "evidence"])

    assert result == expected
    assert json.loads(capsys.readouterr().out) == expected


def test_closure_document_and_project_sources_record_exact_boundary():
    closure = CLOSURE_DOCUMENT.read_text(encoding="utf-8")
    assert CLOSURE_STATUS in closure
    assert RECORDED_REPORT_SHA256 in closure
    assert EXECUTION_COMMIT in closure
    assert "12" in closure
    assert "HOLD_CASH" in closure
    assert "Round 2 is not registered" in closure

    for name in ("VISION.md", "ARCHITECTURE.md", "ROADMAP.md", "CURRENT_MISSION.md", "LOG.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Round 1 Closure" in text
        assert RECORDED_REPORT_SHA256 in text
        assert "Candidate v2" in text
