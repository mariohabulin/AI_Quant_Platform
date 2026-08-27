"""Fail-closed Kraken BTC/ETH/XRP native-daily acquisition and data lock."""

import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

DATASET_SCHEMA_VERSION = 2
DATASET_ID = (
    "kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2"
)
ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
RESEARCH_START_INCLUSIVE = "2019-01-01T00:00:00Z"
RESEARCH_END_EXCLUSIVE = "2026-04-01T00:00:00Z"
INTERVAL_MINUTES = 1440
CANONICAL_COLUMN_ORDER = ("Date", "Open", "High", "Low", "Close", "Volume")
ARCHIVE_COMPLETE_FILENAME = "Kraken_OHLCVT.zip"
ARCHIVE_Q1_2026_FILENAME = "Kraken_OHLCVT_Q1_2026.zip"
OFFICIAL_COMPLETE_ARCHIVE_URL = (
    "https://drive.google.com/file/d/1ptNqWYidLkhb2VAKuLCxmp2OXEfGO-AP/"
    "view?usp=sharing"
)
OFFICIAL_QUARTERLY_ARCHIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/"
    "15RSlNuW_h0kVM8or8McOGOMfHeBFvFGI?usp=sharing"
)
PROVIDER_AUDIT_NORMALIZED_SHA256 = (
    "fc71ff88e11b5984ebf5168fdbe09446554f720fc3ec0241eef0839ca90b3fca"
)
LOCK_PROTOCOL_NORMALIZED_SHA256 = (
    "814cd561e1869023832315050683665c142f3b216ae354d45019a28edcc6a05a"
)
DEFAULT_PROVIDER_AUDIT_PATH = Path(
    "BTC_ETH_XRP_PROVIDER_AND_HISTORICAL_AVAILABILITY_AUDIT_V1.md"
)
DEFAULT_LOCK_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_PROTOCOL_V2.md"
)
FROZEN_ARCHIVE_SPECS = {
    ARCHIVE_COMPLETE_FILENAME: {
        "role": "COMPLETE",
        "bytes": 7_885_068_519,
        "sha256": "e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d",
    },
    ARCHIVE_Q1_2026_FILENAME: {
        "role": "QUARTERLY_UPDATE",
        "bytes": 545_431_093,
        "sha256": "95b2fec056bbacdfb5426e859a756d269bb19ba31eac7ea9e814759dfccd77b1",
    },
}
PAIR_METADATA = {
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


def _parse_utc(value, label):
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a UTC timestamp string.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} is not a valid UTC timestamp.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be UTC.")
    return parsed.astimezone(timezone.utc)


