"""Timestamp-only Stage 2 data-sufficiency and resolution audit for Kraken V2."""

import argparse
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

try:
    from kraken_ai_driven_v2_true_learning_contract import (
        ASSET_ORDER,
        TRUE_LEARNING_CONTRACT_LOCK,
        learning_contract_declaration,
    )
    from kraken_daily_dataset import (
        ARCHIVE_COMPLETE_FILENAME,
        FROZEN_ARCHIVE_SPECS,
        PAIR_METADATA,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_true_learning_contract import (
        ASSET_ORDER,
        TRUE_LEARNING_CONTRACT_LOCK,
        learning_contract_declaration,
    )
    from .kraken_daily_dataset import (
        ARCHIVE_COMPLETE_FILENAME,
        FROZEN_ARCHIVE_SPECS,
        PAIR_METADATA,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-stage-2-"
    "data-sufficiency-resolution-audit-v1"
)
AUDIT_ID = "kraken-ai-v2-stage-2-data-sufficiency-resolution-audit-v1"
STAGE_1_COMMIT = "796c8de"
STATUS = (
    "KRAKEN_AI_V2_STAGE_2_DATA_SUFFICIENCY_AUDIT_"
    "IMPLEMENTED_NO_RUN_AUTHORIZATION"
)
AUDIT_STATUS_RESOLUTION_SELECTED = (
    "KRAKEN_AI_V2_STAGE_2_RESOLUTION_SELECTED_DATASET_LOCK_REQUIRED"
)
AUDIT_STATUS_NO_SELECTION = (
    "KRAKEN_AI_V2_STAGE_2_NO_RESOLUTION_SELECTED_DATA_EXTENSION_REQUIRED"
)
AUTHORIZATION_PHRASE = (
    "EXECUTE_KRAKEN_AI_V2_STAGE_2_DATA_SUFFICIENCY_AUDIT_ONCE"
)
DEVELOPMENT_START_UTC = "2019-01-01T00:00:00Z"
DEVELOPMENT_END_EXCLUSIVE_UTC = "2024-04-01T00:00:00Z"
FEATURE_WARMUP_DAYS = 90
LABEL_HORIZON_DAYS = 30
EVIDENCE_DIRECTORY_NAME = "stage_2_data_sufficiency_resolution_audit_v1"
STAGING_DIRECTORY_NAME = ".stage_2_data_sufficiency_resolution_audit_v1.staging"
REPORT_FILENAME = "kraken_ai_v2_stage_2_data_sufficiency_report.json"
REPORT_SHA256_FILENAME = "kraken_ai_v2_stage_2_data_sufficiency_report.sha256"

FROZEN_COMPLETE_ARCHIVE_SPEC = {
    "filename": ARCHIVE_COMPLETE_FILENAME,
    "bytes": FROZEN_ARCHIVE_SPECS[ARCHIVE_COMPLETE_FILENAME]["bytes"],
    "sha256": FROZEN_ARCHIVE_SPECS[ARCHIVE_COMPLETE_FILENAME]["sha256"],
}

CANDIDATE_RESOLUTIONS = (
    {
        "resolution_id": "KRAKEN_NATIVE_1D",
        "timeframe": "1d",
        "interval_minutes": 1440,
        "archive_member_interval": 1440,
        "source_mode": "OFFICIAL_KRAKEN_OHLCVT_ARCHIVE_NATIVE",
    },
    {
        "resolution_id": "KRAKEN_NATIVE_12H",
        "timeframe": "12h",
        "interval_minutes": 720,
        "archive_member_interval": 720,
        "source_mode": "OFFICIAL_KRAKEN_OHLCVT_ARCHIVE_NATIVE",
    },
    {
        "resolution_id": "KRAKEN_NATIVE_4H",
        "timeframe": "4h",
        "interval_minutes": 240,
        "archive_member_interval": 240,
        "source_mode": "OFFICIAL_KRAKEN_OHLCVT_ARCHIVE_NATIVE",
    },
)

AUDIT_GATES = {
    "minimum_observed_coverage_fraction_per_asset": 0.995,
    "minimum_valid_examples_per_asset": 9000,
    "minimum_nonoverlapping_horizons_per_asset": 48,
    "minimum_largest_continuous_segment_days_per_asset": 730,
    "maximum_gap_utc_days_per_asset": 7,
    "minimum_training_examples_per_asset_per_fold": 3000,
    "minimum_validation_examples_per_asset_per_fold": 900,
}

FOLD_PLAN = (
    {
        "fold_id": "FOLD_1",
        "training_start_utc": DEVELOPMENT_START_UTC,
        "training_end_exclusive_utc": "2021-03-02T00:00:00Z",
        "purge_start_utc": "2021-03-02T00:00:00Z",
        "validation_start_utc": "2021-04-01T00:00:00Z",
        "validation_end_exclusive_utc": "2022-04-01T00:00:00Z",
        "embargo_end_exclusive_utc": "2022-05-01T00:00:00Z",
        "purge_utc_days": 30,
        "embargo_utc_days": 30,
    },
    {
        "fold_id": "FOLD_2",
        "training_start_utc": DEVELOPMENT_START_UTC,
        "training_end_exclusive_utc": "2022-04-01T00:00:00Z",
        "purge_start_utc": "2022-04-01T00:00:00Z",
        "validation_start_utc": "2022-05-01T00:00:00Z",
        "validation_end_exclusive_utc": "2023-05-01T00:00:00Z",
        "embargo_end_exclusive_utc": "2023-05-31T00:00:00Z",
        "purge_utc_days": 30,
        "embargo_utc_days": 30,
    },
    {
        "fold_id": "FOLD_3",
        "training_start_utc": DEVELOPMENT_START_UTC,
        "training_end_exclusive_utc": "2023-05-01T00:00:00Z",
        "purge_start_utc": "2023-05-01T00:00:00Z",
        "validation_start_utc": "2023-05-31T00:00:00Z",
        "validation_end_exclusive_utc": DEVELOPMENT_END_EXCLUSIVE_UTC,
        "embargo_end_exclusive_utc": "2024-05-01T00:00:00Z",
        "purge_utc_days": 30,
        "embargo_utc_days": 30,
    },
)

PROHIBITED_PERFORMANCE_FIELDS = {
    "returns",
    "return_fraction",
    "expectancy",
    "profit_factor",
    "win_rate",
    "model_score",
    "pnl",
    "drawdown",
    "sharpe",
    "sortino",
    "trade_count",
}


def canonical_json_bytes(value):
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("Stage 2 evidence must be canonical JSON data.") from exc


def _utc(value, label):
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a UTC timestamp string.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} is not a valid UTC timestamp.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be UTC.")
    return parsed.astimezone(timezone.utc)


