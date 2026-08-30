import json
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_round_1_family_execution_review import (
    COMPONENT_BINDINGS,
    EXECUTION_COMPONENT_NORMALIZED_SHA256,
    EXECUTION_PROTOCOL_NORMALIZED_SHA256,
    load_execution_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (
    ROOT
    / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_1_FAMILY_EXECUTION_PROTOCOL_V1.md"
)
COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_round_1_family_execution.py"


def test_review_hash_binds_signal_parent_and_execution_artifacts():
    _, protocol_digest = load_execution_protocol(PROTOCOL)

    assert protocol_digest == EXECUTION_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(COMPONENT) == EXECUTION_COMPONENT_NORMALIZED_SHA256
    assert len(COMPONENT_BINDINGS) == 3
    for binding in COMPONENT_BINDINGS:
        assert normalized_text_sha256(ROOT / binding["path"]) == binding["sha256"]


@pytest.mark.parametrize("binding_index", range(3))
def test_changed_causal_signal_parent_binding_is_rejected(tmp_path, binding_index):
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
            execution_protocol_path=PROTOCOL,
            execution_component_path=COMPONENT,
        )


@pytest.mark.parametrize(
    "source,keyword",
    [
        (PROTOCOL, "family execution protocol SHA256"),
        (COMPONENT, "family execution component SHA256"),
    ],
)
def test_changed_execution_artifact_is_rejected(tmp_path, source, keyword):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    kwargs = {
        "execution_protocol_path": PROTOCOL,
        "execution_component_path": COMPONENT,
    }
    if source == PROTOCOL:
        kwargs["execution_protocol_path"] = changed
    else:
        kwargs["execution_component_path"] = changed

    with pytest.raises(RuntimeError, match=keyword):
        review_declaration(**kwargs)


def test_review_confirms_family_execution_but_keeps_runner_and_data_closed():
    declaration = review_declaration()

    assert declaration["status"] == (
        "KRAKEN_AI_V2_ROUND_1_FAMILY_EXECUTION_REVIEWED_"
        "DISCOVERY_RUNNER_REQUIRED"
    )
    assert declaration["parent_causal_signal_review_passed"] is True
    assert declaration["family_execution_components_implemented"] is True
    assert declaration["family_count"] == 4
    assert declaration["baseline_cost_profile_implemented"] is True
    assert declaration["stress_cost_profile_implemented"] is True
    assert declaration["shared_safety_envelope_implemented"] is True
    assert declaration["protective_execution_implemented"] is True
    assert declaration["discovery_runner_implemented"] is False
    assert declaration["dataset_opened"] is False
    assert declaration["development_data_opened"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["development_run_authorized"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["automatic_ranking_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["live_execution_authorized"] is False
    assert declaration["next_stage"] == (
        "IMPLEMENT_ROUND_1_DEVELOPMENT_DISCOVERY_RUNNER"
    )


def test_review_cli_prints_only_declaration(capsys):
    result = main([])
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["family_execution_components_implemented"] is True
    assert payload["discovery_runner_implemented"] is False
    assert payload["development_data_opened"] is False


def test_protocol_and_project_documents_record_execution_only_boundary():
    protocol = PROTOCOL.read_text(encoding="utf-8")
    assert "four family-specific execution adapters" in protocol
    assert "stop gap before scheduled exit" in protocol
    assert "same-bar stop and target: `STOP_FIRST`" in protocol
    assert "execution components implemented: `true`" in protocol
    assert "development data opened: `false`" in protocol
    assert "real orders submitted: `false`" in protocol
    assert "Reference A" in protocol
    assert "Candidate v2" in protocol

    for name in (
        "VISION.md",
        "ARCHITECTURE.md",
        "ROADMAP.md",
        "CURRENT_MISSION.md",
        "LOG.md",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Round 1 Family Execution" in text
        assert "four" in text.lower()
        assert "Reference A" in text
        assert "Candidate v2" in text
