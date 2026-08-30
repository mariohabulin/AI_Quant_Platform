import json
import os
import sys
from pathlib import Path

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_round_1_closure_review import (
    CLOSURE_COMPONENT_NORMALIZED_SHA256,
    CLOSURE_DOCUMENT_NORMALIZED_SHA256,
    PARENT_BINDINGS,
    load_closure_document,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "KRAKEN_AI_DRIVEN_V2_ROUND_1_CLOSURE.md"
COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_round_1_closure.py"


def test_review_hash_binds_discovery_runner_parent_and_closure_artifacts():
    _, document_digest = load_closure_document(DOCUMENT)

    assert document_digest == CLOSURE_DOCUMENT_NORMALIZED_SHA256
    assert normalized_text_sha256(COMPONENT) == CLOSURE_COMPONENT_NORMALIZED_SHA256
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
        (COMPONENT, "closure component SHA256"),
    ],
)
def test_changed_closure_artifact_is_rejected(tmp_path, source, keyword):
    changed = tmp_path / source.name
    changed.write_text(source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    kwargs = {"closure_document_path": DOCUMENT, "closure_component_path": COMPONENT}
    if source == DOCUMENT:
        kwargs["closure_document_path"] = changed
    else:
        kwargs["closure_component_path"] = changed

    with pytest.raises(RuntimeError, match=keyword):
        review_declaration(**kwargs)


def test_review_confirms_closure_contract_but_does_not_open_evidence():
    declaration = review_declaration()

    assert declaration["status"].endswith("EXTERNAL_EVIDENCE_REQUIRED")
    assert declaration["execution_commit"].startswith("98a7218")
    assert declaration["recorded_report_sha256"] == (
        "3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b"
    )
    assert declaration["parent_discovery_runner_review_passed"] is True
    assert declaration["round_1_closure_implemented"] is True
    assert declaration["offline_feedback_attribution_implemented"] is True
    assert declaration["external_evidence_required_for_closure"] is True
    assert declaration["round_1_evidence_opened"] is False
    assert declaration["round_1_closed"] is False
    assert declaration["round_1_rerun_authorized"] is False
    assert declaration["round_2_manifest_registered"] is False
    assert declaration["development_data_opened"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["automatic_ranking_generated"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["real_orders_submitted"] is False
    assert declaration["live_execution_authorized"] is False
    assert declaration["next_stage"] == "RUN_READ_ONLY_ROUND_1_CLOSURE_ON_LOCKED_EVIDENCE"


def test_parent_review_cannot_claim_execution_or_data_access():
    def bad_parent():
        from kraken_ai_driven_v2_round_1_discovery_runner_review import review_declaration as parent

        result = parent()
        result["development_run_executed"] = True
        return result

    with pytest.raises(RuntimeError, match="parent safety mismatch"):
        review_declaration(parent_reviewer=bad_parent)


def test_review_cli_prints_only_declaration(capsys):
    result = main([])
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["round_1_closure_implemented"] is True
    assert payload["round_1_evidence_opened"] is False


def test_document_records_hold_cash_and_blocks_round_2_registration():
    text = DOCUMENT.read_text(encoding="utf-8")

    assert "KRAKEN_AI_V2_ROUND_1_CLOSED_NO_ELIGIBLE_ROUTE_HOLD_CASH" in text
    assert "Round 1 rerun authorization is permanently false" in text
    assert "Feedback describes frozen evidence" in text
    assert "Round 2 is not registered" in text
    assert "Calibration, Evaluation and Candidate v2 remain unauthorized" in text
