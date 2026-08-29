import json
import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_state_review import (
    DATASET_ID,
    DATASET_MANIFEST_SHA256,
    FEATURE_COMPONENT_NORMALIZED_SHA256,
    FEATURE_PROTOCOL_ID,
    FEATURE_PROTOCOL_NORMALIZED_SHA256,
    STATE_COMPONENT_NORMALIZED_SHA256,
    STATE_PROTOCOL_ID,
    STATE_PROTOCOL_NORMALIZED_SHA256,
    V1_BTC_EPISODE_EVIDENCE_SHA256,
    load_feature_protocol,
    load_state_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)
from kraken_ai_driven_v2_state_machine import PARAMETER_SET_ID


ROOT = Path(__file__).resolve().parents[1]
FEATURE_PROTOCOL = (
    ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_CAUSAL_FEATURE_PROTOCOL_V1.md"
)
FEATURE_COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_features.py"
STATE_PROTOCOL = ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_STATE_MACHINE_PROTOCOL_V1.md"
STATE_COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_state_machine.py"


def test_state_review_inputs_are_exact_hash_bound():
    _, feature_protocol_digest = load_feature_protocol(FEATURE_PROTOCOL)
    _, state_protocol_digest = load_state_protocol(STATE_PROTOCOL)

    assert feature_protocol_digest == FEATURE_PROTOCOL_NORMALIZED_SHA256
    assert state_protocol_digest == STATE_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(FEATURE_COMPONENT) == (
        FEATURE_COMPONENT_NORMALIZED_SHA256
    )
    assert normalized_text_sha256(STATE_COMPONENT) == (
        STATE_COMPONENT_NORMALIZED_SHA256
    )


@pytest.mark.parametrize(
    "source,position,error",
    [
        (FEATURE_PROTOCOL, 0, "feature protocol SHA256"),
        (FEATURE_COMPONENT, 1, "feature component SHA256"),
        (STATE_PROTOCOL, 2, "state protocol SHA256"),
        (STATE_COMPONENT, 3, "state component SHA256"),
    ],
)
def test_changed_state_review_input_is_rejected(tmp_path, source, position, error):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    paths = [FEATURE_PROTOCOL, FEATURE_COMPONENT, STATE_PROTOCOL, STATE_COMPONENT]
    paths[position] = changed

    with pytest.raises(RuntimeError, match=error):
        review_declaration(*paths)


def test_state_review_declaration_is_nonexecuting_and_risk_blocked():
    declaration = review_declaration(
        FEATURE_PROTOCOL,
        FEATURE_COMPONENT,
        STATE_PROTOCOL,
        STATE_COMPONENT,
    )

    assert declaration["status"].endswith("RISK_EXECUTION_REQUIRED")
    assert declaration["state_protocol_id"] == STATE_PROTOCOL_ID
    assert declaration["feature_protocol_id"] == FEATURE_PROTOCOL_ID
    assert declaration["parameter_set_id"] == PARAMETER_SET_ID
    assert declaration["dataset_id"] == DATASET_ID
    assert declaration["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert declaration["asset_order"] == ["BTC-USD", "ETH-USD", "XRP-USD"]
    assert declaration["v1_btc_episode_evidence_sha256"] == (
        V1_BTC_EPISODE_EVIDENCE_SHA256
    )
    assert declaration["causal_feature_component_implemented"] is True
    assert declaration["reference_state_parameters_frozen"] is True
    assert declaration["deterministic_state_machine_implemented"] is True
    assert declaration["state_path"] == ["FLAT", "ARMED", "LONG", "FLAT"]
    assert declaration["action_intents_emitted"] is True
    assert declaration["action_intents_are_fills"] is False
    assert declaration["real_order_fills_executed"] is False
    assert declaration["risk_adapter_implemented"] is False
    assert declaration["dataset_opened"] is False
    assert declaration["real_data_state_run_executed"] is False
    assert declaration["network_requests_executed"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["optimization_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["cloud_execution_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_state_review_cli_prints_only_declaration(capsys):
    result = main(
        [
            "--feature-protocol",
            str(FEATURE_PROTOCOL),
            "--feature-component",
            str(FEATURE_COMPONENT),
            "--state-protocol",
            str(STATE_PROTOCOL),
            "--state-component",
            str(STATE_COMPONENT),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["dataset_opened"] is False
    assert payload["real_order_fills_executed"] is False
    assert payload["performance_evaluation_executed"] is False


def test_project_documents_name_state_machine_and_next_risk_boundary():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mission = (ROOT / "CURRENT_MISSION.md").read_text(encoding="utf-8")
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    vision = (ROOT / "VISION.md").read_text(encoding="utf-8")
    log = (ROOT / "LOG.md").read_text(encoding="utf-8")

    assert "AI-Driven v2 State Machine" in roadmap
    assert "STATE MACHINE IMPLEMENTED" in mission
    assert "AI-Driven v2 Signal-State Layer" in architecture
    assert "FLAT -> ARMED -> LONG -> FLAT" in vision
    assert "AI-Driven v2 State Machine" in log
    for text in (roadmap, mission, architecture, vision, log):
        assert PARAMETER_SET_ID in text
        assert V1_BTC_EPISODE_EVIDENCE_SHA256 in text
        assert "Candidate v2" in text
        assert "live" in text.lower()
