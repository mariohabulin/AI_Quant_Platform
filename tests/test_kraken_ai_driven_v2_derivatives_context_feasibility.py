import hashlib
import os
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_derivatives_context_feasibility import (
    ASSET_SYMBOLS,
    MINIMUM_COMMON_DAYS,
    MINIMUM_PERIOD_COVERAGE,
    PARENT_RESULT_SHA256,
    PROTOCOL_ID,
    SOURCE_SERIES,
    STATUS_EXTENSION_REQUIRED,
    STATUS_FEASIBLE,
    _list_url,
    audit_inventory,
    canonical_json_bytes,
    derivatives_context_feasibility_declaration,
    list_public_object_keys,
    run_source_feasibility_audit,
    write_audit_result,
)


ROOT = Path(__file__).resolve().parents[1]


def _keys(source_id, symbol, start="2021-12-01", end="2024-04-01"):
    source = SOURCE_SERIES[source_id]
    start = pd.Timestamp(start, tz="UTC")
    end = pd.Timestamp(end, tz="UTC")
    frequency = "MS" if source["cadence"] == "MONTHLY" else "D"
    periods = pd.date_range(start, end, freq=frequency, inclusive="left")
    keys = []
    prefix = source["prefix"].format(symbol=symbol)
    for period in periods:
        value = period.strftime("%Y-%m" if source["cadence"] == "MONTHLY" else "%Y-%m-%d")
        keys.append(prefix + source["filename"].format(symbol=symbol, period=value))
    return keys


def _complete_inventory(start="2021-12-01", end="2024-04-01"):
    return {
        source_id: {
            asset: _keys(source_id, symbol, start=start, end=end)
            for asset, symbol in ASSET_SYMBOLS.items()
        }
        for source_id in SOURCE_SERIES
    }


def _xml(keys, *, truncated=False, token=None):
    contents = "".join(f"<Contents><Key>{key}</Key></Contents>" for key in keys)
    next_token = f"<NextContinuationToken>{token}</NextContinuationToken>" if token else ""
    return (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<ListBucketResult xmlns='http://s3.amazonaws.com/doc/2006-03-01/'>"
        f"{contents}<IsTruncated>{str(truncated).lower()}</IsTruncated>{next_token}"
        "</ListBucketResult>"
    ).encode("utf-8")


