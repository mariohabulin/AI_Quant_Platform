"""Hash-bound Binance USD-M context dataset lock and independent reader."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

import pandas as pd


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-v2-derivatives-context-dataset-lock-reader-v1"
COMPONENT_ID = "kraken-ai-v2-derivatives-context-dataset-lock-reader-v1"
DATASET_ID = "binance-usdm-btc-eth-xrp-derivatives-context-20211201-20240401-v1"
PARENT_COMMIT = "af0af86"
PARENT_PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-v2-derivatives-context-learning-hypothesis-v1"
)
PARENT_FEASIBILITY_REPORT_SHA256 = (
    "3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29"
)
RECOVERY_PARENT_COMMIT = "25d55b6"
ATTEMPT_1_INCIDENT_SHA256 = (
    "3abae269bc80b13b975e77afb4bbfc7e7f442856ab4510fd5ad9023221aebca8"
)
ATTEMPT_2_INCIDENT_SHA256 = (
    "76ce94fc848d888c489ea6466044a094443775f329bfcc51a3117bac5497a39f"
)
ATTEMPT_3_INCIDENT_SHA256 = (
    "ce08144f2e27788a17b23bb0fbbfdf0728854b6332b82c98378e79b09e201cc6"
)
ATTEMPT_3_STAGING_FILE_COUNT = 1390
ATTEMPT_3_STAGING_TOTAL_BYTES = 7317431
ATTEMPT_3_STAGING_INVENTORY_SHA256 = (
    "8de82f8905358c79f3e0cb609f8b8ecd782e32e02497e9ef784e85b528aa63dd"
)
ATTEMPT_3_RESUME_OBJECT_COUNT = 695
AUTHORIZATION_PHRASE = (
    "EXECUTE_KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_RECOVERY_ATTEMPT_4_ONCE"
)
BASE_URL = "https://data.binance.vision/"
COMMON_START_UTC = "2021-12-01T00:00:00Z"
COMMON_END_EXCLUSIVE_UTC = "2024-04-01T00:00:00Z"
MAXIMUM_ZIP_BYTES = 128 * 1024 * 1024
MAXIMUM_MEMBER_BYTES = 512 * 1024 * 1024
MAXIMUM_TRANSPORT_ATTEMPTS = 12
MAXIMUM_TRANSPORT_BACKOFF_SECONDS = 60

ASSET_SYMBOLS = {
    "BTC-USD": "BTCUSDT",
    "ETH-USD": "ETHUSDT",
    "XRP-USD": "XRPUSDT",
}

SOURCE_SPECS = {
    "FUNDING_RATE": {
        "cadence": "MONTHLY",
        "prefix": "data/futures/um/monthly/fundingRate/{symbol}/",
        "filename": "{symbol}-fundingRate-{period}.zip",
        "normalized_header": ("source_timestamp", "funding_rate"),
    },
    "OPEN_INTEREST_METRICS": {
        "cadence": "DAILY",
        "prefix": "data/futures/um/daily/metrics/{symbol}/",
        "filename": "{symbol}-metrics-{period}.zip",
        "normalized_header": ("source_timestamp", "open_interest"),
    },
    "MARK_PRICE_12H": {
        "cadence": "MONTHLY",
        "prefix": "data/futures/um/monthly/markPriceKlines/{symbol}/12h/",
        "filename": "{symbol}-12h-{period}.zip",
        "normalized_header": ("open_timestamp", "close_timestamp", "close"),
    },
    "INDEX_PRICE_12H": {
        "cadence": "MONTHLY",
        "prefix": "data/futures/um/monthly/indexPriceKlines/{symbol}/12h/",
        "filename": "{symbol}-12h-{period}.zip",
        "normalized_header": ("open_timestamp", "close_timestamp", "close"),
    },
}

FUNDING_HEADER = (
    "calc_time",
    "funding_interval_hours",
    "last_funding_rate",
)
METRICS_HEADER = (
    "create_time",
    "symbol",
    "sum_open_interest",
    "sum_open_interest_value",
    "count_toptrader_long_short_ratio",
    "sum_toptrader_long_short_ratio",
    "count_long_short_ratio",
    "sum_taker_long_short_vol_ratio",
)
OPTIONAL_METRICS_COLUMNS = METRICS_HEADER[4:]
OPEN_INTEREST_ZERO_SENTINEL_LITERAL = "0E-8"
OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256 = (
    "791ddfb1d1b584abbbd551bbcce77baef2de51b23f9c3f2668f4e6d6d41d5cbb"
)
_OPEN_INTEREST_ZERO_SENTINEL_BLOCKS = (
    ("2022-03-07T15:30:00Z", 102),
    ("2022-03-08T00:00:00Z", 14),
    ("2022-03-08T07:10:00Z", 1),
    ("2023-06-06T11:20:00Z", 4),
    ("2023-08-09T02:35:00Z", 1),
    ("2023-11-11T22:00:00Z", 1),
    ("2023-11-20T09:20:00Z", 6),
    ("2023-11-23T03:55:00Z", 2),
    ("2023-11-26T00:50:00Z", 2),
)


def _expand_open_interest_zero_sentinel_timestamps():
    return tuple(
        (pd.Timestamp(start) + offset * pd.Timedelta(minutes=5))
        .isoformat()
        .replace("+00:00", "Z")
        for start, count in _OPEN_INTEREST_ZERO_SENTINEL_BLOCKS
        for offset in range(count)
    )


OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMPS = (
    _expand_open_interest_zero_sentinel_timestamps()
)
KLINE_HEADER = (
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
    "ignore",
)
KLINE_DOCUMENTED_HEADER = (
    "Open time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Close time",
    "Quote asset volume",
    "Number of trades",
    "Taker buy base asset volume",
    "Taker buy quote asset volume",
    "Ignore",
)


def _utc(value, name="Timestamp"):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware.")
    return timestamp.tz_convert("UTC")


def _iso(value):
    return _utc(value).isoformat().replace("+00:00", "Z")


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


def _sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def _periods(cadence):
    start = _utc(COMMON_START_UTC)
    end = _utc(COMMON_END_EXCLUSIVE_UTC)
    frequency = "MS" if cadence == "MONTHLY" else "D"
    return list(pd.date_range(start, end, freq=frequency, inclusive="left"))


def expected_object_registry():
    registry = []
    for source_id, source in SOURCE_SPECS.items():
        period_format = "%Y-%m" if source["cadence"] == "MONTHLY" else "%Y-%m-%d"
        for asset, symbol in ASSET_SYMBOLS.items():
            for timestamp in _periods(source["cadence"]):
                period = timestamp.strftime(period_format)
                filename = source["filename"].format(symbol=symbol, period=period)
                key = source["prefix"].format(symbol=symbol) + filename
                registry.append(
                    {
                        "source_id": source_id,
                        "asset": asset,
                        "symbol": symbol,
                        "cadence": source["cadence"],
                        "period": period,
                        "key": key,
                        "filename": filename,
                        "url": BASE_URL + key,
                        "checksum_url": BASE_URL + key + ".CHECKSUM",
                    }
                )
    return registry


def dataset_lock_declaration():
    observed_zero_timestamp_sha256 = _sha256(
        canonical_json_bytes(list(OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMPS))
    )
    if observed_zero_timestamp_sha256 != OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256:
        raise RuntimeError("Frozen open-interest zero-sentinel list hash mismatch.")
    registry = expected_object_registry()
    source_counts = {
        source_id: sum(item["source_id"] == source_id for item in registry)
        for source_id in SOURCE_SPECS
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "dataset_id": DATASET_ID,
        "parent_commit": PARENT_COMMIT,
        "recovery_parent_commit": RECOVERY_PARENT_COMMIT,
        "parent_protocol_id": PARENT_PROTOCOL_ID,
        "parent_feasibility_report_sha256": PARENT_FEASIBILITY_REPORT_SHA256,
        "attempt_1_authorization_consumed": True,
        "attempt_1_final_dataset_exists": False,
        "attempt_1_staging_required": True,
        "attempt_1_incident_sha256": ATTEMPT_1_INCIDENT_SHA256,
        "attempt_2_authorization_consumed": True,
        "attempt_2_final_dataset_exists": False,
        "attempt_2_staging_required": True,
        "attempt_2_incident_sha256": ATTEMPT_2_INCIDENT_SHA256,
        "attempt_3_authorization_consumed": True,
        "attempt_3_final_dataset_exists": False,
        "attempt_3_staging_required": True,
        "attempt_3_incident_sha256": ATTEMPT_3_INCIDENT_SHA256,
        "attempt_3_staging_file_count": ATTEMPT_3_STAGING_FILE_COUNT,
        "attempt_3_staging_total_bytes": ATTEMPT_3_STAGING_TOTAL_BYTES,
        "attempt_3_staging_inventory_sha256": (
            ATTEMPT_3_STAGING_INVENTORY_SHA256
        ),
        "verified_resume_object_count": ATTEMPT_3_RESUME_OBJECT_COUNT,
        "public_download_object_count": len(registry)
        - ATTEMPT_3_RESUME_OBJECT_COUNT,
        "maximum_transport_attempts_per_fetch": MAXIMUM_TRANSPORT_ATTEMPTS,
        "maximum_transport_backoff_seconds": MAXIMUM_TRANSPORT_BACKOFF_SECONDS,
        "recovery_attempt": 4,
        "authorization_phrase": AUTHORIZATION_PHRASE,
        "authorization_phrase_active": False,
        "asset_order": list(ASSET_SYMBOLS),
        "source_series_order": list(SOURCE_SPECS),
        "common_start_utc": COMMON_START_UTC,
        "common_end_exclusive_utc": COMMON_END_EXCLUSIVE_UTC,
        "expected_object_count": len(registry),
        "expected_object_counts_by_source": source_counts,
        "official_checksum_required": True,
        "raw_zip_hash_implemented": True,
        "csv_member_hash_implemented": True,
        "normalized_file_hash_implemented": True,
        "atomic_dataset_lock_implemented": True,
        "independent_reader_implemented": True,
        "optional_metrics_blank_policy_implemented": True,
        "optional_metrics_blank_counts_recorded": True,
        "open_interest_zero_sentinel_policy_implemented": True,
        "open_interest_zero_sentinel_count": 399,
        "open_interest_zero_sentinel_count_per_asset": 133,
        "open_interest_zero_sentinel_timestamp_sha256": (
            OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256
        ),
        "source_objects_downloaded": False,
        "market_values_opened": False,
        "development_data_opened": False,
        "labels_generated": False,
        "model_training_executed": False,
        "hyperparameter_sweep_authorized": False,
        "threshold_sweep_authorized": False,
        "automatic_model_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_RECOVERY_IMPLEMENTED_NO_ATTEMPT_4_AUTHORIZATION",
        "next_stage": "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_DERIVATIVES_CONTEXT_DATASET_LOCK_RECOVERY_ATTEMPT_4",
    }


def _default_fetch_bytes(url):
    request = Request(url, headers={"User-Agent": "AI-Quant-Platform/1.0"})
    last_error = None
    for attempt in range(MAXIMUM_TRANSPORT_ATTEMPTS):
        try:
            with urlopen(request, timeout=120) as response:
                return response.read()
        except HTTPError as exc:  # pragma: no cover - depends on remote server
            if 400 <= exc.code < 500 and exc.code not in (408, 429):
                raise RuntimeError(
                    f"Frozen source object returned permanent HTTP {exc.code}: {url}."
                ) from exc
            last_error = exc
        except OSError as exc:  # pragma: no cover - depends on transport
            last_error = exc
        if attempt + 1 < MAXIMUM_TRANSPORT_ATTEMPTS:
            delay = min(2**attempt, MAXIMUM_TRANSPORT_BACKOFF_SECONDS)
            print(
                f"TRANSPORT_RETRY={attempt + 2}/{MAXIMUM_TRANSPORT_ATTEMPTS}|"
                f"DELAY_SECONDS={delay}|URL={url}",
                flush=True,
            )
            time.sleep(delay)
    raise RuntimeError(f"Unable to download frozen source object: {url}.") from last_error


def parse_official_checksum(payload, expected_filename):
    try:
        text = payload.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ValueError("Official checksum must be ASCII.") from exc
    match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", text)
    if match is None:
        raise ValueError("Official checksum format mismatch.")
    filename = PurePosixPath(match.group(2).replace("\\", "/")).name
    if filename != expected_filename:
        raise ValueError("Official checksum filename mismatch.")
    return match.group(1).lower()


def _decimal_text(value, name, *, positive=False):
    try:
        parsed = Decimal(value.strip())
    except (AttributeError, InvalidOperation) as exc:
        raise ValueError(f"{name} must be a finite decimal.") from exc
    if not parsed.is_finite() or (positive and parsed <= 0):
        qualifier = "positive " if positive else "finite "
        raise ValueError(f"{name} must be a {qualifier}decimal.")
    return value.strip()


def _timestamp(value, name):
    value = value.strip()
    try:
        numeric = Decimal(value)
    except InvalidOperation:
        numeric = None
    if numeric is not None and numeric.is_finite():
        absolute = abs(numeric)
        unit = "s"
        if absolute >= Decimal("1e14"):
            unit = "us"
        elif absolute >= Decimal("1e11"):
            unit = "ms"
        try:
            timestamp = pd.to_datetime(int(numeric), unit=unit, utc=True)
        except (ValueError, OverflowError) as exc:
            raise ValueError(f"{name} timestamp is invalid.") from exc
    else:
        try:
            timestamp = pd.to_datetime(value, utc=True)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{name} timestamp is invalid.") from exc
    if pd.isna(timestamp):
        raise ValueError(f"{name} timestamp is invalid.")
    return pd.Timestamp(timestamp)


def _period_bounds(spec):
    start = pd.Timestamp(spec["period"], tz="UTC")
    end = (
        start + pd.offsets.MonthBegin(1)
        if spec["cadence"] == "MONTHLY"
        else start + pd.Timedelta(days=1)
    )
    return start, end


def _validate_chronology(timestamps, spec):
    if not timestamps:
        raise ValueError("Source CSV contains no data rows.")
    index = pd.DatetimeIndex(timestamps)
    if not index.is_monotonic_increasing or not index.is_unique:
        raise ValueError("Source timestamps must be strictly increasing and unique.")
    period_start, period_end = _period_bounds(spec)
    if index.min() < period_start or index.max() >= period_end:
        raise ValueError("Source row crosses its frozen archive period.")


def _csv_rows(member_bytes):
    try:
        text = member_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Source CSV must be UTF-8.") from exc
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if any(not row for row in rows):
        raise ValueError("Source CSV contains an empty row.")
    return rows


def _normalized_csv(header, rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _parse_funding(rows, spec):
    if tuple(rows[0]) != FUNDING_HEADER:
        raise ValueError("Funding source schema mismatch.")
    normalized = []
    timestamps = []
    for number, row in enumerate(rows[1:], start=2):
        if len(row) != len(FUNDING_HEADER):
            raise ValueError(f"Funding row {number} column-count mismatch.")
        timestamp = _timestamp(row[0], "Funding")
        interval = _decimal_text(row[1], "Funding interval", positive=True)
        if Decimal(interval) > 12:
            raise ValueError("Funding interval exceeds the frozen 12-hour age bound.")
        rate = _decimal_text(row[2], "Funding rate")
        timestamps.append(timestamp)
        normalized.append((_iso(timestamp), rate))
    _validate_chronology(timestamps, spec)
    return normalized, timestamps


def _parse_metrics(rows, spec):
    if tuple(rows[0]) != METRICS_HEADER:
        raise ValueError("Open-interest metrics schema mismatch.")
    normalized = []
    timestamps = []
    optional_blank_counts = {name: 0 for name in OPTIONAL_METRICS_COLUMNS}
    zero_sentinel_timestamps = []
    allowed_zero_timestamps = set(OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMPS)
    for number, row in enumerate(rows[1:], start=2):
        if len(row) != len(METRICS_HEADER):
            raise ValueError(f"Metrics row {number} column-count mismatch.")
        if row[1] != spec["symbol"]:
            raise ValueError("Open-interest metrics symbol mismatch.")
        timestamp = _timestamp(row[0], "Open-interest metrics")
        timestamp_text = _iso(timestamp)
        open_interest = _decimal_text(row[2], "Open-interest metrics value")
        open_interest_value = _decimal_text(row[3], METRICS_HEADER[3])
        parsed_open_interest = Decimal(open_interest)
        is_zero_sentinel = parsed_open_interest == 0
        if parsed_open_interest < 0:
            raise ValueError("Open-interest metrics value must be a positive decimal.")
        if is_zero_sentinel:
            if (
                row[2] != OPEN_INTEREST_ZERO_SENTINEL_LITERAL
                or row[3] != OPEN_INTEREST_ZERO_SENTINEL_LITERAL
                or timestamp_text not in allowed_zero_timestamps
            ):
                raise ValueError("Open-interest zero sentinel is not frozen or paired.")
            zero_sentinel_timestamps.append(timestamp_text)
        for column, name in zip(row[4:], OPTIONAL_METRICS_COLUMNS):
            if column == "":
                optional_blank_counts[name] += 1
            else:
                _decimal_text(column, name)
        timestamps.append(timestamp)
        if not is_zero_sentinel:
            normalized.append((timestamp_text, open_interest))
    _validate_chronology(timestamps, spec)
    return normalized, timestamps, optional_blank_counts, zero_sentinel_timestamps


def _parse_kline(rows, spec):
    if tuple(rows[0]) in (KLINE_HEADER, KLINE_DOCUMENTED_HEADER):
        rows = rows[1:]
    normalized = []
    timestamps = []
    for number, row in enumerate(rows, start=1):
        if len(row) != len(KLINE_HEADER):
            raise ValueError(f"Kline row {number} column-count mismatch.")
        open_timestamp = _timestamp(row[0], "Kline open")
        close_timestamp = _timestamp(row[6], "Kline close")
        interval_seconds = int(pd.Timedelta(hours=12).total_seconds())
        if int(open_timestamp.timestamp()) % interval_seconds:
            raise ValueError("Kline open timestamp is not on the native 12h grid.")
        if close_timestamp <= open_timestamp:
            raise ValueError("Kline close timestamp must follow its open.")
        for index in (1, 2, 3, 4, 5, 7, 9, 10, 11):
            _decimal_text(row[index], KLINE_HEADER[index])
        if not row[8].strip().isdigit() or int(row[8]) < 0:
            raise ValueError("Kline trade count must be a non-negative integer.")
        close = _decimal_text(row[4], "Kline close", positive=True)
        timestamps.append(open_timestamp)
        normalized.append((_iso(open_timestamp), _iso(close_timestamp), close))
    _validate_chronology(timestamps, spec)
    return normalized, timestamps


def validate_source_archive(spec, zip_bytes, checksum_bytes):
    required = {
        "source_id",
        "asset",
        "symbol",
        "cadence",
        "period",
        "key",
        "filename",
        "url",
        "checksum_url",
    }
    if set(spec) != required:
        raise ValueError("Frozen source object identity mismatch.")
    if spec["source_id"] not in SOURCE_SPECS:
        raise ValueError("Unknown frozen source series.")
    if ASSET_SYMBOLS.get(spec["asset"]) != spec["symbol"]:
        raise ValueError("Frozen source asset identity mismatch.")
    if len(zip_bytes) > MAXIMUM_ZIP_BYTES:
        raise ValueError("Source ZIP exceeds the frozen compressed-size limit.")
    expected_digest = parse_official_checksum(checksum_bytes, spec["filename"])
    observed_digest = _sha256(zip_bytes)
    if observed_digest != expected_digest:
        raise ValueError("Source ZIP does not match its official checksum.")

    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError("Source object is not a valid ZIP.") from exc
    with archive:
        members = [member for member in archive.infolist() if not member.is_dir()]
        if len(members) != 1:
            raise ValueError("Source ZIP must contain exactly one CSV member.")
        member = members[0]
        expected_member = spec["filename"][:-4] + ".csv"
        path = PurePosixPath(member.filename.replace("\\", "/"))
        if path.name != member.filename or path.name != expected_member:
            raise ValueError("Source ZIP member identity is unsafe or unexpected.")
        if member.flag_bits & 0x1:
            raise ValueError("Encrypted source ZIP members are prohibited.")
        if member.file_size > MAXIMUM_MEMBER_BYTES:
            raise ValueError("Source CSV exceeds the frozen member-size limit.")
        member_bytes = archive.read(member)

    rows = _csv_rows(member_bytes)
    source_id = spec["source_id"]
    optional_blank_counts = None
    if source_id == "FUNDING_RATE":
        normalized_rows, timestamps = _parse_funding(rows, spec)
    elif source_id == "OPEN_INTEREST_METRICS":
        (
            normalized_rows,
            timestamps,
            optional_blank_counts,
            zero_sentinel_timestamps,
        ) = _parse_metrics(rows, spec)
    else:
        normalized_rows, timestamps = _parse_kline(rows, spec)
    normalized = _normalized_csv(
        SOURCE_SPECS[source_id]["normalized_header"], normalized_rows
    )
    result = {
        "source_id": source_id,
        "asset": spec["asset"],
        "symbol": spec["symbol"],
        "cadence": spec["cadence"],
        "period": spec["period"],
        "key": spec["key"],
        "filename": spec["filename"],
        "zip_bytes": len(zip_bytes),
        "zip_sha256": observed_digest,
        "checksum_bytes": len(checksum_bytes),
        "checksum_sha256": _sha256(checksum_bytes),
        "csv_member_name": expected_member,
        "csv_member_bytes": len(member_bytes),
        "csv_member_sha256": _sha256(member_bytes),
        "row_count": len(timestamps),
        "normalized_row_count": len(normalized_rows),
        "first_timestamp_utc": _iso(timestamps[0]),
        "last_timestamp_utc": _iso(timestamps[-1]),
        "normalized_bytes": normalized,
    }
    if optional_blank_counts is not None:
        result["optional_blank_counts"] = optional_blank_counts
        result["open_interest_zero_sentinel_timestamps"] = zero_sentinel_timestamps
    return result


def _safe_raw_relative(spec):
    return Path("raw") / spec["source_id"] / spec["symbol"] / spec["filename"]


def _write_bytes(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _atomic_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _directory_inventory(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Required prior-attempt staging is absent: {root}.")
    records = []
    total_bytes = 0
    for path in sorted((item for item in root.rglob("*") if item.is_file())):
        payload = path.read_bytes()
        total_bytes += len(payload)
        records.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "bytes": len(payload),
                "sha256": _sha256(payload),
            }
        )
    return {
        "file_count": len(records),
        "total_bytes": total_bytes,
        "inventory_sha256": _sha256(canonical_json_bytes(records)),
    }


def _expected_zero_sentinel_timestamps_by_asset(registry):
    expected = {asset: [] for asset in ASSET_SYMBOLS}
    for spec in registry:
        if spec["source_id"] != "OPEN_INTEREST_METRICS":
            continue
        expected[spec["asset"]].extend(
            timestamp
            for timestamp in OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMPS
            if timestamp[:10] == spec["period"]
        )
    return expected


def _validate_attempt_3_resume_staging(root, registry):
    if len(registry) < ATTEMPT_3_RESUME_OBJECT_COUNT:
        raise RuntimeError("Frozen registry is shorter than the resume prefix.")
    expected_paths = []
    for spec in registry[:ATTEMPT_3_RESUME_OBJECT_COUNT]:
        raw_relative = _safe_raw_relative(spec)
        expected_paths.extend(
            (raw_relative.as_posix(), raw_relative.as_posix() + ".CHECKSUM")
        )
    observed_paths = sorted(
        path.relative_to(root).as_posix()
        for path in Path(root).rglob("*")
        if path.is_file()
    )
    if observed_paths != sorted(expected_paths):
        raise RuntimeError("Attempt 3 staging is not the frozen contiguous prefix.")


class DerivativesContextDatasetLocker:
    def __init__(self, fetch_bytes=None):
        self.fetch_bytes = _default_fetch_bytes if fetch_bytes is None else fetch_bytes

    def run(
        self,
        output_root,
        authorization_phrase,
        prior_attempt_1_staging=None,
        prior_attempt_2_staging=None,
        prior_attempt_3_staging=None,
    ):
        if authorization_phrase != AUTHORIZATION_PHRASE:
            raise PermissionError(
                "Exact one-shot recovery Attempt 4 authorization is required."
            )
        if any(
            path is None
            for path in (
                prior_attempt_1_staging,
                prior_attempt_2_staging,
                prior_attempt_3_staging,
            )
        ):
            raise PermissionError(
                "Preserved Attempt 1, Attempt 2 and Attempt 3 staging are required."
            )
        prior_attempt_1_staging = Path(prior_attempt_1_staging).resolve()
        prior_attempt_2_staging = Path(prior_attempt_2_staging).resolve()
        prior_attempt_3_staging = Path(prior_attempt_3_staging).resolve()
        prior_paths = {
            prior_attempt_1_staging,
            prior_attempt_2_staging,
            prior_attempt_3_staging,
        }
        if len(prior_paths) != 3:
            raise ValueError("Prior-attempt staging directories must be distinct.")
        attempt_1_inventory = _directory_inventory(prior_attempt_1_staging)
        attempt_2_inventory = _directory_inventory(prior_attempt_2_staging)
        attempt_3_inventory = _directory_inventory(prior_attempt_3_staging)
        if (
            attempt_1_inventory["file_count"] == 0
            or attempt_2_inventory["file_count"] == 0
            or attempt_3_inventory["file_count"] == 0
        ):
            raise RuntimeError("Preserved prior-attempt staging must be non-empty.")
        expected_attempt_3_inventory = {
            "file_count": ATTEMPT_3_STAGING_FILE_COUNT,
            "total_bytes": ATTEMPT_3_STAGING_TOTAL_BYTES,
            "inventory_sha256": ATTEMPT_3_STAGING_INVENTORY_SHA256,
        }
        if attempt_3_inventory != expected_attempt_3_inventory:
            raise RuntimeError("Attempt 3 staging inventory mismatch.")
        output_root = Path(output_root).resolve()
        if output_root.exists():
            raise FileExistsError(f"Final dataset lock already exists: {output_root}.")
        staging = output_root.with_name(f".{output_root.name}.staging")
        if staging in prior_paths or output_root in prior_paths:
            raise ValueError("Recovery output must not reuse prior-attempt staging.")
        if staging.exists():
            raise FileExistsError(f"Dataset-lock staging already exists: {staging}.")
        staging.mkdir(parents=True)

        object_records = []
        aggregate_optional_blank_counts = {
            name: 0 for name in OPTIONAL_METRICS_COLUMNS
        }
        aggregate_zero_sentinel_timestamps = {asset: [] for asset in ASSET_SYMBOLS}
        normalized_chunks = {
            (source_id, asset): []
            for source_id in SOURCE_SPECS
            for asset in ASSET_SYMBOLS
        }
        seen_normalized_timestamps = {
            identity: set() for identity in normalized_chunks
        }
        registry = expected_object_registry()
        _validate_attempt_3_resume_staging(prior_attempt_3_staging, registry)
        for object_number, spec in enumerate(registry, start=1):
            if (
                object_number == 1
                or object_number % 25 == 0
                or object_number == len(registry)
            ):
                print(
                    f"DATASET_LOCK_PROGRESS={object_number}/{len(registry)}|"
                    f"{spec['source_id']}|{spec['asset']}|{spec['period']}",
                    flush=True,
                )
            if object_number <= ATTEMPT_3_RESUME_OBJECT_COUNT:
                prior_raw = prior_attempt_3_staging / _safe_raw_relative(spec)
                zip_bytes = prior_raw.read_bytes()
                checksum_bytes = Path(str(prior_raw) + ".CHECKSUM").read_bytes()
                acquisition_origin = "VERIFIED_ATTEMPT_3_STAGING"
            else:
                zip_bytes = self.fetch_bytes(spec["url"])
                checksum_bytes = self.fetch_bytes(spec["checksum_url"])
                acquisition_origin = "PUBLIC_SOURCE_ATTEMPT_4"
            validated = validate_source_archive(spec, zip_bytes, checksum_bytes)
            validated["acquisition_origin"] = acquisition_origin
            for name, count in validated.get("optional_blank_counts", {}).items():
                aggregate_optional_blank_counts[name] += count
            aggregate_zero_sentinel_timestamps[spec["asset"]].extend(
                validated.get("open_interest_zero_sentinel_timestamps", [])
            )
            raw_relative = _safe_raw_relative(spec)
            _write_bytes(staging / raw_relative, zip_bytes)
            _write_bytes(staging / (str(raw_relative) + ".CHECKSUM"), checksum_bytes)

            normalized_rows = _csv_rows(validated.pop("normalized_bytes"))
            header = normalized_rows[0]
            expected_header = list(SOURCE_SPECS[spec["source_id"]]["normalized_header"])
            if header != expected_header:
                raise RuntimeError("Internal normalized schema mismatch.")
            identity = (spec["source_id"], spec["asset"])
            for row in normalized_rows[1:]:
                timestamp = row[0]
                if timestamp in seen_normalized_timestamps[identity]:
                    raise ValueError("Duplicate timestamp across frozen source objects.")
                seen_normalized_timestamps[identity].add(timestamp)
                normalized_chunks[identity].append(row)
            validated["raw_relative_path"] = raw_relative.as_posix()
            validated["checksum_relative_path"] = raw_relative.as_posix() + ".CHECKSUM"
            object_records.append(validated)

        expected_zero_sentinel_timestamps = (
            _expected_zero_sentinel_timestamps_by_asset(registry)
        )
        if aggregate_zero_sentinel_timestamps != expected_zero_sentinel_timestamps:
            raise RuntimeError("Frozen open-interest zero-sentinel registry mismatch.")

        normalized_records = []
        for source_id in SOURCE_SPECS:
            header = SOURCE_SPECS[source_id]["normalized_header"]
            for asset, symbol in ASSET_SYMBOLS.items():
                rows = normalized_chunks[(source_id, asset)]
                if not rows:
                    raise RuntimeError(f"Normalized dataset is empty: {source_id}|{asset}.")
                payload = _normalized_csv(header, rows)
                relative = Path("normalized") / symbol / f"{source_id}.csv"
                _write_bytes(staging / relative, payload)
                normalized_records.append(
                    {
                        "source_id": source_id,
                        "asset": asset,
                        "symbol": symbol,
                        "relative_path": relative.as_posix(),
                        "row_count": len(rows),
                        "first_timestamp_utc": rows[0][0],
                        "last_timestamp_utc": rows[-1][0],
                        "bytes": len(payload),
                        "sha256": _sha256(payload),
                    }
                )

        if _directory_inventory(prior_attempt_1_staging) != attempt_1_inventory:
            raise RuntimeError("Attempt 1 staging changed during recovery.")
        if _directory_inventory(prior_attempt_2_staging) != attempt_2_inventory:
            raise RuntimeError("Attempt 2 staging changed during recovery.")
        if _directory_inventory(prior_attempt_3_staging) != attempt_3_inventory:
            raise RuntimeError("Attempt 3 staging changed during recovery.")

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "component_id": COMPONENT_ID,
            "dataset_id": DATASET_ID,
            "execution_parent_commit": RECOVERY_PARENT_COMMIT,
            "hypothesis_parent_commit": PARENT_COMMIT,
            "parent_feasibility_report_sha256": PARENT_FEASIBILITY_REPORT_SHA256,
            "attempt_1_incident_sha256": ATTEMPT_1_INCIDENT_SHA256,
            "attempt_2_incident_sha256": ATTEMPT_2_INCIDENT_SHA256,
            "attempt_3_incident_sha256": ATTEMPT_3_INCIDENT_SHA256,
            "attempt_1_staging_inventory": attempt_1_inventory,
            "attempt_2_staging_inventory": attempt_2_inventory,
            "attempt_3_staging_inventory": attempt_3_inventory,
            "recovery_attempt": 4,
            "verified_resume_object_count": ATTEMPT_3_RESUME_OBJECT_COUNT,
            "public_download_object_count": len(registry)
            - ATTEMPT_3_RESUME_OBJECT_COUNT,
            "maximum_transport_attempts_per_fetch": MAXIMUM_TRANSPORT_ATTEMPTS,
            "maximum_transport_backoff_seconds": (
                MAXIMUM_TRANSPORT_BACKOFF_SECONDS
            ),
            "common_start_utc": COMMON_START_UTC,
            "common_end_exclusive_utc": COMMON_END_EXCLUSIVE_UTC,
            "asset_order": list(ASSET_SYMBOLS),
            "source_series_order": list(SOURCE_SPECS),
            "object_count": len(object_records),
            "normalized_file_count": len(normalized_records),
            "optional_metrics_blank_counts": aggregate_optional_blank_counts,
            "optional_metrics_blank_policy": "EXACT_BLANK_RECORDED_NO_FILL_UNUSED_RATIO_FIELDS",
            "open_interest_zero_sentinel_literal": (
                OPEN_INTEREST_ZERO_SENTINEL_LITERAL
            ),
            "open_interest_zero_sentinel_timestamp_sha256": (
                OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256
            ),
            "open_interest_zero_sentinel_timestamps_by_asset": (
                aggregate_zero_sentinel_timestamps
            ),
            "open_interest_zero_sentinel_count": sum(
                len(values) for values in aggregate_zero_sentinel_timestamps.values()
            ),
            "open_interest_zero_sentinel_policy": (
                "FROZEN_EXACT_PAIRED_ZERO_OMITTED_NO_FILL"
            ),
            "objects": object_records,
            "normalized_files": normalized_records,
            "source_objects_downloaded": True,
            "market_values_opened": True,
            "development_data_opened": True,
            "labels_generated": False,
            "model_training_executed": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "candidate_v2_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
            "status": "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_DATASET_LOCKED",
            "next_stage": "INDEPENDENTLY_REVIEW_LOCK_THEN_IMPLEMENT_FROZEN_CONTEXT_LEARNING_RUNNER",
        }
        payload = canonical_json_bytes(manifest)
        digest = _sha256(payload)
        _atomic_write(staging / "manifest.json", payload)
        _atomic_write(
            staging / "manifest.sha256",
            f"{digest}  manifest.json\n".encode("ascii"),
        )
        os.replace(staging, output_root)
        return {
            "status": "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_EVIDENCE_RECORDED",
            "dataset_root": str(output_root),
            "manifest_sha256": digest,
            "object_count": len(object_records),
            "normalized_file_count": len(normalized_records),
            "optional_metrics_blank_counts": aggregate_optional_blank_counts,
            "attempt_1_staging_inventory_sha256": attempt_1_inventory[
                "inventory_sha256"
            ],
            "attempt_2_staging_inventory_sha256": attempt_2_inventory[
                "inventory_sha256"
            ],
            "attempt_3_staging_inventory_sha256": attempt_3_inventory[
                "inventory_sha256"
            ],
            "verified_resume_object_count": ATTEMPT_3_RESUME_OBJECT_COUNT,
            "public_download_object_count": len(registry)
            - ATTEMPT_3_RESUME_OBJECT_COUNT,
            "open_interest_zero_sentinel_count": sum(
                len(values) for values in aggregate_zero_sentinel_timestamps.values()
            ),
            "recovery_attempt": 4,
            "market_values_opened": True,
            "labels_generated": False,
            "model_training_executed": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "candidate_v2_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
        }


def _verify_file(root, record, path_field, hash_field, bytes_field=None):
    path = root / record[path_field]
    if not path.is_file():
        raise RuntimeError(f"Locked dataset file missing: {record[path_field]}.")
    payload = path.read_bytes()
    if bytes_field is not None and len(payload) != record[bytes_field]:
        raise RuntimeError(f"Locked dataset byte-count mismatch: {record[path_field]}.")
    if _sha256(payload) != record[hash_field]:
        raise RuntimeError(f"Locked dataset hash mismatch: {record[path_field]}.")
    return payload


def read_locked_derivatives_context_dataset(
    dataset_root, *, expected_manifest_sha256=None, verify_raw=True
):
    root = Path(dataset_root).resolve()
    manifest_path = root / "manifest.json"
    sidecar_path = root / "manifest.sha256"
    if not manifest_path.is_file() or not sidecar_path.is_file():
        raise RuntimeError("Locked derivatives-context manifest is incomplete.")
    payload = manifest_path.read_bytes()
    digest = _sha256(payload)
    expected_sidecar = f"{digest}  manifest.json\n".encode("ascii")
    if sidecar_path.read_bytes() != expected_sidecar:
        raise RuntimeError("Locked derivatives-context manifest sidecar mismatch.")
    if expected_manifest_sha256 is not None and digest != expected_manifest_sha256:
        raise RuntimeError("Locked derivatives-context manifest identity mismatch.")
    try:
        manifest = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Locked derivatives-context manifest is invalid JSON.") from exc
    if canonical_json_bytes(manifest) != payload:
        raise RuntimeError("Locked derivatives-context manifest is not canonical.")
    if manifest.get("dataset_id") != DATASET_ID:
        raise RuntimeError("Locked derivatives-context dataset identity mismatch.")
    if manifest.get("object_count") != len(expected_object_registry()):
        raise RuntimeError("Locked derivatives-context object count mismatch.")
    if manifest.get("normalized_file_count") != 12:
        raise RuntimeError("Locked derivatives-context normalized registry mismatch.")
    if manifest.get("recovery_attempt") != 4:
        raise RuntimeError("Locked derivatives-context recovery identity mismatch.")
    if manifest.get("execution_parent_commit") != RECOVERY_PARENT_COMMIT:
        raise RuntimeError("Locked derivatives-context execution binding mismatch.")
    if manifest.get("attempt_1_incident_sha256") != ATTEMPT_1_INCIDENT_SHA256:
        raise RuntimeError("Locked derivatives-context incident binding mismatch.")
    if manifest.get("attempt_2_incident_sha256") != ATTEMPT_2_INCIDENT_SHA256:
        raise RuntimeError("Locked Attempt 2 incident binding mismatch.")
    if manifest.get("attempt_3_incident_sha256") != ATTEMPT_3_INCIDENT_SHA256:
        raise RuntimeError("Locked Attempt 3 incident binding mismatch.")
    for attempt in (1, 2, 3):
        prior_inventory = manifest.get(f"attempt_{attempt}_staging_inventory")
        if not isinstance(prior_inventory, dict) or set(prior_inventory) != {
            "file_count",
            "total_bytes",
            "inventory_sha256",
        }:
            raise RuntimeError("Locked prior-staging inventory schema mismatch.")
        if (
            not isinstance(prior_inventory["file_count"], int)
            or prior_inventory["file_count"] <= 0
            or not isinstance(prior_inventory["total_bytes"], int)
            or prior_inventory["total_bytes"] <= 0
            or re.fullmatch(r"[0-9a-f]{64}", prior_inventory["inventory_sha256"])
            is None
        ):
            raise RuntimeError("Locked prior-staging inventory value mismatch.")
    if manifest["attempt_3_staging_inventory"] != {
        "file_count": ATTEMPT_3_STAGING_FILE_COUNT,
        "total_bytes": ATTEMPT_3_STAGING_TOTAL_BYTES,
        "inventory_sha256": ATTEMPT_3_STAGING_INVENTORY_SHA256,
    }:
        raise RuntimeError("Locked Attempt 3 staging inventory mismatch.")
    if (
        manifest.get("verified_resume_object_count")
        != ATTEMPT_3_RESUME_OBJECT_COUNT
        or manifest.get("public_download_object_count")
        != len(expected_object_registry()) - ATTEMPT_3_RESUME_OBJECT_COUNT
        or manifest.get("maximum_transport_attempts_per_fetch")
        != MAXIMUM_TRANSPORT_ATTEMPTS
        or manifest.get("maximum_transport_backoff_seconds")
        != MAXIMUM_TRANSPORT_BACKOFF_SECONDS
    ):
        raise RuntimeError("Locked recovery transport evidence mismatch.")
    if manifest.get("optional_metrics_blank_policy") != (
        "EXACT_BLANK_RECORDED_NO_FILL_UNUSED_RATIO_FIELDS"
    ):
        raise RuntimeError("Locked optional-metrics blank policy mismatch.")
    if manifest.get("open_interest_zero_sentinel_policy") != (
        "FROZEN_EXACT_PAIRED_ZERO_OMITTED_NO_FILL"
    ):
        raise RuntimeError("Locked open-interest zero-sentinel policy mismatch.")
    if (
        manifest.get("open_interest_zero_sentinel_literal")
        != OPEN_INTEREST_ZERO_SENTINEL_LITERAL
        or manifest.get("open_interest_zero_sentinel_timestamp_sha256")
        != OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256
    ):
        raise RuntimeError("Locked open-interest zero-sentinel identity mismatch.")
    expected_identities = [
        (item["source_id"], item["asset"], item["period"], item["key"], item["filename"])
        for item in expected_object_registry()
    ]
    observed_identities = [
        (
            item.get("source_id"),
            item.get("asset"),
            item.get("period"),
            item.get("key"),
            item.get("filename"),
        )
        for item in manifest.get("objects", [])
    ]
    if observed_identities != expected_identities:
        raise RuntimeError("Locked derivatives-context object identity registry mismatch.")
    expected_origins = [
        "VERIFIED_ATTEMPT_3_STAGING"
        if number <= ATTEMPT_3_RESUME_OBJECT_COUNT
        else "PUBLIC_SOURCE_ATTEMPT_4"
        for number in range(1, len(expected_identities) + 1)
    ]
    if [item.get("acquisition_origin") for item in manifest["objects"]] != (
        expected_origins
    ):
        raise RuntimeError("Locked recovery acquisition-origin registry mismatch.")
    aggregate_optional_blank_counts = {
        name: 0 for name in OPTIONAL_METRICS_COLUMNS
    }
    aggregate_zero_sentinel_timestamps = {asset: [] for asset in ASSET_SYMBOLS}
    for record in manifest["objects"]:
        counts = record.get("optional_blank_counts")
        if record["source_id"] == "OPEN_INTEREST_METRICS":
            if not isinstance(counts, dict) or set(counts) != set(OPTIONAL_METRICS_COLUMNS):
                raise RuntimeError("Locked optional-metrics missingness schema mismatch.")
            if any(not isinstance(value, int) or value < 0 for value in counts.values()):
                raise RuntimeError("Locked optional-metrics missingness count mismatch.")
            for name, count in counts.items():
                aggregate_optional_blank_counts[name] += count
            zero_timestamps = record.get("open_interest_zero_sentinel_timestamps")
            if not isinstance(zero_timestamps, list):
                raise RuntimeError("Locked zero-sentinel timestamp schema mismatch.")
            aggregate_zero_sentinel_timestamps[record["asset"]].extend(
                zero_timestamps
            )
        elif counts is not None:
            raise RuntimeError("Unexpected optional-metrics evidence on another source.")
    if manifest.get("optional_metrics_blank_counts") != aggregate_optional_blank_counts:
        raise RuntimeError("Locked optional-metrics aggregate mismatch.")
    expected_zero_sentinel_timestamps = _expected_zero_sentinel_timestamps_by_asset(
        expected_object_registry()
    )
    if (
        aggregate_zero_sentinel_timestamps != expected_zero_sentinel_timestamps
        or manifest.get("open_interest_zero_sentinel_timestamps_by_asset")
        != expected_zero_sentinel_timestamps
        or manifest.get("open_interest_zero_sentinel_count")
        != sum(len(values) for values in expected_zero_sentinel_timestamps.values())
    ):
        raise RuntimeError("Locked open-interest zero-sentinel registry mismatch.")
    if verify_raw:
        for spec, record in zip(expected_object_registry(), manifest["objects"]):
            zip_payload = _verify_file(
                root, record, "raw_relative_path", "zip_sha256", "zip_bytes"
            )
            checksum_payload = _verify_file(
                root,
                record,
                "checksum_relative_path",
                "checksum_sha256",
                "checksum_bytes",
            )
            official_digest = parse_official_checksum(
                checksum_payload, record["filename"]
            )
            if official_digest != _sha256(zip_payload):
                raise RuntimeError(
                    f"Locked official checksum mismatch: {record['raw_relative_path']}."
                )
            revalidated = validate_source_archive(spec, zip_payload, checksum_payload)
            revalidated.pop("normalized_bytes")
            for field, value in revalidated.items():
                if record.get(field) != value:
                    raise RuntimeError(
                        f"Locked raw validation evidence mismatch: {record['filename']}."
                    )

    normalized = {}
    for record in manifest["normalized_files"]:
        data = _verify_file(root, record, "relative_path", "sha256", "bytes")
        frame = pd.read_csv(io.BytesIO(data), dtype=str)
        expected_columns = SOURCE_SPECS[record["source_id"]]["normalized_header"]
        if tuple(frame.columns) != expected_columns or len(frame) != record["row_count"]:
            raise RuntimeError("Locked normalized source schema or row count mismatch.")
        normalized[(record["source_id"], record["asset"])] = frame
    if set(normalized) != {
        (source_id, asset)
        for source_id in SOURCE_SPECS
        for asset in ASSET_SYMBOLS
    }:
        raise RuntimeError("Locked normalized source identities mismatch.")

    sources = {}
    for asset in ASSET_SYMBOLS:
        funding = normalized[("FUNDING_RATE", asset)].copy()
        funding.index = pd.to_datetime(funding.pop("source_timestamp"), utc=True)
        funding["funding_rate"] = pd.to_numeric(funding["funding_rate"], errors="raise")

        open_interest = normalized[("OPEN_INTEREST_METRICS", asset)].copy()
        open_interest.index = pd.to_datetime(
            open_interest.pop("source_timestamp"), utc=True
        )
        open_interest["open_interest"] = pd.to_numeric(
            open_interest["open_interest"], errors="raise"
        )
        if (open_interest["open_interest"] <= 0).any():
            raise RuntimeError(f"Locked open interest is not positive for {asset}.")

        mark = normalized[("MARK_PRICE_12H", asset)].copy()
        index = normalized[("INDEX_PRICE_12H", asset)].copy()
        mark.index = pd.to_datetime(mark.pop("open_timestamp"), utc=True)
        index.index = pd.to_datetime(index.pop("open_timestamp"), utc=True)
        if not mark.index.equals(index.index):
            raise RuntimeError(f"Mark/index timestamp mismatch for {asset}.")
        mark_close_time = pd.to_datetime(mark.pop("close_timestamp"), utc=True)
        index_close_time = pd.to_datetime(index.pop("close_timestamp"), utc=True)
        if not mark_close_time.equals(index_close_time):
            raise RuntimeError(f"Mark/index completion-time mismatch for {asset}.")
        mark_index = pd.DataFrame(
            {
                "mark_close": pd.to_numeric(mark["close"], errors="raise"),
                "index_close": pd.to_numeric(index["close"], errors="raise"),
            },
            index=mark.index,
        )
        for name, frame in (
            ("funding", funding),
            ("open_interest", open_interest),
            ("mark_index_12h", mark_index),
        ):
            if not frame.index.is_monotonic_increasing or not frame.index.is_unique:
                raise RuntimeError(f"Locked {name} chronology mismatch for {asset}.")
            if not all(math.isfinite(float(value)) for value in frame.to_numpy().flat):
                raise RuntimeError(f"Locked {name} contains non-finite values for {asset}.")
        sources[asset] = {
            "funding": funding,
            "open_interest": open_interest,
            "mark_index_12h": mark_index,
        }
    return sources, manifest, digest


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Lock or independently read the frozen derivatives-context dataset."
    )
    parser.add_argument("--declaration-only", action="store_true")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--authorization-phrase")
    parser.add_argument("--prior-attempt-1-staging", type=Path)
    parser.add_argument("--prior-attempt-2-staging", type=Path)
    parser.add_argument("--prior-attempt-3-staging", type=Path)
    parser.add_argument("--read-summary", type=Path)
    parser.add_argument("--expected-manifest-sha256")
    args = parser.parse_args(argv)
    if args.output_root is not None:
        result = DerivativesContextDatasetLocker().run(
            args.output_root,
            args.authorization_phrase,
            args.prior_attempt_1_staging,
            args.prior_attempt_2_staging,
            args.prior_attempt_3_staging,
        )
    elif args.read_summary is not None:
        sources, manifest, digest = read_locked_derivatives_context_dataset(
            args.read_summary,
            expected_manifest_sha256=args.expected_manifest_sha256,
        )
        result = {
            "status": "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_READER_PASS",
            "dataset_id": manifest["dataset_id"],
            "manifest_sha256": digest,
            "asset_order": list(sources),
            "source_series_order": list(SOURCE_SPECS),
            "object_count": manifest["object_count"],
            "recovery_attempt": manifest["recovery_attempt"],
            "verified_resume_object_count": manifest[
                "verified_resume_object_count"
            ],
            "public_download_object_count": manifest[
                "public_download_object_count"
            ],
            "open_interest_zero_sentinel_count": manifest[
                "open_interest_zero_sentinel_count"
            ],
            "optional_metrics_blank_counts": manifest[
                "optional_metrics_blank_counts"
            ],
            "labels_generated": False,
            "model_training_executed": False,
            "candidate_v2_authorized": False,
            "real_orders_submitted": False,
        }
    else:
        result = dataset_lock_declaration()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
