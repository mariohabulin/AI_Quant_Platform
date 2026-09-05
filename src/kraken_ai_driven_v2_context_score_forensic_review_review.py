"""Static source-binding review for context score forensics V1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_context_score_forensic_review import (
        ATTEMPT_1_RESULT_DOCUMENT_SHA256,
        EXPECTED_REPORT_SHA256,
        PARENT_COMMIT,
        RUNNER_COMPONENT_SHA256,
        RUNNER_PROTOCOL_SHA256,
        STATIC_STATUS,
        forensic_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_context_score_forensic_review import (
        ATTEMPT_1_RESULT_DOCUMENT_SHA256,
        EXPECTED_REPORT_SHA256,
        PARENT_COMMIT,
        RUNNER_COMPONENT_SHA256,
        RUNNER_PROTOCOL_SHA256,
        STATIC_STATUS,
        forensic_declaration,
    )


EXPECTED_PARENT_COMMIT = "4e3867dfadc9795ca39e24ebafc7f405d40f3c8d"
EXPECTED_REPORT_SHA256 = (
    "bddb6f7c0a9b056dcf8a4ca79fc3b8128dbf4ded4aac47e19022a84222215fb4"
)
EXPECTED_HASHES = {
    "attempt_1_result": "16c357ecde8104dfd8aee920219b56b3748e9cb522e100ec122f568720e16f4a",
    "runner_protocol": "91dc2ca8e9348e7eae9c0a056b750894418d945a10f6257d80f453f863711de3",
    "runner_component": "e31d4062cd714fcf067ed308ac12428a8ec4db20c6ce6015c83d404aa5b59108",
    "forensic_protocol": "da1acc2eb4aba5ed7e1f84e8438e09bd5b60fb448e1afd5285a21cca5af8eebe",
    "forensic_component": "a40b1f9b0a5058901a029ceecea7e24b5b8870e0b04957ca9382df421afced2d",
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_context_score_forensics(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "attempt_1_result": root
        / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_ATTEMPT_1_RESULT.md",
        "runner_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md",
        "runner_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_development_learning_runner.py",
        "forensic_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_CONTEXT_SCORE_FORENSIC_REVIEW_PROTOCOL_V1.md",
        "forensic_component": root
        / "src"
        / "kraken_ai_driven_v2_context_score_forensic_review.py",
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Context score forensic source binding mismatch: {name}.")
    declaration = forensic_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Context score forensic parent commit mismatch.")
    if EXPECTED_REPORT_SHA256 != declaration["expected_learning_report_sha256"]:
        raise RuntimeError("Context score forensic report binding mismatch.")
    if ATTEMPT_1_RESULT_DOCUMENT_SHA256 != observed["attempt_1_result"]:
        raise RuntimeError("Context score forensic Attempt 1 result binding mismatch.")
    if RUNNER_PROTOCOL_SHA256 != observed["runner_protocol"]:
        raise RuntimeError("Context score forensic runner protocol binding mismatch.")
    if RUNNER_COMPONENT_SHA256 != observed["runner_component"]:
        raise RuntimeError("Context score forensic runner component binding mismatch.")
    for field in (
        "read_only_forensics_implemented",
        "matched_row_validation_implemented",
        "nonoverlapping_decile_economics_implemented",
    ):
        if declaration[field] is not True:
            raise RuntimeError("Context score forensic implementation boundary mismatch.")
    for field in (
        "external_evidence_opened",
        "model_artifacts_unpickled",
        "labels_generated",
        "model_training_executed",
        "threshold_sweep_authorized",
        "automatic_experiment_2_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if declaration[field] is not False:
            raise RuntimeError("Context score forensic safety boundary mismatch.")
    return {
        **declaration,
        "status": STATIC_STATUS,
        "source_sha256_matches": {name: True for name in observed},
        "forensic_protocol_sha256": observed["forensic_protocol"],
        "forensic_component_sha256": observed["forensic_component"],
        "next_stage": "RUN_READ_ONLY_CONTEXT_SCORE_FORENSIC_REVIEW",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review context score forensics V1.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(json.dumps(review_context_score_forensics(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
