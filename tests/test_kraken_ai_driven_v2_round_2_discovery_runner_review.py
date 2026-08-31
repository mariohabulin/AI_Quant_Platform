import json
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_round_2_discovery_runner_review import (
    COMPONENT_BINDINGS,
    RUNNER_COMPONENT_NORMALIZED_SHA256,
    RUNNER_PROTOCOL_NORMALIZED_SHA256,
    load_runner_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_2_DISCOVERY_RUNNER_PROTOCOL_V1.md"
COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_round_2_discovery_runner.py"


def test_review_hash_binds_family_execution_parent_and_runner_artifacts():
    _, protocol_digest = load_runner_protocol(PROTOCOL)

    assert protocol_digest == RUNNER_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(COMPONENT) == RUNNER_COMPONENT_NORMALIZED_SHA256
    assert len(COMPONENT_BINDINGS) == 3
    for binding in COMPONENT_BINDINGS:
        assert normalized_text_sha256(ROOT / binding["path"]) == binding["sha256"]


@pytest.mark.parametrize("binding_index", range(3))
def test_changed_family_execution_parent_is_rejected(tmp_path, binding_index):
    changed_paths = [ROOT / item["path"] for item in COMPONENT_BINDINGS]
    source = changed_paths[binding_index]
    changed = tmp_path / source.name
    changed.write_text(source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    changed_paths[binding_index] = changed

    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        review_declaration(
            *changed_paths,
            runner_protocol_path=PROTOCOL,
            runner_component_path=COMPONENT,
        )


@pytest.mark.parametrize(
    "source,keyword",
    [
        (PROTOCOL, "discovery runner protocol SHA256"),
        (COMPONENT, "discovery runner component SHA256"),
    ],
)
def test_changed_runner_artifact_is_rejected(tmp_path, source, keyword):
    changed = tmp_path / source.name
    changed.write_text(source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    kwargs = {"runner_protocol_path": PROTOCOL, "runner_component_path": COMPONENT}
    if source == PROTOCOL:
        kwargs["runner_protocol_path"] = changed
    else:
        kwargs["runner_component_path"] = changed

    with pytest.raises(RuntimeError, match=keyword):
        review_declaration(**kwargs)


def test_review_confirms_runner_but_keeps_data_and_authorization_closed():
    declaration = review_declaration()

    assert declaration["status"].endswith("EXECUTION_AUTHORIZATION_REQUIRED")
    assert declaration["parent_family_execution_review_passed"] is True
    assert declaration["route_count"] == 7
    assert declaration["route_order"] == [
        "BTC-USD|CAPITULATION_RECOVERY",
        "BTC-USD|VOLATILITY_BREAKOUT",
        "BTC-USD|TREND_PULLBACK_CONTINUATION",
        "ETH-USD|CAPITULATION_RECOVERY",
        "ETH-USD|VOLATILITY_BREAKOUT",
        "ETH-USD|TREND_PULLBACK_CONTINUATION",
        "XRP-USD|CAPITULATION_RECOVERY",
    ]
    assert declaration["discovery_runner_implemented"] is True
    assert declaration["development_only_reader_reused"] is True
    assert declaration["independent_evidence_lock_implemented"] is True
    assert declaration["authorization_phrase_active"] is False
    assert declaration["dataset_opened"] is False
    assert declaration["development_data_opened"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["development_run_authorized"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["automatic_ranking_generated"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["real_orders_submitted"] is False
    assert declaration["live_execution_authorized"] is False
    assert declaration["next_stage"].startswith("SEPARATE_OPERATOR_DECISION")


def test_parent_review_cannot_claim_data_or_execution():
    def bad_parent():
        return {
            "status": "KRAKEN_AI_V2_ROUND_2_FAMILY_EXECUTION_REVIEWED_DISCOVERY_RUNNER_REQUIRED",
            "parent_source_binding_matches": {"x": True},
            "family_execution_components_implemented": True,
            "baseline_cost_profile_implemented": True,
            "stress_cost_profile_implemented": True,
            "shared_safety_envelope_implemented": True,
            "protective_execution_implemented": True,
            "discovery_runner_implemented": False,
            "dataset_opened": True,
            "development_data_opened": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "performance_evaluation_executed": False,
            "candidate_v2_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
        }

    with pytest.raises(RuntimeError, match="parent safety mismatch for dataset_opened"):
        review_declaration(parent_reviewer=bad_parent)


def test_review_cli_prints_only_declaration(capsys):
    result = main([])
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["discovery_runner_implemented"] is True
    assert payload["development_run_authorized"] is False


def test_protocol_and_project_documents_record_unexecuted_runner_boundary():
    protocol = PROTOCOL.read_text(encoding="utf-8")
    assert "seven pre-registered Round 2 asset-family routes" in protocol
    assert "independent USD 5,000 research ledger" in protocol
    assert "A no-trade slice does not count as nonnegative" in protocol
    assert "Synthetic terminal force-close is prohibited" in protocol
    assert "development data opened: `false`" in protocol
    assert "development run authorized: `false`" in protocol
    assert "Reference A" in protocol
    assert "Candidate v2" in protocol

    for name in ("VISION.md", "ARCHITECTURE.md", "ROADMAP.md", "CURRENT_MISSION.md", "LOG.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Round 2 Discovery Runner" in text
        assert "7" in text
        assert "Reference A" in text
        assert "Candidate v2" in text
