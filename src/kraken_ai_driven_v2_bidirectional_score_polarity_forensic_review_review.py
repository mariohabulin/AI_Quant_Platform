"""Static source-binding review for bidirectional score/polarity forensics V1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review import (
        ATTEMPT_1_RESULT_DOCUMENT_SHA256,
        EXPECTED_REPORT_SHA256,
        PARENT_COMMIT,
        RUNNER_COMPONENT_SHA256,
        RUNNER_PROTOCOL_SHA256,
        RUNNER_REVIEW_SHA256,
        STATIC_STATUS,
        forensic_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review import (
        ATTEMPT_1_RESULT_DOCUMENT_SHA256,
        EXPECTED_REPORT_SHA256,
        PARENT_COMMIT,
        RUNNER_COMPONENT_SHA256,
        RUNNER_PROTOCOL_SHA256,
        RUNNER_REVIEW_SHA256,
        STATIC_STATUS,
        forensic_declaration,
    )


EXPECTED_PARENT_COMMIT = "ca1cd9186ecfac934d4ad84000da12c572d633a3"
EXPECTED_REPORT_SHA256 = (
    "7176ca3a005b7bdbfbdcbc2259fafd11c154ee45b0517eab26894e675aa26b3f"
)
EXPECTED_HASHES = {
    "attempt_1_result": "e394f0daf01b5262f3d1b2318c1e8d443ec59ac9e63561d13dd9d0e6b1951996",
    "runner_protocol": "b9e5d092c24dfc8952766de480dd6db8daf2c9f8e83b25cc6c326b4ed37d794e",
    "runner_component": "6b37f6a1df2c40941202216179b38c25997ac16d3cf5fb261809c579222ea6c4",
    "runner_review": "e0ccd282d00faab3b09ca2607c77df1d9bb2c810c85c988d3071f778fbb70da3",
    "forensic_protocol": "55a21dbc3c29203474c9ab3fa51648abf62b8cb8fb241b14ddee53160ebca3ef",
    "forensic_component": "4af5ada205b5fc55724d9900651fd3495f922168c0d625ef7b60347387be12a5",
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_bidirectional_score_polarity_forensics(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "attempt_1_result": root
        / "KRAKEN_AI_DRIVEN_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_ATTEMPT_1_RESULT.md",
        "runner_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md",
        "runner_component": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_development_learning_runner.py",
        "runner_review": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_development_learning_runner_review.py",
        "forensic_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_PROTOCOL_V1.md",
        "forensic_component": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review.py",
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(
                f"Bidirectional score/polarity forensic source binding mismatch: {name}."
            )

    declaration = forensic_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Bidirectional forensic parent commit mismatch.")
    if EXPECTED_REPORT_SHA256 != declaration["expected_learning_report_sha256"]:
        raise RuntimeError("Bidirectional forensic report binding mismatch.")
    bindings = {
        "attempt_1_result": ATTEMPT_1_RESULT_DOCUMENT_SHA256,
        "runner_protocol": RUNNER_PROTOCOL_SHA256,
        "runner_component": RUNNER_COMPONENT_SHA256,
        "runner_review": RUNNER_REVIEW_SHA256,
    }
    for name, declared in bindings.items():
        if declared != observed[name]:
            raise RuntimeError(f"Bidirectional forensic declared binding mismatch: {name}.")

    for field in (
        "action_reconstruction_implemented",
        "matched_row_validation_implemented",
        "label_polarity_validation_implemented",
        "direction_calibration_diagnostics_implemented",
        "fixed_score_deciles_implemented",
        "selected_policy_economics_implemented",
        "read_only_forensics_implemented",
    ):
        if declaration[field] is not True:
            raise RuntimeError("Bidirectional forensic implementation boundary mismatch.")
    for field in (
        "external_evidence_opened",
        "model_artifacts_unpickled",
        "labels_generated",
        "model_training_executed",
        "retrospective_threshold_search_authorized",
        "polarity_flip_authorized",
        "automatic_next_experiment_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if declaration[field] is not False:
            raise RuntimeError("Bidirectional forensic safety boundary mismatch.")

    return {
        **declaration,
        "status": STATIC_STATUS,
        "source_sha256_matches": {name: True for name in observed},
        "forensic_protocol_sha256": observed["forensic_protocol"],
        "forensic_component_sha256": observed["forensic_component"],
        "next_stage": "RUN_READ_ONLY_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review bidirectional score/polarity forensics V1."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_bidirectional_score_polarity_forensics(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
