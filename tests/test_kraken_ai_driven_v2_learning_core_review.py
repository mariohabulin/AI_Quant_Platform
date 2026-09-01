import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_learning_core_review import (
    EXPECTED_COMPONENT_SHA256,
    EXPECTED_PROTOCOL_SHA256,
    STATUS,
    review_learning_core,
)


ROOT = Path(__file__).resolve().parents[1]


def test_review_binds_the_executable_core_and_preserves_attempt_one():
    review = review_learning_core(ROOT)

    assert review["status"] == STATUS
    assert review["parent_commit"] == "8c51695"
    assert review["stage_2_attempt_1_report_sha256"] == (
        "ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1"
    )
    assert review["stage_2_attempt_1_preserved"] is True
    assert review["timestamp_forensic_scan_completed"] is True
    assert review["four_hour_reader_bug_found"] is False
    assert review["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert review["component_sha256"] == EXPECTED_COMPONENT_SHA256
    assert review["protocol_sha256_match"] is True
    assert review["component_sha256_match"] is True


def test_review_confirms_real_learning_code_and_no_real_run():
    review = review_learning_core(ROOT)

    assert review["active_resolution"] == "12h"
    assert review["retired_stage_2_per_asset_gate_active"] is False
    assert review["resolution_selection_claims_profitability"] is False
    assert review["causal_features_implemented"] is True
    assert review["triple_barrier_labels_implemented"] is True
    assert review["walk_forward_training_implemented"] is True
    assert review["parameters_learned_from_labels"] is True
    assert review["model_family_count"] == 2
    assert review["automatic_model_selection"] is False
    assert review["rule_discovery_rounds_active"] is False
    assert review["real_development_training_executed"] is False
    assert review["dataset_opened"] is False
    assert review["calibration_data_opened"] is False
    assert review["evaluation_data_opened"] is False
    assert review["candidate_v2_authorized"] is False
    assert review["paper_authorized"] is False
    assert review["real_orders_submitted"] is False
    assert review["live_execution_authorized"] is False


def test_review_fails_closed_if_component_is_changed(tmp_path):
    for relative in (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_LEARNING_CORE_PROTOCOL_V1.md",
        "src/kraken_ai_driven_v2_learning_core.py",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    component = tmp_path / "src" / "kraken_ai_driven_v2_learning_core.py"
    component.write_text(component.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="component SHA-256 mismatch"):
        review_learning_core(tmp_path)


def test_active_project_documents_are_concise_and_point_to_real_learning():
    names = ("VISION.md", "ARCHITECTURE.md", "ROADMAP.md", "CURRENT_MISSION.md", "LOG.md")
    for name in names:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Learning Core" in text
        assert "12h" in text
        assert "Candidate v2" in text
        assert len(text.splitlines()) < 200

    assert "Hash-Bound 12h Development Learning Runner — ATTEMPT 3 COMPLETED" in (
        ROOT / "ROADMAP.md"
    ).read_text(encoding="utf-8")
    assert "trained artifacts: six" in (
        ROOT / "CURRENT_MISSION.md"
    ).read_text(encoding="utf-8")
