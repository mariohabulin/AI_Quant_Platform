"""Nonexecuting review declaration for the first Kraken AI-driven v2 layer."""

import argparse
import hashlib
import json
from pathlib import Path


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1"
DATASET_ID = (
    "kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2"
)
DATASET_MANIFEST_SHA256 = (
    "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
)
V1_SELECTION_SCHEDULE_SHA256 = (
    "3e805044356777f0bdfa2901db267d714c1e14d11415dd4686acaaaed92f1042"
)
V1_BTC_EPISODE_EVIDENCE_SHA256 = (
    "56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60"
)
V1_CLOSEOUT_NORMALIZED_SHA256 = (
    "d5cd90987f943ddd62c7a63780eab9abe60c9bb850aeb16180cb2cf2c401db72"
)
FEATURE_PROTOCOL_NORMALIZED_SHA256 = (
    "cd387d4fa07f55b45004ccddb40bf53932882e1af7ef1d413101ed9a982aefd5"
)
FEATURE_COMPONENT_NORMALIZED_SHA256 = (
    "4a00ce71f96a1c17c6ec04b9d5e5befb9e5a94a78e3695fa4bffc35030769893"
)
DEFAULT_V1_CLOSEOUT_PATH = Path(
    "KRAKEN_BTC_SUPERVISED_BLINDED_REPLAY_EPISODE_01_CLOSEOUT_V1.md"
)
DEFAULT_FEATURE_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_CAUSAL_FEATURE_PROTOCOL_V1.md"
)
DEFAULT_FEATURE_COMPONENT_PATH = Path("src/kraken_ai_driven_v2_features.py")


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read AI-driven v2 review input: {path}") from exc
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


def load_v1_closeout(path=DEFAULT_V1_CLOSEOUT_PATH):
    return _load_hash_bound_text(
        path,
        V1_CLOSEOUT_NORMALIZED_SHA256,
        (
            "V1_PAUSED_AFTER_SINGLE_BTC_EPISODE_NO_PERFORMANCE",
            V1_SELECTION_SCHEDULE_SHA256,
            V1_BTC_EPISODE_EVIDENCE_SHA256,
            "additional supervised v1 replay authorized: `false`",
        ),
        "Supervised v1 closeout",
    )


def load_feature_protocol(path=DEFAULT_FEATURE_PROTOCOL_PATH):
    return _load_hash_bound_text(
        path,
        FEATURE_PROTOCOL_NORMALIZED_SHA256,
        (
            "AI_DRIVEN_V2_CAUSAL_FEATURE_CONTRACT_REVIEWED_SYNTHETIC_TESTS_ONLY",
            PROTOCOL_ID,
            DATASET_MANIFEST_SHA256,
            "FLAT -> ARMED -> LONG -> FLAT",
            "production feature parameters frozen: `false`",
        ),
        "AI-driven v2 feature protocol",
    )


def load_feature_component(path=DEFAULT_FEATURE_COMPONENT_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != FEATURE_COMPONENT_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 feature component SHA256 mismatch: "
            f"{digest} != {FEATURE_COMPONENT_NORMALIZED_SHA256}."
        )
    return digest


def review_declaration(
    v1_closeout_path=DEFAULT_V1_CLOSEOUT_PATH,
    feature_protocol_path=DEFAULT_FEATURE_PROTOCOL_PATH,
    feature_component_path=DEFAULT_FEATURE_COMPONENT_PATH,
):
    _, closeout_digest = load_v1_closeout(v1_closeout_path)
    _, protocol_digest = load_feature_protocol(feature_protocol_path)
    component_digest = load_feature_component(feature_component_path)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "KRAKEN_AI_DRIVEN_V2_CAUSAL_FEATURE_CONTRACT_REVIEWED_"
            "STATE_MACHINE_REQUIRED"
        ),
        "protocol_id": PROTOCOL_ID,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "asset_order": ["BTC-USD", "ETH-USD", "XRP-USD"],
        "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
        "v1_selection_schedule_sha256": V1_SELECTION_SCHEDULE_SHA256,
        "v1_btc_episode_evidence_sha256": V1_BTC_EPISODE_EVIDENCE_SHA256,
        "v1_closeout_sha256_match": (
            closeout_digest == V1_CLOSEOUT_NORMALIZED_SHA256
        ),
        "feature_protocol_sha256_match": (
            protocol_digest == FEATURE_PROTOCOL_NORMALIZED_SHA256
        ),
        "feature_component_sha256_match": (
            component_digest == FEATURE_COMPONENT_NORMALIZED_SHA256
        ),
        "v1_btc_episode_completed": True,
        "v1_eth_episode_opened": False,
        "v1_xrp_episode_opened": False,
        "additional_supervised_v1_replay_authorized": False,
        "existing_locked_dataset_reusable": True,
        "dataset_update_required_before_v2_development": False,
        "future_archive_update_requires_new_dataset_identity": True,
        "dataset_opened": False,
        "network_requests_executed": False,
        "causal_feature_component_implemented": True,
        "production_feature_parameters_frozen": False,
        "state_machine_implemented": False,
        "trading_actions_emitted": False,
        "prior_rejected_strategy_reused": False,
        "risk_adapter_implemented": False,
        "performance_evaluation_executed": False,
        "optimization_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review the nonexecuting Kraken AI-driven v2 feature boundary."
    )
    parser.add_argument("--v1-closeout", default=str(DEFAULT_V1_CLOSEOUT_PATH))
    parser.add_argument(
        "--feature-protocol", default=str(DEFAULT_FEATURE_PROTOCOL_PATH)
    )
    parser.add_argument(
        "--feature-component", default=str(DEFAULT_FEATURE_COMPONENT_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    declaration = review_declaration(
        args.v1_closeout,
        args.feature_protocol,
        args.feature_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
