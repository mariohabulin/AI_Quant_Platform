import json
import os
from pathlib import Path
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from btc_eth_xrp_provider_audit import (
    ASSET_ORDER,
    AUDIT_ID,
    DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256,
    RESEARCH_END_EXCLUSIVE,
    RESEARCH_START_INCLUSIVE,
    BtcEthXrpProviderAudit,
    load_daily_crypto_protocol,
    main,
    normalized_text_sha256,
    provider_audit_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
DAILY_PROTOCOL = ROOT / "BTC_ETH_XRP_DAILY_DATA_AND_BLINDED_REPLAY_PROTOCOL_V1.md"
AUDIT_DOCUMENT = ROOT / "BTC_ETH_XRP_PROVIDER_AND_HISTORICAL_AVAILABILITY_AUDIT_V1.md"


def test_audit_selects_one_common_venue_without_acquiring_data():
    declaration = provider_audit_declaration()

    assert declaration["schema_version"] == 1
    assert declaration["audit_id"] == AUDIT_ID
    assert declaration["status"] == (
        "PROVIDER_AUDIT_REVIEWED_SOURCE_SELECTED_ACQUISITION_NOT_EXECUTED"
    )
    assert declaration["asset_order"] == list(ASSET_ORDER)
    assert declaration["primary_provider"] == "Kraken Spot"
    assert declaration["primary_source"] == "OFFICIAL_KRAKEN_OHLCVT_ARCHIVE"
    assert declaration["one_common_venue_selected"] is True
    assert declaration["data_acquisition_executed"] is False
    assert declaration["all_asset_dataset_locked"] is False


def test_target_window_matches_the_existing_daily_research_boundary():
    window = provider_audit_declaration()["research_window"]

    assert RESEARCH_START_INCLUSIVE == "2019-01-01T00:00:00Z"
    assert RESEARCH_END_EXCLUSIVE == "2026-08-01T00:00:00Z"
    assert window == {
        "start": RESEARCH_START_INCLUSIVE,
        "end": RESEARCH_END_EXCLUSIVE,
        "range_semantics": "START_INCLUSIVE_END_EXCLUSIVE",
        "timeframe": "1d",
        "granularity_minutes": 1440,
        "timestamp_alignment": "UTC_MIDNIGHT",
    }


def test_kraken_pair_mapping_is_explicit_and_xrp_predates_window():
    pairs = provider_audit_declaration()["primary_pair_mapping"]

    assert pairs == {
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
    }
    declaration = provider_audit_declaration()
    assert declaration["xrp_usd_provider_listing_announced"] == "2017-05-18"
    assert declaration["xrp_usd_predates_research_start"] is True


def test_coinbase_is_rejected_only_as_common_three_asset_primary_source():
    coinbase = provider_audit_declaration()["candidate_assessments"]["coinbase_exchange"]

    assert coinbase["decision"] == "REJECT_AS_PRIMARY_COMMON_THREE_ASSET_SOURCE"
    assert coinbase["existing_btc_eth_reference_retained"] is True
    assert coinbase["xrp_trading_suspended_at"] == "2021-01-19T18:00:00Z"
    assert coinbase["xrp_relisted_date"] == "2023-07-13"
    assert coinbase["continuous_xrp_window_2019_2026"] is False
    assert coinbase["cross_venue_reference_use_allowed"] is True
    assert coinbase["merge_coinbase_and_kraken_volume"] is False


def test_kraken_archive_and_rest_roles_cannot_be_swapped():
    acquisition = provider_audit_declaration()["acquisition_contract"]

    assert acquisition["historical_baseline"] == (
        "COMPLETE_OFFICIAL_OHLCVT_ARCHIVE_PLUS_ALL_REQUIRED_QUARTERLY_UPDATES"
    )
    assert acquisition["daily_file_interval_minutes"] == 1440
    assert acquisition["rest_ohlc_max_recent_entries"] == 720
    assert acquisition["rest_only_full_history_allowed"] is False
    assert acquisition["rest_last_uncommitted_bar_must_be_removed"] is True
    assert acquisition["same_venue_overlap_must_match_exactly"] is True
    assert acquisition["overlap_mismatch_policy"] == "FAIL_CLOSED_NO_FINAL_DATASET"
    assert acquisition["download_hashes_required"] is True


def test_missing_daily_intervals_are_never_fabricated():
    gaps = provider_audit_declaration()["missing_interval_policy"]

    assert gaps["provider_omits_intervals_without_trades"] is True
    assert gaps["synthetic_fill_allowed"] is False
    assert gaps["forward_fill_allowed"] is False
    assert gaps["zero_volume_candle_insertion_allowed"] is False
    assert gaps["every_missing_timestamp_recorded"] is True
    assert gaps["replay_segments_split_at_gaps"] is True
    assert gaps["missing_interval_trading_state"] == "NO_TRADE_UNAVAILABLE"


def test_volume_semantics_are_per_asset_and_venue_bound():
    volume = provider_audit_declaration()["volume_contract"]

    assert volume["provider_definition"] == "TOTAL_VOLUME_TRADED_BY_ALL_TRADES"
    assert volume["expected_unit"] == "BASE_ASSET_UNITS"
    assert volume["pair_base_unit_confirmation_required"] is True
    assert volume["relative_volume_baseline"] == "PER_ASSET_LAGGED_TRAILING_HISTORY"
    assert volume["raw_cross_asset_comparison_allowed"] is False
    assert volume["raw_cross_venue_comparison_allowed"] is False


def test_current_fee_observation_is_not_a_frozen_execution_profile():
    costs = provider_audit_declaration()["execution_cost_observation"]

    assert costs["observed_at"] == "2026-08-27"
    assert costs["kraken_spot_tier_1_maker_percent"] == 0.40
    assert costs["kraken_spot_tier_1_taker_percent"] == 0.80
    assert costs["fee_schedule_is_strategy_cost_profile"] is False
    assert costs["spread_snapshot_required_before_performance"] is True
    assert costs["slippage_and_gap_stress_required_before_performance"] is True
    assert costs["cost_profile_frozen"] is False


def test_all_sources_are_official_and_dated():
    sources = provider_audit_declaration()["official_sources"]

    assert len(sources) >= 7
    assert all(source["official_primary_source"] is True for source in sources)
    assert all(source["url"].startswith("https://") for source in sources)
    assert all(source["reviewed_at"] == "2026-08-27" for source in sources)
    assert {source["provider"] for source in sources} == {"Coinbase", "Kraken"}


def test_audit_document_matches_selection_limitations_and_next_boundary():
    text = AUDIT_DOCUMENT.read_text(encoding="utf-8")

    required = (
        "BTC/ETH/XRP Provider and Historical Availability Audit v1",
        "`REVIEWED_SOURCE_SELECTED_ACQUISITION_NOT_EXECUTED`",
        "`Kraken Spot official OHLCVT archives`",
        "`2021-01-19T18:00:00Z`",
        "was relisted on `2023-07-13`",
        "returns at most `720` recent entries",
        "byte-level historical bucket inventory completed: `false`",
        "maker: `0.40%`",
        "taker: `0.80%`",
        "data acquisition executed: `false`",
        "live execution authorized: `false`",
    )
    assert all(value in text for value in required)


def test_audit_document_cites_only_reviewed_provider_owned_domains():
    text = AUDIT_DOCUMENT.read_text(encoding="utf-8")

    assert "https://www.coinbase.com/" in text
    assert "https://docs.cdp.coinbase.com/" in text
    assert "https://blog.kraken.com/" in text
    assert "https://support.kraken.com/" in text
    assert "https://docs.kraken.com/" in text
    assert "https://www.kraken.com/" in text
    assert "coingecko" not in text.lower()
    assert "cryptocompare" not in text.lower()


def test_project_documents_record_kraken_acquisition_progression():
    vision = (ROOT / "VISION.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    mission = (ROOT / "CURRENT_MISSION.md").read_text(encoding="utf-8")
    log = (ROOT / "LOG.md").read_text(encoding="utf-8")

    assert "Venue-Bound Crypto Evidence" in vision
    assert "[x] Audit official provider/history evidence" in roadmap
    assert "[x] Acquire, byte-inventory and lock" in roadmap
    assert "Provider and Historical Availability Boundary v1" in architecture
    assert "fail-closed Kraken daily acquisition" in mission
    assert "Provider and Historical Availability Audit v1" in log


def test_audit_authorizes_no_replay_performance_paper_cloud_or_live_activity():
    declaration = provider_audit_declaration()

    assert declaration["provider_audit_completed"] is True
    assert declaration["documentary_historical_availability_audit_completed"] is True
    assert declaration["byte_level_historical_bucket_inventory_completed"] is False
    assert declaration["bounded_data_acquisition_review_eligible"] is True
    assert declaration["data_acquisition_executed"] is False
    assert declaration["real_chart_replay_authorized"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["optimization_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["cloud_execution_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_daily_protocol_hash_is_line_ending_stable(tmp_path):
    crlf = tmp_path / DAILY_PROTOCOL.name
    crlf.write_bytes(
        DAILY_PROTOCOL.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8")
    )

    assert normalized_text_sha256(DAILY_PROTOCOL) == (
        DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256
    )
    assert normalized_text_sha256(crlf) == DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256
    assert load_daily_crypto_protocol(crlf)[1] == DAILY_CRYPTO_PROTOCOL_NORMALIZED_SHA256


def test_tampered_daily_protocol_is_rejected(tmp_path):
    changed = tmp_path / DAILY_PROTOCOL.name
    changed.write_text(
        DAILY_PROTOCOL.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="Daily crypto protocol SHA256 mismatch"):
        load_daily_crypto_protocol(changed)


def test_review_binds_protocol_and_keeps_acquisition_as_next_gate():
    result = BtcEthXrpProviderAudit().review(DAILY_PROTOCOL)

    assert result["status"] == (
        "BTC_ETH_XRP_PROVIDER_AUDIT_REVIEWED_ACQUISITION_REQUIRED"
    )
    assert result["daily_crypto_protocol_sha256_match"] is True
    assert result["provider_audit_completed"] is True
    assert result["documentary_historical_availability_audit_completed"] is True
    assert result["byte_level_historical_bucket_inventory_completed"] is False
    assert result["primary_provider_selected"] == "Kraken Spot"
    assert result["one_common_venue_selected"] is True
    assert result["bounded_data_acquisition_review_eligible"] is True
    assert result["data_acquisition_executed"] is False
    assert result["all_asset_dataset_locked"] is False
    assert result["real_chart_replay_authorized"] is False
    assert result["performance_evaluation_executed"] is False
    assert result["live_execution_authorized"] is False


def test_cli_emits_safe_audit_review_without_network_or_market_execution(capsys):
    exit_code = main(["--daily-crypto-protocol", str(DAILY_PROTOCOL)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"].endswith("ACQUISITION_REQUIRED")
    assert payload["provider_audit_completed"] is True
    assert payload["data_acquisition_executed"] is False
    assert payload["network_requests_executed"] is False
    assert payload["real_chart_replay_authorized"] is False
    assert payload["live_execution_authorized"] is False
