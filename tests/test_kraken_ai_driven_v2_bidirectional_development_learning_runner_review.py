import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_bidirectional_development_learning_runner_review import (
    EXPECTED_HASHES,
    STATUS,
    review_bidirectional_development_learning_runner,
)


ROOT = Path(__file__).resolve().parents[1]


def test_static_review_binds_every_input_and_new_runner_source():
    result = review_bidirectional_development_learning_runner(ROOT)

    assert result["status"] == STATUS
    assert result["parent_commit"].startswith("82ea7f1")
    assert result["runner_protocol_sha256_match"] is True
    assert result["runner_component_sha256_match"] is True
    assert all(result["source_sha256_matches"].values())
    assert result["maximum_fold_model_fits"] == 12
    assert result["paired_directional_rows_implemented"] is True
    assert result["latest_outcome_purge_implemented"] is True
    assert result["model_training_executed"] is False


def test_expected_hashes_are_lowercase_sha256_values():
    assert set(EXPECTED_HASHES) == {
        "learning_core_component",
        "spot_reader_component",
        "context_feature_component",
        "dataset_protocol",
        "dataset_component",
        "dataset_review",
        "dataset_result",
        "bidirectional_protocol",
        "bidirectional_component",
        "bidirectional_review",
        "context_forensic_result",
        "runner_protocol",
        "runner_component",
    }
    assert all(
        len(value) == 64 and value == value.lower()
        for value in EXPECTED_HASHES.values()
    )


def test_static_review_keeps_real_learning_and_later_stages_closed():
    result = review_bidirectional_development_learning_runner(ROOT)
    for field in (
        "authorization_phrase_active",
        "network_download_authorized",
        "source_archive_opened",
        "context_dataset_opened",
        "development_data_opened",
        "labels_generated",
        "model_training_authorized",
        "model_training_executed",
        "feature_search_authorized",
        "hyperparameter_sweep_authorized",
        "threshold_sweep_authorized",
        "automatic_model_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        assert result[field] is False


def test_static_review_rejects_tampered_runner_component(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(ROOT, copy)
    target = (
        copy
        / "src"
        / "kraken_ai_driven_v2_bidirectional_development_learning_runner.py"
    )
    target.write_bytes(target.read_bytes() + b"\n# tamper\n")
    with pytest.raises(RuntimeError, match="runner_component"):
        review_bidirectional_development_learning_runner(copy)
