"""Nonexecuting review for the Kraken AI-driven v2 risk/execution milestone."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_risk_execution import (
        COST_PROFILE_ID,
        REFERENCE_COST_PROFILE,
        REFERENCE_RISK_EXECUTION_POLICY,
        RISK_EXECUTION_POLICY_ID,
    )
    from kraken_ai_driven_v2_state_machine import PARAMETER_SET_ID
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_risk_execution import (
        COST_PROFILE_ID,
        REFERENCE_COST_PROFILE,
        REFERENCE_RISK_EXECUTION_POLICY,
        RISK_EXECUTION_POLICY_ID,
    )
    from .kraken_ai_driven_v2_state_machine import PARAMETER_SET_ID


SCHEMA_VERSION = 1
RISK_EXECUTION_PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-risk-execution-v1"
)
STATE_PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-state-machine-v1"
DATASET_ID = (
    "kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2"
)
DATASET_MANIFEST_SHA256 = (
    "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
)
V1_BTC_EPISODE_EVIDENCE_SHA256 = (
    "56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60"
)
STATE_PROTOCOL_NORMALIZED_SHA256 = (
    "816553684ae3ab6a93b5f0499b61224eebc2bb9808d85d0c1e5c78247931e792"
)
STATE_COMPONENT_NORMALIZED_SHA256 = (
    "72339aaaa21346e5ac0001581eb0a363c7e1a5743f22e0c322ddfa2ac3f7f326"
)
RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256 = (
    "ff8729dd6b53aa992a70a2fae4960c592088d1d14b4f017659f5e0607d005b1f"
)
RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256 = (
    "2629880a0100b1b6afd2eed4516db91893b2f6668a8aa5f0e54077eb6930daea"
)
DEFAULT_STATE_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_STATE_MACHINE_PROTOCOL_V1.md"
)
DEFAULT_STATE_COMPONENT_PATH = Path("src/kraken_ai_driven_v2_state_machine.py")
DEFAULT_RISK_EXECUTION_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_RISK_EXECUTION_PROTOCOL_V1.md"
)
DEFAULT_RISK_EXECUTION_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_risk_execution.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 risk/execution review input: {path}"
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


def load_state_protocol(path=DEFAULT_STATE_PROTOCOL_PATH):
    return _load_hash_bound_text(
        path,
        STATE_PROTOCOL_NORMALIZED_SHA256,
        (
            "AI_DRIVEN_V2_STATE_MACHINE_REVIEWED_SYNTHETIC_TESTS_ONLY",
            STATE_PROTOCOL_ID,
            PARAMETER_SET_ID,
            "risk adapter implemented: `false`",
        ),
        "AI-driven v2 state protocol",
    )


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


def _load_component(path, expected_sha256, label):
    digest = normalized_text_sha256(path)
    if digest != expected_sha256:
        raise RuntimeError(
            f"{label} SHA256 mismatch: {digest} != {expected_sha256}."
        )
    return digest


def review_declaration(
    state_protocol_path=DEFAULT_STATE_PROTOCOL_PATH,
    state_component_path=DEFAULT_STATE_COMPONENT_PATH,
    risk_execution_protocol_path=DEFAULT_RISK_EXECUTION_PROTOCOL_PATH,
    risk_execution_component_path=DEFAULT_RISK_EXECUTION_COMPONENT_PATH,
):
    _, state_protocol_digest = load_state_protocol(state_protocol_path)
    state_component_digest = _load_component(
        state_component_path,
        STATE_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 state component",
    )
    _, risk_protocol_digest = load_risk_execution_protocol(
        risk_execution_protocol_path
    )
    risk_component_digest = _load_component(
        risk_execution_component_path,
        RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 risk/execution component",
    )
    policy = REFERENCE_RISK_EXECUTION_POLICY
    costs = REFERENCE_COST_PROFILE
    return {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "KRAKEN_AI_DRIVEN_V2_RISK_EXECUTION_REVIEWED_"
            "PARTITION_PROTOCOL_REQUIRED"
        ),
        "risk_execution_protocol_id": RISK_EXECUTION_PROTOCOL_ID,
        "risk_execution_policy_id": policy.policy_id,
        "cost_profile_id": costs.profile_id,
        "state_protocol_id": STATE_PROTOCOL_ID,
        "state_parameter_set_id": PARAMETER_SET_ID,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "asset_order": ["BTC-USD", "ETH-USD", "XRP-USD"],
        "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
        "v1_btc_episode_evidence_sha256": V1_BTC_EPISODE_EVIDENCE_SHA256,
        "state_protocol_sha256_match": (
            state_protocol_digest == STATE_PROTOCOL_NORMALIZED_SHA256
        ),
        "state_component_sha256_match": (
            state_component_digest == STATE_COMPONENT_NORMALIZED_SHA256
        ),
        "risk_execution_protocol_sha256_match": (
            risk_protocol_digest == RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256
        ),
        "risk_execution_component_sha256_match": (
            risk_component_digest == RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256
        ),
        "deterministic_state_machine_implemented": True,
        "synthetic_risk_execution_adapter_implemented": True,
        "action_intents_are_real_fills": False,
        "adverse_taker_cost_model_frozen": True,
        "commission_rate_per_side": costs.commission_rate,
        "assumed_slippage_rate_per_side": costs.slippage_rate,
        "assumed_full_spread_rate": costs.full_spread_rate,
        "risk_per_trade_fraction": policy.risk_per_trade_fraction,
        "maximum_total_open_risk_fraction": (
            policy.maximum_total_open_risk_fraction
        ),
        "minimum_net_reward_risk": policy.minimum_net_reward_risk,
        "maximum_holding_completed_bars": (
            policy.maximum_holding_completed_bars
        ),
        "real_account_fee_tier_verified": False,
        "venue_minimum_order_rules_implemented": False,
        "real_orders_or_fills_executed": False,
        "dataset_opened": False,
        "real_data_execution_run_executed": False,
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
            "Review the nonexecuting Kraken AI-driven v2 risk/execution "
            "boundary."
        )
    )
    parser.add_argument("--state-protocol", default=str(DEFAULT_STATE_PROTOCOL_PATH))
    parser.add_argument(
        "--state-component", default=str(DEFAULT_STATE_COMPONENT_PATH)
    )
    parser.add_argument(
        "--risk-execution-protocol",
        default=str(DEFAULT_RISK_EXECUTION_PROTOCOL_PATH),
    )
    parser.add_argument(
        "--risk-execution-component",
        default=str(DEFAULT_RISK_EXECUTION_COMPONENT_PATH),
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    declaration = review_declaration(
        args.state_protocol,
        args.state_component,
        args.risk_execution_protocol,
        args.risk_execution_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
