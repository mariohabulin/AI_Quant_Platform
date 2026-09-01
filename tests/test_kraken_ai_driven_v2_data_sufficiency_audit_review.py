import json
import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_data_sufficiency_audit_review import (
    COMPONENT_NORMALIZED_SHA256,
    PROTOCOL_NORMALIZED_SHA256,
    REVIEW_STATUS,
    load_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DATA_SUFFICIENCY_RESOLUTION_AUDIT_PROTOCOL_V1.md"
COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_data_sufficiency_audit.py"


def test_review_is_hash_bound_nonexecuting_and_requires_separate_authorization():
    declaration = review_declaration()

    assert declaration["status"] == REVIEW_STATUS
    assert declaration["protocol_sha256_match"] is True
    assert declaration["component_sha256_match"] is True
    assert all(declaration["stage_1_parent_binding_matches"].values())
    assert declaration["stage_1_commit"] == "796c8de"
    assert declaration["candidate_resolution_minutes"] == [1440, 720, 240]
    assert declaration["audit_runner_implemented"] is True
    assert declaration["authorization_phrase_active"] is False
    assert declaration["source_archive_opened"] is False
    assert declaration["timestamp_columns_opened"] is False
    assert declaration["ohlcvt_value_columns_opened"] is False
    assert declaration["selected_resolution"] is None
    assert declaration["labels_generated"] is False
    assert declaration["model_training_executed"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["next_stage"] == (
        "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_STAGE_2_TIMESTAMP_AUDIT"
    )


def test_protocol_and_component_hashes_are_exact():
    _, protocol_digest = load_protocol(PROTOCOL)

    assert protocol_digest == PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(COMPONENT) == COMPONENT_NORMALIZED_SHA256


def test_protocol_or_component_tampering_fails(tmp_path):
    changed_protocol = tmp_path / "protocol.md"
    changed_protocol.write_text(PROTOCOL.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="protocol SHA256 mismatch"):
        review_declaration(protocol_path=changed_protocol)

    changed_component = tmp_path / "component.py"
    changed_component.write_text(COMPONENT.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="component SHA256 mismatch"):
        review_declaration(component_path=changed_component)


def test_parent_review_failure_fails_closed():
    def invalid_parent():
        return {"status": "WRONG", "stage_0_parent_binding_matches": {"x": True}}

    with pytest.raises(RuntimeError, match="parent review"):
        review_declaration(parent_reviewer=invalid_parent)


def test_review_cli_prints_canonical_boundary(capsys):
    declaration = main([])
    printed = json.loads(capsys.readouterr().out)

    assert declaration == printed
    assert printed["status"] == REVIEW_STATUS
    assert printed["performance_evaluation_executed"] is False


def test_core_project_sources_record_stage_two_and_true_learning_boundary():
    for name in ("VISION.md", "ARCHITECTURE.md", "ROADMAP.md", "CURRENT_MISSION.md", "LOG.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Stage 2" in text
        assert "796c8de" in text
        assert "1d, 12h and 4h" in text
        assert "timestamp-only" in text
        assert "no model training" in text
        assert "Candidate v2" in text
