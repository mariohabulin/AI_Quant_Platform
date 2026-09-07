import copy
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import us_equity_point_in_time_data_feasibility_result_review as review
from us_equity_point_in_time_data_feasibility import (
    STATUS_GAP,
    audit_no_cost_source_capabilities,
    canonical_json_bytes,
)


def _evidence_record():
    return {
        "schema_version": 1,
        "audit_date_utc": "2026-09-07",
        "execution_commit": review.EXECUTION_COMMIT,
        "protocol_id": review.FEASIBILITY_PROTOCOL_ID,
        "evidence_scope": "OFFICIAL_DOCUMENTATION_AND_PUBLIC_SCHEMA_ONLY",
        "sources": [
            {
                "source_id": source_id,
                "official_urls": list(review.EXPECTED_SOURCE_URLS[source_id]),
                "finding": f"Reviewed documentation for {source_id}.",
                "license_reuse_reviewed": source_id == "SEC_EDGAR_PUBLIC_APIS",
                "market_values_opened": False,
            }
            for source_id in review.EXPECTED_SOURCE_IDS
        ],
        "source_documentation_opened": True,
        "free_schema_sample_opened": True,
        "market_values_opened": False,
        "labels_generated": False,
        "performance_evaluation_executed": False,
        "model_training_executed": False,
        "paid_subscription_authorized": False,
        "paid_api_key_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
    }


def _write_package(root, observations=None, evidence=None, report=None):
    root.mkdir()
    observations = copy.deepcopy(review.EXPECTED_OBSERVATIONS if observations is None else observations)
    evidence = _evidence_record() if evidence is None else evidence
    report = (
        audit_no_cost_source_capabilities(observations)
        if report is None
        else report
    )
    payloads = {
        review.OBSERVATIONS_FILENAME: json.dumps(observations, indent=2).encode() + b"\n",
        review.SOURCE_EVIDENCE_FILENAME: json.dumps(evidence, indent=2).encode() + b"\n",
        review.REPORT_FILENAME: canonical_json_bytes(report),
    }
    hashes = {}
    for filename, payload in payloads.items():
        path = root / filename
        path.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        hashes[filename] = digest
        (root / f"{filename}.sha256").write_text(
            f"{digest}  {filename}\n", encoding="ascii"
        )
    return observations, evidence, report, hashes


