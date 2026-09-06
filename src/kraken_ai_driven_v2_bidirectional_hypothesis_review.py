"""Static hash and safety review for the frozen bidirectional hypothesis."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_bidirectional_hypothesis import (
        COMPONENT_ID,
        CONTEXT_FEATURE_COLUMNS,
        CONTEXT_FORENSIC_REPORT_SHA256,
        DIRECTION_ORDER,
        FOLD_PLAN,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        SPOT_FEATURE_COLUMNS,
        VARIANT_SPECS,
        bidirectional_hypothesis_declaration,
        fold_plan_is_causal,
    )
except ImportError:  # pragma: no cover
    from .kraken_ai_driven_v2_bidirectional_hypothesis import (
        COMPONENT_ID,
        CONTEXT_FEATURE_COLUMNS,
        CONTEXT_FORENSIC_REPORT_SHA256,
        DIRECTION_ORDER,
        FOLD_PLAN,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        SPOT_FEATURE_COLUMNS,
        VARIANT_SPECS,
        bidirectional_hypothesis_declaration,
        fold_plan_is_causal,
    )


SCHEMA_VERSION = 1
STATUS = "KRAKEN_AI_V2_BIDIRECTIONAL_DEVELOPMENT_HYPOTHESIS_REVIEWED_RUNNER_REQUIRED"
EXPECTED_PARENT_COMMIT = "bde314d47e30804a7380493f959f61e8f3a40212"
EXPECTED_CONTEXT_FORENSIC_REPORT_SHA256 = (
    "ed4ee096a9d45eee4d1ee0970dbb062473e74c9caad3597f20eda17cb4dba91f"
)
EXPECTED_CONTEXT_LEARNING_RESULT_SHA256 = (
    "16c357ecde8104dfd8aee920219b56b3748e9cb522e100ec122f568720e16f4a"
)
EXPECTED_CONTEXT_FORENSIC_PROTOCOL_SHA256 = (
    "da1acc2eb4aba5ed7e1f84e8438e09bd5b60fb448e1afd5285a21cca5af8eebe"
)
EXPECTED_CONTEXT_FORENSIC_COMPONENT_SHA256 = (
    "a40b1f9b0a5058901a029ceecea7e24b5b8870e0b04957ca9382df421afced2d"
)
EXPECTED_CONTEXT_FORENSIC_REVIEW_SHA256 = (
    "89955449c30f6334d310d723ce6b4e91aa2e2f57e96c99c731223013f988e0f6"
)
EXPECTED_CONTEXT_FORENSIC_RESULT_SHA256 = (
    "4898f0cd92f54af92047753f3afede8d36031ed4f9d36667cf68c483de7fed6a"
)
EXPECTED_PROTOCOL_SHA256 = (
    "66e58f29c848f3843b4c07df2d42f194e15aebda4ad1ae9c49b755e6ace199dd"
)
EXPECTED_COMPONENT_SHA256 = (
    "68e9a61e0614e7159a2f5279e4158bc9a6c781c61061b5458a67ff9dd8d8a80c"
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_bidirectional_hypothesis(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "context_learning_result": root
        / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_ATTEMPT_1_RESULT.md",
        "context_forensic_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_CONTEXT_SCORE_FORENSIC_REVIEW_PROTOCOL_V1.md",
        "context_forensic_component": root
        / "src"
        / "kraken_ai_driven_v2_context_score_forensic_review.py",
        "context_forensic_review": root
        / "src"
        / "kraken_ai_driven_v2_context_score_forensic_review_review.py",
        "context_forensic_result": root
        / "KRAKEN_AI_DRIVEN_V2_CONTEXT_SCORE_FORENSIC_REVIEW_ATTEMPT_1_RESULT.md",
        "protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_DEVELOPMENT_HYPOTHESIS_PROTOCOL_V1.md",
        "component": root / "src" / "kraken_ai_driven_v2_bidirectional_hypothesis.py",
    }
    expected = {
        "context_learning_result": EXPECTED_CONTEXT_LEARNING_RESULT_SHA256,
        "context_forensic_protocol": EXPECTED_CONTEXT_FORENSIC_PROTOCOL_SHA256,
        "context_forensic_component": EXPECTED_CONTEXT_FORENSIC_COMPONENT_SHA256,
        "context_forensic_review": EXPECTED_CONTEXT_FORENSIC_REVIEW_SHA256,
        "context_forensic_result": EXPECTED_CONTEXT_FORENSIC_RESULT_SHA256,
        "protocol": EXPECTED_PROTOCOL_SHA256,
        "component": EXPECTED_COMPONENT_SHA256,
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, digest in expected.items():
        if observed[name] != digest:
            raise RuntimeError(f"Bidirectional hypothesis binding mismatch: {name}.")

    declaration = bidirectional_hypothesis_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Bidirectional hypothesis parent commit mismatch.")
    if CONTEXT_FORENSIC_REPORT_SHA256 != EXPECTED_CONTEXT_FORENSIC_REPORT_SHA256:
        raise RuntimeError("Context forensic evidence mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID or declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Bidirectional hypothesis identity mismatch.")
    if tuple(declaration["direction_order"]) != DIRECTION_ORDER:
        raise RuntimeError("Bidirectional direction registry mismatch.")
    if tuple(declaration["spot_feature_order"]) != SPOT_FEATURE_COLUMNS:
        raise RuntimeError("Bidirectional spot feature registry mismatch.")
    if tuple(declaration["context_feature_order"]) != CONTEXT_FEATURE_COLUMNS:
        raise RuntimeError("Bidirectional context feature registry mismatch.")
    if tuple(declaration["variant_order"]) != tuple(VARIANT_SPECS):
        raise RuntimeError("Bidirectional variant registry mismatch.")
    if declaration["matched_control"] != MATCHED_CONTROL:
        raise RuntimeError("Bidirectional matched control mismatch.")
    if declaration["fold_plan"] != [dict(fold) for fold in FOLD_PLAN] or not fold_plan_is_causal():
        raise RuntimeError("Bidirectional fold plan mismatch.")
    if declaration["maximum_fold_model_fits"] != 12:
        raise RuntimeError("Bidirectional model-fit budget mismatch.")
    if declaration["new_indicator_count"] != 0:
        raise RuntimeError("Bidirectional hypothesis added an unregistered indicator.")

    required_false = (
        "market_values_opened",
        "labels_generated",
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
        raise RuntimeError("Bidirectional hypothesis safety boundary mismatch.")

    return {
        **declaration,
        "status": STATUS,
        "context_forensic_human_review_recorded": True,
        "long_only_derivatives_context_closed": True,
        "symmetric_long_short_labels_implemented": True,
        "same_bar_stop_first_implemented": True,
        "positive_maximum_action_rule_implemented": True,
        "fold_plan_causal": True,
        "source_sha256_matches": {name: True for name in observed},
        "context_forensic_result_document_sha256": observed["context_forensic_result"],
        "protocol_sha256": observed["protocol"],
        "protocol_sha256_match": True,
        "component_sha256": observed["component"],
        "component_sha256_match": True,
        "next_stage": "IMPLEMENT_HASH_BOUND_BIDIRECTIONAL_DEVELOPMENT_LEARNING_RUNNER",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review the frozen bidirectional hypothesis.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(json.dumps(review_bidirectional_hypothesis(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
