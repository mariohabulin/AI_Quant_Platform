"""Static source-binding review for the frozen derivatives-context hypothesis."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_derivatives_context_hypothesis import (
        COMPONENT_ID,
        CONTEXT_FEATURE_COLUMNS,
        FEASIBILITY_REPORT_SHA256,
        FOLD_PLAN,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        VARIANT_SPECS,
        derivatives_context_hypothesis_declaration,
        fold_plan_is_causal,
    )
except ImportError:  # pragma: no cover
    from .kraken_ai_driven_v2_derivatives_context_hypothesis import (
        COMPONENT_ID,
        CONTEXT_FEATURE_COLUMNS,
        FEASIBILITY_REPORT_SHA256,
        FOLD_PLAN,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        VARIANT_SPECS,
        derivatives_context_hypothesis_declaration,
        fold_plan_is_causal,
    )


SCHEMA_VERSION = 1
STATUS = (
    "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_HYPOTHESIS_REVIEWED_DATA_LOCK_READER_REQUIRED"
)
EXPECTED_PARENT_COMMIT = "99f62423d19d7684c80ed67ed99666e2f48b0fbc"
EXPECTED_FEASIBILITY_REPORT_SHA256 = (
    "3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29"
)
EXPECTED_FEASIBILITY_PROTOCOL_SHA256 = (
    "08523d94d47f9e47f71b30e8f64f8dfd0108cf43cef6b6f36f6db6c9f93d6698"
)
EXPECTED_FEASIBILITY_COMPONENT_SHA256 = (
    "cb9d37eca11a3d7295feecb330d15b3a9417f4d9240a7725f95dd6371b872c6b"
)
EXPECTED_FEASIBILITY_REVIEW_SHA256 = (
    "7524b1db67e5d2b4d8e15801a589b1d4b05225229bdddc0b292c82005dd05340"
)
EXPECTED_FEASIBILITY_RESULT_DOCUMENT_SHA256 = (
    "4d18d88c525c2539e27bc36aa99c29ba7a0e154d768542172c8f0943e946f63c"
)
EXPECTED_PROTOCOL_SHA256 = (
    "81074ffcd8213fcf86c44e5f118293936632b279602b5750a67332848d6fd865"
)
EXPECTED_COMPONENT_SHA256 = (
    "5355bb5d8e672d539776fc88705f2864b4974a767b12aaabfd4615aeb42288b3"
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_derivatives_context_hypothesis(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "feasibility_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_FEASIBILITY_PROTOCOL_V1.md",
        "feasibility_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_feasibility.py",
        "feasibility_review": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_feasibility_review.py",
        "feasibility_result_document": root
        / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_FEASIBILITY_ATTEMPT_1_RESULT.md",
        "protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_LEARNING_HYPOTHESIS_PROTOCOL_V1.md",
        "component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_hypothesis.py",
    }
    expected = {
        "feasibility_protocol": EXPECTED_FEASIBILITY_PROTOCOL_SHA256,
        "feasibility_component": EXPECTED_FEASIBILITY_COMPONENT_SHA256,
        "feasibility_review": EXPECTED_FEASIBILITY_REVIEW_SHA256,
        "feasibility_result_document": EXPECTED_FEASIBILITY_RESULT_DOCUMENT_SHA256,
        "protocol": EXPECTED_PROTOCOL_SHA256,
        "component": EXPECTED_COMPONENT_SHA256,
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, digest in expected.items():
        if observed[name] != digest:
            raise RuntimeError(f"Derivatives-context hypothesis binding mismatch: {name}.")

    declaration = derivatives_context_hypothesis_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Derivatives-context hypothesis parent commit mismatch.")
    if FEASIBILITY_REPORT_SHA256 != EXPECTED_FEASIBILITY_REPORT_SHA256:
        raise RuntimeError("Derivatives-context feasibility evidence mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Derivatives-context hypothesis protocol mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Derivatives-context hypothesis component mismatch.")
    if tuple(declaration["context_feature_order"]) != CONTEXT_FEATURE_COLUMNS:
        raise RuntimeError("Derivatives-context feature registry mismatch.")
    if tuple(declaration["variant_order"]) != tuple(VARIANT_SPECS):
        raise RuntimeError("Derivatives-context variant registry mismatch.")
    if declaration["matched_control"] != MATCHED_CONTROL:
        raise RuntimeError("Derivatives-context matched controls mismatch.")
    if declaration["fold_plan"] != [dict(fold) for fold in FOLD_PLAN]:
        raise RuntimeError("Derivatives-context fold plan mismatch.")
    if not fold_plan_is_causal():
        raise RuntimeError("Derivatives-context fold plan is not causal.")

    required_false = (
        "market_values_opened",
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
        raise RuntimeError("Derivatives-context hypothesis safety boundary mismatch.")
    if declaration["control_variants_candidate_eligible"] is not False:
        raise RuntimeError("Derivatives-context control promotion boundary mismatch.")

    return {
        **declaration,
        "status": STATUS,
        "causal_feature_schema_implemented": True,
        "matched_ablation_design_implemented": True,
        "fold_plan_causal": True,
        "feasibility_protocol_sha256": observed["feasibility_protocol"],
        "feasibility_protocol_sha256_match": True,
        "feasibility_component_sha256": observed["feasibility_component"],
        "feasibility_component_sha256_match": True,
        "feasibility_review_sha256": observed["feasibility_review"],
        "feasibility_review_sha256_match": True,
        "feasibility_result_document_sha256": observed[
            "feasibility_result_document"
        ],
        "feasibility_result_document_sha256_match": True,
        "protocol_sha256": observed["protocol"],
        "protocol_sha256_match": True,
        "component_sha256": observed["component"],
        "component_sha256_match": True,
        "next_stage": "IMPLEMENT_HASH_BOUND_DERIVATIVES_CONTEXT_DATASET_LOCK_AND_READER",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the frozen derivatives-context learning hypothesis."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(json.dumps(review_derivatives_context_hypothesis(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
