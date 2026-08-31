import json
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_round_2_causal_signals_review import (
    COMPONENT_BINDINGS,
    SIGNAL_COMPONENT_NORMALIZED_SHA256,
    SIGNAL_PROTOCOL_NORMALIZED_SHA256,
    load_signal_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (
    ROOT
    / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_2_CAUSAL_SIGNALS_PROTOCOL_V1.md"
)
COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_round_2_causal_signals.py"


def test_review_hash_binds_round_2_registration_and_signal_artifacts():
    _, protocol_digest = load_signal_protocol(PROTOCOL)

    assert protocol_digest == SIGNAL_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(COMPONENT) == SIGNAL_COMPONENT_NORMALIZED_SHA256
    assert len(COMPONENT_BINDINGS) == 3
    for binding in COMPONENT_BINDINGS:
        assert normalized_text_sha256(ROOT / binding["path"]) == binding["sha256"]


@pytest.mark.parametrize("binding_index", range(3))
def test_changed_round_2_parent_binding_is_rejected(tmp_path, binding_index):
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
            signal_protocol_path=PROTOCOL,
            signal_component_path=COMPONENT,
        )


@pytest.mark.parametrize(
    "source,keyword",
    [
        (PROTOCOL, "causal signals protocol SHA256"),
        (COMPONENT, "causal signals component SHA256"),
    ],
)
def test_changed_signal_artifact_is_rejected(tmp_path, source, keyword):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    kwargs = {
        "signal_protocol_path": PROTOCOL,
        "signal_component_path": COMPONENT,
    }
    if source == PROTOCOL:
        kwargs["signal_protocol_path"] = changed
    else:
        kwargs["signal_component_path"] = changed

    with pytest.raises(RuntimeError, match=keyword):
        review_declaration(**kwargs)


def test_bad_round_2_parent_review_is_rejected():
    def bad_parent_review():
        return {
            "status": "WRONG",
            "parent_source_binding_matches": {"bad": True},
        }

    with pytest.raises(RuntimeError, match="parent review status mismatch"):
        review_declaration(parent_reviewer=bad_parent_review)


def test_review_confirms_signals_but_keeps_execution_and_data_closed():
    declaration = review_declaration()

    assert declaration["status"] == (
        "KRAKEN_AI_V2_ROUND_2_CAUSAL_SIGNALS_REVIEWED_"
        "EXECUTION_COMPONENTS_REQUIRED"
    )
    assert declaration["parent_round_2_review_passed"] is True
    assert declaration["feature_component_implemented"] is True
    assert declaration["regime_components_implemented"] is True
    assert declaration["signal_components_implemented"] is True
    assert declaration["family_count"] == 3
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
        "IMPLEMENT_ROUND_2_FAMILY_EXECUTION_COMPONENTS_SYNTHETIC_ONLY"
    )


def test_review_cli_prints_only_declaration(capsys):
    result = main([])
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["signal_components_implemented"] is True
    assert payload["execution_components_implemented"] is False
    assert payload["development_data_opened"] is False


def test_protocol_and_project_documents_record_signal_only_boundary():
    protocol = PROTOCOL.read_text(encoding="utf-8")
    assert "three exact" in protocol
    assert "At least two completed post-setup bars" in protocol
    assert "rolling baseline current bar included is `false`" in protocol
    assert "Round 2 execution components implemented: `false`" in protocol
    assert "Development data opened: `false`" in protocol
    assert "3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b" in protocol
    assert "Candidate v2" in protocol

    for name in (
        "VISION.md",
        "ARCHITECTURE.md",
        "ROADMAP.md",
        "CURRENT_MISSION.md",
        "LOG.md",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Round 2 Causal Signals" in text
        assert "three" in text.lower()
        assert "3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b" in text
        assert "Candidate v2" in text