def test_declaration_freezes_metadata_only_new_information_bundle():
    declaration = derivatives_context_feasibility_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["parent_commit"] == "cdb1ccc"
    assert declaration["parent_result_sha256"] == PARENT_RESULT_SHA256
    assert declaration["asset_order"] == list(ASSET_SYMBOLS)
    assert declaration["source_series_order"] == list(SOURCE_SERIES)
    assert declaration["information_families"] == ["FUNDING", "OPEN_INTEREST", "BASIS"]
    assert declaration["minimum_common_days"] == MINIMUM_COMMON_DAYS == 730
    assert declaration["minimum_period_coverage"] == MINIMUM_PERIOD_COVERAGE == 0.98
    assert declaration["public_object_metadata_only"] is True
    assert declaration["market_values_opened"] is False
    assert declaration["model_training_executed"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False


def test_registry_requires_funding_oi_and_both_basis_legs():
    assert list(SOURCE_SERIES) == [
        "FUNDING_RATE",
        "OPEN_INTEREST_METRICS",
        "MARK_PRICE_12H",
        "INDEX_PRICE_12H",
    ]
    assert SOURCE_SERIES["FUNDING_RATE"]["cadence"] == "MONTHLY"
    assert SOURCE_SERIES["OPEN_INTEREST_METRICS"]["cadence"] == "DAILY"
    assert SOURCE_SERIES["MARK_PRICE_12H"]["information_family"] == "BASIS_MARK_LEG"
    assert SOURCE_SERIES["INDEX_PRICE_12H"]["information_family"] == "BASIS_INDEX_LEG"


def test_s3_listing_paginates_without_opening_market_files():
    calls = []

    def fetch(url):
        calls.append(url)
        token = parse_qs(urlparse(url).query).get("continuation-token")
        if token is None:
            return _xml(["prefix/one.zip"], truncated=True, token="next page")
        return _xml(["prefix/two.zip"])

    keys = list_public_object_keys("prefix/", fetch_bytes=fetch)

    assert keys == ["prefix/one.zip", "prefix/two.zip"]
    assert len(calls) == 2
    assert "continuation-token=next+page" in calls[1]
    assert _list_url("prefix/").startswith("https://s3-ap-northeast-1.amazonaws.com/")


def test_listing_fails_closed_on_invalid_xml_or_pagination():
    with pytest.raises(RuntimeError, match="Invalid public-object listing"):
        list_public_object_keys("broken/", fetch_bytes=lambda _url: b"not xml")

    with pytest.raises(RuntimeError, match="Invalid public-object pagination"):
        list_public_object_keys(
            "broken/", fetch_bytes=lambda _url: _xml([], truncated=True)
        )


def test_complete_two_year_common_inventory_is_feasible_without_profitability_claim():
    result = audit_inventory(_complete_inventory())

    assert result["status"] == STATUS_FEASIBLE
    assert result["source_feasible"] is True
    assert result["action"] == "DESIGN_NEW_INFORMATION_HYPOTHESIS"
    assert result["candidate_common_start_utc"] == "2021-12-01T00:00:00Z"
    assert result["candidate_common_end_exclusive_utc"] == "2024-04-01T00:00:00Z"
    assert result["common_calendar_days"] >= 730
    assert result["minimum_observed_period_coverage"] == 1.0
    assert all(result["gates"].values())
    assert result["market_values_opened"] is False
    assert result["labels_generated"] is False
    assert result["model_training_executed"] is False
    assert result["candidate_v2_authorized"] is False


def test_short_common_history_requires_extension_instead_of_relaxation():
    result = audit_inventory(_complete_inventory(start="2023-01-01"))

    assert result["status"] == STATUS_EXTENSION_REQUIRED
    assert result["source_feasible"] is False
    assert result["gates"]["minimum_common_days_pass"] is False
    assert result["action"] == "EXTEND_OR_CHANGE_DATA_SOURCE"


def test_missing_daily_oi_history_fails_coverage_gate():
    inventory = _complete_inventory()
    for asset in ASSET_SYMBOLS:
        inventory["OPEN_INTEREST_METRICS"][asset] = inventory[
            "OPEN_INTEREST_METRICS"
        ][asset][::2]

    result = audit_inventory(inventory)

    assert result["status"] == STATUS_EXTENSION_REQUIRED
    assert result["gates"]["minimum_period_coverage_pass"] is False
    assert result["minimum_observed_period_coverage"] < 0.51


def test_missing_source_identity_fails_closed_or_reports_extension():
    inventory = _complete_inventory()
    inventory["FUNDING_RATE"]["XRP-USD"] = []
    result = audit_inventory(inventory)
    assert result["source_feasible"] is False
    assert result["gates"]["all_source_asset_identities_present"] is False

    del inventory["FUNDING_RATE"]["XRP-USD"]
    with pytest.raises(ValueError, match=r"FUNDING_RATE\|XRP-USD"):
        audit_inventory(inventory)


def test_network_runner_only_requests_frozen_listing_prefixes():
    requested_prefixes = []

    def fetch(url):
        prefix = parse_qs(urlparse(url).query)["prefix"][0]
        requested_prefixes.append(prefix)
        source_id = next(
            source_id
            for source_id, spec in SOURCE_SERIES.items()
            if spec["prefix"].split("{symbol}", 1)[0] in prefix
        )
        symbol = next(symbol for symbol in ASSET_SYMBOLS.values() if symbol in prefix)
        return _xml(_keys(source_id, symbol))

    result = run_source_feasibility_audit(fetch_bytes=fetch)

    assert result["status"] == STATUS_FEASIBLE
    assert len(requested_prefixes) == len(SOURCE_SERIES) * len(ASSET_SYMBOLS)
    assert all(prefix.startswith("data/futures/um/") for prefix in requested_prefixes)


def test_atomic_result_and_sidecar_are_canonical_and_matching(tmp_path):
    result = audit_inventory(_complete_inventory())
    output = tmp_path / "audit.json"
    digest = write_audit_result(result, output)

    assert output.read_bytes() == canonical_json_bytes(result)
    assert digest == hashlib.sha256(output.read_bytes()).hexdigest()
    assert output.with_suffix(".json.sha256").read_text(encoding="ascii") == (
        f"{digest}  audit.json\n"
    )


def test_protocol_prohibits_disguised_ohlcv_retry_and_value_access():
    protocol = (
        ROOT
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_FEASIBILITY_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")

    assert "There is no seventh learner" in protocol
    assert "download or parse market-value CSV rows" in protocol
    assert "at least 730 common calendar days" in protocol
    assert "at least 98%" in protocol
    assert "Calibration and Evaluation: unopened" in protocol
    assert "EXTEND_OR_CHANGE_DATA_SOURCE" in protocol
