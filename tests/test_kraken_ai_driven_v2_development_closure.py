import json
import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_development_closure import (
    CLOSURE_STATUS,
    EXECUTION_COMMIT,
    RECORDED_DEVELOPMENT_REPORT_SHA256,
    closure_declaration,
    main,
)
from kraken_ai_driven_v2_development_review import review_declaration


ROOT = Path(__file__).resolve().parents[1]
CLOSURE_DOCUMENT = (
    ROOT / "KRAKEN_AI_DRIVEN_V2_DEVELOPMENT_REFERENCE_A_CLOSURE.md"
)


STATE_TRANSITIONS = {
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


def recorded_report():
    return {
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
        "state_transition_counts": STATE_TRANSITIONS,
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


class FakeLockedEvidence:
    def __init__(self, report=None, digest=RECORDED_DEVELOPMENT_REPORT_SHA256):
        self.report = report or recorded_report()
        self.report_sha256 = digest
        self.status = "KRAKEN_AI_V2_DEVELOPMENT_EVIDENCE_LOCK_PASS"


class FakeEvidenceLock:
    def __init__(self, locked=None):
        self.locked = locked or FakeLockedEvidence()

    def lock(self, evidence_directory):
        assert str(evidence_directory) == "evidence"
        return self.locked


def test_exact_recorded_evidence_closes_reference_a_as_no_trade_hold_cash():
    result = closure_declaration(
        "evidence",
        evidence_lock=FakeEvidenceLock(),
        dependency_reviewer=review_declaration,
    )

    assert result["status"] == CLOSURE_STATUS
    assert result["execution_commit"] == EXECUTION_COMMIT == "1f040e2"
    assert result["development_report_sha256"] == (
        RECORDED_DEVELOPMENT_REPORT_SHA256
    )
    assert result["confirmation_long_count"] == 13
    assert result["approved_entry_count"] == 0
    assert result["rejected_entry_count"] == 13
    assert result["closed_trade_count"] == 0
    assert result["action"] == "HOLD_CASH"
    assert result["reference_a_closed"] is True
    assert result["calibration_authorized"] is False
    assert result["evaluation_authorized"] is False
    assert result["candidate_v2_authorized"] is False
    assert result["live_execution_authorized"] is False


def test_changed_report_hash_is_rejected():
    evidence_lock = FakeEvidenceLock(FakeLockedEvidence(digest="a" * 64))

    with pytest.raises(ValueError, match="report SHA-256"):
        closure_declaration(
            "evidence",
            evidence_lock=evidence_lock,
            dependency_reviewer=review_declaration,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("approved_entry_count", 1),
        ("rejected_entry_count", 12),
        ("closed_trade_count", 1),
        ("realized_cash", 4999.0),
        ("calibration_data_opened", True),
        ("evaluation_rows_parsed", 1),
        ("candidate_v2_authorized", True),
    ],
)
def test_changed_recorded_outcome_is_rejected(field, value):
    report = recorded_report()
    report[field] = value

    with pytest.raises(ValueError, match="recorded outcome mismatch"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(FakeLockedEvidence(report=report)),
            dependency_reviewer=review_declaration,
        )


def test_changed_dependency_binding_is_rejected():
    changed_review = review_declaration()
    changed_review["upstream_binding_matches"][
        "AI-driven v2 feature component"
    ] = False

    with pytest.raises(ValueError, match="dependency binding"):
        closure_declaration(
            "evidence",
            evidence_lock=FakeEvidenceLock(),
            dependency_reviewer=lambda: changed_review,
        )


def test_closure_cli_prints_only_the_declaration(monkeypatch, capsys):
    expected = {"status": CLOSURE_STATUS}
    monkeypatch.setattr(
        "kraken_ai_driven_v2_development_closure.closure_declaration",
        lambda evidence_directory: expected,
    )

    result = main(["--evidence-directory", "evidence"])

    assert result == expected
    assert json.loads(capsys.readouterr().out) == expected


def test_closure_document_and_project_sources_record_the_exact_boundary():
    closure = CLOSURE_DOCUMENT.read_text(encoding="utf-8")
    assert CLOSURE_STATUS in closure
    assert RECORDED_DEVELOPMENT_REPORT_SHA256 in closure
    assert EXECUTION_COMMIT in closure
    assert "13" in closure
    assert "HOLD_CASH" in closure
    assert "not a break-even strategy result" in closure

    for name in (
        "VISION.md",
        "ARCHITECTURE.md",
        "ROADMAP.md",
        "CURRENT_MISSION.md",
        "LOG.md",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert CLOSURE_STATUS in text
        assert RECORDED_DEVELOPMENT_REPORT_SHA256 in text
        assert "Candidate v2" in text
