"""Static source-binding review for the derivatives-context dataset lock."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_derivatives_context_dataset import (
        ASSET_SYMBOLS,
        ATTEMPT_1_INCIDENT_SHA256,
        ATTEMPT_2_INCIDENT_SHA256,
        ATTEMPT_3_INCIDENT_SHA256,
        ATTEMPT_3_RESUME_OBJECT_COUNT,
        ATTEMPT_3_STAGING_FILE_COUNT,
        ATTEMPT_3_STAGING_INVENTORY_SHA256,
        ATTEMPT_3_STAGING_TOTAL_BYTES,
        ATTEMPT_4_EXECUTION_COMMIT,
        ATTEMPT_4_MANIFEST_SHA256,
        ATTEMPT_4_READER_INCIDENT_SHA256,
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DATASET_ID,
        PARENT_COMMIT,
        PARENT_FEASIBILITY_REPORT_SHA256,
        PARENT_PROTOCOL_ID,
        PROTOCOL_ID,
        OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256,
        MAXIMUM_TRANSPORT_ATTEMPTS,
        MAXIMUM_TRANSPORT_BACKOFF_SECONDS,
        RECOVERY_PARENT_COMMIT,
        SOURCE_SPECS,
        dataset_lock_declaration,
        expected_object_registry,
    )
except ImportError:  # pragma: no cover
    from .kraken_ai_driven_v2_derivatives_context_dataset import (
        ASSET_SYMBOLS,
        ATTEMPT_1_INCIDENT_SHA256,
        ATTEMPT_2_INCIDENT_SHA256,
        ATTEMPT_3_INCIDENT_SHA256,
        ATTEMPT_3_RESUME_OBJECT_COUNT,
        ATTEMPT_3_STAGING_FILE_COUNT,
        ATTEMPT_3_STAGING_INVENTORY_SHA256,
        ATTEMPT_3_STAGING_TOTAL_BYTES,
        ATTEMPT_4_EXECUTION_COMMIT,
        ATTEMPT_4_MANIFEST_SHA256,
        ATTEMPT_4_READER_INCIDENT_SHA256,
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DATASET_ID,
        PARENT_COMMIT,
        PARENT_FEASIBILITY_REPORT_SHA256,
        PARENT_PROTOCOL_ID,
        PROTOCOL_ID,
        OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256,
        MAXIMUM_TRANSPORT_ATTEMPTS,
        MAXIMUM_TRANSPORT_BACKOFF_SECONDS,
        RECOVERY_PARENT_COMMIT,
        SOURCE_SPECS,
        dataset_lock_declaration,
        expected_object_registry,
    )


SCHEMA_VERSION = 1
STATUS = (
    "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_READER_RECOVERY_REVIEWED_READ_ONLY_RERUN_REQUIRED"
)
EXPECTED_PARENT_COMMIT = "af0af86"
EXPECTED_RECOVERY_PARENT_COMMIT = "25d55b6"
EXPECTED_PARENT_PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-v2-derivatives-context-learning-hypothesis-v1"
)
EXPECTED_PARENT_FEASIBILITY_REPORT_SHA256 = (
    "3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29"
)
EXPECTED_PARENT_PROTOCOL_SHA256 = (
    "81074ffcd8213fcf86c44e5f118293936632b279602b5750a67332848d6fd865"
)
EXPECTED_PARENT_COMPONENT_SHA256 = (
    "5355bb5d8e672d539776fc88705f2864b4974a767b12aaabfd4615aeb42288b3"
)
EXPECTED_PARENT_REVIEW_SHA256 = (
    "48cff3f16d576a77a993694fb37d7410027daaecc87f3f010f910e2b6111fb05"
)
EXPECTED_ATTEMPT_1_INCIDENT_SHA256 = (
    "3abae269bc80b13b975e77afb4bbfc7e7f442856ab4510fd5ad9023221aebca8"
)
EXPECTED_ATTEMPT_2_INCIDENT_SHA256 = (
    "76ce94fc848d888c489ea6466044a094443775f329bfcc51a3117bac5497a39f"
)
EXPECTED_ATTEMPT_3_INCIDENT_SHA256 = (
    "ce08144f2e27788a17b23bb0fbbfdf0728854b6332b82c98378e79b09e201cc6"
)
EXPECTED_ATTEMPT_4_EXECUTION_COMMIT = (
    "40b5943442c96d5ef26434db95d9dc955ca41c12"
)
EXPECTED_ATTEMPT_4_MANIFEST_SHA256 = (
    "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916"
)
EXPECTED_ATTEMPT_4_READER_INCIDENT_SHA256 = (
    "33d6e9fc1f2688032ec0f28c986d735f7e71bf009b5856673c32e440915b3020"
)
EXPECTED_PROTOCOL_SHA256 = (
    "51aeef000af0a2f311cace28c2ef9ccfe006075340d90226312aa56e3fa736dc"
)
EXPECTED_COMPONENT_SHA256 = (
    "e948493b88068985e2a4e3041213979fde3c7424863a853833f07d601214a4d8"
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_derivatives_context_dataset_lock(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "parent_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_LEARNING_HYPOTHESIS_PROTOCOL_V1.md",
        "parent_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_hypothesis.py",
        "parent_review": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_hypothesis_review.py",
        "protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_READER_PROTOCOL_V1.md",
        "component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_dataset.py",
        "attempt_1_incident": root
        / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ATTEMPT_1_INCIDENT.md",
        "attempt_2_incident": root
        / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ATTEMPT_2_INCIDENT.md",
        "attempt_3_incident": root
        / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ATTEMPT_3_INCIDENT.md",
        "attempt_4_reader_incident": root
        / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ATTEMPT_4_READER_INCIDENT.md",
    }
    expected = {
        "parent_protocol": EXPECTED_PARENT_PROTOCOL_SHA256,
        "parent_component": EXPECTED_PARENT_COMPONENT_SHA256,
        "parent_review": EXPECTED_PARENT_REVIEW_SHA256,
        "protocol": EXPECTED_PROTOCOL_SHA256,
        "component": EXPECTED_COMPONENT_SHA256,
        "attempt_1_incident": EXPECTED_ATTEMPT_1_INCIDENT_SHA256,
        "attempt_2_incident": EXPECTED_ATTEMPT_2_INCIDENT_SHA256,
        "attempt_3_incident": EXPECTED_ATTEMPT_3_INCIDENT_SHA256,
        "attempt_4_reader_incident": EXPECTED_ATTEMPT_4_READER_INCIDENT_SHA256,
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, digest in expected.items():
        if observed[name] != digest:
            raise RuntimeError(f"Derivatives-context dataset binding mismatch: {name}.")

    declaration = dataset_lock_declaration()
    registry = expected_object_registry()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Derivatives-context dataset parent commit mismatch.")
    if RECOVERY_PARENT_COMMIT != EXPECTED_RECOVERY_PARENT_COMMIT:
        raise RuntimeError("Derivatives-context recovery parent commit mismatch.")
    if ATTEMPT_1_INCIDENT_SHA256 != EXPECTED_ATTEMPT_1_INCIDENT_SHA256:
        raise RuntimeError("Derivatives-context Attempt 1 incident mismatch.")
    if ATTEMPT_2_INCIDENT_SHA256 != EXPECTED_ATTEMPT_2_INCIDENT_SHA256:
        raise RuntimeError("Derivatives-context Attempt 2 incident mismatch.")
    if ATTEMPT_3_INCIDENT_SHA256 != EXPECTED_ATTEMPT_3_INCIDENT_SHA256:
        raise RuntimeError("Derivatives-context Attempt 3 incident mismatch.")
    if ATTEMPT_4_EXECUTION_COMMIT != EXPECTED_ATTEMPT_4_EXECUTION_COMMIT:
        raise RuntimeError("Derivatives-context Attempt 4 execution mismatch.")
    if ATTEMPT_4_MANIFEST_SHA256 != EXPECTED_ATTEMPT_4_MANIFEST_SHA256:
        raise RuntimeError("Derivatives-context Attempt 4 manifest mismatch.")
    if ATTEMPT_4_READER_INCIDENT_SHA256 != EXPECTED_ATTEMPT_4_READER_INCIDENT_SHA256:
        raise RuntimeError("Derivatives-context Attempt 4 reader incident mismatch.")
    if PARENT_PROTOCOL_ID != EXPECTED_PARENT_PROTOCOL_ID:
        raise RuntimeError("Derivatives-context dataset parent protocol mismatch.")
    if PARENT_FEASIBILITY_REPORT_SHA256 != EXPECTED_PARENT_FEASIBILITY_REPORT_SHA256:
        raise RuntimeError("Derivatives-context dataset feasibility evidence mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Derivatives-context dataset protocol mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Derivatives-context dataset component mismatch.")
    if declaration["dataset_id"] != DATASET_ID:
        raise RuntimeError("Derivatives-context dataset identity mismatch.")
    if declaration["authorization_phrase"] != AUTHORIZATION_PHRASE:
        raise RuntimeError("Derivatives-context dataset authorization mismatch.")
    if tuple(declaration["asset_order"]) != tuple(ASSET_SYMBOLS):
        raise RuntimeError("Derivatives-context dataset asset registry mismatch.")
    if tuple(declaration["source_series_order"]) != tuple(SOURCE_SPECS):
        raise RuntimeError("Derivatives-context source registry mismatch.")
    if declaration["expected_object_count"] != len(registry) or len(registry) != 2808:
        raise RuntimeError("Derivatives-context object registry count mismatch.")
    if len({item["key"] for item in registry}) != len(registry):
        raise RuntimeError("Derivatives-context object registry contains duplicates.")

    required_true = (
        "official_checksum_required",
        "raw_zip_hash_implemented",
        "csv_member_hash_implemented",
        "normalized_file_hash_implemented",
        "atomic_dataset_lock_implemented",
        "independent_reader_implemented",
        "optional_metrics_blank_policy_implemented",
        "optional_metrics_blank_counts_recorded",
        "open_interest_zero_sentinel_policy_implemented",
        "read_only_iso8601_timestamp_recovery_implemented",
    )
    if any(declaration[field] is not True for field in required_true):
        raise RuntimeError("Derivatives-context dataset integrity boundary mismatch.")
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
    if any(declaration[field] is not False for field in required_false):
        raise RuntimeError("Derivatives-context dataset safety boundary mismatch.")
    if declaration["attempt_1_authorization_consumed"] is not True:
        raise RuntimeError("Derivatives-context Attempt 1 consumption mismatch.")
    if declaration["attempt_1_final_dataset_exists"] is not False:
        raise RuntimeError("Derivatives-context Attempt 1 final-state mismatch.")
    if declaration["attempt_1_staging_required"] is not True:
        raise RuntimeError("Derivatives-context Attempt 1 staging mismatch.")
    if declaration["attempt_2_authorization_consumed"] is not True:
        raise RuntimeError("Derivatives-context Attempt 2 consumption mismatch.")
    if declaration["attempt_2_final_dataset_exists"] is not False:
        raise RuntimeError("Derivatives-context Attempt 2 final-state mismatch.")
    if declaration["attempt_2_staging_required"] is not True:
        raise RuntimeError("Derivatives-context Attempt 2 staging mismatch.")
    if declaration["attempt_3_authorization_consumed"] is not True:
        raise RuntimeError("Derivatives-context Attempt 3 consumption mismatch.")
    if declaration["attempt_3_final_dataset_exists"] is not False:
        raise RuntimeError("Derivatives-context Attempt 3 final-state mismatch.")
    if declaration["attempt_3_staging_required"] is not True:
        raise RuntimeError("Derivatives-context Attempt 3 staging mismatch.")
    if declaration["attempt_4_authorization_consumed"] is not True:
        raise RuntimeError("Derivatives-context Attempt 4 consumption mismatch.")
    if declaration["attempt_4_final_dataset_recorded"] is not True:
        raise RuntimeError("Derivatives-context Attempt 4 final-state mismatch.")
    if declaration["attempt_4_execution_commit"] != ATTEMPT_4_EXECUTION_COMMIT:
        raise RuntimeError("Derivatives-context Attempt 4 execution binding mismatch.")
    if declaration["attempt_4_manifest_sha256"] != ATTEMPT_4_MANIFEST_SHA256:
        raise RuntimeError("Derivatives-context Attempt 4 manifest binding mismatch.")
    if (
        declaration["attempt_4_reader_incident_sha256"]
        != ATTEMPT_4_READER_INCIDENT_SHA256
    ):
        raise RuntimeError("Derivatives-context Attempt 4 reader binding mismatch.")
    if declaration["recovery_attempt"] != 4:
        raise RuntimeError("Derivatives-context recovery attempt mismatch.")
    if (
        declaration["attempt_3_staging_file_count"]
        != ATTEMPT_3_STAGING_FILE_COUNT
        or declaration["attempt_3_staging_total_bytes"]
        != ATTEMPT_3_STAGING_TOTAL_BYTES
        or declaration["attempt_3_staging_inventory_sha256"]
        != ATTEMPT_3_STAGING_INVENTORY_SHA256
        or declaration["verified_resume_object_count"]
        != ATTEMPT_3_RESUME_OBJECT_COUNT
        or declaration["public_download_object_count"]
        != len(registry) - ATTEMPT_3_RESUME_OBJECT_COUNT
        or declaration["maximum_transport_attempts_per_fetch"]
        != MAXIMUM_TRANSPORT_ATTEMPTS
        or declaration["maximum_transport_backoff_seconds"]
        != MAXIMUM_TRANSPORT_BACKOFF_SECONDS
    ):
        raise RuntimeError("Derivatives-context recovery transport boundary mismatch.")
    if (
        declaration["open_interest_zero_sentinel_count"] != 399
        or declaration["open_interest_zero_sentinel_count_per_asset"] != 133
        or declaration["open_interest_zero_sentinel_timestamp_sha256"]
        != OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256
    ):
        raise RuntimeError("Derivatives-context zero-sentinel evidence mismatch.")

    return {
        **declaration,
        "status": STATUS,
        "parent_protocol_sha256": observed["parent_protocol"],
        "parent_protocol_sha256_match": True,
        "parent_component_sha256": observed["parent_component"],
        "parent_component_sha256_match": True,
        "parent_review_sha256": observed["parent_review"],
        "parent_review_sha256_match": True,
        "protocol_sha256": observed["protocol"],
        "protocol_sha256_match": True,
        "component_sha256": observed["component"],
        "component_sha256_match": True,
        "source_schema_validation_implemented": True,
        "causal_timestamp_validation_implemented": True,
        "raw_and_normalized_lock_implemented": True,
        "attempt_1_incident_sha256_match": True,
        "attempt_2_incident_sha256_match": True,
        "attempt_3_incident_sha256_match": True,
        "attempt_4_reader_incident_sha256_match": True,
        "attempt_4_acquisition_completed": True,
        "acquisition_rerun_authorized": False,
        "explicit_iso8601_normalized_timestamp_parser_implemented": True,
        "complete_metrics_forensic_scan_recorded": True,
        "recovery_new_root_required": True,
        "prior_staging_inventory_implemented": True,
        "verified_resume_staging_binding_implemented": True,
        "bounded_transport_retry_implemented": True,
        "next_stage": "RUN_READ_ONLY_ATTEMPT_4_FINAL_LOCK_REVIEW_AFTER_ISO8601_READER_FIX",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the frozen derivatives-context dataset lock and reader."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_derivatives_context_dataset_lock(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
