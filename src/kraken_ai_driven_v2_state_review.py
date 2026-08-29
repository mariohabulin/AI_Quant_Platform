"""Nonexecuting review for the Kraken AI-driven v2 signal state milestone."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_state_machine import PARAMETER_SET_ID
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_state_machine import PARAMETER_SET_ID


SCHEMA_VERSION = 1
STATE_PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-state-machine-v1"
FEATURE_PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1"
)
DATASET_ID = (
    "kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2"
)
DATASET_MANIFEST_SHA256 = (
    "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
)
V1_BTC_EPISODE_EVIDENCE_SHA256 = (
    "56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60"
)
FEATURE_PROTOCOL_NORMALIZED_SHA256 = (
    "cd387d4fa07f55b45004ccddb40bf53932882e1af7ef1d413101ed9a982aefd5"
)
FEATURE_COMPONENT_NORMALIZED_SHA256 = (
    "4a00ce71f96a1c17c6ec04b9d5e5befb9e5a94a78e3695fa4bffc35030769893"
)
STATE_PROTOCOL_NORMALIZED_SHA256 = (
    "816553684ae3ab6a93b5f0499b61224eebc2bb9808d85d0c1e5c78247931e792"
)
STATE_COMPONENT_NORMALIZED_SHA256 = (
    "72339aaaa21346e5ac0001581eb0a363c7e1a5743f22e0c322ddfa2ac3f7f326"
)
DEFAULT_FEATURE_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_CAUSAL_FEATURE_PROTOCOL_V1.md"
)
DEFAULT_FEATURE_COMPONENT_PATH = Path("src/kraken_ai_driven_v2_features.py")
DEFAULT_STATE_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_STATE_MACHINE_PROTOCOL_V1.md"
)
DEFAULT_STATE_COMPONENT_PATH = Path("src/kraken_ai_driven_v2_state_machine.py")


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read AI-driven v2 state review input: {path}") from exc
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


def load_feature_protocol(path=DEFAULT_FEATURE_PROTOCOL_PATH):
    return _load_hash_bound_text(
        path,
        FEATURE_PROTOCOL_NORMALIZED_SHA256,
        (
            "AI_DRIVEN_V2_CAUSAL_FEATURE_CONTRACT_REVIEWED_SYNTHETIC_TESTS_ONLY",
            FEATURE_PROTOCOL_ID,
            DATASET_MANIFEST_SHA256,
            "production feature parameters frozen: `false`",
        ),
        "AI-driven v2 feature protocol",
    )


def load_state_protocol(path=DEFAULT_STATE_PROTOCOL_PATH):
    return _load_hash_bound_text(
        path,
        STATE_PROTOCOL_NORMALIZED_SHA256,
        (
            "AI_DRIVEN_V2_STATE_MACHINE_REVIEWED_SYNTHETIC_TESTS_ONLY",
            STATE_PROTOCOL_ID,
            PARAMETER_SET_ID,
            "FLAT -> ARMED -> LONG -> FLAT",
            "risk adapter implemented: `false`",
        ),
        "AI-driven v2 state protocol",
    )


def _load_component(path, expected_sha256, label):
    digest = normalized_text_sha256(path)
    if digest != expected_sha256:
        raise RuntimeError(
            f"{label} SHA256 mismatch: {digest} != {expected_sha256}."
        )
    return digest


def review_declaration(
    feature_protocol_path=DEFAULT_FEATURE_PROTOCOL_PATH,
    feature_component_path=DEFAULT_FEATURE_COMPONENT_PATH,
    state_protocol_path=DEFAULT_STATE_PROTOCOL_PATH,
    state_component_path=DEFAULT_STATE_COMPONENT_PATH,
):
    _, feature_protocol_digest = load_feature_protocol(feature_protocol_path)
    feature_component_digest = _load_component(
        feature_component_path,
        FEATURE_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 feature component",
    )
    _, state_protocol_digest = load_state_protocol(state_protocol_path)
    state_component_digest = _load_component(
        state_component_path,
        STATE_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 state component",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "KRAKEN_AI_DRIVEN_V2_STATE_MACHINE_REVIEWED_"
            "RISK_EXECUTION_REQUIRED"
        ),
        "state_protocol_id": STATE_PROTOCOL_ID,
        "feature_protocol_id": FEATURE_PROTOCOL_ID,
        "parameter_set_id": PARAMETER_SET_ID,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "asset_order": ["BTC-USD", "ETH-USD", "XRP-USD"],
        "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
        "v1_btc_episode_evidence_sha256": V1_BTC_EPISODE_EVIDENCE_SHA256,
        "feature_protocol_sha256_match": (
            feature_protocol_digest == FEATURE_PROTOCOL_NORMALIZED_SHA256
        ),
        "feature_component_sha256_match": (
            feature_component_digest == FEATURE_COMPONENT_NORMALIZED_SHA256
        ),
        "state_protocol_sha256_match": (
            state_protocol_digest == STATE_PROTOCOL_NORMALIZED_SHA256
        ),
        "state_component_sha256_match": (
            state_component_digest == STATE_COMPONENT_NORMALIZED_SHA256
        ),
        "causal_feature_component_implemented": True,
        "reference_state_parameters_frozen": True,
        "deterministic_state_machine_implemented": True,
        "state_path": ["FLAT", "ARMED", "LONG", "FLAT"],
        "action_intents_emitted": True,
        "action_intents_are_fills": False,
        "real_order_fills_executed": False,
        "risk_adapter_implemented": False,
        "dataset_opened": False,
        "real_data_state_run_executed": False,
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
        description="Review the nonexecuting Kraken AI-driven v2 state boundary."
    )
    parser.add_argument(
        "--feature-protocol", default=str(DEFAULT_FEATURE_PROTOCOL_PATH)
    )
    parser.add_argument(
        "--feature-component", default=str(DEFAULT_FEATURE_COMPONENT_PATH)
    )
    parser.add_argument("--state-protocol", default=str(DEFAULT_STATE_PROTOCOL_PATH))
    parser.add_argument(
        "--state-component", default=str(DEFAULT_STATE_COMPONENT_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    declaration = review_declaration(
        args.feature_protocol,
        args.feature_component,
        args.state_protocol,
        args.state_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
