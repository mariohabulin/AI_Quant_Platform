"""Static source-binding review for the derivatives-context feasibility audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_derivatives_context_feasibility import (
        COMPONENT_ID,
        PARENT_COMMIT,
        PARENT_RESULT_SHA256,
        PROTOCOL_ID,
        SOURCE_SERIES,
        derivatives_context_feasibility_declaration,
    )
except ImportError:  # pragma: no cover
    from .kraken_ai_driven_v2_derivatives_context_feasibility import (
        COMPONENT_ID,
        PARENT_COMMIT,
        PARENT_RESULT_SHA256,
        PROTOCOL_ID,
        SOURCE_SERIES,
        derivatives_context_feasibility_declaration,
    )


SCHEMA_VERSION = 1
STATUS = "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_FEASIBILITY_REVIEWED_METADATA_AUDIT_REQUIRED"
EXPECTED_PARENT_COMMIT = "cdb1ccc"
EXPECTED_PARENT_RESULT_SHA256 = (
    "d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703"
)
EXPECTED_PARENT_PROTOCOL_SHA256 = (
    "79125bf45c717c4454403369834d1b8df465596cb03f84831a3588f250a9f3b6"
)
EXPECTED_PARENT_COMPONENT_SHA256 = (
    "b565d5f9bf99347f3573e1abb726cbd81554749e5e8926c86d013221407a1e5f"
)
EXPECTED_PARENT_RESULT_DOCUMENT_SHA256 = (
    "1ff92ff810f5db3deecaebb153d2ad5deba8709685b98cfcd3663c8d92672071"
)
EXPECTED_PROTOCOL_SHA256 = (
    "08523d94d47f9e47f71b30e8f64f8dfd0108cf43cef6b6f36f6db6c9f93d6698"
)
EXPECTED_COMPONENT_SHA256 = (
    "cb9d37eca11a3d7295feecb330d15b3a9417f4d9240a7725f95dd6371b872c6b"
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_derivatives_context_feasibility(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "parent_protocol": root / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ALPHA_RESEARCH_LAB_PROTOCOL_V1.md",
        "parent_component": root / "src" / "kraken_ai_driven_v2_alpha_research_lab.py",
        "parent_result_document": root / "KRAKEN_AI_DRIVEN_V2_ALPHA_RESEARCH_LAB_ATTEMPT_1_RESULT.md",
        "protocol": root / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_FEASIBILITY_PROTOCOL_V1.md",
        "component": root / "src" / "kraken_ai_driven_v2_derivatives_context_feasibility.py",
    }
    expected = {
        "parent_protocol": EXPECTED_PARENT_PROTOCOL_SHA256,
        "parent_component": EXPECTED_PARENT_COMPONENT_SHA256,
        "parent_result_document": EXPECTED_PARENT_RESULT_DOCUMENT_SHA256,
        "protocol": EXPECTED_PROTOCOL_SHA256,
        "component": EXPECTED_COMPONENT_SHA256,
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, digest in expected.items():
        if observed[name] != digest:
            raise RuntimeError(f"Derivatives-context source binding mismatch: {name}.")

    declaration = derivatives_context_feasibility_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Derivatives-context parent commit mismatch.")
    if PARENT_RESULT_SHA256 != EXPECTED_PARENT_RESULT_SHA256:
        raise RuntimeError("Derivatives-context parent result mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Derivatives-context protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Derivatives-context component identity mismatch.")
    if tuple(declaration["source_series_order"]) != tuple(SOURCE_SERIES):
        raise RuntimeError("Derivatives-context source registry mismatch.")
    required_false = (
        "market_values_opened",
        "ohlcvt_values_opened",
        "labels_generated",
        "model_training_executed",
        "hyperparameter_sweep_executed",
        "automatic_model_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    if any(declaration[field] is not False for field in required_false):
        raise RuntimeError("Derivatives-context safety boundary mismatch.")

    return {
        **declaration,
        "status": STATUS,
        "parent_protocol_sha256": observed["parent_protocol"],
        "parent_protocol_sha256_match": True,
        "parent_component_sha256": observed["parent_component"],
        "parent_component_sha256_match": True,
        "parent_result_document_sha256": observed["parent_result_document"],
        "parent_result_document_sha256_match": True,
        "protocol_sha256": observed["protocol"],
        "protocol_sha256_match": True,
        "component_sha256": observed["component"],
        "component_sha256_match": True,
        "next_stage": "RUN_READ_ONLY_PUBLIC_OBJECT_METADATA_FEASIBILITY_AUDIT",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the derivatives-context metadata audit component."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(json.dumps(review_derivatives_context_feasibility(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
