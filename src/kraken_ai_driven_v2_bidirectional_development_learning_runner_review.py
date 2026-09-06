"""Static source-binding review for the bidirectional Development runner."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_bidirectional_development_learning_runner import (
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DATASET_MANIFEST_SHA256,
        DIRECTION_ORDER,
        FOLD_PLAN,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        SOURCE_BINDING_SHA256,
        VARIANT_SPECS,
        runner_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_bidirectional_development_learning_runner import (
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DATASET_MANIFEST_SHA256,
        DIRECTION_ORDER,
        FOLD_PLAN,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        SOURCE_BINDING_SHA256,
        VARIANT_SPECS,
        runner_declaration,
    )


SCHEMA_VERSION = 1
STATUS = (
    "KRAKEN_AI_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_RUNNER_"
    "REVIEWED_EXECUTION_AUTHORIZATION_REQUIRED"
)
EXPECTED_PARENT_COMMIT = "82ea7f12d8786d6d5ed1d6fa49e57da34d73b9fe"
EXPECTED_DATASET_MANIFEST_SHA256 = (
    "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916"
)
EXPECTED_HASHES = {
    **SOURCE_BINDING_SHA256,
    "runner_protocol": (
        "b9e5d092c24dfc8952766de480dd6db8daf2c9f8e83b25cc6c326b4ed37d794e"
    ),
    "runner_component": (
        "6b37f6a1df2c40941202216179b38c25997ac16d3cf5fb261809c579222ea6c4"
    ),
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_bidirectional_development_learning_runner(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "learning_core_component": root
        / "src"
        / "kraken_ai_driven_v2_learning_core.py",
        "spot_reader_component": root
        / "src"
        / "kraken_ai_driven_v2_12h_development_learning_runner.py",
        "context_feature_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_hypothesis.py",
        "dataset_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_READER_PROTOCOL_V1.md",
        "dataset_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_dataset.py",
        "dataset_review": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_dataset_review.py",
        "dataset_result": root
        / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ATTEMPT_4_RESULT.md",
        "bidirectional_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_DEVELOPMENT_HYPOTHESIS_PROTOCOL_V1.md",
        "bidirectional_component": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_hypothesis.py",
        "bidirectional_review": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_hypothesis_review.py",
        "context_forensic_result": root
        / "KRAKEN_AI_DRIVEN_V2_CONTEXT_SCORE_FORENSIC_REVIEW_ATTEMPT_1_RESULT.md",
        "runner_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md",
        "runner_component": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_development_learning_runner.py",
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Bidirectional runner source binding mismatch: {name}.")

    declaration = runner_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Bidirectional runner parent commit mismatch.")
    if DATASET_MANIFEST_SHA256 != EXPECTED_DATASET_MANIFEST_SHA256:
        raise RuntimeError("Bidirectional runner dataset manifest mismatch.")
    if SOURCE_BINDING_SHA256 != {
        name: EXPECTED_HASHES[name] for name in SOURCE_BINDING_SHA256
    }:
        raise RuntimeError("Bidirectional runner frozen source registry mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Bidirectional runner protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Bidirectional runner component identity mismatch.")
    if declaration["authorization_phrase"] != AUTHORIZATION_PHRASE:
        raise RuntimeError("Bidirectional runner authorization phrase mismatch.")
    if declaration["variant_order"] != list(VARIANT_SPECS):
        raise RuntimeError("Bidirectional runner variant registry mismatch.")
    if declaration["direction_order"] != list(DIRECTION_ORDER):
        raise RuntimeError("Bidirectional runner direction registry mismatch.")
    if declaration["matched_control"] != MATCHED_CONTROL:
        raise RuntimeError("Bidirectional runner matched control mismatch.")
    expected_fit_count = len(VARIANT_SPECS) * len(DIRECTION_ORDER) * len(FOLD_PLAN)
    if (
        declaration["maximum_fold_model_fits"] != expected_fit_count
        or expected_fit_count != 12
    ):
        raise RuntimeError("Bidirectional runner model-fit budget mismatch.")

    required_true = (
        "paired_directional_rows_implemented",
        "latest_outcome_purge_implemented",
        "positive_maximum_action_rule_implemented",
        "absolute_and_incremental_gates_implemented",
        "real_model_artifact_persistence_implemented",
        "out_of_fold_prediction_artifact_implemented",
        "canonical_binary_lf_sidecars_implemented",
        "one_shot_atomic_evidence_implemented",
        "independent_evidence_reader_implemented",
    )
    if any(declaration[field] is not True for field in required_true):
        raise RuntimeError("Bidirectional runner implementation boundary mismatch.")
    required_false = (
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
    )
    if any(declaration[field] is not False for field in required_false):
        raise RuntimeError("Bidirectional runner safety boundary mismatch.")

    return {
        **declaration,
        "status": STATUS,
        "source_sha256_matches": {
            name: observed[name] == EXPECTED_HASHES[name]
            for name in SOURCE_BINDING_SHA256
        },
        "runner_protocol_sha256": observed["runner_protocol"],
        "runner_protocol_sha256_match": True,
        "runner_component_sha256": observed["runner_component"],
        "runner_component_sha256_match": True,
        "model_training_executed": False,
        "next_stage": (
            "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_BIDIRECTIONAL_"
            "DEVELOPMENT_LEARNING_RUN"
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the frozen bidirectional Development runner."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_bidirectional_development_learning_runner(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
