"""Nonexecuting review for the Kraken AI-driven v2 development runner."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_development_runner import (
        AUTHORIZATION_PHRASE,
        DEVELOPMENT_PROTOCOL_ID,
        DEVELOPMENT_RUN_ID,
        INITIAL_CAPITAL,
        development_configuration,
    )
    from kraken_ai_driven_v2_partition import (
        ASSET_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        PARTITION_PROTOCOL_ID,
        REFERENCE_PARTITION_CONTRACT,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_development_runner import (
        AUTHORIZATION_PHRASE,
        DEVELOPMENT_PROTOCOL_ID,
        DEVELOPMENT_RUN_ID,
        INITIAL_CAPITAL,
        development_configuration,
    )
    from .kraken_ai_driven_v2_partition import (
        ASSET_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        PARTITION_PROTOCOL_ID,
        REFERENCE_PARTITION_CONTRACT,
    )


SCHEMA_VERSION = 1
DEVELOPMENT_PROTOCOL_NORMALIZED_SHA256 = (
    "7f9fbec917f3a7cfd3acc9b05d86b329b3d1f03e17ee819e9bcb0c6481b4f7f0"
)
DEVELOPMENT_RUNNER_NORMALIZED_SHA256 = (
    "a82060f438cb97e51bfaf0dc16234a85a48958eed9fe7c6eb275756c1660551f"
)
COMPONENT_BINDINGS = (
    {
        "label": "AI-driven v2 feature protocol",
        "path": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_CAUSAL_FEATURE_PROTOCOL_V1.md",
        "sha256": "cd387d4fa07f55b45004ccddb40bf53932882e1af7ef1d413101ed9a982aefd5",
    },
    {
        "label": "AI-driven v2 feature component",
        "path": "src/kraken_ai_driven_v2_features.py",
        "sha256": "4a00ce71f96a1c17c6ec04b9d5e5befb9e5a94a78e3695fa4bffc35030769893",
    },
    {
        "label": "AI-driven v2 state protocol",
        "path": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_STATE_MACHINE_PROTOCOL_V1.md",
        "sha256": "816553684ae3ab6a93b5f0499b61224eebc2bb9808d85d0c1e5c78247931e792",
    },
    {
        "label": "AI-driven v2 state component",
        "path": "src/kraken_ai_driven_v2_state_machine.py",
        "sha256": "72339aaaa21346e5ac0001581eb0a363c7e1a5743f22e0c322ddfa2ac3f7f326",
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
DEFAULT_DEVELOPMENT_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DEVELOPMENT_RUNNER_PROTOCOL_V1.md"
)
DEFAULT_DEVELOPMENT_RUNNER_PATH = Path(
    "src/kraken_ai_driven_v2_development_runner.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 development review input: {path}"
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


def load_development_protocol(path=DEFAULT_DEVELOPMENT_PROTOCOL_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != DEVELOPMENT_PROTOCOL_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 development protocol SHA256 mismatch: "
            f"{digest} != {DEVELOPMENT_PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        "AI_DRIVEN_V2_DEVELOPMENT_RUNNER_REVIEWED_SYNTHETIC_TESTS_ONLY",
        DEVELOPMENT_PROTOCOL_ID,
        DEVELOPMENT_RUN_ID,
        AUTHORIZATION_PHRASE,
        "2024-04-01T00:00:00Z",
        "calibration data opened: `false`",
        "evaluation data opened: `false`",
        "live execution",
    )
    if any(value not in text for value in required):
        raise RuntimeError(
            "AI-driven v2 development protocol required contract text is missing."
        )
    return text, digest


def review_declaration(
    feature_protocol_path=Path(COMPONENT_BINDINGS[0]["path"]),
    feature_component_path=Path(COMPONENT_BINDINGS[1]["path"]),
    state_protocol_path=Path(COMPONENT_BINDINGS[2]["path"]),
    state_component_path=Path(COMPONENT_BINDINGS[3]["path"]),
    risk_protocol_path=Path(COMPONENT_BINDINGS[4]["path"]),
    risk_component_path=Path(COMPONENT_BINDINGS[5]["path"]),
    partition_protocol_path=Path(COMPONENT_BINDINGS[6]["path"]),
    partition_component_path=Path(COMPONENT_BINDINGS[7]["path"]),
    *,
    development_protocol_path=DEFAULT_DEVELOPMENT_PROTOCOL_PATH,
    development_runner_path=DEFAULT_DEVELOPMENT_RUNNER_PATH,
):
    paths = (
        feature_protocol_path,
        feature_component_path,
        state_protocol_path,
        state_component_path,
        risk_protocol_path,
        risk_component_path,
        partition_protocol_path,
        partition_component_path,
    )
    binding_matches = {}
    for binding, path in zip(COMPONENT_BINDINGS, paths):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]
    _, protocol_digest = load_development_protocol(development_protocol_path)
    runner_digest = _load_exact(
        development_runner_path,
        DEVELOPMENT_RUNNER_NORMALIZED_SHA256,
        "AI-driven v2 development runner",
    )
    configuration = development_configuration()
    return {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "KRAKEN_AI_DRIVEN_V2_DEVELOPMENT_RUNNER_REVIEWED_"
            "EXECUTION_AUTHORIZATION_REQUIRED"
        ),
        "development_protocol_id": DEVELOPMENT_PROTOCOL_ID,
        "development_run_id": DEVELOPMENT_RUN_ID,
        "partition_protocol_id": PARTITION_PROTOCOL_ID,
        "partition_plan_sha256": REFERENCE_PARTITION_CONTRACT.plan_sha256(),
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "asset_order": list(ASSET_ORDER),
        "partition": "DEVELOPMENT",
        "development_start_utc": configuration["development_start_utc"],
        "development_end_exclusive_utc": (
            configuration["development_end_exclusive_utc"]
        ),
        "initial_capital": INITIAL_CAPITAL,
        "quote_currency": configuration["quote_currency"],
        "authorization_phrase": AUTHORIZATION_PHRASE,
        "upstream_binding_matches": binding_matches,
        "development_protocol_sha256_match": (
            protocol_digest == DEVELOPMENT_PROTOCOL_NORMALIZED_SHA256
        ),
        "development_runner_sha256_match": (
            runner_digest == DEVELOPMENT_RUNNER_NORMALIZED_SHA256
        ),
        "development_only_reader_implemented": True,
        "full_asset_files_hashed_as_opaque_bytes": True,
        "nondevelopment_ohlcv_parsing_permitted": False,
        "terminal_synthetic_force_close_permitted": False,
        "one_shot_atomic_evidence_implemented": True,
        "independent_evidence_lock_implemented": True,
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_run_authorized": False,
        "development_run_executed": False,
        "network_requests_executed": False,
        "real_orders_or_fills_executed": False,
        "performance_evaluation_executed": False,
        "parameter_sweep_executed": False,
        "optimization_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review the nonexecuting Kraken AI v2 development runner."
    )
    for index, binding in enumerate(COMPONENT_BINDINGS):
        parser.add_argument(
            f"--binding-{index}",
            default=binding["path"],
        )
    parser.add_argument(
        "--development-protocol",
        default=str(DEFAULT_DEVELOPMENT_PROTOCOL_PATH),
    )
    parser.add_argument(
        "--development-runner",
        default=str(DEFAULT_DEVELOPMENT_RUNNER_PATH),
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(8)]
    declaration = review_declaration(
        *binding_paths,
        development_protocol_path=args.development_protocol,
        development_runner_path=args.development_runner,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
