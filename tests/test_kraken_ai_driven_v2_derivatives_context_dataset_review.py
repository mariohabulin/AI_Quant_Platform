import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_derivatives_context_dataset_review import (
    EXPECTED_COMPONENT_SHA256,
    EXPECTED_PARENT_COMPONENT_SHA256,
    EXPECTED_PARENT_PROTOCOL_SHA256,
    EXPECTED_PROTOCOL_SHA256,
    STATUS,
    review_derivatives_context_dataset_lock,
)


ROOT = Path(__file__).resolve().parents[1]


def test_review_binds_parent_hypothesis_and_new_lock_component():
    review = review_derivatives_context_dataset_lock(ROOT)

    assert review["status"] == STATUS
    assert review["parent_commit"] == "af0af86"
    assert review["recovery_parent_commit"] == "8181d05"
    assert review["recovery_attempt"] == 3
    assert review["parent_protocol_sha256"] == EXPECTED_PARENT_PROTOCOL_SHA256
    assert review["parent_protocol_sha256_match"] is True
    assert review["parent_component_sha256"] == EXPECTED_PARENT_COMPONENT_SHA256
    assert review["parent_component_sha256_match"] is True
    assert review["parent_review_sha256_match"] is True
    assert review["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert review["protocol_sha256_match"] is True
    assert review["component_sha256"] == EXPECTED_COMPONENT_SHA256
    assert review["component_sha256_match"] is True


def test_review_confirms_exact_2808_object_integrity_and_reader_boundary():
    review = review_derivatives_context_dataset_lock(ROOT)

    assert review["expected_object_count"] == 2808
    assert review["expected_object_counts_by_source"] == {
        "FUNDING_RATE": 84,
        "OPEN_INTEREST_METRICS": 2556,
        "MARK_PRICE_12H": 84,
        "INDEX_PRICE_12H": 84,
    }
    assert review["official_checksum_required"] is True
    assert review["raw_zip_hash_implemented"] is True
    assert review["csv_member_hash_implemented"] is True
    assert review["normalized_file_hash_implemented"] is True
    assert review["atomic_dataset_lock_implemented"] is True
    assert review["independent_reader_implemented"] is True
    assert review["source_schema_validation_implemented"] is True
    assert review["causal_timestamp_validation_implemented"] is True
    assert review["optional_metrics_blank_policy_implemented"] is True
    assert review["optional_metrics_blank_counts_recorded"] is True
    assert review["attempt_1_authorization_consumed"] is True
    assert review["attempt_1_final_dataset_exists"] is False
    assert review["attempt_1_staging_required"] is True
    assert review["attempt_1_incident_sha256_match"] is True
    assert review["attempt_2_authorization_consumed"] is True
    assert review["attempt_2_final_dataset_exists"] is False
    assert review["attempt_2_staging_required"] is True
    assert review["attempt_2_incident_sha256_match"] is True
    assert review["complete_metrics_forensic_scan_recorded"] is True
    assert review["open_interest_zero_sentinel_policy_implemented"] is True
    assert review["open_interest_zero_sentinel_count"] == 399
    assert review["open_interest_zero_sentinel_count_per_asset"] == 133
    assert review["recovery_new_root_required"] is True
    assert review["prior_staging_inventory_implemented"] is True


def test_review_keeps_download_values_learning_and_later_stages_closed():
    review = review_derivatives_context_dataset_lock(ROOT)
    required_false = (
        "authorization_phrase_active",
        "source_objects_downloaded",
        "market_values_opened",
        "development_data_opened",
        "labels_generated",
        "model_training_executed",
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
    )
    assert all(review[field] is False for field in required_false)


def test_review_fails_closed_if_parent_or_new_component_changes(tmp_path):
    relatives = (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_LEARNING_HYPOTHESIS_PROTOCOL_V1.md",
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_READER_PROTOCOL_V1.md",
        "src/kraken_ai_driven_v2_derivatives_context_hypothesis.py",
        "src/kraken_ai_driven_v2_derivatives_context_hypothesis_review.py",
        "src/kraken_ai_driven_v2_derivatives_context_dataset.py",
        "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ATTEMPT_1_INCIDENT.md",
        "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ATTEMPT_2_INCIDENT.md",
    )
    for relative in relatives:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    component = tmp_path / "src" / "kraken_ai_driven_v2_derivatives_context_dataset.py"
    component.write_text(component.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="component"):
        review_derivatives_context_dataset_lock(tmp_path)
