import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from us_equity_point_in_time_data_feasibility_review import (
    EXPECTED_HASHES,
    STATUS,
    review_equity_data_feasibility,
)


ROOT = Path(__file__).resolve().parents[1]
BOUND_FILES = {
    "research_mandate": "SELECTIVE_SWING_TRADING_RESEARCH_MANDATE_V1.md",
    "portfolio_protocol": "SELECTIVE_SWING_PORTFOLIO_CONSTRUCTION_PROTOCOL_V1.md",
    "terminal_result": (
        "KRAKEN_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_ATTEMPT_1_RESULT.md"
    ),
    "feasibility_protocol": "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_PROTOCOL_V1.md",
    "feasibility_component": "src/us_equity_point_in_time_data_feasibility.py",
}


def _copy_bound_files(tmp_path):
    for relative in BOUND_FILES.values():
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_static_review_binds_terminal_crypto_result_and_equity_foundations():
    result = review_equity_data_feasibility(ROOT)

    assert result["status"] == STATUS
    assert result["parent_commit"] == (
        "816deff3bef51b3ddd8cf51ab89144587721a196"
    )
    assert result["parent_result_sha256"] == (
        "a972088fca185266a4a726b3a4512a90bed15f4e1d3a3467e76bedd171a7f286"
    )
    assert set(result["source_sha256_matches"]) == set(BOUND_FILES)
    assert all(result["source_sha256_matches"].values())
    assert result["checkout_stable_hashing"] is True


def test_static_review_keeps_cost_learning_and_execution_closed():
    result = review_equity_data_feasibility(ROOT)

    assert result["monthly_data_budget_usd"] == 0
    assert result["paid_subscription_authorized"] is False
    assert result["paid_api_key_authorized"] is False
    assert result["market_values_opened"] is False
    assert result["performance_evaluation_executed"] is False
    assert result["model_training_executed"] is False
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False
    assert result["candidate_v2_authorized"] is False
    assert result["real_orders_submitted"] is False


def test_static_hash_registry_is_exact_lowercase_sha256():
    assert set(EXPECTED_HASHES) == set(BOUND_FILES)
    assert all(
        len(value) == 64 and value == value.lower()
        for value in EXPECTED_HASHES.values()
    )


@pytest.mark.parametrize("tampered_name", tuple(BOUND_FILES))
def test_static_review_rejects_any_bound_source_tamper(tmp_path, tampered_name):
    _copy_bound_files(tmp_path)
    target = tmp_path / BOUND_FILES[tampered_name]
    target.write_bytes(target.read_bytes() + b"tamper\n")
    with pytest.raises(RuntimeError, match=tampered_name):
        review_equity_data_feasibility(tmp_path)


def test_new_sources_are_checkout_stable_across_real_crlf(tmp_path):
    _copy_bound_files(tmp_path)
    for name in ("feasibility_protocol", "feasibility_component"):
        target = tmp_path / BOUND_FILES[name]
        lf_payload = target.read_bytes().replace(b"\r\n", b"\n")
        crlf_payload = lf_payload.replace(b"\n", b"\r\n")
        assert b"\r\r\n" not in crlf_payload
        target.write_bytes(crlf_payload)
    result = review_equity_data_feasibility(tmp_path)
    assert all(result["source_sha256_matches"].values())
