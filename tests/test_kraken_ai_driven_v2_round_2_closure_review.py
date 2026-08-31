import json
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_round_2_closure_review import (
    CLOSURE_COMPONENT_NORMALIZED_SHA256,
    CLOSURE_DOCUMENT_NORMALIZED_SHA256,
    PARENT_BINDINGS,
    SCOPE_CORRECTION_DOCUMENT_NORMALIZED_SHA256,
    load_closure_document,
    load_scope_correction_document,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "KRAKEN_AI_DRIVEN_V2_ROUND_2_CLOSURE.md"
COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_round_2_closure.py"
SCOPE_CORRECTION = ROOT / "KRAKEN_AI_DRIVEN_V2_SCOPE_GAP_CORRECTION_V1.md"


def test_review_hash_binds_discovery_runner_parent_and_closure_artifacts():
    _, document_digest = load_closure_document(DOCUMENT)
    _, scope_digest = load_scope_correction_document(SCOPE_CORRECTION)

    assert document_digest == CLOSURE_DOCUMENT_NORMALIZED_SHA256
    assert normalized_text_sha256(COMPONENT) == CLOSURE_COMPONENT_NORMALIZED_SHA256
    assert scope_digest == SCOPE_CORRECTION_DOCUMENT_NORMALIZED_SHA256
    assert len(PARENT_BINDINGS) == 3
    for binding in PARENT_BINDINGS:
        assert normalized_text_sha256(ROOT / binding["path"]) == binding["sha256"]


@pytest.mark.parametrize("binding_index", range(3))
def test_changed_discovery_runner_parent_is_rejected(tmp_path, binding_index):
    changed_paths = [ROOT / item["path"] for item in PARENT_BINDINGS]
    source = changed_paths[binding_index]
    changed = tmp_path / source.name
    changed.write_text(source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    changed_paths[binding_index] = changed

    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        review_declaration(
            *changed_paths,
            closure_document_path=DOCUMENT,
            closure_component_path=COMPONENT,
        )


@pytest.mark.parametrize(
    "source,keyword",
    [
        (DOCUMENT, "closure document SHA256"),
        (SCOPE_CORRECTION, "scope correction document SHA256"),
        (COMPONENT, "closure component SHA256"),
    ],
)
def test_changed_closure_artifact_is_rejected(tmp_path, source, keyword):
    changed = tmp_path / source.name
    changed.write_text(source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    kwargs = {
        "closure_document_path": DOCUMENT,
        "scope_correction_document_path": SCOPE_CORRECTION,
        "closure_component_path": COMPONENT,
    }
    if source == DOCUMENT:
        kwargs["closure_document_path"] = changed
    elif source == SCOPE_CORRECTION:
        kwargs["scope_correction_document_path"] = changed
    else:
        kwargs["closure_component_path"] = changed

    with pytest.raises(RuntimeError, match=keyword):
        review_declaration(**kwargs)


def test_review_confirms_closure_contract_but_does_not_open_evidence():
    declaration = review_declaration()

    assert declaration["status"].endswith("EXTERNAL_EVIDENCE_REQUIRED")
    assert declaration["execution_commit"].startswith("a601a32")
    assert declaration["recorded_report_sha256"] == (
        "5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01"
    )
    assert declaration["parent_discovery_runner_review_passed"] is True
    assert declaration["round_2_closure_implemented"] is True
    assert declaration["offline_feedback_attribution_implemented"] is True
    assert declaration["external_evidence_required_for_closure"] is True
    assert declaration["round_2_evidence_opened"] is False
    assert declaration["round_2_closed"] is False
    assert declaration["round_2_rerun_authorized"] is False
    assert declaration["true_learning_engine_implemented"] is False
    assert declaration["scope_gap_correction_recorded"] is True
    assert declaration["development_data_opened"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["automatic_ranking_generated"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["real_orders_submitted"] is False
    assert declaration["live_execution_authorized"] is False
    assert declaration["next_stage"] == (
        "RUN_READ_ONLY_ROUND_2_CLOSURE_THEN_IMPLEMENT_TRUE_LEARNING_CONTRACT_V1"
    )


def test_parent_review_cannot_claim_execution_or_data_access():
    def bad_parent():
        from kraken_ai_driven_v2_round_2_discovery_runner_review import review_declaration as parent

        result = parent()
        result["development_run_executed"] = True
        return result

    with pytest.raises(RuntimeError, match="parent safety mismatch"):
        review_declaration(parent_reviewer=bad_parent)


def test_review_cli_prints_only_declaration(capsys):
    result = main([])
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["round_2_closure_implemented"] is True
    assert payload["round_2_evidence_opened"] is False


def test_documents_record_hold_cash_and_correct_learning_scope():
    text = DOCUMENT.read_text(encoding="utf-8")
    scope = SCOPE_CORRECTION.read_text(encoding="utf-8")

    assert "KRAKEN_AI_V2_ROUND_2_CLOSED_NO_ELIGIBLE_ROUTE_HOLD_CASH" in text
    assert "Round 2 rerun authorization is permanently false" in text
    assert "Feedback describes frozen evidence" in text
    assert "Rule Discovery Foundation is not a Learning Engine" in text
    assert "Calibration, Evaluation and Candidate v2 remain unauthorized" in text
    assert "True Learning Engine is not implemented" in scope
    assert "offline learning" in scope
    assert "learned model artifact" in scope
