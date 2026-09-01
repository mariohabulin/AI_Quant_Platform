import json
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_true_learning_contract_review import (
    COMPONENT_NORMALIZED_SHA256,
    PARENT_BINDINGS,
    PROTOCOL_NORMALIZED_SHA256,
    load_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_TRUE_LEARNING_CONTRACT_V1.md"
COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_true_learning_contract.py"


def test_review_hash_binds_stage_zero_and_true_learning_artifacts():
    _, protocol_digest = load_protocol(PROTOCOL)

    assert protocol_digest == PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(COMPONENT) == COMPONENT_NORMALIZED_SHA256
    assert len(PARENT_BINDINGS) == 4
    for binding in PARENT_BINDINGS:
        assert normalized_text_sha256(ROOT / binding["path"]) == binding["sha256"]


@pytest.mark.parametrize("binding_index", range(4))
def test_changed_parent_binding_is_rejected(tmp_path, binding_index):
    paths = [ROOT / item["path"] for item in PARENT_BINDINGS]
    source = paths[binding_index]
    changed = tmp_path / source.name
    changed.write_text(source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    paths[binding_index] = changed

    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        review_declaration(*paths, protocol_path=PROTOCOL, component_path=COMPONENT)


@pytest.mark.parametrize(
    "source,keyword",
    [
        (PROTOCOL, "protocol SHA256"),
        (COMPONENT, "component SHA256"),
    ],
)
def test_changed_true_learning_artifact_is_rejected(tmp_path, source, keyword):
    changed = tmp_path / source.name
    changed.write_text(source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    kwargs = {"protocol_path": PROTOCOL, "component_path": COMPONENT}
    if source == PROTOCOL:
        kwargs["protocol_path"] = changed
    else:
        kwargs["component_path"] = changed

    with pytest.raises(RuntimeError, match=keyword):
        review_declaration(**kwargs)


def test_review_confirms_contract_without_data_training_or_candidate():
    declaration = review_declaration()

    assert declaration["status"] == (
        "KRAKEN_AI_V2_TRUE_LEARNING_CONTRACT_REVIEWED_STAGE_2_AUDIT_REQUIRED"
    )
    assert declaration["protocol_sha256_match"] is True
    assert declaration["component_sha256_match"] is True
    assert declaration["stage_0_parent_binding_matches"] == {
        item["label"]: True for item in PARENT_BINDINGS
    }
    assert declaration["round_2_closed"] is True
    assert declaration["round_2_rerun_authorized"] is False
    assert declaration["true_learning_contract_frozen"] is True
    assert declaration["selected_resolution"] is None
    assert declaration["model_family_count"] == 2
    assert declaration["maximum_total_variants"] == 12
    assert declaration["parameters_learned_from_labels_required"] is True
    assert declaration["learned_model_artifact_required"] is True
    assert declaration["dataset_opened"] is False
    assert declaration["development_data_opened"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["labels_generated"] is False
    assert declaration["model_training_executed"] is False
    assert declaration["runtime_learning_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["live_execution_authorized"] is False
    assert declaration["next_stage"] == (
        "IMPLEMENT_STAGE_2_NONPERFORMANCE_DATA_SUFFICIENCY_AND_RESOLUTION_AUDIT"
    )


def test_parent_contract_cannot_claim_data_or_training_access():
    def bad_parent():
        from kraken_ai_driven_v2_round_2_closure_review import review_declaration as parent

        result = parent()
        result["development_data_opened"] = True
        return result

    with pytest.raises(RuntimeError, match="parent safety mismatch"):
        review_declaration(parent_reviewer=bad_parent)


def test_review_cli_prints_only_declaration(capsys):
    result = main([])
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["true_learning_contract_frozen"] is True
    assert payload["model_training_executed"] is False


def test_core_project_sources_record_stage_one_and_next_boundary():
    for name in ("VISION.md", "ARCHITECTURE.md", "ROADMAP.md", "CURRENT_MISSION.md", "LOG.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "True Learning Contract V1" in text
        assert "70e7bca" in text
        assert "three-class" in text
        assert "resolution remains unselected" in text
        assert "Candidate v2" in text
