"""Reviewed provider selection for the BTC/ETH/XRP daily research dataset."""

import argparse
import hashlib
import json
from pathlib import Path


AUDIT_SCHEMA_VERSION = 1
AUDIT_ID = "btc-eth-xrp-provider-historical-availability-audit-v1"
ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
RESEARCH_START_INCLUSIVE = "2019-01-01T00:00:00Z"
RESEARCH_END_EXCLUSIVE = "2026-08-01T00:00:00Z"
DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256 = (
    "4a195360d58f6c86d7eaae61b39300bf2cac00d947c5c9b2d7615df421e686ea"
)
DEFAULT_DAILY_CRYPTO_PROTOCOL_PATH = Path(
    "BTC_ETH_XRP_DAILY_DATA_AND_BLINDED_REPLAY_PROTOCOL_V1.md"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read daily crypto protocol: {path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def load_daily_crypto_protocol(
    path, expected_sha256=DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256
):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(
            f"Daily crypto protocol SHA256 mismatch: {digest} != {expected_sha256}."
        )
    text = raw.decode("utf-8")
    required = (
        "BTC/ETH/XRP Daily Data and Blinded Replay Protocol v1",
        "PROTOCOL_AND_REPLAY_COMPONENT_REVIEWED_PROVIDER_AUDIT_REQUIRED",
        "BTC-USD`, `ETH-USD`, `XRP-USD",
        "never synthesize or forward-fill a missing candle",
        "performance evaluation executed: `false`",
    )
    if any(value not in text for value in required):
        raise RuntimeError("Daily crypto protocol required contract text is missing.")
    return text, digest


def _official_sources():
    reviewed_at = "2026-08-27"
    return [
        {
            "provider": "Coinbase",
            "purpose": "XRP_SUSPENSION_AND_RELISTING",
            "title": "Coinbase will suspend trading in XRP on January 19",
            "url": (
                "https://www.coinbase.com/blog/"
                "coinbase-will-suspend-trading-in-xrp-on-january-19"
            ),
            "reviewed_at": reviewed_at,
            "official_primary_source": True,
        },
        {
            "provider": "Coinbase",
            "purpose": "CANDLE_SCHEMA_PAGINATION_AND_MISSING_TICKS",
            "title": "Get product candles",
            "url": (
                "https://docs.cdp.coinbase.com/api-reference/exchange-api/"
                "rest-api/products/get-product-candles"
            ),
            "reviewed_at": reviewed_at,
            "official_primary_source": True,
        },
        {
            "provider": "Coinbase",
            "purpose": "VOLUME_UNIT",
            "title": "Get product stats",
            "url": (
                "https://docs.cdp.coinbase.com/api-reference/exchange-api/"
                "rest-api/products/get-product-stats"
            ),
            "reviewed_at": reviewed_at,
            "official_primary_source": True,
        },
        {
            "provider": "Kraken",
            "purpose": "XRP_USD_LISTING_HISTORY",
            "title": "Kraken Introduces New Fiat Pairs for Ripple (XRP) Trading",
            "url": (
                "https://blog.kraken.com/product/"
                "kraken-introduces-new-fiat-pairs-for-ripple-xrp"
            ),
            "reviewed_at": reviewed_at,
            "official_primary_source": True,
        },
        {
            "provider": "Kraken",
            "purpose": "COMPLETE_AND_QUARTERLY_OHLCVT_ARCHIVES",
            "title": "Downloadable historical OHLCVT data",
            "url": (
                "https://support.kraken.com/articles/360047124832-"
                "downloadable-historical-ohlcvt-open-high-low-close-volume-"
                "trades-data"
            ),
            "reviewed_at": reviewed_at,
            "official_primary_source": True,
        },
        {
            "provider": "Kraken",
            "purpose": "REST_OHLC_RETENTION_AND_UNCOMMITTED_LAST_BAR",
            "title": "Get OHLC Data",
            "url": "https://docs.kraken.com/api-reference/market-data/get-ohlc-data",
            "reviewed_at": reviewed_at,
            "official_primary_source": True,
        },
        {
            "provider": "Kraken",
            "purpose": "SPOT_FEE_SCHEDULE",
            "title": "Fee Structures",
            "url": "https://www.kraken.com/features/fee-schedule",
            "reviewed_at": reviewed_at,
            "official_primary_source": True,
        },
        {
            "provider": "Kraken",
            "purpose": "BASE_AND_QUOTE_VOLUME_SEMANTICS",
            "title": "Trades History FAQ",
            "url": (
                "https://support.kraken.com/articles/360001184886-"
                "how-to-interpret-trades-history-fields"
            ),
            "reviewed_at": reviewed_at,
            "official_primary_source": True,
        },
    ]


def provider_audit_declaration():
    """Return the reviewed, non-networked provider selection declaration."""

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit_id": AUDIT_ID,
        "status": "PROVIDER_AUDIT_REVIEWED_SOURCE_SELECTED_ACQUISITION_NOT_EXECUTED",
        "reviewed_at": "2026-08-27",
        "asset_order": list(ASSET_ORDER),
        "research_window": {
            "start": RESEARCH_START_INCLUSIVE,
            "end": RESEARCH_END_EXCLUSIVE,
            "range_semantics": "START_INCLUSIVE_END_EXCLUSIVE",
            "timeframe": "1d",
            "granularity_minutes": 1440,
            "timestamp_alignment": "UTC_MIDNIGHT",
        },
        "primary_provider": "Kraken Spot",
        "primary_source": "OFFICIAL_KRAKEN_OHLCVT_ARCHIVE",
        "one_common_venue_selected": True,
        "selection_reason": (
            "ONE_USD_SPOT_VENUE_WITH_OFFICIAL_NATIVE_DAILY_OHLCVT_FOR_ALL_ASSETS_"
            "AND_XRP_USD_LISTED_BEFORE_RESEARCH_START"
        ),
        "primary_pair_mapping": {
            "BTC-USD": {
                "provider_display_pair": "BTC/USD",
                "provider_legacy_pair": "XBT/USD",
                "archive_pair_stem": "XBTUSD",
            },
            "ETH-USD": {
                "provider_display_pair": "ETH/USD",
                "provider_legacy_pair": "ETH/USD",
                "archive_pair_stem": "ETHUSD",
            },
            "XRP-USD": {
                "provider_display_pair": "XRP/USD",
                "provider_legacy_pair": "XRP/USD",
                "archive_pair_stem": "XRPUSD",
            },
        },
        "xrp_usd_provider_listing_announced": "2017-05-18",
        "xrp_usd_predates_research_start": True,
        "candidate_assessments": {
            "coinbase_exchange": {
                "decision": "REJECT_AS_PRIMARY_COMMON_THREE_ASSET_SOURCE",
                "existing_btc_eth_reference_retained": True,
                "existing_btc_eth_reference_role": (
                    "INDEPENDENT_RECORDED_CROSS_VENUE_REFERENCE"
                ),
                "xrp_trading_suspended_at": "2021-01-19T18:00:00Z",
                "xrp_relisted_date": "2023-07-13",
                "continuous_xrp_window_2019_2026": False,
                "cross_venue_reference_use_allowed": True,
                "merge_coinbase_and_kraken_volume": False,
                "reason": "KNOWN_MULTI_YEAR_XRP_TRADING_SUSPENSION",
            },
            "kraken_spot": {
                "decision": "SELECT_FOR_BOUNDED_THREE_ASSET_ACQUISITION",
                "common_usd_spot_venue": True,
                "official_1440_minute_archive": True,
                "archive_claims_history_from_market_inception": True,
                "quarterly_updates_available": True,
                "exact_requested_window_still_requires_byte_level_acquisition_audit": True,
            },
        },
        "acquisition_contract": {
            "historical_baseline": (
                "COMPLETE_OFFICIAL_OHLCVT_ARCHIVE_PLUS_ALL_REQUIRED_QUARTERLY_"
                "UPDATES"
            ),
            "daily_file_interval_minutes": 1440,
            "rest_incremental_role": (
                "SAME_VENUE_RECENT_COMPLETED_BAR_BRIDGE_AND_OVERLAP_VERIFICATION"
            ),
            "rest_ohlc_max_recent_entries": 720,
            "rest_only_full_history_allowed": False,
            "rest_last_uncommitted_bar_must_be_removed": True,
            "same_venue_overlap_must_match_exactly": True,
            "overlap_mismatch_policy": "FAIL_CLOSED_NO_FINAL_DATASET",
            "download_hashes_required": True,
            "archive_member_inventory_required": True,
            "exact_first_and_last_observed_bucket_required_per_asset": True,
            "duplicate_precedence_without_equality_allowed": False,
            "provider_revision_or_restated_row_must_be_recorded": True,
            "canonical_output_order": [
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ],
            "data_files_written_by_audit": False,
        },
        "missing_interval_policy": {
            "provider_omits_intervals_without_trades": True,
            "synthetic_fill_allowed": False,
            "forward_fill_allowed": False,
            "zero_volume_candle_insertion_allowed": False,
            "every_missing_timestamp_recorded": True,
            "replay_segments_split_at_gaps": True,
            "missing_interval_trading_state": "NO_TRADE_UNAVAILABLE",
        },
        "volume_contract": {
            "provider_definition": "TOTAL_VOLUME_TRADED_BY_ALL_TRADES",
            "expected_unit": "BASE_ASSET_UNITS",
            "pair_base_unit_confirmation_required": True,
            "relative_volume_baseline": "PER_ASSET_LAGGED_TRAILING_HISTORY",
            "raw_cross_asset_comparison_allowed": False,
            "raw_cross_venue_comparison_allowed": False,
            "volume_normalization_across_assets_allowed": False,
        },
        "execution_cost_observation": {
            "observed_at": "2026-08-27",
            "kraken_spot_tier_1_30_day_volume_usd_min": 0,
            "kraken_spot_tier_1_maker_percent": 0.40,
            "kraken_spot_tier_1_taker_percent": 0.80,
            "fee_schedule_is_strategy_cost_profile": False,
            "account_fee_tier_must_be_rechecked": True,
            "spread_snapshot_required_before_performance": True,
            "slippage_and_gap_stress_required_before_performance": True,
            "minimum_notional_and_liquidity_review_required": True,
            "cost_profile_frozen": False,
        },
        "official_sources": _official_sources(),
        "provider_audit_completed": True,
        "documentary_historical_availability_audit_completed": True,
        "byte_level_historical_bucket_inventory_completed": False,
        "bounded_data_acquisition_review_eligible": True,
        "data_acquisition_executed": False,
        "network_requests_executed": False,
        "all_asset_dataset_locked": False,
        "real_chart_replay_authorized": False,
        "crypto_strategy_implemented": False,
        "performance_evaluation_executed": False,
        "optimization_authorized": False,
        "automatic_strategy_selection_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
    }


class BtcEthXrpProviderAudit:
    """Bind the reviewed source decision to the frozen daily replay protocol."""

    def review(self, daily_crypto_protocol_path=DEFAULT_DAILY_CRYPTO_PROTOCOL_PATH):
        _, protocol_digest = load_daily_crypto_protocol(daily_crypto_protocol_path)
        declaration = provider_audit_declaration()
        return {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "status": "BTC_ETH_XRP_PROVIDER_AUDIT_REVIEWED_ACQUISITION_REQUIRED",
            "audit_id": AUDIT_ID,
            "daily_crypto_protocol_sha256_match": (
                protocol_digest == DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256
            ),
            "provider_audit_completed": True,
            "documentary_historical_availability_audit_completed": True,
            "byte_level_historical_bucket_inventory_completed": False,
            "primary_provider_selected": declaration["primary_provider"],
            "one_common_venue_selected": declaration["one_common_venue_selected"],
            "coinbase_common_source_rejected": True,
            "coinbase_btc_eth_reference_retained": True,
            "bounded_data_acquisition_review_eligible": True,
            "data_acquisition_executed": False,
            "network_requests_executed": False,
            "all_asset_dataset_locked": False,
            "real_chart_replay_authorized": False,
            "crypto_strategy_implemented": False,
            "performance_evaluation_executed": False,
            "optimization_authorized": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
        }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review BTC/ETH/XRP provider and historical availability audit v1."
    )
    parser.add_argument(
        "--daily-crypto-protocol",
        default=str(DEFAULT_DAILY_CRYPTO_PROTOCOL_PATH),
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    result = BtcEthXrpProviderAudit().review(args.daily_crypto_protocol)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
