import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from us_equity_point_in_time_data_feasibility_result_review_review import (
    EXPECTED_HASHES,
    STATUS,
    review_zero_cost_source_audit_result_component,
)


ROOT = Path(__file__).resolve().parents[1]
BOUND_FILES = {
    "line_ending_policy": ".gitattributes",
    "windows_sidecar_incident": "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_RESULT_REVIEW_WINDOWS_CRLF_INCIDENT.md",
    "feasibility_protocol": "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_PROTOCOL_V1.md",
    "feasibility_component": "src/us_equity_point_in_time_data_feasibility.py",
    "feasibility_review": "src/us_equity_point_in_time_data_feasibility_review.py",
    "attempt_1_result": "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_ATTEMPT_1_RESULT.md",
    "result_review_protocol": "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_RESULT_REVIEW_PROTOCOL_V1.md",
    "result_review_component": "src/us_equity_point_in_time_data_feasibility_result_review.py",
}


def _copy_bound_files(tmp_path):
    for relative in BOUND_FILES.values():
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_static_review_binds_gap_result_and_all_governing_sources():
    result = review_zero_cost_source_audit_result_component(ROOT)

    assert result["status"] == STATUS
    assert set(result["source_sha256_matches"]) == set(BOUND_FILES)
    assert all(result["source_sha256_matches"].values())
    assert result["checkout_stable_hashing"] is True
    assert result["source_feasible"] is False
    assert result["monthly_data_cost_usd"] == 0
    assert result["paid_subscription_authorized"] is False
    assert result["market_values_opened"] is False
    assert result["model_training_executed"] is False


def test_static_hash_registry_is_exact_lowercase_sha256():
    assert set(EXPECTED_HASHES) == set(BOUND_FILES)
    assert all(len(value) == 64 and value == value.lower() for value in EXPECTED_HASHES.values())


@pytest.mark.parametrize("tampered_name", tuple(BOUND_FILES))
def test_static_review_rejects_any_bound_source_tamper(tmp_path, tampered_name):
    _copy_bound_files(tmp_path)
    target = tmp_path / BOUND_FILES[tampered_name]
    target.write_bytes(target.read_bytes() + b"tamper\n")
    with pytest.raises(RuntimeError, match=tampered_name):
        review_zero_cost_source_audit_result_component(tmp_path)


def test_new_result_sources_are_checkout_stable_across_real_crlf(tmp_path):
    _copy_bound_files(tmp_path)
    for name in ("attempt_1_result", "result_review_protocol", "result_review_component"):
        target = tmp_path / BOUND_FILES[name]
        lf_payload = target.read_bytes().replace(b"\r\n", b"\n")
        crlf_payload = lf_payload.replace(b"\n", b"\r\n")
        assert b"\r\r\n" not in crlf_payload
        target.write_bytes(crlf_payload)
    result = review_zero_cost_source_audit_result_component(tmp_path)
    assert all(result["source_sha256_matches"].values())


def test_attempt_1_result_records_exact_gap_without_purchase_or_model():
    text = (ROOT / BOUND_FILES["attempt_1_result"]).read_text(encoding="utf-8")
    for marker in (
        "6a185e6d0dd9a7e31513f951a234601cfb9b06fa",
        "8f2348138376438129f3db1a94d0321e6b10177cd486f5436c935a167de0d2cb",
        "US_EQUITY_POINT_IN_TIME_NO_COST_SOURCE_GAP_RECORDED_NO_PURCHASE_AUTHORIZED",
        "six of twelve",
        "HOLD_RESEARCH_OR_FIND_ANOTHER_NO_COST_SOURCE",
        "0 USD",
        "No market values, labels or models",
        "no automatic purchase",
    ):
        assert marker in text
