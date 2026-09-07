"""Static binding review for the zero-cost source-audit result reviewer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from us_equity_point_in_time_data_feasibility_result_review import (
        EXECUTION_COMMIT,
        EXPECTED_ACTION,
        EXPECTED_MISSING_CAPABILITIES,
        EXPECTED_REPORT_SHA256,
        EXPECTED_SOURCE_IDS,
        STATIC_STATUS as RESULT_REVIEW_STATIC_STATUS,
        result_review_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .us_equity_point_in_time_data_feasibility_result_review import (
        EXECUTION_COMMIT,
        EXPECTED_ACTION,
        EXPECTED_MISSING_CAPABILITIES,
        EXPECTED_REPORT_SHA256,
        EXPECTED_SOURCE_IDS,
        STATIC_STATUS as RESULT_REVIEW_STATIC_STATUS,
        result_review_declaration,
    )


STATUS = (
    "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_RESULT_REVIEW_COMPONENT_BOUND_"
    "OPERATOR_DECISION_REQUIRED"
)
EXPECTED_HASHES = {
    "line_ending_policy": (
        "0cc450c4a2fe9a9fdf974fba4a75e7cd5d63b5897469b4f28e888d7c1bc1185e"
    ),
    "feasibility_protocol": (
        "8b860e2e282f38e13a2195b451d5d7359ae1a8321f12dc302478ce455d0d77bd"
    ),
    "feasibility_component": (
        "b1c48c79269bd24720e78282d55e93b3378616529fadffa183865fa448eb6e3e"
    ),
    "feasibility_review": (
        "b55909a7a49dd8d8eaf130326b7304ad1a66aecb0a12ac08cab50ccbbe8f785e"
    ),
    "attempt_1_result": (
        "f28d991fda72016bb47b732606b5ee1721714755cfe24a17fb9ad02a56ddf99c"
    ),
    "result_review_protocol": (
        "f2958251dd4289b81b2919c6874fef9a2f1cfdc00c76a3370aae223f58bcc179"
    ),
    "result_review_component": (
        "5225c4a55779d9cad934cd27b278edb99b0c4d0410db38075a2061a8d509b148"
    ),
}


def _checkout_stable_sha256(path):
    payload = Path(path).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(payload).hexdigest()


def review_zero_cost_source_audit_result_component(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "line_ending_policy": root / ".gitattributes",
        "feasibility_protocol": root
        / "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_PROTOCOL_V1.md",
        "feasibility_component": root
        / "src"
        / "us_equity_point_in_time_data_feasibility.py",
        "feasibility_review": root
        / "src"
        / "us_equity_point_in_time_data_feasibility_review.py",
        "attempt_1_result": root
        / "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_ATTEMPT_1_RESULT.md",
        "result_review_protocol": root
        / "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_RESULT_REVIEW_PROTOCOL_V1.md",
        "result_review_component": root
        / "src"
        / "us_equity_point_in_time_data_feasibility_result_review.py",
    }
    observed = {name: _checkout_stable_sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Zero-cost source-audit result binding mismatch: {name}.")

    declaration = result_review_declaration()
    if declaration.get("status") != RESULT_REVIEW_STATIC_STATUS:
        raise RuntimeError("Zero-cost source-audit result-review status mismatch.")
    if declaration.get("execution_commit") != EXECUTION_COMMIT:
        raise RuntimeError("Zero-cost source-audit execution commit mismatch.")
    if declaration.get("expected_report_sha256") != EXPECTED_REPORT_SHA256:
        raise RuntimeError("Zero-cost source-audit report binding mismatch.")
    if declaration.get("expected_observation_source_ids") != list(EXPECTED_SOURCE_IDS):
        raise RuntimeError("Zero-cost source-audit source registry mismatch.")
    if declaration.get("expected_missing_capabilities") != list(
        EXPECTED_MISSING_CAPABILITIES
    ):
        raise RuntimeError("Zero-cost source-audit capability gap mismatch.")
    if declaration.get("expected_action") != EXPECTED_ACTION:
        raise RuntimeError("Zero-cost source-audit action mismatch.")
    required_false = (
        "external_evidence_opened",
        "market_values_opened",
        "labels_generated",
        "performance_evaluation_executed",
        "model_training_executed",
        "paid_subscription_authorized",
        "paid_api_key_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    if any(declaration.get(field) is not False for field in required_false):
        raise RuntimeError("Zero-cost source-audit static safety mismatch.")
    return {
        **declaration,
        "status": STATUS,
        "source_sha256_matches": {name: True for name in observed},
        "checkout_stable_hashing": True,
        "source_feasible": False,
        "monthly_data_cost_usd": 0,
        "next_stage": "OPERATOR_DECISION_NO_AUTOMATIC_PURCHASE",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the zero-cost source-audit result-review component."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_zero_cost_source_audit_result_component(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
