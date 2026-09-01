import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_12h_development_economic_review_review import (
    EXPECTED_COMPONENT_SHA256,
    EXPECTED_PROTOCOL_SHA256,
    STATUS,
    review_12h_development_economic_review,
)


ROOT = Path(__file__).resolve().parents[1]


def test_static_review_binds_parent_and_economic_review_sources():
    review = review_12h_development_economic_review(ROOT)

    assert review["status"] == STATUS
    assert review["parent_commit"] == "9c1156e0527c34c71f9efec381f3770fdc7b4238"
    assert review["economic_review_protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert review["economic_review_component_sha256"] == EXPECTED_COMPONENT_SHA256
    assert review["parent_runner_protocol_sha256_match"] is True
    assert review["parent_runner_component_sha256_match"] is True
    assert review["economic_review_protocol_sha256_match"] is True
    assert review["economic_review_component_sha256_match"] is True


def test_static_review_preserves_read_only_no_selection_boundary():
    review = review_12h_development_economic_review(ROOT)

    assert review["fixed_rule"] == "3*p_target_3r_first-p_stop_1r_first>0"
    assert review["threshold_sweep_authorized"] is False
    assert review["learning_evidence_opened"] is False
    assert review["model_artifacts_unpickled"] is False
    assert review["model_training_executed"] is False
    assert review["automatic_model_selection"] is False
    assert review["candidate_v2_authorized"] is False
    assert review["calibration_data_opened"] is False
    assert review["evaluation_data_opened"] is False
    assert review["live_execution_authorized"] is False


def test_static_review_fails_closed_if_economic_component_changes(tmp_path):
    relatives = (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_12H_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md",
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_12H_DEVELOPMENT_ECONOMIC_EVIDENCE_REVIEW_PROTOCOL_V1.md",
        "src/kraken_ai_driven_v2_12h_development_learning_runner.py",
        "src/kraken_ai_driven_v2_12h_development_economic_review.py",
    )
    for relative in relatives:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    component = tmp_path / "src" / "kraken_ai_driven_v2_12h_development_economic_review.py"
    component.write_text(component.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="economic_review_component"):
        review_12h_development_economic_review(tmp_path)


def test_protocol_explains_no_tuning_no_portfolio_claim_and_hold_cash():
    protocol = (
        ROOT
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_12H_DEVELOPMENT_ECONOMIC_EVIDENCE_REVIEW_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    assert "There is no threshold sweep" in protocol
    assert "Neither view is a portfolio simulation" in protocol
    assert "at least 30 raw eligible" in protocol
    assert "at least 10 non-overlapping" in protocol
    assert "does not create or authorize Candidate v2" in protocol
    assert "`HOLD_CASH`" in protocol
