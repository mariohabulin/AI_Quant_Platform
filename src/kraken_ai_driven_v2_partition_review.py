"""Nonexecuting review for the Kraken AI-driven v2 partition milestone."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_partition import (
        ASSET_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        PARTITION_ORDER,
        PARTITION_PROTOCOL_ID,
        REFERENCE_PARTITION_CONTRACT,
        V1_BTC_EPISODE_EVIDENCE_SHA256,
    )
    from kraken_ai_driven_v2_risk_execution import (
        COST_PROFILE_ID,
        RISK_EXECUTION_POLICY_ID,
    )
    from kraken_ai_driven_v2_risk_execution_review import (
        RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256,
        RISK_EXECUTION_PROTOCOL_ID,
        RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_partition import (
        ASSET_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        PARTITION_ORDER,
        PARTITION_PROTOCOL_ID,
        REFERENCE_PARTITION_CONTRACT,
        V1_BTC_EPISODE_EVIDENCE_SHA256,
    )
    from .kraken_ai_driven_v2_risk_execution import (
        COST_PROFILE_ID,
        RISK_EXECUTION_POLICY_ID,
    )
    from .kraken_ai_driven_v2_risk_execution_review import (
        RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256,
        RISK_EXECUTION_PROTOCOL_ID,
        RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256,
    )


SCHEMA_VERSION = 1
PARTITION_PROTOCOL_NORMALIZED_SHA256 = (
    "091d64ca9b7f80f8f3ebae2f3038b78cc305f49b19042a159a8e9050db5476ac"
)
PARTITION_COMPONENT_NORMALIZED_SHA256 = (
    "337d44259a05d1d7b10a3b81f636f776f0752411eab0bb239e8cf7f485da5a37"
)
DEFAULT_RISK_EXECUTION_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_RISK_EXECUTION_PROTOCOL_V1.md"
)
DEFAULT_RISK_EXECUTION_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_risk_execution.py"
)
DEFAULT_PARTITION_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_PARTITION_PROTOCOL_V1.md"
)
DEFAULT_PARTITION_COMPONENT_PATH = Path("src/kraken_ai_driven_v2_partition.py")


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 partition review input: {path}"
        ) from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _load_hash_bound_text(path, expected_sha256, required, label):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(
            f"{label} SHA256 mismatch: {digest} != {expected_sha256}."
        )
    text = raw.decode("utf-8")
    if any(value not in text for value in required):
        raise RuntimeError(f"{label} required contract text is missing.")
    return text, digest


def load_risk_execution_protocol(path=DEFAULT_RISK_EXECUTION_PROTOCOL_PATH):
    return _load_hash_bound_text(
        path,
        RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256,
        (
            "AI_DRIVEN_V2_RISK_EXECUTION_REVIEWED_SYNTHETIC_TESTS_ONLY",
            RISK_EXECUTION_PROTOCOL_ID,
            RISK_EXECUTION_POLICY_ID,
            COST_PROFILE_ID,
            "external dataset opened: `false`",
            "live execution authorized: `false`",
        ),
        "AI-driven v2 risk/execution protocol",
    )


def load_partition_protocol(path=DEFAULT_PARTITION_PROTOCOL_PATH):
    return _load_hash_bound_text(
        path,
        PARTITION_PROTOCOL_NORMALIZED_SHA256,
        (
            "AI_DRIVEN_V2_PARTITION_PROTOCOL_REVIEWED_SYNTHETIC_TESTS_ONLY",
            PARTITION_PROTOCOL_ID,
            DATASET_ID,
            DATASET_MANIFEST_SHA256,
            "2025-04-01T00:00:00Z",
            "sealed one-time evaluation",
            "development data opened: `false`",
            "live execution",
        ),
        "AI-driven v2 partition protocol",
    )


def _load_component(path, expected_sha256, label):
    digest = normalized_text_sha256(path)
    if digest != expected_sha256:
        raise RuntimeError(
            f"{label} SHA256 mismatch: {digest} != {expected_sha256}."
        )
    return digest


def review_declaration(
    risk_execution_protocol_path=DEFAULT_RISK_EXECUTION_PROTOCOL_PATH,
    risk_execution_component_path=DEFAULT_RISK_EXECUTION_COMPONENT_PATH,
    partition_protocol_path=DEFAULT_PARTITION_PROTOCOL_PATH,
    partition_component_path=DEFAULT_PARTITION_COMPONENT_PATH,
):
    _, risk_protocol_digest = load_risk_execution_protocol(
        risk_execution_protocol_path
    )
    risk_component_digest = _load_component(
        risk_execution_component_path,
        RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 risk/execution component",
    )
    _, partition_protocol_digest = load_partition_protocol(
        partition_protocol_path
    )
    partition_component_digest = _load_component(
        partition_component_path,
        PARTITION_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 partition component",
    )
    contract = REFERENCE_PARTITION_CONTRACT
    windows = {window.name: window for window in contract.windows}
    plan = contract.configuration()
    return {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "KRAKEN_AI_DRIVEN_V2_PARTITION_PROTOCOL_REVIEWED_"
            "DEVELOPMENT_RUNNER_REQUIRED"
        ),
        "partition_protocol_id": PARTITION_PROTOCOL_ID,
        "partition_plan_sha256": contract.plan_sha256(),
        "risk_execution_protocol_id": RISK_EXECUTION_PROTOCOL_ID,
        "risk_execution_policy_id": RISK_EXECUTION_POLICY_ID,
        "cost_profile_id": COST_PROFILE_ID,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "asset_order": list(ASSET_ORDER),
        "partition_order": list(PARTITION_ORDER),
        "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
        "v1_btc_episode_evidence_sha256": V1_BTC_EPISODE_EVIDENCE_SHA256,
        "v1_btc_episode_partition": "CALIBRATION",
        "v1_btc_episode_is_unseen": False,
        "risk_execution_protocol_sha256_match": (
            risk_protocol_digest == RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256
        ),
        "risk_execution_component_sha256_match": (
            risk_component_digest == RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256
        ),
        "partition_protocol_sha256_match": (
            partition_protocol_digest == PARTITION_PROTOCOL_NORMALIZED_SHA256
        ),
        "partition_component_sha256_match": (
            partition_component_digest == PARTITION_COMPONENT_NORMALIZED_SHA256
        ),
        "development_start_utc": windows["DEVELOPMENT"].start_utc,
        "development_end_exclusive_utc": (
            windows["DEVELOPMENT"].end_exclusive_utc
        ),
        "calibration_start_utc": windows["CALIBRATION"].start_utc,
        "calibration_end_exclusive_utc": (
            windows["CALIBRATION"].end_exclusive_utc
        ),
        "evaluation_start_utc": windows["EVALUATION"].start_utc,
        "evaluation_end_exclusive_utc": (
            windows["EVALUATION"].end_exclusive_utc
        ),
        "expected_calendar_buckets": {
            name: windows[name].expected_calendar_buckets
            for name in PARTITION_ORDER
        },
        "expected_observed_rows": plan["expected_observed_rows"],
        "known_gaps_utc": plan["known_gaps_utc"],
        "evaluation_is_genuinely_untouched": (
            windows["EVALUATION"].genuinely_untouched
        ),
        "partition_boundaries_selected_from_performance": False,
        "state_carry_across_partitions": False,
        "state_carry_across_gaps": False,
        "synthetic_partition_validator_implemented": True,
        "dataset_opened": False,
        "partitions_materialized_from_dataset": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_runner_authorized": False,
        "development_runner_executed": False,
        "network_requests_executed": False,
        "performance_evaluation_executed": False,
        "optimization_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
    }


def _parser():
    parser = argparse.ArgumentParser(
        description=(
            "Review the nonexecuting Kraken AI-driven v2 partition boundary."
        )
    )
    parser.add_argument(
        "--risk-execution-protocol",
        default=str(DEFAULT_RISK_EXECUTION_PROTOCOL_PATH),
    )
    parser.add_argument(
        "--risk-execution-component",
        default=str(DEFAULT_RISK_EXECUTION_COMPONENT_PATH),
    )
    parser.add_argument(
        "--partition-protocol", default=str(DEFAULT_PARTITION_PROTOCOL_PATH)
    )
    parser.add_argument(
        "--partition-component", default=str(DEFAULT_PARTITION_COMPONENT_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    declaration = review_declaration(
        args.risk_execution_protocol,
        args.risk_execution_component,
        args.partition_protocol,
        args.partition_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
