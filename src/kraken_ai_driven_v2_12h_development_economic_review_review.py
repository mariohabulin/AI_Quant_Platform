"""Static source-binding review for the 12h Development economic review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_12h_development_economic_review import (
        COMPONENT_ID,
        EXPECTED_LEARNING_REPORT_SHA256,
        PARENT_COMMIT,
        PROTOCOL_ID,
        economic_review_declaration,
    )
except ImportError:  # pragma: no cover
    from .kraken_ai_driven_v2_12h_development_economic_review import (
        COMPONENT_ID,
        EXPECTED_LEARNING_REPORT_SHA256,
        PARENT_COMMIT,
        PROTOCOL_ID,
        economic_review_declaration,
    )


SCHEMA_VERSION = 1
STATUS = "KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_REVIEW_REVIEWED_EXTERNAL_EVIDENCE_REQUIRED"
EXPECTED_PARENT_COMMIT = "9c1156e0527c34c71f9efec381f3770fdc7b4238"
EXPECTED_PARENT_RUNNER_PROTOCOL_SHA256 = (
    "a1fb0e369adab2aba469567b74bef76ad5404007c62287dd232e98166fd486be"
)
EXPECTED_PARENT_RUNNER_COMPONENT_SHA256 = (
    "8cbeb478b2d78bccbe33ebb96ab8a1e2838492b10f52e7e42b363c1c9e545082"
)
EXPECTED_PROTOCOL_SHA256 = (
    "dbefb78c1b14a4e6a809eb7dbd1dc32c00344ad3c3335b59b4185483e646a559"
)
EXPECTED_COMPONENT_SHA256 = (
    "1e946f0b370081114d017b1968bce8e38104225229328254b4b32bafad2c535e"
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_12h_development_economic_review(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "parent_runner_protocol": root / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_12H_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md",
        "parent_runner_component": root / "src" / "kraken_ai_driven_v2_12h_development_learning_runner.py",
        "economic_review_protocol": root / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_12H_DEVELOPMENT_ECONOMIC_EVIDENCE_REVIEW_PROTOCOL_V1.md",
        "economic_review_component": root / "src" / "kraken_ai_driven_v2_12h_development_economic_review.py",
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    expected = {
        "parent_runner_protocol": EXPECTED_PARENT_RUNNER_PROTOCOL_SHA256,
        "parent_runner_component": EXPECTED_PARENT_RUNNER_COMPONENT_SHA256,
        "economic_review_protocol": EXPECTED_PROTOCOL_SHA256,
        "economic_review_component": EXPECTED_COMPONENT_SHA256,
    }
    for name, digest in expected.items():
        if observed[name] != digest:
            raise RuntimeError(f"12h Development economic review source binding mismatch: {name}.")
    declaration = economic_review_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT or declaration["parent_commit"] != PARENT_COMMIT:
        raise RuntimeError("12h Development economic review parent commit mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID or declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("12h Development economic review identity mismatch.")
    required_false = (
        "threshold_sweep_authorized",
        "learning_evidence_opened",
        "source_archive_opened",
        "model_artifacts_unpickled",
        "labels_generated",
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
        raise RuntimeError("12h Development economic review safety boundary mismatch.")
    return {
        **declaration,
        "status": STATUS,
        "expected_learning_report_sha256": EXPECTED_LEARNING_REPORT_SHA256,
        "parent_runner_protocol_sha256": observed["parent_runner_protocol"],
        "parent_runner_protocol_sha256_match": True,
        "parent_runner_component_sha256": observed["parent_runner_component"],
        "parent_runner_component_sha256_match": True,
        "economic_review_protocol_sha256": observed["economic_review_protocol"],
        "economic_review_protocol_sha256_match": True,
        "economic_review_component_sha256": observed["economic_review_component"],
        "economic_review_component_sha256_match": True,
        "next_stage": "RUN_READ_ONLY_12H_DEVELOPMENT_ECONOMIC_EVIDENCE_REVIEW",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review the Kraken V2 Development economic-review component.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(json.dumps(review_12h_development_economic_review(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
