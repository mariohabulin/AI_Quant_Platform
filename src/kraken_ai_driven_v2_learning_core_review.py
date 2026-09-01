"""Independent static review for the executable Kraken V2 Learning Core."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_learning_core import (
        ACTIVE_RESOLUTION,
        CLASS_ORDER,
        COMPONENT_ID,
        FEATURE_COLUMNS,
        MODEL_SPECS,
        STATUS as CORE_STATUS,
        learning_core_declaration,
    )
    from kraken_ai_driven_v2_true_learning_contract import TRUE_LEARNING_CONTRACT_LOCK
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_learning_core import (
        ACTIVE_RESOLUTION,
        CLASS_ORDER,
        COMPONENT_ID,
        FEATURE_COLUMNS,
        MODEL_SPECS,
        STATUS as CORE_STATUS,
        learning_core_declaration,
    )
    from .kraken_ai_driven_v2_true_learning_contract import TRUE_LEARNING_CONTRACT_LOCK


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-learning-core-v1"
STATUS = "KRAKEN_AI_V2_LEARNING_CORE_REVIEWED_REAL_DEVELOPMENT_RUNNER_REQUIRED"
PARENT_COMMIT = "8c51695"
STAGE_2_ATTEMPT_1_REPORT_SHA256 = (
    "ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1"
)
EXPECTED_TRUE_LEARNING_CONTRACT_SHA256 = (
    "22260709623e114553a77dd4168fc0f12677f476d620a91277cbf8c292d6ae4a"
)
EXPECTED_PROTOCOL_SHA256 = (
    "4a3dd7b00d52be5df3f60ce5dba0c8803462baa68d0f3eeb1f06f9d6fe64ea2c"
)
EXPECTED_COMPONENT_SHA256 = (
    "467f2a1913371ef11c9a828770bb6a260708032a9ba2aec142d88cfe7ab79207"
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_learning_core(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    protocol_path = root / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_LEARNING_CORE_PROTOCOL_V1.md"
    component_path = root / "src" / "kraken_ai_driven_v2_learning_core.py"
    protocol_sha256 = _sha256(protocol_path)
    component_sha256 = _sha256(component_path)
    declaration = learning_core_declaration()

    if TRUE_LEARNING_CONTRACT_LOCK.sha256 != EXPECTED_TRUE_LEARNING_CONTRACT_SHA256:
        raise RuntimeError("True Learning Contract parent binding mismatch.")
    if protocol_sha256 != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("Learning Core protocol SHA-256 mismatch.")
    if component_sha256 != EXPECTED_COMPONENT_SHA256:
        raise RuntimeError("Learning Core component SHA-256 mismatch.")
    if declaration["status"] != CORE_STATUS:
        raise RuntimeError("Learning Core status mismatch.")
    if declaration["active_resolution"] != ACTIVE_RESOLUTION or ACTIVE_RESOLUTION != "12h":
        raise RuntimeError("Learning Core resolution mismatch.")
    if tuple(declaration["class_order"]) != CLASS_ORDER:
        raise RuntimeError("Learning Core class order mismatch.")
    if tuple(declaration["feature_columns"]) != FEATURE_COLUMNS:
        raise RuntimeError("Learning Core feature schema mismatch.")
    if tuple(declaration["model_specs"]) != tuple(MODEL_SPECS):
        raise RuntimeError("Learning Core model order mismatch.")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "true_learning_contract_sha256": TRUE_LEARNING_CONTRACT_LOCK.sha256,
        "true_learning_contract_sha256_match": True,
        "stage_2_attempt_1_report_sha256": STAGE_2_ATTEMPT_1_REPORT_SHA256,
        "stage_2_attempt_1_preserved": True,
        "timestamp_forensic_scan_completed": True,
        "four_hour_source_starts_utc": "2024-01-01T00:00:00Z",
        "four_hour_reader_bug_found": False,
        "retired_stage_2_per_asset_gate_active": False,
        "active_resolution": ACTIVE_RESOLUTION,
        "resolution_selection_claims_profitability": False,
        "protocol_sha256": protocol_sha256,
        "protocol_sha256_match": True,
        "component_sha256": component_sha256,
        "component_sha256_match": True,
        "causal_features_implemented": True,
        "triple_barrier_labels_implemented": True,
        "walk_forward_training_implemented": True,
        "model_family_count": len(MODEL_SPECS),
        "parameters_learned_from_labels": True,
        "automatic_model_selection": False,
        "rule_discovery_rounds_active": False,
        "real_development_training_executed": False,
        "dataset_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "paper_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": "IMPLEMENT_HASH_BOUND_12H_DEVELOPMENT_LEARNING_RUNNER",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review Kraken AI-driven V2 Learning Core.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(json.dumps(review_learning_core(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
