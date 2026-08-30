import json
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_strategy_discovery import PROTOCOL_ID, STATUS
from kraken_ai_driven_v2_strategy_discovery_review import (
    COMPONENT_BINDINGS,
    DISCOVERY_COMPONENT_NORMALIZED_SHA256,
    DISCOVERY_PROTOCOL_NORMALIZED_SHA256,
    load_discovery_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (
    ROOT
    / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_STRATEGY_DISCOVERY_LEARNING_PROTOCOL_V1.md"
)
COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_strategy_discovery.py"


def test_review_exactly_hash_binds_closure_safety_partition_and_new_contract():
    _, protocol_digest = load_discovery_protocol(PROTOCOL)

    assert protocol_digest == DISCOVERY_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(COMPONENT) == (
        DISCOVERY_COMPONENT_NORMALIZED_SHA256
    )
    assert len(COMPONENT_BINDINGS) == 6
    for binding in COMPONENT_BINDINGS:
        assert normalized_text_sha256(ROOT / binding["path"]) == binding["sha256"]


@pytest.mark.parametrize("binding_index", range(6))
def test_changed_upstream_binding_is_rejected(tmp_path, binding_index):
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
            discovery_protocol_path=PROTOCOL,
            discovery_component_path=COMPONENT,
        )


@pytest.mark.parametrize(
    "source,keyword",
    [
        (PROTOCOL, "discovery protocol SHA256"),
        (COMPONENT, "discovery component SHA256"),
    ],
)
def test_changed_new_discovery_artifact_is_rejected(tmp_path, source, keyword):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    kwargs = {
        "discovery_protocol_path": PROTOCOL,
        "discovery_component_path": COMPONENT,
    }
    if source == PROTOCOL:
        kwargs["discovery_protocol_path"] = changed
    else:
        kwargs["discovery_component_path"] = changed

    with pytest.raises(RuntimeError, match=keyword):
        review_declaration(**kwargs)


def test_review_is_nonexecuting_and_requires_a_separate_hypothesis_manifest():
    declaration = review_declaration()

    assert declaration["status"] == (
        "KRAKEN_AI_V2_HYBRID_DISCOVERY_PROTOCOL_REVIEWED_"
        "HYPOTHESIS_MANIFEST_REQUIRED"
    )
    assert declaration["discovery_protocol_status"] == STATUS
    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["strategy_family_count"] == 4
    assert declaration["regime_count"] == 5
    assert declaration["hybrid_routing_contract_implemented"] is True
    assert declaration["bounded_manifest_validator_implemented"] is True
    assert declaration["reference_a_closed"] is True
    assert declaration["reference_a_rerun_authorized"] is False
    assert declaration["hypothesis_manifest_registered"] is False
    assert declaration["discovery_runner_implemented"] is False
    assert declaration["development_data_opened"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["automatic_ranking_authorized"] is False
    assert declaration["runtime_learning_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["live_execution_authorized"] is False
    assert declaration["next_stage"] == (
        "PRE_REGISTER_BOUNDED_HYBRID_DISCOVERY_ROUND_1"
    )


def test_review_cli_prints_only_declaration(capsys):
    result = main([])
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["hypothesis_manifest_registered"] is False
    assert payload["development_data_opened"] is False
    assert payload["evaluation_data_opened"] is False


def test_protocol_and_project_documents_record_the_hybrid_boundary():
    protocol = PROTOCOL.read_text(encoding="utf-8")
    assert PROTOCOL_ID in protocol
    assert "shared catalog, asset/regime-specific routing" in protocol
    assert "HOLD_CASH" in protocol
    assert "six hypotheses" in protocol
    assert "runtime learning" in protocol
    assert "calibration data opened: `false`" in protocol
    assert "evaluation data opened: `false`" in protocol

    for name in (
        "VISION.md",
        "ARCHITECTURE.md",
        "ROADMAP.md",
        "CURRENT_MISSION.md",
        "LOG.md",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert PROTOCOL_ID in text
        assert "hybrid" in text.lower()
        assert "Reference A" in text
        assert "Candidate v2" in text
