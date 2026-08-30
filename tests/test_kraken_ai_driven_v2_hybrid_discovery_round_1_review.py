import json
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_hybrid_discovery_round_1 import (
    PROTOCOL_ID,
    ROUND_ID,
    STATUS,
)
from kraken_ai_driven_v2_hybrid_discovery_round_1_review import (
    COMPONENT_BINDINGS,
    ROUND_1_COMPONENT_NORMALIZED_SHA256,
    ROUND_1_PROTOCOL_NORMALIZED_SHA256,
    load_round_1_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (
    ROOT
    / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_HYBRID_DISCOVERY_ROUND_1_PROTOCOL_V1.md"
)
COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_hybrid_discovery_round_1.py"


def test_review_hash_binds_parent_hybrid_contract_and_round_1_artifacts():
    _, protocol_digest = load_round_1_protocol(PROTOCOL)

    assert protocol_digest == ROUND_1_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(COMPONENT) == (
        ROUND_1_COMPONENT_NORMALIZED_SHA256
    )
    assert len(COMPONENT_BINDINGS) == 3
    for binding in COMPONENT_BINDINGS:
        assert normalized_text_sha256(ROOT / binding["path"]) == binding["sha256"]


@pytest.mark.parametrize("binding_index", range(3))
def test_changed_parent_binding_is_rejected(tmp_path, binding_index):
    changed_paths = [ROOT / item["path"] for item in COMPONENT_BINDINGS]
    source = changed_paths[binding_index]
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    changed_paths[binding_index] = changed

    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        review_declaration(
            *changed_paths,
            round_1_protocol_path=PROTOCOL,
            round_1_component_path=COMPONENT,
        )


@pytest.mark.parametrize(
    "source,keyword",
    [
        (PROTOCOL, "Round 1 protocol SHA256"),
        (COMPONENT, "Round 1 component SHA256"),
    ],
)
def test_changed_round_1_artifact_is_rejected(tmp_path, source, keyword):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    kwargs = {
        "round_1_protocol_path": PROTOCOL,
        "round_1_component_path": COMPONENT,
    }
    if source == PROTOCOL:
        kwargs["round_1_protocol_path"] = changed
    else:
        kwargs["round_1_component_path"] = changed

    with pytest.raises(RuntimeError, match=keyword):
        review_declaration(**kwargs)


def test_review_confirms_registration_but_no_component_or_run_authorization():
    declaration = review_declaration()

    assert declaration["status"] == (
        "KRAKEN_AI_V2_HYBRID_DISCOVERY_ROUND_1_REVIEWED_"
        "COMPONENT_IMPLEMENTATION_REQUIRED"
    )
    assert declaration["round_1_status"] == STATUS
    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["round_id"] == ROUND_ID
    assert declaration["hypothesis_count"] == 4
    assert declaration["hypothesis_manifest_registered"] is True
    assert declaration["configuration_lock_implemented"] is True
    assert declaration["parent_hybrid_review_passed"] is True
    assert declaration["regime_components_implemented"] is False
    assert declaration["signal_components_implemented"] is False
    assert declaration["execution_components_implemented"] is False
    assert declaration["discovery_runner_implemented"] is False
    assert declaration["development_data_opened"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["development_run_authorized"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["automatic_ranking_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["live_execution_authorized"] is False
    assert declaration["next_stage"] == (
        "IMPLEMENT_ROUND_1_CAUSAL_COMPONENTS_SYNTHETIC_ONLY"
    )


def test_review_cli_prints_only_declaration(capsys):
    result = main([])
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["hypothesis_manifest_registered"] is True
    assert payload["development_data_opened"] is False
    assert payload["evaluation_data_opened"] is False


def test_protocol_and_project_documents_record_exact_round_1_boundary():
    protocol = PROTOCOL.read_text(encoding="utf-8")
    assert PROTOCOL_ID in protocol
    assert ROUND_ID in protocol
    assert "four hypotheses" in protocol
    assert "eight closed trades" in protocol
    assert "five fixed development slices" in protocol
    assert "components implemented: `false`" in protocol
    assert "development data opened: `false`" in protocol
    assert "evaluation data opened: `false`" in protocol
    assert "Candidate v2" in protocol

    for name in (
        "VISION.md",
        "ARCHITECTURE.md",
        "ROADMAP.md",
        "CURRENT_MISSION.md",
        "LOG.md",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert PROTOCOL_ID in text
        assert "Round 1" in text
        assert "four" in text.lower()
        assert "Reference A" in text
        assert "Candidate v2" in text
