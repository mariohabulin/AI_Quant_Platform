"""Static source review for the regime-gated selective terminal result review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_regime_gated_selective_development_result_review import (
        ATTEMPT_1_RESULT_DOCUMENT_SHA256,
        EXECUTION_COMMIT,
        EXPECTED_REPORT_SHA256,
        EXPECTED_PREDICTION_SHA256,
        RUNNER_COMPONENT_SHA256,
        RUNNER_PROTOCOL_SHA256,
        RUNNER_REVIEW_SHA256,
        STATIC_STATUS,
        result_review_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_regime_gated_selective_development_result_review import (
        ATTEMPT_1_RESULT_DOCUMENT_SHA256,
        EXECUTION_COMMIT,
        EXPECTED_REPORT_SHA256,
        EXPECTED_PREDICTION_SHA256,
        RUNNER_COMPONENT_SHA256,
        RUNNER_PROTOCOL_SHA256,
        RUNNER_REVIEW_SHA256,
        STATIC_STATUS,
        result_review_declaration,
    )


EXPECTED_EXECUTION_COMMIT = "40d98117613d3f4a74e809f76dcd371804b3fc31"
EXPECTED_REPORT_SHA256 = (
    "a972088fca185266a4a726b3a4512a90bed15f4e1d3a3467e76bedd171a7f286"
)
EXPECTED_PREDICTION_SHA256 = (
    "728b60750ed9de5070281d8d3cebecddbef701f2f6ea604dbeec7c2ea7015400"
)
EXPECTED_HASHES = {
    "line_ending_policy": (
        "0cc450c4a2fe9a9fdf974fba4a75e7cd5d63b5897469b4f28e888d7c1bc1185e"
    ),
    "attempt_1_result": (
        "d9f1ac12d56571752dc78f13dc0157df3df7023be37e07448e75e0f700c87794"
    ),
    "runner_protocol": (
        "dd1df5ebef5d4e2d73bc4e358307164f270ab83045b18a7aa6264e90289396df"
    ),
    "runner_component": (
        "d60506b7d753fbc7efc329c77db0327c655ff4002ecefb9f2798ad4bb2c6f732"
    ),
    "runner_review": (
        "d35b55367e8687b6b54eef46e8e45fedcf05d70c2f4e3ceb9a045cbd9b5d6da5"
    ),
    "result_review_protocol": (
        "ef4d4f8fb8b771c12bb7129255b9ba2e54779a15b899823a165f9fa24d7ebb7b"
    ),
    "result_review_component": (
        "8d4692bcb704332a7fc50e795a2bd0aa9a2174ce9f9731686f49041c9e1474e7"
    ),
}


def _checkout_stable_sha256(path):
    payload = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def review_regime_gated_selective_terminal_result_component(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "line_ending_policy": root / ".gitattributes",
        "attempt_1_result": root
        / "KRAKEN_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_ATTEMPT_1_RESULT.md",
        "runner_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_RUNNER_PROTOCOL_V1.md",
        "runner_component": root
        / "src"
        / "kraken_ai_driven_v2_regime_gated_selective_development_runner.py",
        "runner_review": root
        / "src"
        / "kraken_ai_driven_v2_regime_gated_selective_development_runner_review.py",
        "result_review_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_RESULT_REVIEW_PROTOCOL_V1.md",
        "result_review_component": root
        / "src"
        / "kraken_ai_driven_v2_regime_gated_selective_development_result_review.py",
    }
    observed = {name: _checkout_stable_sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(
                f"Regime-gated terminal result source binding mismatch: {name}."
            )

    declaration = result_review_declaration()
    if EXECUTION_COMMIT != EXPECTED_EXECUTION_COMMIT:
        raise RuntimeError("Regime-gated terminal execution commit mismatch.")
    if declaration["expected_report_sha256"] != EXPECTED_REPORT_SHA256:
        raise RuntimeError("Regime-gated terminal report binding mismatch.")
    if declaration["expected_prediction_sha256"] != EXPECTED_PREDICTION_SHA256:
        raise RuntimeError("Regime-gated terminal prediction binding mismatch.")
    declared_hashes = {
        "attempt_1_result": ATTEMPT_1_RESULT_DOCUMENT_SHA256,
        "runner_protocol": RUNNER_PROTOCOL_SHA256,
        "runner_component": RUNNER_COMPONENT_SHA256,
        "runner_review": RUNNER_REVIEW_SHA256,
    }
    for name, declared in declared_hashes.items():
        if declared != observed[name]:
            raise RuntimeError(
                f"Regime-gated terminal declared binding mismatch: {name}."
            )
    if declaration["terminal_action"] != "HOLD_CASH":
        raise RuntimeError("Regime-gated terminal action mismatch.")
    if not declaration["terminal_status"].endswith("STOP_KRAKEN_12H_RESEARCH"):
        raise RuntimeError("Regime-gated terminal stop mismatch.")
    required_false = (
        "external_evidence_opened",
        "model_artifacts_unpickled",
        "labels_generated",
        "model_training_executed",
        "retry_authorized",
        "threshold_rescue_authorized",
        "automatic_successor_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    if any(declaration[field] is not False for field in required_false):
        raise RuntimeError("Regime-gated terminal static safety boundary mismatch.")
    return {
        **declaration,
        "status": STATIC_STATUS,
        "source_sha256_matches": {name: True for name in observed},
        "checkout_stable_hashing": True,
        "next_stage": "RUN_READ_ONLY_TERMINAL_RESULT_REVIEW",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the regime-gated terminal result-review component."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_regime_gated_selective_terminal_result_component(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