def test_declaration_freezes_gap_result_and_keeps_every_later_stage_closed():
    declaration = review.result_review_declaration()

    assert declaration["status"] == review.STATIC_STATUS
    assert declaration["execution_commit"] == (
        "6a185e6d0dd9a7e31513f951a234601cfb9b06fa"
    )
    assert declaration["expected_report_sha256"] == review.EXPECTED_REPORT_SHA256
    assert declaration["expected_missing_capabilities"] == list(
        review.EXPECTED_MISSING_CAPABILITIES
    )
    assert declaration["expected_action"] == "HOLD_RESEARCH_OR_FIND_ANOTHER_NO_COST_SOURCE"
    for field in (
        "external_evidence_opened",
        "market_values_opened",
        "labels_generated",
        "performance_evaluation_executed",
        "model_training_executed",
        "paid_subscription_authorized",
        "paid_api_key_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        assert declaration[field] is False


def test_independent_analysis_recomputes_capability_union_and_exact_gap():
    observations = copy.deepcopy(review.EXPECTED_OBSERVATIONS)
    evidence = _evidence_record()
    report = audit_no_cost_source_capabilities(observations)

    result = review.analyze_zero_cost_source_audit(observations, evidence, report)

    assert result["status"] == review.STATUS
    assert result["source_status"] == STATUS_GAP
    assert result["source_feasible"] is False
    assert result["missing_capabilities"] == list(review.EXPECTED_MISSING_CAPABILITIES)
    assert result["documented_capability_count"] == 6
    assert result["observed_source_count"] == 3
    assert result["eligible_source_count"] == 1
    assert result["monthly_data_cost_usd"] == 0
    assert result["purchase_authorized"] is False


def test_analysis_rejects_capability_or_report_tamper():
    observations = copy.deepcopy(review.EXPECTED_OBSERVATIONS)
    evidence = _evidence_record()
    report = audit_no_cost_source_capabilities(observations)

    observations[0]["capabilities"]["active_and_delisted_daily_ohlcv"] = True
    with pytest.raises(RuntimeError, match="observation registry mismatch"):
        review.analyze_zero_cost_source_audit(observations, evidence, report)

    observations = copy.deepcopy(review.EXPECTED_OBSERVATIONS)
    changed_report = copy.deepcopy(report)
    changed_report["source_feasible"] = True
    with pytest.raises(RuntimeError, match="recomputed report mismatch"):
        review.analyze_zero_cost_source_audit(observations, evidence, changed_report)


def test_analysis_rejects_source_evidence_or_safety_tamper():
    observations = copy.deepcopy(review.EXPECTED_OBSERVATIONS)
    report = audit_no_cost_source_capabilities(observations)
    evidence = _evidence_record()
    evidence["sources"][0]["official_urls"] = ["https://example.com/not-official"]
    with pytest.raises(RuntimeError, match="official URL registry mismatch"):
        review.analyze_zero_cost_source_audit(observations, evidence, report)

    evidence = _evidence_record()
    evidence["market_values_opened"] = True
    with pytest.raises(RuntimeError, match="safety boundary mismatch"):
        review.analyze_zero_cost_source_audit(observations, evidence, report)


def test_external_reader_hashes_sidecars_recomputes_and_writes_nothing(
    tmp_path, monkeypatch
):
    root = tmp_path / review.EVIDENCE_DIRECTORY_NAME
    _, _, _, hashes = _write_package(root)
    monkeypatch.setattr(review, "EXPECTED_OBSERVATIONS_SHA256", hashes[review.OBSERVATIONS_FILENAME])
    monkeypatch.setattr(review, "EXPECTED_SOURCE_EVIDENCE_SHA256", hashes[review.SOURCE_EVIDENCE_FILENAME])
    monkeypatch.setattr(review, "EXPECTED_REPORT_SHA256", hashes[review.REPORT_FILENAME])
    before = {path.name: path.read_bytes() for path in root.iterdir()}

    result = review.read_zero_cost_source_audit_result(root)

    after = {path.name: path.read_bytes() for path in root.iterdir()}
    assert before == after
    assert result["status"] == review.STATUS
    assert result["evidence_unchanged"] is True
    assert result["market_values_opened"] is False
    assert result["model_training_executed"] is False
    assert result["next_stage"] == "OPERATOR_DECISION_NO_AUTOMATIC_PURCHASE"


def test_external_reader_rejects_sidecar_and_extra_file(tmp_path, monkeypatch):
    root = tmp_path / review.EVIDENCE_DIRECTORY_NAME
    _, _, _, hashes = _write_package(root)
    monkeypatch.setattr(review, "EXPECTED_OBSERVATIONS_SHA256", hashes[review.OBSERVATIONS_FILENAME])
    monkeypatch.setattr(review, "EXPECTED_SOURCE_EVIDENCE_SHA256", hashes[review.SOURCE_EVIDENCE_FILENAME])
    monkeypatch.setattr(review, "EXPECTED_REPORT_SHA256", hashes[review.REPORT_FILENAME])
    (root / f"{review.REPORT_FILENAME}.sha256").write_text("bad\n", encoding="ascii")
    with pytest.raises(RuntimeError, match="sidecar mismatch"):
        review.read_zero_cost_source_audit_result(root)

    root = tmp_path / "extra"
    _write_package(root)
    (root / "unexpected.txt").write_text("x", encoding="ascii")
    with pytest.raises(RuntimeError, match="file registry mismatch"):
        review.read_zero_cost_source_audit_result(root)


def test_cli_without_evidence_is_static_and_nonexecuting(capsys):
    assert review.main([]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["status"] == review.STATIC_STATUS
    assert printed["external_evidence_opened"] is False
    assert printed["next_stage"] == "EXTERNAL_ZERO_COST_AUDIT_EVIDENCE_REVIEW"
