"""Declaration and evidence lock for provider-audited daily crypto replay."""

import argparse
import hashlib
import json
from pathlib import Path


PROTOCOL_SCHEMA_VERSION = 1
DAILY_CRYPTO_REPLAY_PROTOCOL_ID = "btc-eth-xrp-daily-data-blinded-replay-v1"
DAILY_CRYPTO_ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
MANDATE_NORMALIZED_SHA256 = (
    "7c4e6405f8b09c138748644bb51abcc69d06c5c45cfcd7c2df450dfd1efe0c98"
)
BTC_ETH_1D_MANIFEST_SHA256 = (
    "77bc9765a828174b1fd5d46b0d06d216db47e3edab5d91cc65f47a350a335691"
)
DEFAULT_MANDATE_PATH = Path("SELECTIVE_SWING_TRADING_RESEARCH_MANDATE_V1.md")
DEFAULT_BTC_ETH_MANIFEST_PATH = Path(
    "data/research/timeframe_sensitivity_v1/1d/manifest.json"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read mandate: {path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def load_selective_swing_mandate(path, expected_sha256=MANDATE_NORMALIZED_SHA256):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(
            f"Selective swing mandate SHA256 mismatch: {digest} != {expected_sha256}."
        )
    text = raw.decode("utf-8")
    required = (
        "Selective Swing Trading Research Mandate v1",
        "`DECLARED_NOT_EXECUTED`",
        "Crypto Capitulation-Volume Reversal v1",
        "BTC, ETH and XRP",
        "blinded chart-replay workflow",
    )
    if any(value not in text for value in required):
        raise RuntimeError("Selective swing mandate required contract text is missing.")
    return text, digest


def _canonical_manifest_bytes(payload):
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _read_sidecar(manifest_path):
    sidecar = manifest_path.with_name("manifest.sha256")
    try:
        fields = sidecar.read_text(encoding="ascii").strip().split()
    except (OSError, UnicodeError) as exc:
        raise RuntimeError("BTC/ETH daily manifest SHA256 sidecar is unavailable.") from exc
    if len(fields) != 2 or fields[1] != manifest_path.name or len(fields[0]) != 64:
        raise RuntimeError("BTC/ETH daily manifest SHA256 sidecar is malformed.")
    return fields[0].lower()


def load_btc_eth_daily_manifest(
    path, expected_sha256=BTC_ETH_1D_MANIFEST_SHA256
):
    manifest_path = Path(path)
    try:
        raw = manifest_path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("BTC/ETH daily manifest is unreadable.") from exc
    if raw != _canonical_manifest_bytes(payload):
        raise RuntimeError("BTC/ETH daily manifest is not canonical JSON.")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(
            f"BTC/ETH daily manifest SHA256 mismatch: {digest} != {expected_sha256}."
        )
    if _read_sidecar(manifest_path) != digest:
        raise RuntimeError("BTC/ETH daily manifest sidecar SHA256 mismatch.")

    contract = payload.get("contract")
    expected_contract = {
        "dataset_id": (
            "coinbase-exchange-btc-eth-native-1d-20190101-20260801-"
            "timeframe-study-v1"
        ),
        "end": "2026-08-01T00:00:00Z",
        "expected_rows_per_product": 2769,
        "granularity_seconds": 86400,
        "products": ["BTC-USD", "ETH-USD"],
        "range_semantics": "start_inclusive_end_exclusive",
        "start": "2019-01-01T00:00:00Z",
        "timeframe": "1d",
    }
    if contract != expected_contract:
        raise RuntimeError("BTC/ETH daily manifest contract drift detected.")
    assets = payload.get("assets")
    if not isinstance(assets, dict) or tuple(assets) != ("BTC-USD", "ETH-USD"):
        raise RuntimeError("BTC/ETH daily manifest assets are not exact.")
    if any(asset.get("rows") != 2769 for asset in assets.values()):
        raise RuntimeError("BTC/ETH daily manifest asset row contract drift detected.")
    source = payload.get("source")
    if not isinstance(source, dict) or source.get("provider") != (
        "Coinbase Exchange public REST"
    ):
        raise RuntimeError("BTC/ETH daily manifest source contract drift detected.")
    return payload, digest


def protocol_declaration():
    return {
        "schema_version": PROTOCOL_SCHEMA_VERSION,
        "status": "DAILY_CRYPTO_REPLAY_PROTOCOL_DECLARED_PROVIDER_AUDIT_REQUIRED",
        "protocol_id": DAILY_CRYPTO_REPLAY_PROTOCOL_ID,
        "dataset_role": "INSPECTED_HYPOTHESIS_RECONSTRUCTION_ONLY",
        "assets": list(DAILY_CRYPTO_ASSET_ORDER),
        "timeframe": "1d",
        "granularity_seconds": 86400,
        "decision_context_bars": 30,
        "cash_is_default": True,
        "mandate_normalized_sha256": MANDATE_NORMALIZED_SHA256,
        "btc_eth_recorded_manifest_sha256": BTC_ETH_1D_MANIFEST_SHA256,
        "btc_eth_provider": "Coinbase Exchange public REST",
        "xrp_provider_status": "PROVIDER_AUDIT_REQUIRED",
        "xrp_provider": None,
        "data_contract": {
            "bars": "PROVIDER_VENUE_NATIVE_COMPLETED_DAILY_OHLCV",
            "timestamp_alignment": "UTC_MIDNIGHT",
            "candle_fill_policy": "NO_SYNTHETIC_CANDLE_FILL",
            "missing_interval_policy": "EXPLICIT_UNAVAILABLE_INTERVALS",
            "availability_segments": "REPLAY_SEPARATELY",
            "volume_semantics": "PROVIDER_VENUE_NATIVE_BASE_VOLUME",
            "relative_volume_normalization": "PER_ASSET_CAUSAL_TRAILING",
            "cross_provider_raw_volume_comparison": "PROHIBITED",
            "provider_history_audit": "REQUIRED_BEFORE_ALL_ASSET_LOCK",
            "venue_liquidity_and_cost_audit": "REQUIRED_BEFORE_PERFORMANCE",
        },
        "replay_contract": {
            "future_bars_visible": False,
            "decision_before_next_bar": True,
            "allowed_flat_actions": ["ENTER", "SKIP"],
            "allowed_long_actions": ["EXIT", "HOLD"],
            "reason_required": True,
            "performance_metrics_generated": False,
            "parameter_selection_generated": False,
        },
        "data_acquisition_executed": False,
        "real_chart_replay_executed": False,
        "performance_evaluation_executed": False,
        "optimization_authorized": False,
        "automatic_strategy_selection": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
    }


class DailyCryptoReplayProtocol:
    """Review the declaration against frozen, non-performance prerequisites."""

    def review(self, mandate_path=DEFAULT_MANDATE_PATH, manifest_path=DEFAULT_BTC_ETH_MANIFEST_PATH):
        _, mandate_digest = load_selective_swing_mandate(mandate_path)
        _, manifest_digest = load_btc_eth_daily_manifest(manifest_path)
        return {
            "schema_version": PROTOCOL_SCHEMA_VERSION,
            "status": "DAILY_CRYPTO_REPLAY_PROTOCOL_REVIEWED_PROVIDER_AUDIT_REQUIRED",
            "protocol_id": DAILY_CRYPTO_REPLAY_PROTOCOL_ID,
            "mandate_sha256_match": mandate_digest == MANDATE_NORMALIZED_SHA256,
            "btc_eth_manifest_sha256_match": (
                manifest_digest == BTC_ETH_1D_MANIFEST_SHA256
            ),
            "replay_component_reviewed": True,
            "xrp_provider_audit_completed": False,
            "all_asset_data_locked": False,
            "prerequisites_satisfied": False,
            "data_acquisition_executed": False,
            "real_chart_replay_executed": False,
            "real_replay_authorized": False,
            "performance_evaluation_executed": False,
            "optimization_authorized": False,
            "automatic_strategy_selection": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
        }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review the daily crypto data and blinded replay protocol."
    )
    parser.add_argument("--mandate", default=str(DEFAULT_MANDATE_PATH))
    parser.add_argument(
        "--btc-eth-manifest", default=str(DEFAULT_BTC_ETH_MANIFEST_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    result = DailyCryptoReplayProtocol().review(
        args.mandate, args.btc_eth_manifest
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
