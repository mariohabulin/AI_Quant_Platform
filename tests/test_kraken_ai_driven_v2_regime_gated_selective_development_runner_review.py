import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_regime_gated_selective_development_runner_review import (
    EXPECTED_HASHES,
    STATUS,
    review_regime_gated_selective_development_runner,
)


ROOT = Path(__file__).resolve().parents[1]
BOUND_FILES = {
    "line_ending_policy": ".gitattributes",
    "learning_core_component": "src/kraken_ai_driven_v2_learning_core.py",
    "spot_reader_component": "src/kraken_ai_driven_v2_12h_development_learning_runner.py",
    "bidirectional_runner_component": "src/kraken_ai_driven_v2_bidirectional_development_learning_runner.py",
    "context_dataset_component": "src/kraken_ai_driven_v2_derivatives_context_dataset.py",
    "context_hypothesis_component": "src/kraken_ai_driven_v2_derivatives_context_hypothesis.py",
    "regime_hypothesis_protocol": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_HYPOTHESIS_PROTOCOL_V1.md",
    "regime_hypothesis_component": "src/kraken_ai_driven_v2_regime_gated_selective_hypothesis.py",
    "regime_hypothesis_review": "src/kraken_ai_driven_v2_regime_gated_selective_hypothesis_review.py",
    "runner_protocol": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_RUNNER_PROTOCOL_V1.md",
    "runner_component": "src/kraken_ai_driven_v2_regime_gated_selective_development_runner.py",
}


def test_static_review_binds_all_sources_and_keeps_execution_closed():
    result = review_regime_gated_selective_development_runner(ROOT)
    assert result["status"] == STATUS
    assert result["parent_commit"].startswith("87927ef")
    assert result["maximum_base_model_fits"] == 12
    assert result["maximum_calibrator_fits"] == 12
    assert result["maximum_total_fits"] == 24
    assert result["terminal_research_stop_implemented"] is True
    assert result["runner_protocol_sha256_match"] is True
    assert result["runner_component_sha256_match"] is True
    assert all(result["source_sha256_matches"].values())
    for field in (
        "authorization_phrase_active",
        "development_data_opened",
        "labels_generated",
        "model_training_authorized",
        "model_training_executed",
        "automatic_model_selection",
        "automatic_successor_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        assert result[field] is False


def test_expected_hash_registry_is_complete_lowercase_sha256():
    assert set(EXPECTED_HASHES) == set(BOUND_FILES)
    assert all(
        len(value) == 64 and value == value.lower()
        for value in EXPECTED_HASHES.values()
    )


@pytest.mark.parametrize("tampered_name", tuple(BOUND_FILES))
def test_review_rejects_any_bound_source_tamper(tmp_path, tampered_name):
    for relative in BOUND_FILES.values():
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    target = tmp_path / BOUND_FILES[tampered_name]
    target.write_bytes(target.read_bytes() + b"tamper\n")
    with pytest.raises(RuntimeError, match=tampered_name):
        review_regime_gated_selective_development_runner(tmp_path)
