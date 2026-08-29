import json
import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_risk_execution import (
    COST_PROFILE_ID,
    RISK_EXECUTION_POLICY_ID,
)
from kraken_ai_driven_v2_risk_execution_review import (
    DATASET_ID,
    DATASET_MANIFEST_SHA256,
    RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256,
    RISK_EXECUTION_PROTOCOL_ID,
    RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256,
    STATE_COMPONENT_NORMALIZED_SHA256,
    STATE_PROTOCOL_ID,
    STATE_PROTOCOL_NORMALIZED_SHA256,
    V1_BTC_EPISODE_EVIDENCE_SHA256,
    load_risk_execution_protocol,
    load_state_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)
from kraken_ai_driven_v2_state_machine import PARAMETER_SET_ID


ROOT = Path(__file__).resolve().parents[1]
STATE_PROTOCOL = ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_STATE_MACHINE_PROTOCOL_V1.md"
STATE_COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_state_machine.py"
RISK_PROTOCOL = (
    ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_RISK_EXECUTION_PROTOCOL_V1.md"
)
RISK_COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_risk_execution.py"


def test_risk_execution_review_inputs_are_exact_hash_bound():
    _, state_protocol_digest = load_state_protocol(STATE_PROTOCOL)
    _, risk_protocol_digest = load_risk_execution_protocol(RISK_PROTOCOL)

    assert state_protocol_digest == STATE_PROTOCOL_NORMALIZED_SHA256
    assert risk_protocol_digest == RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(STATE_COMPONENT) == (
        STATE_COMPONENT_NORMALIZED_SHA256
    )
    assert normalized_text_sha256(RISK_COMPONENT) == (
        RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256
    )


@pytest.mark.parametrize(
    "source,position,error",
    [
        (STATE_PROTOCOL, 0, "state protocol SHA256"),
        (STATE_COMPONENT, 1, "state component SHA256"),
        (RISK_PROTOCOL, 2, "risk/execution protocol SHA256"),
        (RISK_COMPONENT, 3, "risk/execution component SHA256"),
    ],
)
def test_changed_risk_execution_review_input_is_rejected(
    tmp_path, source, position, error
):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    paths = [STATE_PROTOCOL, STATE_COMPONENT, RISK_PROTOCOL, RISK_COMPONENT]
    paths[position] = changed

    with pytest.raises(RuntimeError, match=error):
        review_declaration(*paths)


def test_risk_execution_review_declaration_is_nonexecuting_and_partition_blocked():
    declaration = review_declaration(
        STATE_PROTOCOL,
        STATE_COMPONENT,
        RISK_PROTOCOL,
        RISK_COMPONENT,
    )

    assert declaration["status"].endswith("PARTITION_PROTOCOL_REQUIRED")
    assert declaration["risk_execution_protocol_id"] == RISK_EXECUTION_PROTOCOL_ID
    assert declaration["risk_execution_policy_id"] == RISK_EXECUTION_POLICY_ID
    assert declaration["cost_profile_id"] == COST_PROFILE_ID
    assert declaration["state_protocol_id"] == STATE_PROTOCOL_ID
    assert declaration["state_parameter_set_id"] == PARAMETER_SET_ID
    assert declaration["dataset_id"] == DATASET_ID
    assert declaration["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert declaration["asset_order"] == ["BTC-USD", "ETH-USD", "XRP-USD"]
    assert declaration["v1_btc_episode_evidence_sha256"] == (
        V1_BTC_EPISODE_EVIDENCE_SHA256
    )
    assert declaration["deterministic_state_machine_implemented"] is True
    assert declaration["synthetic_risk_execution_adapter_implemented"] is True
    assert declaration["action_intents_are_real_fills"] is False
    assert declaration["adverse_taker_cost_model_frozen"] is True
    assert declaration["commission_rate_per_side"] == 0.008
    assert declaration["assumed_slippage_rate_per_side"] == 0.0015
    assert declaration["assumed_full_spread_rate"] == 0.003
    assert declaration["risk_per_trade_fraction"] == 0.005
    assert declaration["maximum_total_open_risk_fraction"] == 0.015
    assert declaration["minimum_net_reward_risk"] == 3.0
    assert declaration["maximum_holding_completed_bars"] == 20
    assert declaration["real_account_fee_tier_verified"] is False
    assert declaration["venue_minimum_order_rules_implemented"] is False
    assert declaration["real_orders_or_fills_executed"] is False
    assert declaration["dataset_opened"] is False
    assert declaration["real_data_execution_run_executed"] is False
    assert declaration["network_requests_executed"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["optimization_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["cloud_execution_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_risk_execution_review_cli_prints_only_declaration(capsys):
    result = main(
        [
            "--state-protocol",
            str(STATE_PROTOCOL),
            "--state-component",
            str(STATE_COMPONENT),
            "--risk-execution-protocol",
            str(RISK_PROTOCOL),
            "--risk-execution-component",
            str(RISK_COMPONENT),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["dataset_opened"] is False
    assert payload["real_orders_or_fills_executed"] is False
    assert payload["performance_evaluation_executed"] is False


def test_project_documents_name_risk_execution_and_next_partition_boundary():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mission = (ROOT / "CURRENT_MISSION.md").read_text(encoding="utf-8")
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    vision = (ROOT / "VISION.md").read_text(encoding="utf-8")
    log = (ROOT / "LOG.md").read_text(encoding="utf-8")

    assert "AI-Driven v2 Risk and Execution" in roadmap
    assert "RISK AND EXECUTION ADAPTER IMPLEMENTED" in mission
    assert "AI-Driven v2 Risk and Synthetic Execution Layer" in architecture
    assert "cost-aware" in vision
    assert "AI-Driven v2 Risk and Execution" in log
    for text in (roadmap, mission, architecture, vision, log):
        assert RISK_EXECUTION_POLICY_ID in text
        assert V1_BTC_EPISODE_EVIDENCE_SHA256 in text
        assert "Candidate v2" in text
        assert "live" in text.lower()
