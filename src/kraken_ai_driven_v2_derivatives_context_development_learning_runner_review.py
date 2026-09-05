"""Static source-binding review for the derivatives-context learning runner."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_derivatives_context_development_learning_runner import (
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DATASET_COMPONENT_SHA256,
        DATASET_MANIFEST_SHA256,
        DATASET_PROTOCOL_SHA256,
        DATASET_RESULT_DOCUMENT_SHA256,
        DATASET_REVIEW_SHA256,
        HYPOTHESIS_COMPONENT_SHA256,
        HYPOTHESIS_PROTOCOL_SHA256,
        HYPOTHESIS_REVIEW_SHA256,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        VARIANT_SPECS,
        WINDOWS_SIDECAR_INCIDENT_SHA256,
        runner_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_derivatives_context_development_learning_runner import (
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DATASET_COMPONENT_SHA256,
        DATASET_MANIFEST_SHA256,
        DATASET_PROTOCOL_SHA256,
        DATASET_RESULT_DOCUMENT_SHA256,
        DATASET_REVIEW_SHA256,
        HYPOTHESIS_COMPONENT_SHA256,
        HYPOTHESIS_PROTOCOL_SHA256,
        HYPOTHESIS_REVIEW_SHA256,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        VARIANT_SPECS,
        WINDOWS_SIDECAR_INCIDENT_SHA256,
        runner_declaration,
    )


SCHEMA_VERSION = 1
STATUS = (
    "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_RUNNER_"
    "REVIEWED_EXECUTION_AUTHORIZATION_REQUIRED"
)
EXPECTED_PARENT_COMMIT = "9b23d05eed043c92205e7a2ca62c70312f6b6e8f"
EXPECTED_DATASET_MANIFEST_SHA256 = (
    "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916"
)
EXPECTED_HASHES = {
    "hypothesis_protocol": "81074ffcd8213fcf86c44e5f118293936632b279602b5750a67332848d6fd865",
    "hypothesis_component": "5355bb5d8e672d539776fc88705f2864b4974a767b12aaabfd4615aeb42288b3",
    "hypothesis_review": "48cff3f16d576a77a993694fb37d7410027daaecc87f3f010f910e2b6111fb05",
    "dataset_protocol": "d440ecf75822dcef6c0517402cf3586ae1006452c51f317eb207e89213d8725b",
    "dataset_component": "718167d72b229f1e48af3e81a0835cf367003f81ca433b1bb0eb19035ed5eda0",
    "dataset_review": "63cbf24db6d402f2cc88eec6538690e55f6648a0409edf5f2c0c2caa1a2d4169",
    "dataset_result": "753ff82a36d93382eed5ead23ecabbd884e850dd6ac72f3e2728df32d8c33922",
    "windows_sidecar_incident": "8bd88c1129a449b2dd1670a663be49cf7ea3091691dbed123dc54f5280504c3d",
    "runner_protocol": "91dc2ca8e9348e7eae9c0a056b750894418d945a10f6257d80f453f863711de3",
    "runner_component": "e31d4062cd714fcf067ed308ac12428a8ec4db20c6ce6015c83d404aa5b59108",
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_context_development_learning_runner(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "hypothesis_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_LEARNING_HYPOTHESIS_PROTOCOL_V1.md",
        "hypothesis_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_hypothesis.py",
        "hypothesis_review": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_hypothesis_review.py",
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
        "windows_sidecar_incident": root
        / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_RUNNER_WINDOWS_SIDECAR_INCIDENT.md",
        "runner_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md",
        "runner_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_development_learning_runner.py",
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Context-learning source binding mismatch: {name}.")

    declaration = runner_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Context-learning implementation parent mismatch.")
    if DATASET_MANIFEST_SHA256 != EXPECTED_DATASET_MANIFEST_SHA256:
        raise RuntimeError("Context-learning Dataset Lock identity mismatch.")
    frozen_bindings = {
        "hypothesis_protocol": HYPOTHESIS_PROTOCOL_SHA256,
        "hypothesis_component": HYPOTHESIS_COMPONENT_SHA256,
        "hypothesis_review": HYPOTHESIS_REVIEW_SHA256,
        "dataset_protocol": DATASET_PROTOCOL_SHA256,
        "dataset_component": DATASET_COMPONENT_SHA256,
        "dataset_review": DATASET_REVIEW_SHA256,
        "dataset_result": DATASET_RESULT_DOCUMENT_SHA256,
        "windows_sidecar_incident": WINDOWS_SIDECAR_INCIDENT_SHA256,
    }
    if any(observed[name] != digest for name, digest in frozen_bindings.items()):
        raise RuntimeError("Context-learning parent source binding mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Context-learning protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Context-learning component identity mismatch.")
    if declaration["authorization_phrase"] != AUTHORIZATION_PHRASE:
        raise RuntimeError("Context-learning authorization phrase mismatch.")
    if declaration["variant_order"] != list(VARIANT_SPECS):
        raise RuntimeError("Context-learning variant order mismatch.")
    if declaration["matched_control"] != MATCHED_CONTROL:
        raise RuntimeError("Context-learning matched-control registry mismatch.")
    if declaration["maximum_fold_model_fits"] != 12:
        raise RuntimeError("Context-learning experiment budget mismatch.")
    required_true = (
        "identical_context_complete_rows_implemented",
        "absolute_and_incremental_gates_implemented",
        "real_model_artifact_persistence_implemented",
        "out_of_fold_prediction_artifact_implemented",
        "one_shot_atomic_evidence_implemented",
        "independent_evidence_reader_implemented",
        "canonical_binary_lf_sidecars_implemented",
    )
    if any(declaration[field] is not True for field in required_true):
        raise RuntimeError("Context-learning implementation boundary mismatch.")
    required_false = (
        "authorization_phrase_active",
        "network_download_authorized",
        "source_archive_opened",
        "context_dataset_opened",
        "development_data_opened",
        "labels_generated",
        "model_training_authorized",
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
        raise RuntimeError("Context-learning safety boundary mismatch.")

    return {
        **declaration,
        "status": STATUS,
        "parent_source_bindings": {
            name: observed[name] == EXPECTED_HASHES[name]
            for name in EXPECTED_HASHES
            if name not in {"runner_protocol", "runner_component"}
        },
        "runner_protocol_sha256": observed["runner_protocol"],
        "runner_protocol_sha256_match": True,
        "runner_component_sha256": observed["runner_component"],
        "runner_component_sha256_match": True,
        "dataset_lock_independent_review_passed": True,
        "next_stage": "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_CONTEXT_DEVELOPMENT_LEARNING_RUN",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the frozen derivatives-context Development learning runner."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_context_development_learning_runner(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