def _iso_from_unix(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read contract document: {path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def load_provider_audit(path, expected_sha256=PROVIDER_AUDIT_NORMALIZED_SHA256):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(
            f"Provider audit SHA256 mismatch: {digest} != {expected_sha256}."
        )
    text = raw.decode("utf-8")
    required = (
        "BTC/ETH/XRP Provider and Historical Availability Audit v1",
        "REVIEWED_SOURCE_SELECTED_ACQUISITION_NOT_EXECUTED",
        "Kraken Spot official OHLCVT archives",
        "byte-level historical bucket inventory completed: `false`",
        "performance evaluation executed: `false`",
    )
    if any(value not in text for value in required):
        raise RuntimeError("Provider audit required contract text is missing.")
    return text, digest


def load_lock_protocol(path, expected_sha256=LOCK_PROTOCOL_NORMALIZED_SHA256):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(
            f"Lock protocol SHA256 mismatch: {digest} != {expected_sha256}."
        )
    text = raw.decode("utf-8")
    required = (
        "Kraken BTC/ETH/XRP Daily Dataset Lock Protocol v2",
        "ARCHIVE_ONLY_BUILDER_REVIEWED_LOCK_NOT_EXECUTED",
        DATASET_ID,
        "REST_STITCHING_PROHIBITED",
        FROZEN_ARCHIVE_SPECS[ARCHIVE_COMPLETE_FILENAME]["sha256"],
        FROZEN_ARCHIVE_SPECS[ARCHIVE_Q1_2026_FILENAME]["sha256"],
    )
    if any(value not in text for value in required):
        raise RuntimeError("Lock protocol required contract text is missing.")
    return text, digest


@dataclass(frozen=True)
class KrakenDailyDatasetContract:
    dataset_id: str = DATASET_ID
    assets: tuple = ASSET_ORDER
    start: str = RESEARCH_START_INCLUSIVE
    end: str = RESEARCH_END_EXCLUSIVE
    interval_minutes: int = INTERVAL_MINUTES

    def __post_init__(self):
        if not isinstance(self.dataset_id, str) or not self.dataset_id.strip():
            raise ValueError("Dataset ID must be nonempty.")
        if tuple(self.assets) != ASSET_ORDER:
            raise ValueError("The asset order must remain BTC-USD, ETH-USD, XRP-USD.")
        if self.interval_minutes != INTERVAL_MINUTES:
            raise ValueError("The interval must remain native 1440-minute daily.")
        start = _parse_utc(self.start, "Research start")
        end = _parse_utc(self.end, "Research end")
        if any((start.hour, start.minute, start.second, start.microsecond)) or any(
            (end.hour, end.minute, end.second, end.microsecond)
        ):
            raise ValueError("Research boundaries must align to UTC midnight.")
        if end <= start:
            raise ValueError("Research end must be after start.")
        if (end - start).total_seconds() % 86400:
            raise ValueError("Research range must contain whole UTC days.")

    @property
    def start_datetime(self):
        return _parse_utc(self.start, "Research start")

    @property
    def end_datetime(self):
        return _parse_utc(self.end, "Research end")

    @property
    def start_unix(self):
        return int(self.start_datetime.timestamp())

    @property
    def end_unix(self):
        return int(self.end_datetime.timestamp())

    @property
    def expected_daily_buckets(self):
        return int((self.end_datetime - self.start_datetime).days)

    def as_dict(self):
        return {
            "dataset_id": self.dataset_id,
            "assets": list(self.assets),
            "provider": "Kraken Spot",
            "start": self.start,
            "end": self.end,
            "range_semantics": "START_INCLUSIVE_END_EXCLUSIVE",
            "timeframe": "1d",
            "interval_minutes": self.interval_minutes,
            "timestamp_alignment": "UTC_MIDNIGHT",
            "expected_daily_buckets": self.expected_daily_buckets,
        }


@dataclass(frozen=True)
class ArchiveInput:
    path: Path
    role: str
    source_url: str
    retrieved_at: str

    def __post_init__(self):
        path = Path(self.path)
        role = str(self.role).strip().upper()
        if not path.is_file():
            raise FileNotFoundError(f"Archive does not exist: {path}")
        if path.suffix.lower() != ".zip":
            raise ValueError("Archive input must be a ZIP file.")
        if role not in {"COMPLETE", "QUARTERLY_UPDATE"}:
            raise ValueError("Archive role must be COMPLETE or QUARTERLY_UPDATE.")
        if not isinstance(self.source_url, str) or not self.source_url.startswith(
            "https://"
        ):
            raise ValueError("Archive source URL must use HTTPS.")
        _parse_utc(self.retrieved_at, "Archive retrieval time")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "role", role)


@dataclass(frozen=True)
class _Candle:
    timestamp: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trades: int

    @property
    def comparable(self):
        return (
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
            self.trades,
        )


def _decimal(value, label):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise RuntimeError(f"Candle {label} is not numeric.") from exc
    if not number.is_finite():
        raise RuntimeError(f"Candle {label} must be finite.")
    return number


def _canonical_decimal(value):
    if value == 0:
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _validate_candle(values, *, source):
    if not isinstance(values, (list, tuple)) or len(values) != 7:
        raise RuntimeError(f"{source} candle must contain exactly seven columns.")
    try:
        timestamp = int(values[0])
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{source} candle timestamp is invalid.") from exc
    if timestamp % 86400:
        raise RuntimeError(f"{source} candle timestamp is not UTC midnight.")
    open_ = _decimal(values[1], "Open")
    high = _decimal(values[2], "High")
    low = _decimal(values[3], "Low")
    close = _decimal(values[4], "Close")
    volume = _decimal(values[5], "Volume")
    try:
        trades = int(values[6])
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{source} candle trade count is invalid.") from exc
    if min(open_, high, low, close) <= 0:
        raise RuntimeError(f"{source} candle prices must be positive.")
    if high < max(open_, close) or low > min(open_, close) or high < low:
        raise RuntimeError(f"{source} candle price geometry is invalid.")
    if volume < 0:
        raise RuntimeError(f"{source} candle volume must be nonnegative.")
    if trades <= 0:
        raise RuntimeError(f"{source} candle trade count must be positive.")
    return _Candle(timestamp, open_, high, low, close, volume, trades)


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _file_sha256(path, chunk_bytes=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(chunk_bytes), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_new(path, payload):
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _segments(observed_timestamps):
    if not observed_timestamps:
        return []
    ordered = sorted(observed_timestamps)
    result = []
    start = previous = ordered[0]
    for timestamp in ordered[1:]:
        if timestamp != previous + 86400:
            result.append(
                {
                    "start": _iso_from_unix(start),
                    "end_exclusive": _iso_from_unix(previous + 86400),
                    "rows": ((previous - start) // 86400) + 1,
                }
            )
            start = timestamp
        previous = timestamp
    result.append(
        {
            "start": _iso_from_unix(start),
            "end_exclusive": _iso_from_unix(previous + 86400),
            "rows": ((previous - start) // 86400) + 1,
        }
    )
    return result


def build_review_declaration(
    provider_audit_path=DEFAULT_PROVIDER_AUDIT_PATH,
    lock_protocol_path=DEFAULT_LOCK_PROTOCOL_PATH,
):
    _, audit_digest = load_provider_audit(provider_audit_path)
    _, protocol_digest = load_lock_protocol(lock_protocol_path)
    return {
        "schema_version": DATASET_SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "status": "KRAKEN_DAILY_ARCHIVE_ONLY_BUILDER_REVIEWED_LOCK_REQUIRED",
        "provider": "Kraken Spot",
        "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
        "provider_audit_sha256_match": (
            audit_digest == PROVIDER_AUDIT_NORMALIZED_SHA256
        ),
        "lock_protocol_sha256_match": (
            protocol_digest == LOCK_PROTOCOL_NORMALIZED_SHA256
        ),
        "bounded_data_acquisition_review_eligible": True,
        "data_acquisition_executed": False,
        "network_requests_executed": False,
        "byte_level_historical_bucket_inventory_completed": False,
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


def _validate_frozen_archive_evidence(contract, archive_evidence):
    if contract != KrakenDailyDatasetContract():
        return
    expected_names = tuple(FROZEN_ARCHIVE_SPECS)
    observed_names = tuple(item["filename"] for item in archive_evidence)
    if observed_names != expected_names:
        raise RuntimeError(
            "Production archive order/identity mismatch: "
            f"{observed_names} != {expected_names}."
        )
    for evidence in archive_evidence:
        expected = FROZEN_ARCHIVE_SPECS[evidence["filename"]]
        for field in ("role", "bytes", "sha256"):
            if evidence[field] != expected[field]:
                raise RuntimeError(
                    f"Frozen archive byte evidence mismatch for "
                    f"{evidence['filename']} field {field}."
                )


class KrakenDailyDatasetBuilder:
    """Inventory exact official archives and publish one immutable lock."""

    def __init__(
        self,
        *,
        contract=None,
        archive_inputs,
        provider_audit_path=DEFAULT_PROVIDER_AUDIT_PATH,
        lock_protocol_path=DEFAULT_LOCK_PROTOCOL_PATH,
    ):
        self.contract = contract or KrakenDailyDatasetContract()
        if not isinstance(self.contract, KrakenDailyDatasetContract):
            raise TypeError("Contract must be KrakenDailyDatasetContract.")
        self.archive_inputs = tuple(archive_inputs)
        if not self.archive_inputs or any(
            not isinstance(value, ArchiveInput) for value in self.archive_inputs
        ):
            raise TypeError("Archive inputs must contain ArchiveInput values.")
        if sum(value.role == "COMPLETE" for value in self.archive_inputs) != 1:
            raise ValueError("Acquisition requires exactly one COMPLETE archive.")
        self.provider_audit_path = Path(provider_audit_path)
        _, self.provider_audit_sha256 = load_provider_audit(self.provider_audit_path)
        self.lock_protocol_path = Path(lock_protocol_path)
        _, self.lock_protocol_sha256 = load_lock_protocol(self.lock_protocol_path)
        self._inventory_cache = None

    def inventory_archives(self):
        if self._inventory_cache is not None:
            return self._inventory_cache
        archive_evidence = []
        selected = {asset: [] for asset in ASSET_ORDER}
        for archive_index, source in enumerate(self.archive_inputs):
            payload_sha256 = _file_sha256(source.path)
            try:
                with zipfile.ZipFile(source.path) as archive:
                    infos = archive.infolist()
                    names = [info.filename for info in infos]
                    if len(names) != len(set(names)):
                        raise RuntimeError(
                            f"Archive contains duplicate member names: {source.path.name}."
                        )
                    if any(info.flag_bits & 0x1 for info in infos):
                        raise RuntimeError(
                            f"Encrypted archive members are prohibited: {source.path.name}."
                        )
                    members = [
                        {
                            "name": info.filename,
                            "uncompressed_bytes": info.file_size,
                            "compressed_bytes": info.compress_size,
                            "crc32": f"{info.CRC:08x}",
                            "is_directory": info.is_dir(),
                        }
                        for info in infos
                    ]
                    for asset in ASSET_ORDER:
                        required = f"{PAIR_METADATA[asset]['archive_pair_stem']}_1440.csv"
                        matches = [
                            info for info in infos
                            if not info.is_dir() and Path(info.filename).name == required
                        ]
                        if not matches:
                            raise RuntimeError(
                                f"{asset} required 1440-minute archive member is missing "
                                f"from {source.path.name}."
                            )
                        if len(matches) != 1:
                            raise RuntimeError(
                                f"Archive contains multiple 1440-minute members for "
                                f"{asset}: {source.path.name}."
                            )
                        selected[asset].append(
                            {
                                "archive_index": archive_index,
                                "archive_filename": source.path.name,
                                "archive_sha256": payload_sha256,
                                "member_name": matches[0].filename,
                            }
                        )
            except (OSError, zipfile.BadZipFile) as exc:
                raise RuntimeError(f"Unable to inventory ZIP archive: {source.path}") from exc
            archive_evidence.append(
                {
                    "filename": source.path.name,
                    "role": source.role,
                    "source_url": source.source_url,
                    "retrieved_at": source.retrieved_at,
                    "bytes": source.path.stat().st_size,
                    "sha256": payload_sha256,
                    "member_count": len(members),
                    "members": members,
                }
            )
        _validate_frozen_archive_evidence(self.contract, archive_evidence)
        inventory = {
            "schema_version": 1,
            "inventory_scope": "EVERY_ARCHIVE_MEMBER_BEFORE_SELECTION",
            "selected_interval_minutes": INTERVAL_MINUTES,
            "archives": archive_evidence,
        }
        self._inventory_cache = (inventory, selected)
        return self._inventory_cache

    def _read_archive_member(self, source, member_name, asset):
        rows = {}
        try:
            with (
                zipfile.ZipFile(source.path) as archive,
                archive.open(member_name) as raw,
                io.TextIOWrapper(raw, encoding="utf-8", newline="") as wrapper,
            ):
                for row_number, values in enumerate(csv.reader(wrapper), start=1):
                    if not values:
                        continue
                    candle = _validate_candle(
                        values,
                        source=f"{source.path.name}:{member_name}:{row_number}",
                    )
                    if candle.timestamp in rows:
                        if rows[candle.timestamp].comparable != candle.comparable:
                            raise RuntimeError(
                                f"Conflicting duplicate inside {source.path.name} "
                                f"for {asset} at {_iso_from_unix(candle.timestamp)}."
                            )
                        continue
                    if (
                        self.contract.start_unix
                        <= candle.timestamp
                        < self.contract.end_unix
                    ):
                        rows[candle.timestamp] = candle
        except (OSError, UnicodeError, csv.Error, zipfile.BadZipFile) as exc:
            raise RuntimeError(
                f"Unable to read {asset} native daily archive member."
            ) from exc
        return rows

    def load_archive_rows(self):
        _, selected = self.inventory_archives()
        merged = {asset: {} for asset in ASSET_ORDER}
        equal_duplicates = {asset: 0 for asset in ASSET_ORDER}
        contributions = {asset: [] for asset in ASSET_ORDER}
        for asset in ASSET_ORDER:
            for item in selected[asset]:
                source = self.archive_inputs[item["archive_index"]]
                rows = self._read_archive_member(source, item["member_name"], asset)
                for timestamp, candle in rows.items():
                    previous = merged[asset].get(timestamp)
                    if previous is not None:
                        if previous.comparable != candle.comparable:
                            raise RuntimeError(
                                f"Conflicting duplicate for {asset} at "
                                f"{_iso_from_unix(timestamp)} across official archives."
                            )
                        equal_duplicates[asset] += 1
                    else:
                        merged[asset][timestamp] = candle
                ordered = sorted(rows)
                contributions[asset].append(
                    {
                        "archive_filename": item["archive_filename"],
                        "archive_sha256": item["archive_sha256"],
                        "member_name": item["member_name"],
                        "rows_in_research_window": len(ordered),
                        "first_timestamp": (
                            _iso_from_unix(ordered[0]) if ordered else None
                        ),
                        "last_timestamp": (
                            _iso_from_unix(ordered[-1]) if ordered else None
                        ),
                    }
                )
        return {
            "rows": merged,
            "equal_duplicates": equal_duplicates,
            "contributions": contributions,
        }

    @staticmethod
    def _canonical_csv_bytes(rows):
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(CANONICAL_COLUMN_ORDER)
        for timestamp in sorted(rows):
            candle = rows[timestamp]
            writer.writerow(
                [
                    _iso_from_unix(timestamp),
                    _canonical_decimal(candle.open),
                    _canonical_decimal(candle.high),
                    _canonical_decimal(candle.low),
                    _canonical_decimal(candle.close),
                    _canonical_decimal(candle.volume),
                ]
            )
        return output.getvalue().encode("utf-8")

    def _asset_filename(self, asset):
        return (
            f"{asset.lower().replace('-', '_')}_1d_"
            f"{self.contract.start[:10].replace('-', '')}_"
            f"{self.contract.end[:10].replace('-', '')}.csv"
        )

    def build(self, output_root):
        output_root = Path(output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        final = output_root / self.contract.dataset_id
        if final.exists():
            raise FileExistsError(f"Refusing to overwrite existing dataset: {final}")

        inventory, _ = self.inventory_archives()
        archive_result = self.load_archive_rows()
        merged_assets = {}
        asset_evidence = {}
        for asset in ASSET_ORDER:
            archive_rows = archive_result["rows"][asset]
            merged = dict(archive_rows)
            expected = list(
                range(
                    self.contract.start_unix,
                    self.contract.end_unix,
                    86400,
                )
            )
            missing = [timestamp for timestamp in expected if timestamp not in merged]
            merged_assets[asset] = merged
            asset_evidence[asset] = {
                "provider_display_pair": PAIR_METADATA[asset]["provider_display_pair"],
                "provider_legacy_pair": PAIR_METADATA[asset]["provider_legacy_pair"],
                "archive_pair_stem": PAIR_METADATA[asset]["archive_pair_stem"],
                "expected_daily_buckets": len(expected),
                "observed_rows": len(merged),
                "first_observed_timestamp": (
                    _iso_from_unix(min(merged)) if merged else None
                ),
                "last_observed_timestamp": (
                    _iso_from_unix(max(merged)) if merged else None
                ),
                "missing_count": len(missing),
                "missing_timestamps": [_iso_from_unix(value) for value in missing],
                "missing_interval_trading_state": "NO_TRADE_UNAVAILABLE",
                "continuous_segments": _segments(merged),
                "equal_archive_duplicate_rows": archive_result[
                    "equal_duplicates"
                ][asset],
                "archive_contributions": archive_result["contributions"][asset],
                "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
            }

        staging = output_root / f".{self.contract.dataset_id}.staging-{uuid.uuid4().hex}"
        staging.mkdir()
        try:
            inventory_bytes = _json_bytes(inventory)
            inventory_file = "archive_inventory.json"
            _write_new(staging / inventory_file, inventory_bytes)
            inventory_digest = hashlib.sha256(inventory_bytes).hexdigest()

            for asset in ASSET_ORDER:
                payload = self._canonical_csv_bytes(merged_assets[asset])
                filename = self._asset_filename(asset)
                _write_new(staging / filename, payload)
                asset_evidence[asset]["file"] = filename
                asset_evidence[asset]["bytes"] = len(payload)
                asset_evidence[asset]["sha256"] = hashlib.sha256(payload).hexdigest()

            manifest = {
                "schema_version": DATASET_SCHEMA_VERSION,
                "dataset_id": self.contract.dataset_id,
                "status": "LOCKED_NON_PERFORMANCE_DATASET",
                "contract": self.contract.as_dict(),
                "provider_audit_sha256": self.provider_audit_sha256,
                "lock_protocol_sha256": self.lock_protocol_sha256,
                "provider": "Kraken Spot",
                "provider_identity": "ONE_USD_SPOT_VENUE",
                "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
                "asset_order": list(ASSET_ORDER),
                "canonical_columns": list(CANONICAL_COLUMN_ORDER),
                "canonicalization": {
                    "encoding": "UTF-8",
                    "line_ending": "LF",
                    "timestamp_format": "YYYY-MM-DDTHH:MM:SSZ",
                    "decimal_format": "NON_EXPONENTIAL_MINIMAL_EXACT_DECIMAL",
                    "missing_rows_synthesized": False,
                    "forward_fill_used": False,
                    "zero_volume_rows_inserted": False,
                },
                "source_archives": [
                    {key: value for key, value in archive.items() if key != "members"}
                    for archive in inventory["archives"]
                ],
                "archive_inventory": {
                    "file": inventory_file,
                    "sha256": inventory_digest,
                    "bytes": len(inventory_bytes),
                    "archive_count": len(inventory["archives"]),
                    "member_count": sum(
                        archive["member_count"] for archive in inventory["archives"]
                    ),
                    "completed": True,
                },
                "assets": asset_evidence,
                "data_acquisition_executed": True,
                "network_requests_executed": False,
                "byte_level_historical_bucket_inventory_completed": True,
                "all_asset_dataset_locked": True,
                "real_chart_replay_authorized": False,
                "real_chart_replay_executed": False,
                "crypto_strategy_implemented": False,
                "performance_evaluation_executed": False,
                "optimization_authorized": False,
                "candidate_v2_authorized": False,
                "bounded_forward_paper_review_eligible": False,
                "bounded_forward_paper_authorized": False,
                "cloud_execution_authorized": False,
                "live_execution_authorized": False,
            }
            manifest_bytes = _json_bytes(manifest)
            manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
            _write_new(staging / "manifest.json", manifest_bytes)
            _write_new(
                staging / "manifest.sha256",
                f"{manifest_digest}  manifest.json\n".encode("ascii"),
            )
            staging.replace(final)
        except Exception:
            # Staging is intentionally never promoted on any validation/write error.
            shutil.rmtree(staging, ignore_errors=True)
            raise
        return {
            "status": "LOCKED_NON_PERFORMANCE_DATASET",
            "dataset_path": final,
            "manifest_path": final / "manifest.json",
            "manifest_sha256": manifest_digest,
            "assets": asset_evidence,
        }


@dataclass(frozen=True)
class LockedKrakenDailyDataset:
    contract: KrakenDailyDatasetContract
    manifest: dict
    manifest_sha256: str
    assets: dict


class KrakenDailyDatasetLock:
    """Independently revalidate a published Kraken dataset directory."""

    def __init__(self, contract=None):
        self.contract = contract or KrakenDailyDatasetContract()
        if not isinstance(self.contract, KrakenDailyDatasetContract):
            raise TypeError("Contract must be KrakenDailyDatasetContract.")

    @staticmethod
    def _verify_sha(path, expected):
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch for {path.name}: {actual} != {expected}.")

    def lock(self, dataset_path):
        dataset_path = Path(dataset_path)
        manifest_path = dataset_path / "manifest.json"
        sidecar_path = dataset_path / "manifest.sha256"
        try:
            manifest_bytes = manifest_path.read_bytes()
            sidecar = sidecar_path.read_text(encoding="ascii").strip().split()
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("Unable to read locked Kraken manifest.") from exc
        digest = hashlib.sha256(manifest_bytes).hexdigest()
        if sidecar != [digest, "manifest.json"]:
            raise ValueError("Manifest SHA-256 sidecar mismatch.")
        if manifest_bytes != _json_bytes(manifest):
            raise ValueError("Manifest bytes are not canonical.")
        if manifest.get("schema_version") != DATASET_SCHEMA_VERSION:
            raise ValueError("Locked dataset schema-version mismatch.")
        if manifest.get("dataset_id") != self.contract.dataset_id:
            raise ValueError("Locked dataset identity mismatch.")
        if manifest.get("contract") != self.contract.as_dict():
            raise ValueError("Locked dataset contract mismatch.")
        if manifest.get("provider_audit_sha256") != PROVIDER_AUDIT_NORMALIZED_SHA256:
            raise ValueError("Locked provider audit hash mismatch.")
        if manifest.get("lock_protocol_sha256") != LOCK_PROTOCOL_NORMALIZED_SHA256:
            raise ValueError("Locked archive-only protocol hash mismatch.")
        if manifest.get("source_mode") != "OFFICIAL_OHLCVT_ARCHIVES_ONLY":
            raise ValueError("Locked source mode mismatch.")
        if manifest.get("network_requests_executed") is not False:
            raise ValueError("Archive-only lock cannot contain network execution.")
        _validate_frozen_archive_evidence(
            self.contract,
            manifest.get("source_archives", []),
        )
        inventory = manifest.get("archive_inventory", {})
        self._verify_sha(dataset_path / inventory["file"], inventory["sha256"])
        assets = {}
        if manifest.get("asset_order") != list(ASSET_ORDER):
            raise ValueError("Locked asset order mismatch.")
        for asset in ASSET_ORDER:
            evidence = manifest["assets"][asset]
            path = dataset_path / evidence["file"]
            self._verify_sha(path, evidence["sha256"])
            text = path.read_text(encoding="utf-8")
            rows = list(csv.reader(io.StringIO(text, newline="")))
            if not rows or tuple(rows[0]) != CANONICAL_COLUMN_ORDER:
                raise ValueError(f"Canonical column mismatch for {asset}.")
            if len(rows) - 1 != evidence["observed_rows"]:
                raise ValueError(f"Observed row-count mismatch for {asset}.")
            assets[asset] = rows[1:]
        return LockedKrakenDailyDataset(self.contract, manifest, digest, assets)


def _archive_input_from_path(path, retrieved_at):
    path = Path(path)
    if path.name == ARCHIVE_COMPLETE_FILENAME:
        return ArchiveInput(
            path,
            "COMPLETE",
            OFFICIAL_COMPLETE_ARCHIVE_URL,
            retrieved_at,
        )
    if re.fullmatch(r"Kraken_OHLCVT_Q[1-4]_20\d{2}\.zip", path.name):
        return ArchiveInput(
            path,
            "QUARTERLY_UPDATE",
            OFFICIAL_QUARTERLY_ARCHIVE_FOLDER_URL,
            retrieved_at,
        )
    raise ValueError(
        f"Unreviewed archive filename: {path.name}. Provider review is required."
    )


def _parser():
    parser = argparse.ArgumentParser(
        description=(
            "Review or execute the archive-only Kraken BTC/ETH/XRP daily lock."
        )
    )
    parser.add_argument(
        "--provider-audit",
        default=str(DEFAULT_PROVIDER_AUDIT_PATH),
    )
    parser.add_argument(
        "--lock-protocol",
        default=str(DEFAULT_LOCK_PROTOCOL_PATH),
    )
    parser.add_argument("--archive", action="append", default=[])
    parser.add_argument("--output-root")
    parser.add_argument("--retrieved-at")
    return parser


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    if not args.archive and args.output_root is None and args.retrieved_at is None:
        print(
            json.dumps(
                build_review_declaration(
                    args.provider_audit,
                    args.lock_protocol,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if not args.archive or args.output_root is None:
        parser.error("Build mode requires --archive and --output-root.")
    retrieved_at = args.retrieved_at or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    archive_inputs = tuple(
        _archive_input_from_path(path, retrieved_at) for path in args.archive
    )
    result = KrakenDailyDatasetBuilder(
        archive_inputs=archive_inputs,
        provider_audit_path=args.provider_audit,
        lock_protocol_path=args.lock_protocol,
    ).build(args.output_root)
    print(f"dataset_status={result['status']}")
    print(f"dataset_path={result['dataset_path']}")
    print(f"manifest_sha256={result['manifest_sha256']}")
    for asset in ASSET_ORDER:
        evidence = result["assets"][asset]
        print(
            f"{asset} rows={evidence['observed_rows']} "
            f"missing={evidence['missing_count']} "
            f"sha256={evidence['sha256']} file={evidence['file']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
