"""Hash-bound nonexecuting review of the Kraken V2 hybrid discovery contract."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_strategy_discovery import (
        ASSET_ORDER,
        DISCOVERY_BUDGET,
        FAMILY_CATALOG,
        HYBRID_ARCHITECTURE_MODE,
        PROTOCOL_ID,
        REFERENCE_A_REPORT_SHA256,
        REGIME_CATALOG,
        STATUS,
        discovery_protocol_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_strategy_discovery import (
        ASSET_ORDER,
        DISCOVERY_BUDGET,
        FAMILY_CATALOG,
        HYBRID_ARCHITECTURE_MODE,
        PROTOCOL_ID,
        REFERENCE_A_REPORT_SHA256,
        REGIME_CATALOG,
        STATUS,
        discovery_protocol_declaration,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_HYBRID_DISCOVERY_PROTOCOL_REVIEWED_"
    "HYPOTHESIS_MANIFEST_REQUIRED"
)
DISCOVERY_PROTOCOL_NORMALIZED_SHA256 = (
    "66e3148924965ecbc32954c76eb122ee6f74f7454ae88a4e8ddf7a28cf8d54cb"
)
DISCOVERY_COMPONENT_NORMALIZED_SHA256 = (
    "846fb4d1e096e1ff2d79f579ab0c603a03bbdc527e7492ec20e2c7dfc37b85f6"
)
COMPONENT_BINDINGS = (
    {
        "label": "AI-driven v2 Reference A closure protocol",
        "path": "KRAKEN_AI_DRIVEN_V2_DEVELOPMENT_REFERENCE_A_CLOSURE.md",
        "sha256": "ca832d559aebf7b15ab2e882d8f52f40e1c43b6defd88aa72b99ef4e8d3684ed",
    },
    {
        "label": "AI-driven v2 Reference A closure component",
        "path": "src/kraken_ai_driven_v2_development_closure.py",
        "sha256": "10b17790fc57cae1f4b15fb312e3596f759f13b8e5dd7ecbb7090a6881756cef",
    },
    {
        "label": "AI-driven v2 risk/execution protocol",
        "path": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_RISK_EXECUTION_PROTOCOL_V1.md",
        "sha256": "ff8729dd6b53aa992a70a2fae4960c592088d1d14b4f017659f5e0607d005b1f",
    },
    {
        "label": "AI-driven v2 risk/execution component",
        "path": "src/kraken_ai_driven_v2_risk_execution.py",
        "sha256": "2629880a0100b1b6afd2eed4516db91893b2f6668a8aa5f0e54077eb6930daea",
    },
    {
        "label": "AI-driven v2 partition protocol",
        "path": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_PARTITION_PROTOCOL_V1.md",
        "sha256": "091d64ca9b7f80f8f3ebae2f3038b78cc305f49b19042a159a8e9050db5476ac",
    },
    {
        "label": "AI-driven v2 partition component",
        "path": "src/kraken_ai_driven_v2_partition.py",
        "sha256": "337d44259a05d1d7b10a3b81f636f776f0752411eab0bb239e8cf7f485da5a37",
    },
)
DEFAULT_DISCOVERY_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_STRATEGY_DISCOVERY_LEARNING_PROTOCOL_V1.md"
)
DEFAULT_DISCOVERY_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_strategy_discovery.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 discovery review input: {path}"
        ) from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _load_exact(path, expected_sha256, label):
    digest = normalized_text_sha256(path)
    if digest != expected_sha256:
        raise RuntimeError(
            f"{label} SHA256 mismatch: {digest} != {expected_sha256}."
        )
    return digest


def load_discovery_protocol(path=DEFAULT_DISCOVERY_PROTOCOL_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != DISCOVERY_PROTOCOL_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 discovery protocol SHA256 mismatch: "
            f"{digest} != {DISCOVERY_PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        STATUS,
        PROTOCOL_ID,
        HYBRID_ARCHITECTURE_MODE.split("_")[0].lower(),
        "shared catalog, asset/regime-specific routing",
        "HOLD_CASH",
        "six hypotheses",
        "runtime learning",
        "calibration data opened: `false`",
        "evaluation data opened: `false`",
        REFERENCE_A_REPORT_SHA256,
        "Candidate v2",
    )
    if any(value not in text for value in required):
        raise RuntimeError(
            "AI-driven v2 discovery protocol required contract text is missing."
        )
    return text, digest


def review_declaration(
    closure_protocol_path=Path(COMPONENT_BINDINGS[0]["path"]),
    closure_component_path=Path(COMPONENT_BINDINGS[1]["path"]),
    risk_protocol_path=Path(COMPONENT_BINDINGS[2]["path"]),
    risk_component_path=Path(COMPONENT_BINDINGS[3]["path"]),
    partition_protocol_path=Path(COMPONENT_BINDINGS[4]["path"]),
    partition_component_path=Path(COMPONENT_BINDINGS[5]["path"]),
    *,
    discovery_protocol_path=DEFAULT_DISCOVERY_PROTOCOL_PATH,
    discovery_component_path=DEFAULT_DISCOVERY_COMPONENT_PATH,
):
    paths = (
        closure_protocol_path,
        closure_component_path,
        risk_protocol_path,
        risk_component_path,
        partition_protocol_path,
        partition_component_path,
    )
    binding_matches = {}
    for binding, path in zip(COMPONENT_BINDINGS, paths):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]
    _, protocol_digest = load_discovery_protocol(discovery_protocol_path)
    component_digest = _load_exact(
        discovery_component_path,
        DISCOVERY_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 discovery component",
    )
    contract = discovery_protocol_declaration()
    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "discovery_protocol_status": contract["status"],
        "protocol_id": contract["protocol_id"],
        "architecture_mode": contract["architecture_mode"],
        "asset_order": list(ASSET_ORDER),
        "strategy_family_count": len(FAMILY_CATALOG),
        "regime_count": len(REGIME_CATALOG),
        "discovery_budget": dict(DISCOVERY_BUDGET),
        "reference_a_report_sha256": REFERENCE_A_REPORT_SHA256,
        "reference_a_closed": True,
        "reference_a_rerun_authorized": False,
        "source_binding_matches": binding_matches,
        "discovery_protocol_sha256_match": (
            protocol_digest == DISCOVERY_PROTOCOL_NORMALIZED_SHA256
        ),
        "discovery_component_sha256_match": (
            component_digest == DISCOVERY_COMPONENT_NORMALIZED_SHA256
        ),
        "hybrid_routing_contract_implemented": True,
        "bounded_manifest_validator_implemented": True,
        "shared_safety_envelope_frozen": True,
        "offline_versioned_feedback_contract_frozen": True,
        "hold_cash_is_valid_action": True,
        "hypothesis_manifest_registered": False,
        "strategy_components_implemented": False,
        "discovery_runner_implemented": False,
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_run_authorized": False,
        "performance_evaluation_executed": False,
        "parameter_sweep_authorized": False,
        "automatic_ranking_authorized": False,
        "automatic_strategy_selection_authorized": False,
        "runtime_learning_authorized": False,
        "calibration_authorized": False,
        "evaluation_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
        "next_stage": "PRE_REGISTER_BOUNDED_HYBRID_DISCOVERY_ROUND_1",
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review the nonexecuting Kraken V2 hybrid discovery contract."
    )
    for index, binding in enumerate(COMPONENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument(
        "--discovery-protocol", default=str(DEFAULT_DISCOVERY_PROTOCOL_PATH)
    )
    parser.add_argument(
        "--discovery-component", default=str(DEFAULT_DISCOVERY_COMPONENT_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(6)]
    declaration = review_declaration(
        *binding_paths,
        discovery_protocol_path=args.discovery_protocol,
        discovery_component_path=args.discovery_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
