import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_12h_development_learning_runner_review import (
    EXPECTED_ATTEMPT_1_INCIDENT_SHA256,
    EXPECTED_ATTEMPT_2_INCIDENT_SHA256,
    EXPECTED_LEARNING_CORE_COMPONENT_SHA256,
    EXPECTED_LEARNING_CORE_PROTOCOL_SHA256,
    EXPECTED_RUNNER_COMPONENT_SHA256,
    EXPECTED_RUNNER_PROTOCOL_SHA256,
    STATUS,
    review_12h_development_learning_runner,
)


ROOT = Path(__file__).resolve().parents[1]


def test_review_binds_parent_core_runner_protocol_and_component():
    review = review_12h_development_learning_runner(ROOT)

    assert review["status"] == STATUS
    assert review["parent_commit"] == "203b4c5b81434be3edab7ec5372448cd12472288"
    assert review["attempt_1_incident_sha256"] == EXPECTED_ATTEMPT_1_INCIDENT_SHA256
    assert review["attempt_1_incident_sha256_match"] is True
    assert review["attempt_2_incident_sha256"] == EXPECTED_ATTEMPT_2_INCIDENT_SHA256
    assert review["attempt_2_incident_sha256_match"] is True
    assert review["learning_core_protocol_sha256"] == EXPECTED_LEARNING_CORE_PROTOCOL_SHA256
    assert review["learning_core_component_sha256"] == EXPECTED_LEARNING_CORE_COMPONENT_SHA256
    assert review["runner_protocol_sha256"] == EXPECTED_RUNNER_PROTOCOL_SHA256
    assert review["runner_component_sha256"] == EXPECTED_RUNNER_COMPONENT_SHA256
    assert review["learning_core_protocol_sha256_match"] is True
    assert review["learning_core_component_sha256_match"] is True
    assert review["runner_protocol_sha256_match"] is True
    assert review["runner_component_sha256_match"] is True


def test_review_confirms_inert_real_learning_runner_boundary():
    review = review_12h_development_learning_runner(ROOT)

    assert review["active_resolution"] == "12h"
    assert review["partition"] == "DEVELOPMENT"
    assert review["recovery_attempt"] == 3
    assert review["attempt_1_final_evidence_exists"] is False
    assert review["attempt_1_staging_evidence_exists"] is True
    assert review["attempt_1_authorization_consumed"] is True
    assert review["attempt_2_final_evidence_exists"] is False
    assert review["attempt_2_staging_evidence_exists"] is True
    assert review["attempt_2_authorization_consumed"] is True
    assert review["source_row_column_count"] == 7
    assert review["source_row_schema"] == [
        "Unix time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Trades",
    ]
    assert review["development_trade_count_validation_implemented"] is True
    assert review["eight_column_assumption_active"] is False
    assert review["prior_attempt_staging_count_required"] == 2
    assert review["boundary_missing_bucket_validation_implemented"] is True
    assert review["missing_development_timestamps_recorded"] is True
    assert review["mandatory_endpoint_presence_assumption_active"] is False
    assert review["runner_implemented"] is True
    assert review["real_model_artifact_persistence_implemented"] is True
    assert review["out_of_fold_prediction_artifact_implemented"] is True
    assert review["class_support_hold_cash_branch_implemented"] is True
    assert review["independent_evidence_lock_implemented"] is True
    assert review["one_shot_atomic_evidence_implemented"] is True
    assert review["authorization_phrase_active"] is False
    assert review["source_archive_opened"] is False
    assert review["development_data_opened"] is False
    assert review["labels_generated"] is False
    assert review["model_training_executed"] is False
    assert review["automatic_model_selection"] is False
    assert review["calibration_data_opened"] is False
    assert review["evaluation_data_opened"] is False
    assert review["candidate_v2_authorized"] is False
    assert review["live_execution_authorized"] is False


def test_review_fails_closed_if_runner_component_changes(tmp_path):
    relatives = (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_LEARNING_CORE_PROTOCOL_V1.md",
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_12H_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md",
        "KRAKEN_AI_DRIVEN_V2_12H_DEVELOPMENT_LEARNING_ATTEMPT_1_INCIDENT.md",
        "KRAKEN_AI_DRIVEN_V2_12H_DEVELOPMENT_LEARNING_ATTEMPT_2_INCIDENT.md",
        "src/kraken_ai_driven_v2_learning_core.py",
        "src/kraken_ai_driven_v2_12h_development_learning_runner.py",
    )
    for relative in relatives:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    runner = tmp_path / "src" / "kraken_ai_driven_v2_12h_development_learning_runner.py"
    runner.write_text(runner.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="runner_component"):
        review_12h_development_learning_runner(tmp_path)


def test_protocol_and_active_documents_describe_the_real_runner_without_authorizing_it():
    protocol = (
        ROOT
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_12H_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    assert "exactly six learned" in protocol
    assert "`.pkl` fold-model artifacts" in protocol
    assert "values parsed" in protocol
    assert "does not declare alpha or choose a winner" in protocol
    assert "Calibration or Evaluation access" in protocol
    assert "Unix time, Open, High, Low, Close, Volume, Trades" in protocol
    assert "There is no VWAP field" in protocol

    for name in ("VISION.md", "ARCHITECTURE.md", "ROADMAP.md", "CURRENT_MISSION.md", "LOG.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "12h" in text
        assert "Development Learning Runner" in " ".join(text.split())
        assert len(text.splitlines()) < 220
    mission = (ROOT / "CURRENT_MISSION.md").read_text(encoding="utf-8")
    assert (
        "EXECUTE_KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_RECOVERY_ATTEMPT_3_ONCE"
        in mission
    )
    assert "real Development model has yet been fitted" in mission