def _unix(value):
    return int(_utc(value, "Timestamp").timestamp())


def _iso(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _file_sha256(path, chunk_bytes=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(chunk_bytes)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _assert_no_performance_fields(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in PROHIBITED_PERFORMANCE_FIELDS:
                raise RuntimeError(f"Prohibited performance field in Stage 2 evidence: {key}.")
            _assert_no_performance_fields(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_performance_fields(item)


def _candidate_by_id():
    return {item["resolution_id"]: item for item in CANDIDATE_RESOLUTIONS}


def _validate_fold_plan():
    previous_validation_end = None
    for fold in FOLD_PLAN:
        train_start = _utc(fold["training_start_utc"], "Training start")
        train_end = _utc(fold["training_end_exclusive_utc"], "Training end")
        validation_start = _utc(fold["validation_start_utc"], "Validation start")
        validation_end = _utc(
            fold["validation_end_exclusive_utc"], "Validation end"
        )
        embargo_end = _utc(
            fold["embargo_end_exclusive_utc"], "Embargo end"
        )
        if train_start != _utc(DEVELOPMENT_START_UTC, "Development start"):
            raise RuntimeError("Fold training must start at Development start.")
        if validation_start - train_end != timedelta(days=30):
            raise RuntimeError("Fold purge must be exactly 30 UTC days.")
        if embargo_end - validation_end != timedelta(days=30):
            raise RuntimeError("Fold embargo must be exactly 30 UTC days.")
        if not train_start < train_end < validation_start < validation_end:
            raise RuntimeError("Fold chronology mismatch.")
        if previous_validation_end is not None and validation_start < previous_validation_end:
            raise RuntimeError("Fold validation windows must not overlap.")
        previous_validation_end = validation_end
    if FOLD_PLAN[-1]["validation_end_exclusive_utc"] != DEVELOPMENT_END_EXCLUSIVE_UTC:
        raise RuntimeError("Final validation fold must end at Development end.")


_validate_fold_plan()


def _validate_timestamps(values, interval_minutes, asset):
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{asset} timestamps must be a list or tuple.")
    start = _unix(DEVELOPMENT_START_UTC)
    end = _unix(DEVELOPMENT_END_EXCLUSIVE_UTC)
    step = interval_minutes * 60
    previous = None
    normalized = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{asset} timestamp must be an integer Unix second.")
        if value < start or value >= end:
            raise ValueError(f"{asset} timestamp is outside Development.")
        if (value - start) % step:
            raise ValueError(f"{asset} timestamp alignment mismatch.")
        if previous is not None and value <= previous:
            raise ValueError(f"{asset} timestamps must be strictly increasing.")
        normalized.append(value)
        previous = value
    return normalized


def _segments(timestamps, step):
    if not timestamps:
        return []
    segments = [[timestamps[0]]]
    for timestamp in timestamps[1:]:
        if timestamp - segments[-1][-1] == step:
            segments[-1].append(timestamp)
        else:
            segments.append([timestamp])
    return segments


def _event_rows(segments, warmup_bars, horizon_bars):
    events = []
    warmup_loss = 0
    right_censored = 0
    nonoverlapping_capacity = 0
    for segment in segments:
        size = len(segment)
        warmup_loss += min(size, warmup_bars)
        raw_decisions = max(size - warmup_bars - 1, 0)
        valid_decisions = max(size - warmup_bars - horizon_bars - 1, 0)
        right_censored += raw_decisions - valid_decisions
        nonoverlapping_capacity += (
            (valid_decisions + horizon_bars) // (horizon_bars + 1)
            if valid_decisions
            else 0
        )
        for index in range(warmup_bars, warmup_bars + valid_decisions):
            events.append((segment[index], segment[index + 1 + horizon_bars]))
    return events, warmup_loss, right_censored, nonoverlapping_capacity


def _fold_counts(events):
    counts = {}
    for fold in FOLD_PLAN:
        training_start = _unix(fold["training_start_utc"])
        training_end = _unix(fold["training_end_exclusive_utc"])
        validation_start = _unix(fold["validation_start_utc"])
        validation_end = _unix(fold["validation_end_exclusive_utc"])
        counts[fold["fold_id"]] = {
            "training_example_count": sum(
                decision >= training_start and event_end < training_end
                for decision, event_end in events
            ),
            "validation_example_count": sum(
                decision >= validation_start and event_end < validation_end
                for decision, event_end in events
            ),
        }
    return counts


def _audit_asset(asset, values, interval_minutes):
    timestamps = _validate_timestamps(values, interval_minutes, asset)
    step = interval_minutes * 60
    start = _unix(DEVELOPMENT_START_UTC)
    end = _unix(DEVELOPMENT_END_EXCLUSIVE_UTC)
    expected_rows = (end - start) // step
    segments = _segments(timestamps, step)
    warmup_bars = math.ceil(FEATURE_WARMUP_DAYS * 1440 / interval_minutes)
    horizon_bars = math.ceil(LABEL_HORIZON_DAYS * 1440 / interval_minutes)
    events, warmup_loss, right_censored, independent = _event_rows(
        segments, warmup_bars, horizon_bars
    )
    missing = expected_rows - len(timestamps)
    gaps = []
    for previous, current in zip(timestamps, timestamps[1:]):
        if current - previous > step:
            gaps.append((current - previous) // step - 1)
    fold_counts = _fold_counts(events)
    event_identity = [
        [asset, _iso(decision), _iso(event_end)] for decision, event_end in events
    ]
    return {
        "asset": asset,
        "expected_calendar_buckets": expected_rows,
        "observed_timestamp_rows": len(timestamps),
        "observed_coverage_fraction": (
            len(timestamps) / expected_rows if expected_rows else 0.0
        ),
        "missing_bucket_count": missing,
        "gap_count": len(gaps),
        "maximum_gap_buckets": max(gaps, default=0),
        "continuous_segment_rows": [len(item) for item in segments],
        "largest_continuous_segment_days": max(
            (len(item) * interval_minutes / 1440 for item in segments),
            default=0.0,
        ),
        "feature_warmup_bars": warmup_bars,
        "feature_warmup_loss_count": warmup_loss,
        "label_horizon_bars": horizon_bars,
        "horizon_right_censored_count": right_censored,
        "valid_example_count": len(events),
        "nonoverlapping_horizon_capacity": independent,
        "fold_capacity": fold_counts,
        "valid_example_identity_sha256": hashlib.sha256(
            canonical_json_bytes(event_identity)
        ).hexdigest(),
    }


def _candidate_gate_results(candidate, per_asset):
    interval_minutes = candidate["interval_minutes"]
    results = {}
    for asset in ASSET_ORDER:
        item = per_asset[asset]
        prefix = asset
        results[f"{prefix}|OBSERVED_COVERAGE"] = item[
            "observed_coverage_fraction"
        ] >= AUDIT_GATES["minimum_observed_coverage_fraction_per_asset"]
        results[f"{prefix}|VALID_EXAMPLES"] = item[
            "valid_example_count"
        ] >= AUDIT_GATES["minimum_valid_examples_per_asset"]
        results[f"{prefix}|NONOVERLAPPING_HORIZONS"] = item[
            "nonoverlapping_horizon_capacity"
        ] >= AUDIT_GATES["minimum_nonoverlapping_horizons_per_asset"]
        results[f"{prefix}|CONTINUOUS_SEGMENT_DAYS"] = item[
            "largest_continuous_segment_days"
        ] >= AUDIT_GATES["minimum_largest_continuous_segment_days_per_asset"]
        gap_days = item["maximum_gap_buckets"] * interval_minutes / 1440
        results[f"{prefix}|MAXIMUM_GAP_DAYS"] = gap_days <= AUDIT_GATES[
            "maximum_gap_utc_days_per_asset"
        ]
        for fold_id, counts in item["fold_capacity"].items():
            results[f"{prefix}|{fold_id}|TRAINING_EXAMPLES"] = counts[
                "training_example_count"
            ] >= AUDIT_GATES["minimum_training_examples_per_asset_per_fold"]
            results[f"{prefix}|{fold_id}|VALIDATION_EXAMPLES"] = counts[
                "validation_example_count"
            ] >= AUDIT_GATES["minimum_validation_examples_per_asset_per_fold"]
    return results


def audit_resolution_candidates(candidate_timestamps):
    """Audit timestamp availability only and select no performance input."""

    if not isinstance(candidate_timestamps, dict):
        raise TypeError("Candidate timestamp inventory must be a mapping.")
    expected_ids = [item["resolution_id"] for item in CANDIDATE_RESOLUTIONS]
    if list(candidate_timestamps) != expected_ids:
        raise ValueError("Candidate resolution order or identity mismatch.")
    candidate_results = []
    for candidate in CANDIDATE_RESOLUTIONS:
        resolution_id = candidate["resolution_id"]
        assets = candidate_timestamps[resolution_id]
        if not isinstance(assets, dict) or tuple(assets) != ASSET_ORDER:
            raise ValueError(f"{resolution_id} asset order mismatch.")
        per_asset = {
            asset: _audit_asset(asset, assets[asset], candidate["interval_minutes"])
            for asset in ASSET_ORDER
        }
        gates = _candidate_gate_results(candidate, per_asset)
        candidate_results.append(
            {
                **copy.deepcopy(candidate),
                "per_asset": per_asset,
                "minimum_valid_examples_per_asset": min(
                    item["valid_example_count"] for item in per_asset.values()
                ),
                "minimum_nonoverlapping_horizons_per_asset": min(
                    item["nonoverlapping_horizon_capacity"]
                    for item in per_asset.values()
                ),
                "selection_gate_results": gates,
                "all_gates_passed": all(gates.values()),
            }
        )
    passing = [item for item in candidate_results if item["all_gates_passed"]]
    selected = None
    if passing:
        item = passing[0]
        selected = {
            "resolution_id": item["resolution_id"],
            "timeframe": item["timeframe"],
            "interval_minutes": item["interval_minutes"],
        }
    report = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "audit_id": AUDIT_ID,
        "status": (
            AUDIT_STATUS_RESOLUTION_SELECTED
            if selected is not None
            else AUDIT_STATUS_NO_SELECTION
        ),
        "stage_1_commit": STAGE_1_COMMIT,
        "true_learning_contract_sha256": TRUE_LEARNING_CONTRACT_LOCK.sha256,
        "development_start_utc": DEVELOPMENT_START_UTC,
        "development_end_exclusive_utc": DEVELOPMENT_END_EXCLUSIVE_UTC,
        "feature_warmup_utc_days": FEATURE_WARMUP_DAYS,
        "label_horizon_utc_days": LABEL_HORIZON_DAYS,
        "fold_plan": copy.deepcopy(list(FOLD_PLAN)),
        "audit_gates": copy.deepcopy(AUDIT_GATES),
        "candidate_results": candidate_results,
        "selection_policy": "COARSEST_PASSING_CANDIDATE",
        "selection_uses_performance": False,
        "selected_resolution": selected,
        "source_archive_opened": False,
        "timestamp_columns_opened": False,
        "ohlcvt_value_columns_opened": False,
        "development_market_values_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "performance_fields_opened": False,
        "labels_generated": False,
        "model_training_authorized": False,
        "model_training_executed": False,
        "walk_forward_executed": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": (
            "LOCK_SELECTED_RESOLUTION_DATASET_BEFORE_STAGE_3"
            if selected is not None
            else "EXTEND_OR_RELOCK_SOURCE_DATA_BEFORE_STAGE_3"
        ),
    }
    _assert_no_performance_fields(report)
    return report


def audit_configuration():
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "audit_id": AUDIT_ID,
        "stage_1_commit": STAGE_1_COMMIT,
        "true_learning_contract_sha256": TRUE_LEARNING_CONTRACT_LOCK.sha256,
        "asset_order": list(ASSET_ORDER),
        "candidate_resolutions": copy.deepcopy(list(CANDIDATE_RESOLUTIONS)),
        "development_start_utc": DEVELOPMENT_START_UTC,
        "development_end_exclusive_utc": DEVELOPMENT_END_EXCLUSIVE_UTC,
        "feature_warmup_utc_days": FEATURE_WARMUP_DAYS,
        "label_horizon_utc_days": LABEL_HORIZON_DAYS,
        "fold_plan": copy.deepcopy(list(FOLD_PLAN)),
        "audit_gates": copy.deepcopy(AUDIT_GATES),
        "selection_policy": "COARSEST_PASSING_CANDIDATE",
        "timestamp_columns_only": True,
        "ohlcvt_value_columns_permitted": False,
        "performance_selection_permitted": False,
        "new_resolution_dataset_lock_required": True,
        "label_generation_authorized": False,
        "model_training_authorized": False,
    }


AUDIT_CONFIGURATION_SHA256 = hashlib.sha256(
    canonical_json_bytes(audit_configuration())
).hexdigest()


@dataclass(frozen=True)
class LockedStage2Evidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    payload: dict


@dataclass(frozen=True)
class RecordedStage2Evidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    audit_status: str
    selected_resolution_minutes: int | None

    def as_dict(self):
        return {
            "status": "KRAKEN_AI_V2_STAGE_2_AUDIT_EVIDENCE_RECORDED",
            "audit_status": self.audit_status,
            "report_path": str(self.report_path),
            "checksum_path": str(self.checksum_path),
            "report_sha256": self.report_sha256,
            "selected_resolution_minutes": self.selected_resolution_minutes,
            "source_archive_opened": True,
            "timestamp_columns_opened": True,
            "ohlcvt_value_columns_opened": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "labels_generated": False,
            "model_training_executed": False,
            "candidate_v2_authorized": False,
            "live_execution_authorized": False,
        }


class KrakenAIDrivenV2DataSufficiencyEvidenceLock:
    def lock(self, evidence_directory):
        root = Path(evidence_directory)
        report_path = root / REPORT_FILENAME
        checksum_path = root / REPORT_SHA256_FILENAME
        if not report_path.is_file() or not checksum_path.is_file():
            raise FileNotFoundError("Complete Stage 2 audit evidence is required.")
        raw = report_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        expected_line = f"{digest}  {REPORT_FILENAME}\n"
        if checksum_path.read_text(encoding="ascii") != expected_line:
            raise RuntimeError("Stage 2 audit evidence checksum mismatch.")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Stage 2 audit report is not valid JSON.") from exc
        if canonical_json_bytes(payload) != raw:
            raise RuntimeError("Stage 2 audit report is not canonical JSON.")
        _assert_no_performance_fields(payload)
        if payload.get("protocol_id") != PROTOCOL_ID or payload.get("audit_id") != AUDIT_ID:
            raise RuntimeError("Stage 2 audit evidence identity mismatch.")
        if payload.get("status") not in {
            AUDIT_STATUS_RESOLUTION_SELECTED,
            AUDIT_STATUS_NO_SELECTION,
        }:
            raise RuntimeError("Stage 2 audit evidence status mismatch.")
        required_false = (
            "ohlcvt_value_columns_opened",
            "development_market_values_opened",
            "calibration_data_opened",
            "evaluation_data_opened",
            "performance_fields_opened",
            "labels_generated",
            "model_training_executed",
            "candidate_v2_authorized",
            "live_execution_authorized",
        )
        if any(payload.get(field) is not False for field in required_false):
            raise RuntimeError("Stage 2 audit evidence safety boundary mismatch.")
        return LockedStage2Evidence(report_path, checksum_path, digest, payload)


class KrakenAIDrivenV2DataSufficiencyAuditor:
    @staticmethod
    def _external_paths(archive_path, evidence_root):
        project_root = Path(__file__).resolve().parents[1]
        archive = Path(archive_path).resolve()
        evidence = Path(evidence_root).resolve()
        if archive == project_root or archive.is_relative_to(project_root):
            raise ValueError("Stage 2 source archive must remain outside the repository.")
        if evidence == project_root or evidence.is_relative_to(project_root):
            raise ValueError("Stage 2 evidence must remain outside the repository.")
        if archive == evidence or archive.is_relative_to(evidence) or evidence.is_relative_to(archive):
            raise ValueError("Stage 2 source archive and evidence must not overlap.")
        return archive, evidence

    @staticmethod
    def _assert_one_shot(evidence_root):
        final = evidence_root / EVIDENCE_DIRECTORY_NAME
        staging = evidence_root / STAGING_DIRECTORY_NAME
        if final.exists():
            raise FileExistsError("Stage 2 audit evidence already exists; refusing repeat.")
        if staging.exists():
            raise FileExistsError("Incomplete Stage 2 audit staging evidence exists.")
        return final, staging

    @staticmethod
    def _validate_archive(archive_path):
        spec = FROZEN_COMPLETE_ARCHIVE_SPEC
        if not archive_path.is_file():
            raise FileNotFoundError(f"Stage 2 source archive does not exist: {archive_path}")
        if archive_path.name != spec["filename"]:
            raise ValueError("Stage 2 source archive filename mismatch.")
        size = archive_path.stat().st_size
        if size != spec["bytes"]:
            raise RuntimeError("Stage 2 source archive byte-size mismatch.")
        digest = _file_sha256(archive_path)
        if digest != spec["sha256"]:
            raise RuntimeError("Stage 2 source archive SHA256 mismatch.")
        return {"filename": archive_path.name, "bytes": size, "sha256": digest}

    @staticmethod
    def _read_member_timestamps(archive, member_name, interval_minutes, asset):
        start = _unix(DEVELOPMENT_START_UTC)
        end = _unix(DEVELOPMENT_END_EXCLUSIVE_UTC)
        timestamps = []
        try:
            with (
                archive.open(member_name) as raw,
                io.TextIOWrapper(raw, encoding="utf-8", newline="") as wrapper,
            ):
                for row_number, line in enumerate(wrapper, start=1):
                    if not line.strip():
                        continue
                    first, separator, _ignored_value_columns = line.partition(",")
                    if not separator:
                        raise RuntimeError(
                            f"Stage 2 timestamp row has no delimiter: {member_name}:{row_number}."
                        )
                    try:
                        timestamp = int(first)
                    except ValueError as exc:
                        raise RuntimeError(
                            f"Stage 2 timestamp is invalid: {member_name}:{row_number}."
                        ) from exc
                    if timestamp >= end:
                        break
                    if timestamp >= start:
                        timestamps.append(timestamp)
        except (OSError, UnicodeError, zipfile.BadZipFile) as exc:
            raise RuntimeError(f"Unable to read timestamp column for {asset}.") from exc
        return timestamps

    def _read_timestamp_inventory(self, archive_path):
        candidate_inputs = {item["resolution_id"]: {} for item in CANDIDATE_RESOLUTIONS}
        member_evidence = []
        try:
            with zipfile.ZipFile(archive_path) as archive:
                infos = archive.infolist()
                names = [item.filename for item in infos]
                if len(names) != len(set(names)):
                    raise RuntimeError("Stage 2 source archive has duplicate member names.")
                if any(item.flag_bits & 0x1 for item in infos):
                    raise RuntimeError("Encrypted Stage 2 archive members are prohibited.")
                for candidate in CANDIDATE_RESOLUTIONS:
                    minutes = candidate["archive_member_interval"]
                    for asset in ASSET_ORDER:
                        required = f"{PAIR_METADATA[asset]['archive_pair_stem']}_{minutes}.csv"
                        matches = [
                            item
                            for item in infos
                            if not item.is_dir() and Path(item.filename).name == required
                        ]
                        if len(matches) != 1:
                            raise RuntimeError(
                                f"Stage 2 requires exactly one {required} archive member."
                            )
                        timestamps = self._read_member_timestamps(
                            archive, matches[0].filename, minutes, asset
                        )
                        candidate_inputs[candidate["resolution_id"]][asset] = timestamps
                        member_evidence.append(
                            {
                                "resolution_id": candidate["resolution_id"],
                                "asset": asset,
                                "member_name": matches[0].filename,
                                "development_timestamp_rows": len(timestamps),
                                "first_development_timestamp": (
                                    _iso(timestamps[0]) if timestamps else None
                                ),
                                "last_development_timestamp": (
                                    _iso(timestamps[-1]) if timestamps else None
                                ),
                                "ohlcvt_value_columns_parsed": False,
                            }
                        )
        except (OSError, zipfile.BadZipFile) as exc:
            raise RuntimeError("Unable to inventory Stage 2 source archive.") from exc
        return candidate_inputs, member_evidence

    def run(self, archive_path, evidence_root, authorization_phrase):
        if authorization_phrase != AUTHORIZATION_PHRASE:
            raise PermissionError("Exact Stage 2 audit authorization phrase is required.")
        archive_path, evidence_root = self._external_paths(archive_path, evidence_root)
        final, staging = self._assert_one_shot(evidence_root)
        archive_evidence = self._validate_archive(archive_path)
        candidate_inputs, member_evidence = self._read_timestamp_inventory(archive_path)
        result = audit_resolution_candidates(candidate_inputs)
        payload = {
            **result,
            "audit_configuration_sha256": AUDIT_CONFIGURATION_SHA256,
            "source_archive": archive_evidence,
            "source_member_evidence": member_evidence,
            "source_archive_opened": True,
            "timestamp_columns_opened": True,
            "ohlcvt_value_columns_opened": False,
            "development_market_values_opened": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "performance_fields_opened": False,
            "labels_generated": False,
            "model_training_authorized": False,
            "model_training_executed": False,
            "walk_forward_executed": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
        }
        _assert_no_performance_fields(payload)
        report_bytes = canonical_json_bytes(payload)
        digest = hashlib.sha256(report_bytes).hexdigest()
        evidence_root.mkdir(parents=True, exist_ok=True)
        staging.mkdir(exist_ok=False)
        (staging / REPORT_FILENAME).write_bytes(report_bytes)
        (staging / REPORT_SHA256_FILENAME).write_text(
            f"{digest}  {REPORT_FILENAME}\n", encoding="ascii"
        )
        staging.rename(final)
        locked = KrakenAIDrivenV2DataSufficiencyEvidenceLock().lock(final)
        selected = payload["selected_resolution"]
        return RecordedStage2Evidence(
            locked.report_path,
            locked.checksum_path,
            locked.report_sha256,
            payload["status"],
            selected["interval_minutes"] if selected else None,
        )


def audit_declaration():
    parent = learning_contract_declaration()
    if parent.get("true_learning_contract_frozen") is not True:
        raise RuntimeError("Stage 2 requires frozen True Learning Contract V1.")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "protocol_id": PROTOCOL_ID,
        "audit_id": AUDIT_ID,
        "stage_1_commit": STAGE_1_COMMIT,
        "true_learning_contract_sha256": TRUE_LEARNING_CONTRACT_LOCK.sha256,
        "audit_configuration_sha256": AUDIT_CONFIGURATION_SHA256,
        "asset_order": list(ASSET_ORDER),
        "candidate_resolution_count": len(CANDIDATE_RESOLUTIONS),
        "candidate_resolution_minutes": [
            item["interval_minutes"] for item in CANDIDATE_RESOLUTIONS
        ],
        "feature_warmup_utc_days": FEATURE_WARMUP_DAYS,
        "label_horizon_utc_days": LABEL_HORIZON_DAYS,
        "fold_count": len(FOLD_PLAN),
        "selection_uses_performance": False,
        "timestamp_column_only_reader_implemented": True,
        "ohlcvt_value_columns_permitted": False,
        "archive_hash_verification_implemented": True,
        "independent_evidence_lock_implemented": True,
        "one_shot_atomic_evidence_implemented": True,
        "audit_runner_implemented": True,
        "authorization_phrase": AUTHORIZATION_PHRASE,
        "authorization_phrase_active": False,
        "source_archive_opened": False,
        "timestamp_columns_opened": False,
        "ohlcvt_value_columns_opened": False,
        "development_market_values_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "audit_run_authorized": False,
        "audit_run_executed": False,
        "performance_evaluation_executed": False,
        "selected_resolution": None,
        "selected_resolution_dataset_locked": False,
        "labels_generated": False,
        "model_training_authorized": False,
        "model_training_executed": False,
        "walk_forward_executed": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": (
            "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_STAGE_2_TIMESTAMP_AUDIT"
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Execute one timestamp-only Kraken V2 Stage 2 sufficiency audit."
    )
    parser.add_argument("--complete-archive", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--authorization-phrase", required=True)
    args = parser.parse_args(argv)
    recorded = KrakenAIDrivenV2DataSufficiencyAuditor().run(
        args.complete_archive,
        args.evidence_root,
        args.authorization_phrase,
    )
    print(json.dumps(recorded.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
