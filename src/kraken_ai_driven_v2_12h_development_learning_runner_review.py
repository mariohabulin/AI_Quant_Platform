"""Static preflight review for the one-shot 12h Development learner."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_12h_development_learning_runner import (
        ASSET_ORDER,
        AUTHORIZATION_PHRASE,
        MODEL_SPECS,
        PARENT_COMMIT,
        PROTOCOL_ID,
        RUN_ID,
        runner_declaration,
    )
    from kraken_ai_driven_v2_learning_core import LEARNING_CORE_CONFIGURATION_SHA256
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_12h_development_learning_runner import (
        ASSET_ORDER,
        AUTHORIZATION_PHRASE,
        MODEL_SPECS,
        PARENT_COMMIT,
        PROTOCOL_ID,
        RUN_ID,
        runner_declaration,
    )
    from .kraken_ai_driven_v2_learning_core import LEARNING_CORE_CONFIGURATION_SHA256


SCHEMA_VERSION = 1
STATUS = "KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_RUNNER_RECOVERY_REVIEWED_ATTEMPT_2_AUTHORIZATION_REQUIRED"
EXPECTED_PARENT_COMMIT = "cc8ae44c45d41182af3bc91ee21cf075e65011b5"
EXPECTED_LEARNING_CORE_PROTOCOL_SHA256 = (
    "4a3dd7b00d52be5df3f60ce5dba0c8803462baa68d0f3eeb1f06f9d6fe64ea2c"
)
EXPECTED_LEARNING_CORE_COMPONENT_SHA256 = (
    "467f2a1913371ef11c9a828770bb6a260708032a9ba2aec142d88cfe7ab79207"
)
EXPECTED_RUNNER_PROTOCOL_SHA256 = (
    "88183f032e999288b3a8a6e0ad1fc51bf7b5af7d0d75fa31a43e0bd677832a9d"
)
EXPECTED_RUNNER_COMPONENT_SHA256 = (
    "4adbc9196a372cb02a02ecc961440f5204f4d4e2ce795ad90e13278ceff3ad2e"
)
EXPECTED_ATTEMPT_1_INCIDENT_SHA256 = (
    "c35b9dadbae7ab1055963231584ca3206be788d43035181706e796caf9a4f8e2"
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_12h_development_learning_runner(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "learning_core_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_LEARNING_CORE_PROTOCOL_V1.md",
        "learning_core_component": root / "src" / "kraken_ai_driven_v2_learning_core.py",
        "runner_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_12H_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md",
        "runner_component": root
        / "src"
        / "kraken_ai_driven_v2_12h_development_learning_runner.py",
        "attempt_1_incident": root
        / "KRAKEN_AI_DRIVEN_V2_12H_DEVELOPMENT_LEARNING_ATTEMPT_1_INCIDENT.md",
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    expected = {
        "learning_core_protocol": EXPECTED_LEARNING_CORE_PROTOCOL_SHA256,
        "learning_core_component": EXPECTED_LEARNING_CORE_COMPONENT_SHA256,
        "runner_protocol": EXPECTED_RUNNER_PROTOCOL_SHA256,
        "runner_component": EXPECTED_RUNNER_COMPONENT_SHA256,
        "attempt_1_incident": EXPECTED_ATTEMPT_1_INCIDENT_SHA256,
    }
    for name in expected:
        if observed[name] != expected[name]:
            raise RuntimeError(f"12h learning source binding mismatch: {name}.")

    declaration = runner_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT or declaration["parent_commit"] != PARENT_COMMIT:
        raise RuntimeError("12h learning parent commit mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID or declaration["run_id"] != RUN_ID:
        raise RuntimeError("12h learning component identity mismatch.")
    if declaration["authorization_phrase"] != AUTHORIZATION_PHRASE:
        raise RuntimeError("12h learning authorization phrase mismatch.")
    if declaration["asset_order"] != list(ASSET_ORDER):
        raise RuntimeError("12h learning asset order mismatch.")
    if declaration["model_order"] != list(MODEL_SPECS):
        raise RuntimeError("12h learning model order mismatch.")
    required_false = (
        "authorization_phrase_active",
        "source_archive_opened",
        "development_data_opened",
        "labels_generated",
        "model_training_authorized",
        "model_training_executed",
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
        raise RuntimeError("12h learning preflight authorization boundary mismatch.")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "protocol_id": PROTOCOL_ID,
        "run_id": RUN_ID,
        "parent_commit": PARENT_COMMIT,
        "recovery_attempt": 2,
        "attempt_1_execution_commit": EXPECTED_PARENT_COMMIT,
        "attempt_1_final_evidence_exists": False,
        "attempt_1_staging_evidence_exists": True,
        "attempt_1_authorization_consumed": True,
        "attempt_1_incident_sha256": observed["attempt_1_incident"],
        "attempt_1_incident_sha256_match": True,
        "source_row_column_count": 7,
        "source_row_schema": [
            "Unix time",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Trades",
        ],
        "development_trade_count_validation_implemented": True,
        "eight_column_assumption_active": False,
        "prior_attempt_staging_required": True,
        "active_resolution": "12h",
        "partition": "DEVELOPMENT",
        "asset_order": list(ASSET_ORDER),
        "model_order": list(MODEL_SPECS),
        "learning_core_configuration_sha256": LEARNING_CORE_CONFIGURATION_SHA256,
        "learning_core_protocol_sha256": observed["learning_core_protocol"],
        "learning_core_protocol_sha256_match": True,
        "learning_core_component_sha256": observed["learning_core_component"],
        "learning_core_component_sha256_match": True,
        "runner_protocol_sha256": observed["runner_protocol"],
        "runner_protocol_sha256_match": True,
        "runner_component_sha256": observed["runner_component"],
        "runner_component_sha256_match": True,
        "runner_implemented": True,
        "real_model_artifact_persistence_implemented": True,
        "out_of_fold_prediction_artifact_implemented": True,
        "class_support_hold_cash_branch_implemented": True,
        "independent_evidence_lock_implemented": True,
        "one_shot_atomic_evidence_implemented": True,
        "authorization_phrase": AUTHORIZATION_PHRASE,
        "authorization_phrase_active": False,
        "source_archive_opened": False,
        "development_data_opened": False,
        "labels_generated": False,
        "model_training_authorized": False,
        "model_training_executed": False,
        "automatic_model_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_12H_DEVELOPMENT_LEARNING_RECOVERY_ATTEMPT_2",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the Kraken V2 12h Development Learning Runner."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_12h_development_learning_runner(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
