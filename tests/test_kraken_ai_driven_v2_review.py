import json
import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_review import (
    DATASET_ID,
    DATASET_MANIFEST_SHA256,
    FEATURE_COMPONENT_NORMALIZED_SHA256,
    FEATURE_PROTOCOL_NORMALIZED_SHA256,
    PROTOCOL_ID,
    V1_BTC_EPISODE_EVIDENCE_SHA256,
    V1_CLOSEOUT_NORMALIZED_SHA256,
    V1_SELECTION_SCHEDULE_SHA256,
    load_feature_component,
    load_feature_protocol,
    load_v1_closeout,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
V1_CLOSEOUT = ROOT / "KRAKEN_BTC_SUPERVISED_BLINDED_REPLAY_EPISODE_01_CLOSEOUT_V1.md"
FEATURE_PROTOCOL = (
    ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_CAUSAL_FEATURE_PROTOCOL_V1.md"
)
FEATURE_COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_features.py"


def test_v2_contract_and_feature_component_are_exact_hash_bound():
    _, closeout_digest = load_v1_closeout(V1_CLOSEOUT)
    _, protocol_digest = load_feature_protocol(FEATURE_PROTOCOL)
    component_digest = load_feature_component(FEATURE_COMPONENT)

    assert closeout_digest == V1_CLOSEOUT_NORMALIZED_SHA256
    assert protocol_digest == FEATURE_PROTOCOL_NORMALIZED_SHA256
    assert component_digest == FEATURE_COMPONENT_NORMALIZED_SHA256
    assert normalized_text_sha256(V1_CLOSEOUT) == V1_CLOSEOUT_NORMALIZED_SHA256
    assert normalized_text_sha256(FEATURE_PROTOCOL) == (
        FEATURE_PROTOCOL_NORMALIZED_SHA256
    )
    assert normalized_text_sha256(FEATURE_COMPONENT) == (
        FEATURE_COMPONENT_NORMALIZED_SHA256
    )


@pytest.mark.parametrize(
    "source,loader,error",
    [
        (V1_CLOSEOUT, load_v1_closeout, "closeout SHA256"),
        (FEATURE_PROTOCOL, load_feature_protocol, "feature protocol SHA256"),
        (FEATURE_COMPONENT, load_feature_component, "feature component SHA256"),
    ],
)
def test_changed_v2_review_input_is_rejected(tmp_path, source, loader, error):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match=error):
        loader(changed)


def test_review_declaration_starts_v2_without_data_strategy_or_performance():
    declaration = review_declaration(V1_CLOSEOUT, FEATURE_PROTOCOL, FEATURE_COMPONENT)

    assert declaration["status"].endswith("STATE_MACHINE_REQUIRED")
    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["dataset_id"] == DATASET_ID
    assert declaration["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert declaration["asset_order"] == ["BTC-USD", "ETH-USD", "XRP-USD"]
    assert declaration["v1_selection_schedule_sha256"] == (
        V1_SELECTION_SCHEDULE_SHA256
    )
    assert declaration["v1_btc_episode_evidence_sha256"] == (
        V1_BTC_EPISODE_EVIDENCE_SHA256
    )
    assert declaration["v1_btc_episode_completed"] is True
    assert declaration["v1_eth_episode_opened"] is False
    assert declaration["v1_xrp_episode_opened"] is False
    assert declaration["additional_supervised_v1_replay_authorized"] is False
    assert declaration["existing_locked_dataset_reusable"] is True
    assert declaration["dataset_update_required_before_v2_development"] is False
    assert declaration["future_archive_update_requires_new_dataset_identity"] is True
    assert declaration["dataset_opened"] is False
    assert declaration["network_requests_executed"] is False
    assert declaration["causal_feature_component_implemented"] is True
    assert declaration["production_feature_parameters_frozen"] is False
    assert declaration["state_machine_implemented"] is False
    assert declaration["trading_actions_emitted"] is False
    assert declaration["prior_rejected_strategy_reused"] is False
    assert declaration["risk_adapter_implemented"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["optimization_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["cloud_execution_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_review_cli_prints_only_nonexecuting_declaration(capsys):
    result = main(
        [
            "--v1-closeout",
            str(V1_CLOSEOUT),
            "--feature-protocol",
            str(FEATURE_PROTOCOL),
            "--feature-component",
            str(FEATURE_COMPONENT),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["dataset_opened"] is False
    assert payload["performance_evaluation_executed"] is False


def test_project_documents_name_v2_as_the_active_nonperformance_boundary():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mission = (ROOT / "CURRENT_MISSION.md").read_text(encoding="utf-8")
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    vision = (ROOT / "VISION.md").read_text(encoding="utf-8")
    log = (ROOT / "LOG.md").read_text(encoding="utf-8")

    assert "AI-Driven Crypto Research v2" in roadmap
    assert "AI-DRIVEN V2 CAUSAL FEATURE CONTRACT" in mission
    assert "AI-Driven v2 Layer Boundary" in architecture
    assert "deterministic AI-driven research agent" in vision
    assert "AI-Driven v2 Causal Feature Contract" in log
    for text in (roadmap, mission, architecture, vision, log):
        assert "56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60" in text
        assert "Candidate v2" in text
        assert "live" in text.lower()
