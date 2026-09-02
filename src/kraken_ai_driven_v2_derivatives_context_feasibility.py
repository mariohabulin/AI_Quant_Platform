"""Read-only public-object inventory for the next Kraken V2 information hypothesis."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

import pandas as pd


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-v2-derivatives-context-feasibility-v1"
COMPONENT_ID = "kraken-ai-v2-derivatives-context-feasibility-v1"
PARENT_COMMIT = "cdb1ccc"
PARENT_RESULT_SHA256 = (
    "d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703"
)
DEVELOPMENT_START_UTC = "2019-01-01T00:00:00Z"
DEVELOPMENT_END_EXCLUSIVE_UTC = "2024-04-01T00:00:00Z"
MINIMUM_COMMON_DAYS = 730
MINIMUM_PERIOD_COVERAGE = 0.98
S3_LIST_ENDPOINT = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"

STATUS_FEASIBLE = (
    "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_SOURCE_FEASIBLE_HYPOTHESIS_DESIGN_REQUIRED"
)
STATUS_EXTENSION_REQUIRED = (
    "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATA_EXTENSION_REQUIRED"
)

ASSET_SYMBOLS = {
    "BTC-USD": "BTCUSDT",
    "ETH-USD": "ETHUSDT",
    "XRP-USD": "XRPUSDT",
}

SOURCE_SERIES = {
    "FUNDING_RATE": {
        "cadence": "MONTHLY",
        "prefix": "data/futures/um/monthly/fundingRate/{symbol}/",
        "filename": "{symbol}-fundingRate-{period}.zip",
        "information_family": "FUNDING",
    },
    "OPEN_INTEREST_METRICS": {
        "cadence": "DAILY",
        "prefix": "data/futures/um/daily/metrics/{symbol}/",
        "filename": "{symbol}-metrics-{period}.zip",
        "information_family": "OPEN_INTEREST",
    },
    "MARK_PRICE_12H": {
        "cadence": "MONTHLY",
        "prefix": "data/futures/um/monthly/markPriceKlines/{symbol}/12h/",
        "filename": "{symbol}-12h-{period}.zip",
        "information_family": "BASIS_MARK_LEG",
    },
    "INDEX_PRICE_12H": {
        "cadence": "MONTHLY",
        "prefix": "data/futures/um/monthly/indexPriceKlines/{symbol}/12h/",
        "filename": "{symbol}-12h-{period}.zip",
        "information_family": "BASIS_INDEX_LEG",
    },
}


def _utc(value):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Derivatives-context timestamps must be timezone-aware.")
    return timestamp.tz_convert("UTC")


def _iso(timestamp):
    return _utc(timestamp).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def derivatives_context_feasibility_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "parent_result_sha256": PARENT_RESULT_SHA256,
        "asset_order": list(ASSET_SYMBOLS),
        "source_series_order": list(SOURCE_SERIES),
        "information_families": ["FUNDING", "OPEN_INTEREST", "BASIS"],
        "development_end_exclusive_utc": DEVELOPMENT_END_EXCLUSIVE_UTC,
        "minimum_common_days": MINIMUM_COMMON_DAYS,
        "minimum_period_coverage": MINIMUM_PERIOD_COVERAGE,
        "public_object_metadata_only": True,
        "market_values_opened": False,
        "ohlcvt_values_opened": False,
        "labels_generated": False,
        "model_training_executed": False,
        "hyperparameter_sweep_executed": False,
        "automatic_model_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_FEASIBILITY_IMPLEMENTED_METADATA_AUDIT_REQUIRED",
        "next_stage": "RUN_READ_ONLY_PUBLIC_OBJECT_METADATA_FEASIBILITY_AUDIT",
    }


def _default_fetch_bytes(url):
    request = Request(url, headers={"User-Agent": "AI-Quant-Platform/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def _list_url(prefix, continuation_token=None):
    query = {"list-type": "2", "prefix": prefix}
    if continuation_token:
        query["continuation-token"] = continuation_token
    return f"{S3_LIST_ENDPOINT}?{urlencode(query)}"


def list_public_object_keys(prefix, *, fetch_bytes=None):
    """List all public object keys for one exact Binance archive prefix."""

    fetch_bytes = _default_fetch_bytes if fetch_bytes is None else fetch_bytes
    keys = []
    continuation_token = None
    seen_tokens = set()
    while True:
        payload = fetch_bytes(_list_url(prefix, continuation_token))
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise RuntimeError(f"Invalid public-object listing for {prefix}.") from exc
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}", 1)[0] + "}"
        keys.extend(
            node.text
            for node in root.findall(f"{namespace}Contents/{namespace}Key")
            if node.text
        )
        truncated = (root.findtext(f"{namespace}IsTruncated") or "false").lower()
        if truncated != "true":
            break
        continuation_token = root.findtext(f"{namespace}NextContinuationToken")
        if not continuation_token or continuation_token in seen_tokens:
            raise RuntimeError(f"Invalid public-object pagination for {prefix}.")
        seen_tokens.add(continuation_token)
    return keys


def _period_pattern(source_id, symbol):
    filename = SOURCE_SERIES[source_id]["filename"]
    period_pattern = r"(?P<period>\d{4}-\d{2})"
    if SOURCE_SERIES[source_id]["cadence"] == "DAILY":
        period_pattern = r"(?P<period>\d{4}-\d{2}-\d{2})"
    expression = filename.format(symbol=re.escape(symbol), period="__PERIOD__")
    return re.compile(rf"(?:^|/){expression.replace('__PERIOD__', period_pattern)}$")


def _extract_periods(source_id, symbol, keys):
    pattern = _period_pattern(source_id, symbol)
    periods = []
    duplicate_count = 0
    observed = set()
    for key in keys:
        match = pattern.search(key)
        if not match:
            continue
        period = pd.Timestamp(match.group("period"), tz="UTC")
        if period in observed:
            duplicate_count += 1
        observed.add(period)
        periods.append(period)
    return sorted(observed), duplicate_count


def _period_end_exclusive(period, cadence):
    if cadence == "MONTHLY":
        return period + pd.offsets.MonthBegin(1)
    return period + pd.Timedelta(days=1)


def _expected_periods(start, end_exclusive, cadence):
    if start >= end_exclusive:
        return []
    if cadence == "MONTHLY":
        first = pd.Timestamp(year=start.year, month=start.month, day=1, tz="UTC")
        return list(pd.date_range(first, end_exclusive, freq="MS", inclusive="left"))
    first = start.normalize()
    return list(pd.date_range(first, end_exclusive, freq="D", inclusive="left"))


def _coverage_summary(source_id, asset, keys):
    symbol = ASSET_SYMBOLS[asset]
    cadence = SOURCE_SERIES[source_id]["cadence"]
    periods, duplicate_count = _extract_periods(source_id, symbol, keys)
    development_start = _utc(DEVELOPMENT_START_UTC)
    development_end = _utc(DEVELOPMENT_END_EXCLUSIVE_UTC)
    periods = [
        period
        for period in periods
        if _period_end_exclusive(period, cadence) > development_start
        and period < development_end
    ]
    if not periods:
        return {
            "source_id": source_id,
            "asset": asset,
            "symbol": symbol,
            "cadence": cadence,
            "object_count": 0,
            "first_period_utc": None,
            "last_period_utc": None,
            "coverage_start_utc": None,
            "coverage_end_exclusive_utc": None,
            "duplicate_period_count": duplicate_count,
        }
    return {
        "source_id": source_id,
        "asset": asset,
        "symbol": symbol,
        "cadence": cadence,
        "object_count": len(periods),
        "first_period_utc": _iso(periods[0]),
        "last_period_utc": _iso(periods[-1]),
        "coverage_start_utc": _iso(max(periods[0], development_start)),
        "coverage_end_exclusive_utc": _iso(
            min(_period_end_exclusive(periods[-1], cadence), development_end)
        ),
        "duplicate_period_count": duplicate_count,
        "_periods": periods,
    }


def audit_inventory(keys_by_source_asset):
    """Evaluate already-listed object names without opening market values."""

    coverage = []
    for source_id in SOURCE_SERIES:
        if source_id not in keys_by_source_asset:
            raise ValueError(f"Missing source inventory: {source_id}.")
        for asset in ASSET_SYMBOLS:
            if asset not in keys_by_source_asset[source_id]:
                raise ValueError(f"Missing source inventory: {source_id}|{asset}.")
            coverage.append(
                _coverage_summary(
                    source_id,
                    asset,
                    keys_by_source_asset[source_id][asset],
                )
            )

    identities_complete = all(item["object_count"] > 0 for item in coverage)
    common_start = None
    common_end = None
    if identities_complete:
        common_start = max(_utc(item["coverage_start_utc"]) for item in coverage)
        common_end = min(_utc(item["coverage_end_exclusive_utc"]) for item in coverage)

    common_days = 0
    minimum_coverage = 0.0
    if common_start is not None and common_end is not None and common_end > common_start:
        common_days = int((common_end - common_start) / pd.Timedelta(days=1))
        ratios = []
        for item in coverage:
            expected = _expected_periods(common_start, common_end, item["cadence"])
            observed = set(item.pop("_periods", []))
            observed_in_common = [period for period in expected if period in observed]
            item["common_expected_period_count"] = len(expected)
            item["common_observed_period_count"] = len(observed_in_common)
            item["common_missing_period_count"] = len(expected) - len(observed_in_common)
            item["common_period_coverage"] = (
                len(observed_in_common) / len(expected) if expected else 0.0
            )
            ratios.append(item["common_period_coverage"])
        minimum_coverage = min(ratios) if ratios else 0.0
    else:
        for item in coverage:
            item.pop("_periods", None)
            item["common_expected_period_count"] = 0
            item["common_observed_period_count"] = 0
            item["common_missing_period_count"] = 0
            item["common_period_coverage"] = 0.0

    gates = {
        "all_source_asset_identities_present": identities_complete,
        "minimum_common_days_pass": common_days >= MINIMUM_COMMON_DAYS,
        "minimum_period_coverage_pass": minimum_coverage >= MINIMUM_PERIOD_COVERAGE,
        "duplicate_periods_absent": all(
            item["duplicate_period_count"] == 0 for item in coverage
        ),
    }
    feasible = all(gates.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "parent_result_sha256": PARENT_RESULT_SHA256,
        "status": STATUS_FEASIBLE if feasible else STATUS_EXTENSION_REQUIRED,
        "action": "DESIGN_NEW_INFORMATION_HYPOTHESIS" if feasible else "EXTEND_OR_CHANGE_DATA_SOURCE",
        "source_feasible": feasible,
        "candidate_common_start_utc": _iso(common_start) if common_start is not None else None,
        "candidate_common_end_exclusive_utc": _iso(common_end) if common_end is not None else None,
        "common_calendar_days": common_days,
        "minimum_observed_period_coverage": minimum_coverage,
        "gates": gates,
        "coverage": coverage,
        "public_object_metadata_only": True,
        "market_values_opened": False,
        "labels_generated": False,
        "model_training_executed": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": (
            "PRE_REGISTER_DERIVATIVES_CONTEXT_LEARNING_HYPOTHESIS_V1"
            if feasible
            else "REVIEW_ALTERNATIVE_HISTORICAL_DATA_SOURCE"
        ),
    }


def run_source_feasibility_audit(*, fetch_bytes=None):
    inventory = {}
    for source_id, source in SOURCE_SERIES.items():
        inventory[source_id] = {}
        for asset, symbol in ASSET_SYMBOLS.items():
            prefix = source["prefix"].format(symbol=symbol)
            inventory[source_id][asset] = list_public_object_keys(
                prefix, fetch_bytes=fetch_bytes
            )
    return audit_inventory(inventory)


def write_audit_result(result, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(result)
    with tempfile.NamedTemporaryFile(
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, output_path)
    checksum_path = output_path.with_suffix(output_path.suffix + ".sha256")
    digest = hashlib.sha256(payload).hexdigest()
    checksum_path.write_text(f"{digest}  {output_path.name}\n", encoding="ascii")
    return digest


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit public derivatives-context object coverage without opening values."
    )
    parser.add_argument("--declaration-only", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.declaration_only:
        result = derivatives_context_feasibility_declaration()
    else:
        result = run_source_feasibility_audit()
    if args.output:
        write_audit_result(result, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
