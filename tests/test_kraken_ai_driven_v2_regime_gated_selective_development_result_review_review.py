import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_regime_gated_selective_development_result_review_review import (
    EXPECTED_HASHES,
    STATIC_STATUS,
    review_regime_gated_selective_terminal_result_component,
)


ROOT = Path(__file__).resolve().parents[1]
BOUND_FILES = {
    "line_ending_policy": ".gitattributes",
    "attempt_1_result": (
        "KRAKEN_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_ATTEMPT_1_RESULT.md"
    ),
    "runner_protocol": (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_RUNNER_PROTOCOL_V1.md"
    ),
    "runner_component": (
        "src/kraken_ai_driven_v2_regime_gated_selective_development_runner.py"
    ),
    "runner_review": (
        "src/kraken_ai_driven_v2_regime_gated_selective_development_runner_review.py"
    ),
    "result_review_protocol": (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_RESULT_REVIEW_PROTOCOL_V1.md"
    ),
    "result_review_component": (
        "src/kraken_ai_driven_v2_regime_gated_selective_development_result_review.py"
    ),
}


def _copy_bound_files(tmp_path):
    for relative in BOUND_FILES.values():
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_static_review_binds_terminal_result_and_runner_sources():
    result = review_regime_gated_selective_terminal_result_component(ROOT)
    assert result["status"] == STATIC_STATUS
    assert all(result["source_sha256_matches"].values())
    assert result["checkout_stable_hashing"] is True
    assert result["external_evidence_opened"] is False
    assert result["model_artifacts_unpickled"] is False
    assert result["model_training_executed"] is False
    assert result["retry_authorized"] is False
    assert result["threshold_rescue_authorized"] is False
    assert result["automatic_successor_authorized"] is False
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False


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
        review_regime_gated_selective_terminal_result_component(tmp_path)


def test_new_result_sources_are_checkout_stable_across_crlf(tmp_path):
    _copy_bound_files(tmp_path)
    for name in (
        "attempt_1_result",
        "result_review_protocol",
        "result_review_component",
    ):
        target = tmp_path / BOUND_FILES[name]
        target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
    result = review_regime_gated_selective_terminal_result_component(tmp_path)
    assert all(result["source_sha256_matches"].values())


def test_attempt_1_result_records_terminal_stop_without_rescue():
    result_record = (
        ROOT
        / "KRAKEN_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_ATTEMPT_1_RESULT.md"
    ).read_text(encoding="utf-8")
    for marker in (
        "40d98117613d3f4a74e809f76dcd371804b3fc31",
        "a972088fca185266a4a726b3a4512a90bed15f4e1d3a3467e76bedd171a7f286",
        "728b60750ed9de5070281d8d3cebecddbef701f2f6ea604dbeec7c2ea7015400",
        "3,793",
        "291",
        "zero raw and zero non-overlapping selections",
        "Action: `HOLD_CASH`",
        "STOP_KRAKEN_12H_RESEARCH",
        "not a recoverable implementation incident",
        "There is no rerun, refit, threshold rescue",
    ):
        assert marker in result_record
