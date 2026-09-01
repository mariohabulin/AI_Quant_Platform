"""One-shot real 12h Development learner for Kraken BTC/ETH/XRP V2.

The component is inert until the exact operator phrase is supplied.  It opens
only official Kraken native 12h rows inside Development, delegates feature,
label and fold fitting to the Learning Core, and atomically records immutable
out-of-fold predictions plus the six learned fold-model artifacts.  It cannot
open Calibration or Evaluation, select a winner, promote a Candidate or place
an order.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

try:
    from kraken_ai_driven_v2_learning_core import (
        ASSET_ORDER,
        BAR_INTERVAL,
        CLASS_ORDER,
        DEVELOPMENT_END_EXCLUSIVE_UTC,
        DEVELOPMENT_START_UTC,
        FEATURE_COLUMNS,
        FOLD_PLAN,
        LEARNING_CORE_CONFIGURATION_SHA256,
        MODEL_SPECS,
        build_labeled_learning_data,
        train_walk_forward,
        validate_development_frames,
    )
    from kraken_daily_dataset import (
        ARCHIVE_COMPLETE_FILENAME,
        FROZEN_ARCHIVE_SPECS,
        PAIR_METADATA,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_learning_core import (
        ASSET_ORDER,
        BAR_INTERVAL,
        CLASS_ORDER,
        DEVELOPMENT_END_EXCLUSIVE_UTC,
        DEVELOPMENT_START_UTC,
        FEATURE_COLUMNS,
        FOLD_PLAN,
        LEARNING_CORE_CONFIGURATION_SHA256,
        MODEL_SPECS,
        build_labeled_learning_data,
        train_walk_forward,
        validate_development_frames,
    )
    from .kraken_daily_dataset import (
        ARCHIVE_COMPLETE_FILENAME,
        FROZEN_ARCHIVE_SPECS,
        PAIR_METADATA,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-12h-development-learning-runner-v1"
)
RUN_ID = "kraken-ai-v2-12h-development-learning-v1"
PARENT_COMMIT = "203b4c5b81434be3edab7ec5372448cd12472288"
STATUS = "KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_RUNNER_RECOVERY_ATTEMPT_3_IMPLEMENTED_NO_RUN_AUTHORIZATION"
REVIEW_REQUIRED_STATUS = (
    "KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_COMPLETED_REVIEW_REQUIRED"
)
INSUFFICIENT_SUPPORT_STATUS = (
    "KRAKEN_AI_V2_12H_DEVELOPMENT_CLASS_SUPPORT_INSUFFICIENT_HOLD_CASH"
)
AUTHORIZATION_PHRASE = (
    "EXECUTE_KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_RECOVERY_ATTEMPT_3_ONCE"
)
EVIDENCE_DIRECTORY_NAME = "v2_12h_development_learning_v1"
STAGING_DIRECTORY_NAME = ".v2_12h_development_learning_v1.staging"
REPORT_FILENAME = "kraken_ai_v2_12h_development_learning_report.json"
REPORT_SHA256_FILENAME = "kraken_ai_v2_12h_development_learning_report.sha256"
PREDICTIONS_FILENAME = "kraken_ai_v2_12h_oof_predictions.json"
PREDICTIONS_SHA256_FILENAME = "kraken_ai_v2_12h_oof_predictions.sha256"
MODEL_DIRECTORY_NAME = "models"
MINIMUM_TRAINING_CLASS_COUNT = 30
MINIMUM_VALIDATION_CLASS_COUNT = 10

FROZEN_COMPLETE_ARCHIVE_SPEC = {
    "filename": ARCHIVE_COMPLETE_FILENAME,
    "bytes": FROZEN_ARCHIVE_SPECS[ARCHIVE_COMPLETE_FILENAME]["bytes"],
    "sha256": FROZEN_ARCHIVE_SPECS[ARCHIVE_COMPLETE_FILENAME]["sha256"],
}
EXPECTED_DEVELOPMENT_ROWS = {
    "BTC-USD": 3833,
    "ETH-USD": 3834,
    "XRP-USD": 3830,
}
EXPECTED_MISSING_BUCKETS = {
    "BTC-USD": 1,
    "ETH-USD": 0,
    "XRP-USD": 4,
}
PRIOR_ATTEMPT_EXECUTION_COMMITS = {
    1: "cc8ae44c45d41182af3bc91ee21cf075e65011b5",
    2: "203b4c5b81434be3edab7ec5372448cd12472288",
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
        raise ValueError("Learning evidence must be canonical JSON data.") from exc


def _file_sha256(path, chunk_bytes=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        while chunk := source.read(chunk_bytes):
            digest.update(chunk)
    return digest.hexdigest()


def _utc(value):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Runner timestamp must be timezone-aware.")
    return timestamp.tz_convert("UTC")


def _iso(value):
    timestamp = _utc(value)
    return timestamp.isoformat().replace("+00:00", "Z")


def _json_scalar(value):
    if isinstance(value, pd.Timestamp):
        return _iso(value)
    if isinstance(value, np.datetime64):
        return _iso(pd.Timestamp(value, tz="UTC"))
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Learning evidence cannot contain a non-finite float.")
        return value
    return value


def _json_ready(value):
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return _json_scalar(value)


def _class_counts(values):
    observed = pd.Series(values).value_counts()
    return {label: int(observed.get(label, 0)) for label in CLASS_ORDER}


def fold_support(table):
    support = []
    all_supported = True
    for fold in FOLD_PLAN:
        training_end = _utc(fold["training_end_exclusive_utc"])
        validation_start = _utc(fold["validation_start_utc"])
        validation_end = _utc(fold["validation_end_exclusive_utc"])
        training = table.loc[
            (table["decision_timestamp"] < training_end)
            & (table["event_end_timestamp"] < training_end)
        ]
        validation = table.loc[
            (table["decision_timestamp"] >= validation_start)
            & (table["decision_timestamp"] < validation_end)
            & (table["event_end_timestamp"] < validation_end)
        ]
        training_counts = _class_counts(training["label"])
        validation_counts = _class_counts(validation["label"])
        supported = (
            min(training_counts.values(), default=0) >= MINIMUM_TRAINING_CLASS_COUNT
            and min(validation_counts.values(), default=0)
            >= MINIMUM_VALIDATION_CLASS_COUNT
        )
        all_supported = all_supported and supported
        support.append(
            {
                "fold_id": fold["fold_id"],
                "training_rows": int(len(training)),
                "validation_rows": int(len(validation)),
                "training_class_counts": training_counts,
                "validation_class_counts": validation_counts,
                "all_class_support_passed": supported,
            }
        )
    return {"all_folds_supported": all_supported, "folds": support}


def _prediction_payload(predictions):
    columns = (
        "fold_id",
        "model_id",
        "asset",
        "decision_timestamp",
        "event_end_timestamp",
        "training_end_timestamp",
        "actual_label",
        "actual_outcome_net_r",
        "p_target_3r_first",
        "p_stop_1r_first",
        "p_timeout_no_barrier",
    )
    if predictions.empty:
        records = []
    else:
        missing = sorted(set(columns) - set(predictions.columns))
        if missing:
            raise RuntimeError(f"OOF predictions are missing columns: {missing}.")
        records = [
            {column: _json_scalar(row[column]) for column in columns}
            for row in predictions.loc[:, columns].to_dict("records")
        ]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "class_order": list(CLASS_ORDER),
        "columns": list(columns),
        "record_count": len(records),
        "records": records,
    }


def _learning_table_identity_sha256(table):
    columns = (
        "asset",
        "decision_timestamp",
        "entry_timestamp",
        "event_end_timestamp",
        "label",
        "outcome_net_r",
    )
    records = [
        {column: _json_scalar(row[column]) for column in columns}
        for row in table.loc[:, columns].to_dict("records")
    ]
    return hashlib.sha256(canonical_json_bytes(records)).hexdigest()


def _artifact_filename(key):
    fold_id, model_id = key.split("|", 1)
    return f"{fold_id.lower()}__{model_id.lower()}.pkl"


@dataclass(frozen=True)
class LockedLearningEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    payload: dict


@dataclass(frozen=True)
class RecordedLearningEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    learning_status: str
    labeled_row_count: int
    trained_model_count: int
    prediction_count: int

    def as_dict(self):
        return {
            "status": "KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_EVIDENCE_RECORDED",
            "recovery_attempt": 3,
            "learning_status": self.learning_status,
            "report_path": str(self.report_path),
            "checksum_path": str(self.checksum_path),
            "report_sha256": self.report_sha256,
            "labeled_row_count": self.labeled_row_count,
            "trained_model_count": self.trained_model_count,
            "out_of_fold_prediction_count": self.prediction_count,
            "development_data_opened": True,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "automatic_model_selection": False,
            "candidate_v2_authorized": False,
            "live_execution_authorized": False,
            "real_orders_submitted": False,
        }


class KrakenAIDrivenV212hLearningEvidenceLock:
    def lock(self, evidence_directory):
        root = Path(evidence_directory)
        report_path = root / REPORT_FILENAME
        checksum_path = root / REPORT_SHA256_FILENAME
        if not report_path.is_file() or not checksum_path.is_file():
            raise FileNotFoundError("Complete 12h learning evidence is required.")
        raw = report_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if checksum_path.read_text(encoding="ascii") != f"{digest}  {REPORT_FILENAME}\n":
            raise RuntimeError("12h learning report checksum mismatch.")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("12h learning report is not valid JSON.") from exc
        if canonical_json_bytes(payload) != raw:
            raise RuntimeError("12h learning report is not canonical JSON.")
        if payload.get("protocol_id") != PROTOCOL_ID or payload.get("run_id") != RUN_ID:
            raise RuntimeError("12h learning evidence identity mismatch.")
        if payload.get("learning_status") not in {
            REVIEW_REQUIRED_STATUS,
            INSUFFICIENT_SUPPORT_STATUS,
        }:
            raise RuntimeError("12h learning evidence status mismatch.")
        required_false = (
            "calibration_data_opened",
            "evaluation_data_opened",
            "automatic_model_selection",
            "candidate_v2_authorized",
            "bounded_forward_paper_authorized",
            "cloud_execution_authorized",
            "real_orders_submitted",
            "live_execution_authorized",
        )
        if any(payload.get(field) is not False for field in required_false):
            raise RuntimeError("12h learning evidence safety boundary mismatch.")
        incidents = payload.get("prior_attempt_incidents", [])
        expected_incidents = [
            {
                "attempt": attempt,
                "execution_commit": execution_commit,
                "final_evidence_exists": False,
                "staging_directory_name": STAGING_DIRECTORY_NAME,
                "staging_entry_count": 0,
                "staging_preserved": True,
            }
            for attempt, execution_commit in PRIOR_ATTEMPT_EXECUTION_COMMITS.items()
        ]
        if incidents != expected_incidents:
            raise RuntimeError("12h learning recovery incident binding mismatch.")
        source = payload.get("source_archive", {})
        if source != FROZEN_COMPLETE_ARCHIVE_SPEC:
            raise RuntimeError("12h learning source binding mismatch.")
        members = payload.get("source_member_evidence", [])
        if [item.get("asset") for item in members] != list(ASSET_ORDER):
            raise RuntimeError("12h learning source member order mismatch.")
        for item in members:
            asset = item["asset"]
            if (
                item.get("development_rows") != EXPECTED_DEVELOPMENT_ROWS[asset]
                or item.get("missing_calendar_buckets")
                != EXPECTED_MISSING_BUCKETS[asset]
                or len(item.get("missing_development_timestamps_utc", []))
                != EXPECTED_MISSING_BUCKETS[asset]
                or item.get("development_trade_counts_validated") is not True
                or item.get("nondevelopment_ohlcvt_values_parsed") is not False
            ):
                raise RuntimeError("12h learning source member boundary mismatch.")
        if payload.get("learning_core_configuration_sha256") != LEARNING_CORE_CONFIGURATION_SHA256:
            raise RuntimeError("12h learning configuration binding mismatch.")
        if payload.get("learning_core_component_sha256") != _file_sha256(
            Path(__file__).with_name("kraken_ai_driven_v2_learning_core.py")
        ):
            raise RuntimeError("12h learning core component binding mismatch.")

        prediction = payload.get("prediction_artifact", {})
        if (
            prediction.get("path") != PREDICTIONS_FILENAME
            or prediction.get("checksum_path") != PREDICTIONS_SHA256_FILENAME
        ):
            raise RuntimeError("OOF prediction artifact path mismatch.")
        prediction_path = root / prediction.get("path", "")
        prediction_sidecar = root / prediction.get("checksum_path", "")
        if not prediction_path.is_file() or not prediction_sidecar.is_file():
            raise FileNotFoundError("OOF prediction artifact is incomplete.")
        prediction_digest = _file_sha256(prediction_path)
        if prediction_digest != prediction.get("sha256"):
            raise RuntimeError("OOF prediction artifact checksum mismatch.")
        if prediction_sidecar.read_text(encoding="ascii") != (
            f"{prediction_digest}  {prediction_path.name}\n"
        ):
            raise RuntimeError("OOF prediction sidecar mismatch.")
        try:
            prediction_payload = json.loads(prediction_path.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("OOF prediction artifact is not valid JSON.") from exc
        if canonical_json_bytes(prediction_payload) != prediction_path.read_bytes():
            raise RuntimeError("OOF prediction artifact is not canonical JSON.")
        if (
            prediction_payload.get("run_id") != RUN_ID
            or prediction_payload.get("record_count") != len(prediction_payload.get("records", []))
            or prediction_payload.get("record_count")
            != payload.get("out_of_fold_prediction_count")
        ):
            raise RuntimeError("OOF prediction artifact content mismatch.")

        expected_files = {
            REPORT_FILENAME,
            REPORT_SHA256_FILENAME,
            prediction["path"],
            prediction["checksum_path"],
        }
        observed_artifact_ids = set()
        valid_artifact_ids = {
            f"{fold['fold_id']}|{model_id}"
            for fold in FOLD_PLAN
            for model_id in MODEL_SPECS
        }
        for artifact in payload.get("model_artifacts", []):
            artifact_id = artifact.get("artifact_id")
            if artifact_id not in valid_artifact_ids or artifact_id in observed_artifact_ids:
                raise RuntimeError("Learned model artifact identity mismatch.")
            observed_artifact_ids.add(artifact_id)
            expected_path = f"{MODEL_DIRECTORY_NAME}/{_artifact_filename(artifact_id)}"
            if artifact.get("path") != expected_path:
                raise RuntimeError("Learned model artifact path mismatch.")
            artifact_path = root / artifact["path"]
            if not artifact_path.is_file():
                raise FileNotFoundError("A learned model artifact is missing.")
            if _file_sha256(artifact_path) != artifact["sha256"]:
                raise RuntimeError("Learned model artifact checksum mismatch.")
            if artifact_path.stat().st_size != artifact["bytes"]:
                raise RuntimeError("Learned model artifact byte-size mismatch.")
            expected_files.add(artifact["path"])
        observed_files = {
            path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
        }
        if observed_files != expected_files:
            raise RuntimeError("12h learning evidence file manifest mismatch.")

        trained = payload.get("trained_model_count")
        prediction_count = payload.get("out_of_fold_prediction_count")
        if payload["learning_status"] == REVIEW_REQUIRED_STATUS:
            if trained != len(FOLD_PLAN) * len(MODEL_SPECS) or prediction_count <= 0:
                raise RuntimeError("Completed learning evidence artifact count mismatch.")
            if payload.get("model_training_executed") is not True:
                raise RuntimeError("Completed learning evidence training flag mismatch.")
        else:
            if trained != 0 or prediction_count != 0:
                raise RuntimeError("Insufficient-support evidence must not contain models.")
            if payload.get("model_training_executed") is not False:
                raise RuntimeError("Insufficient-support evidence training flag mismatch.")
        return LockedLearningEvidence(report_path, checksum_path, digest, payload)


class KrakenAIDrivenV212hDevelopmentLearningRunner:
    @staticmethod
    def _external_paths(archive_path, evidence_root):
        project_root = Path(__file__).resolve().parents[1]
        archive = Path(archive_path).resolve()
        evidence = Path(evidence_root).resolve()
        if archive == project_root or archive.is_relative_to(project_root):
            raise ValueError("12h source archive must remain outside the repository.")
        if evidence == project_root or evidence.is_relative_to(project_root):
            raise ValueError("12h learning evidence must remain outside the repository.")
        if archive == evidence or archive.is_relative_to(evidence) or evidence.is_relative_to(archive):
            raise ValueError("12h source archive and evidence must not overlap.")
        return archive, evidence

    @staticmethod
    def _validate_prior_attempt_staging(
        prior_attempt_staging,
        evidence_root,
        *,
        attempt,
        execution_commit,
    ):
        project_root = Path(__file__).resolve().parents[1]
        prior = Path(prior_attempt_staging).resolve()
        if prior == project_root or prior.is_relative_to(project_root):
            raise ValueError(
                f"Attempt {attempt} staging marker must remain outside the repository."
            )
        if not prior.is_dir() or prior.name != STAGING_DIRECTORY_NAME:
            raise FileNotFoundError(
                f"Exact Attempt {attempt} staging marker is required for recovery."
            )
        if prior == evidence_root or prior.is_relative_to(evidence_root) or evidence_root.is_relative_to(prior):
            raise ValueError(
                f"Attempt {attempt} marker and Attempt 3 evidence must not overlap."
            )
        entries = list(prior.iterdir())
        if entries:
            raise RuntimeError(
                f"Attempt {attempt} staging marker is not the preserved empty incident marker."
            )
        return {
            "attempt": attempt,
            "execution_commit": execution_commit,
            "final_evidence_exists": False,
            "staging_directory_name": STAGING_DIRECTORY_NAME,
            "staging_entry_count": 0,
            "staging_preserved": True,
        }

    @classmethod
    def _validate_prior_attempt_stagings(
        cls,
        attempt_1_staging,
        attempt_2_staging,
        evidence_root,
    ):
        paths = [Path(attempt_1_staging).resolve(), Path(attempt_2_staging).resolve()]
        if (
            paths[0] == paths[1]
            or paths[0].is_relative_to(paths[1])
            or paths[1].is_relative_to(paths[0])
        ):
            raise ValueError("Attempt 1 and Attempt 2 staging markers must be distinct.")
        return [
            cls._validate_prior_attempt_staging(
                path,
                evidence_root,
                attempt=attempt,
                execution_commit=PRIOR_ATTEMPT_EXECUTION_COMMITS[attempt],
            )
            for attempt, path in enumerate(paths, start=1)
        ]

    @staticmethod
    def _assert_one_shot(evidence_root):
        final = evidence_root / EVIDENCE_DIRECTORY_NAME
        staging = evidence_root / STAGING_DIRECTORY_NAME
        if final.exists():
            raise FileExistsError("12h learning evidence already exists; refusing repeat.")
        if staging.exists():
            raise FileExistsError("Incomplete 12h learning staging evidence exists.")
        return final, staging

    @staticmethod
    def _validate_archive(archive_path):
        spec = FROZEN_COMPLETE_ARCHIVE_SPEC
        if not archive_path.is_file():
            raise FileNotFoundError(f"12h source archive does not exist: {archive_path}")
        if archive_path.name != spec["filename"]:
            raise ValueError("12h source archive filename mismatch.")
        size = archive_path.stat().st_size
        if size != spec["bytes"]:
            raise RuntimeError("12h source archive byte-size mismatch.")
        digest = _file_sha256(archive_path)
        if digest != spec["sha256"]:
            raise RuntimeError("12h source archive SHA256 mismatch.")
        return {"filename": archive_path.name, "bytes": size, "sha256": digest}

    @staticmethod
    def _parse_market_value(raw_value, member_name, row_number, column):
        try:
            value = float(raw_value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise RuntimeError(
                f"Invalid {column} in Development row {member_name}:{row_number}."
            ) from exc
        if not math.isfinite(value):
            raise RuntimeError(
                f"Non-finite {column} in Development row {member_name}:{row_number}."
            )
        return value

    @staticmethod
    def _parse_trade_count(raw_value, member_name, row_number):
        try:
            value = int(raw_value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise RuntimeError(
                f"Invalid Trades in Development row {member_name}:{row_number}."
            ) from exc
        if value <= 0:
            raise RuntimeError(
                f"Nonpositive Trades in Development row {member_name}:{row_number}."
            )
        return value

    @classmethod
    def _read_development_member(cls, archive, info, asset):
        start = int(_utc(DEVELOPMENT_START_UTC).timestamp())
        end = int(_utc(DEVELOPMENT_END_EXCLUSIVE_UTC).timestamp())
        interval_seconds = int(BAR_INTERVAL.total_seconds())
        member_digest = hashlib.sha256()
        timestamps = []
        rows = []
        previous_source_timestamp = None
        with archive.open(info) as source:
            for row_number, raw_line in enumerate(source, start=1):
                member_digest.update(raw_line)
                stripped = raw_line.rstrip(b"\r\n")
                if not stripped:
                    continue
                fields = stripped.split(b",")
                if len(fields) != 7:
                    raise RuntimeError(
                        f"12h source row must contain seven columns: {info.filename}:{row_number}."
                    )
                try:
                    timestamp = int(fields[0])
                except ValueError as exc:
                    raise RuntimeError(
                        f"Invalid timestamp in 12h source row {info.filename}:{row_number}."
                    ) from exc
                if previous_source_timestamp is not None and timestamp <= previous_source_timestamp:
                    raise RuntimeError(f"12h source timestamps are not strictly increasing: {info.filename}.")
                previous_source_timestamp = timestamp
                if not start <= timestamp < end:
                    continue
                if timestamp % interval_seconds:
                    raise RuntimeError(f"Misaligned Development timestamp in {info.filename}.")
                open_, high, low, close = (
                    cls._parse_market_value(fields[index], info.filename, row_number, column)
                    for index, column in zip(
                        (1, 2, 3, 4), ("Open", "High", "Low", "Close"), strict=True
                    )
                )
                volume = cls._parse_market_value(fields[5], info.filename, row_number, "Volume")
                cls._parse_trade_count(fields[6], info.filename, row_number)
                timestamps.append(timestamp)
                rows.append((open_, high, low, close, volume))
        if len(timestamps) != EXPECTED_DEVELOPMENT_ROWS[asset]:
            raise RuntimeError(f"Unexpected 12h Development row count for {asset}.")
        expected_timestamps = range(start, end, interval_seconds)
        observed_timestamps = set(timestamps)
        missing_timestamps = [
            timestamp for timestamp in expected_timestamps if timestamp not in observed_timestamps
        ]
        missing = len(missing_timestamps)
        if missing != EXPECTED_MISSING_BUCKETS[asset]:
            raise RuntimeError(f"Unexpected 12h missing-bucket count for {asset}.")
        frame = pd.DataFrame(
            rows,
            columns=("Open", "High", "Low", "Close", "Volume"),
            index=pd.to_datetime(timestamps, unit="s", utc=True),
        )
        identity_digest = hashlib.sha256(
            canonical_json_bytes([_iso(timestamp) for timestamp in frame.index])
        ).hexdigest()
        return frame, {
            "asset": asset,
            "member_name": info.filename,
            "compressed_bytes": int(info.compress_size),
            "uncompressed_bytes": int(info.file_size),
            "member_uncompressed_sha256": member_digest.hexdigest(),
            "development_timestamp_identity_sha256": identity_digest,
            "development_rows": len(frame),
            "missing_calendar_buckets": missing,
            "missing_development_timestamps_utc": [
                _iso(pd.Timestamp(timestamp, unit="s", tz="UTC"))
                for timestamp in missing_timestamps
            ],
            "first_development_timestamp": _iso(frame.index[0]),
            "last_development_timestamp": _iso(frame.index[-1]),
            "development_trade_counts_validated": True,
            "nondevelopment_ohlcvt_values_parsed": False,
        }

    def _load_frames(self, archive_path):
        frames = {}
        evidence = []
        try:
            with zipfile.ZipFile(archive_path) as archive:
                infos = archive.infolist()
                names = [item.filename for item in infos]
                if len(names) != len(set(names)):
                    raise RuntimeError("12h source archive has duplicate member names.")
                if any(item.flag_bits & 0x1 for item in infos):
                    raise RuntimeError("Encrypted 12h source members are prohibited.")
                for asset in ASSET_ORDER:
                    required = f"{PAIR_METADATA[asset]['archive_pair_stem']}_720.csv"
                    matches = [
                        item
                        for item in infos
                        if not item.is_dir() and Path(item.filename).name == required
                    ]
                    if len(matches) != 1:
                        raise RuntimeError(f"Exactly one {required} source member is required.")
                    frame, member = self._read_development_member(
                        archive, matches[0], asset
                    )
                    frames[asset] = frame
                    evidence.append(member)
        except (OSError, zipfile.BadZipFile) as exc:
            raise RuntimeError("Unable to open locked 12h Kraken source archive.") from exc
        return validate_development_frames(frames), evidence

    @staticmethod
    def _core_component_sha256():
        return _file_sha256(Path(__file__).with_name("kraken_ai_driven_v2_learning_core.py"))

    def run(
        self,
        archive_path,
        evidence_root,
        attempt_1_staging,
        attempt_2_staging,
        authorization_phrase,
    ):
        if authorization_phrase != AUTHORIZATION_PHRASE:
            raise PermissionError("Exact one-shot 12h learning authorization phrase is required.")
        archive_path, evidence_root = self._external_paths(archive_path, evidence_root)
        final, staging = self._assert_one_shot(evidence_root)
        prior_attempt_incidents = self._validate_prior_attempt_stagings(
            attempt_1_staging,
            attempt_2_staging,
            evidence_root,
        )
        evidence_root.mkdir(parents=True, exist_ok=True)
        staging.mkdir(exist_ok=False)
        archive_evidence = self._validate_archive(archive_path)
        frames, member_evidence = self._load_frames(archive_path)
        labeled = build_labeled_learning_data(frames)
        support = fold_support(labeled.table)

        if support["all_folds_supported"]:
            learning = train_walk_forward(
                labeled.table,
                minimum_training_class_count=MINIMUM_TRAINING_CLASS_COUNT,
                minimum_validation_class_count=MINIMUM_VALIDATION_CLASS_COUNT,
            )
            learning_status = REVIEW_REQUIRED_STATUS
            model_bytes = learning.model_artifact_bytes
            model_hashes = learning.model_artifact_sha256
            predictions = learning.predictions
            metrics = learning.metrics
            training_executed = True
        else:
            learning_status = INSUFFICIENT_SUPPORT_STATUS
            model_bytes = {}
            model_hashes = {}
            predictions = pd.DataFrame()
            metrics = {}
            training_executed = False

        prediction_bytes = canonical_json_bytes(_prediction_payload(predictions))
        prediction_sha256 = hashlib.sha256(prediction_bytes).hexdigest()
        model_manifest = []
        for key in sorted(model_bytes):
            raw = model_bytes[key]
            digest = hashlib.sha256(raw).hexdigest()
            if digest != model_hashes[key]:
                raise RuntimeError("Learning Core model artifact hash mismatch.")
            filename = _artifact_filename(key)
            model_manifest.append(
                {
                    "artifact_id": key,
                    "path": f"{MODEL_DIRECTORY_NAME}/{filename}",
                    "bytes": len(raw),
                    "sha256": digest,
                }
            )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "run_id": RUN_ID,
            "implementation_parent_commit": PARENT_COMMIT,
            "recovery_attempt": 3,
            "prior_attempt_incidents": prior_attempt_incidents,
            "learning_status": learning_status,
            "partition": "DEVELOPMENT",
            "resolution": "12h",
            "development_start_utc": DEVELOPMENT_START_UTC,
            "development_end_exclusive_utc": DEVELOPMENT_END_EXCLUSIVE_UTC,
            "source_archive": archive_evidence,
            "source_member_evidence": member_evidence,
            "asset_order": list(ASSET_ORDER),
            "class_order": list(CLASS_ORDER),
            "feature_columns": list(FEATURE_COLUMNS),
            "model_order": list(MODEL_SPECS),
            "learning_core_configuration_sha256": LEARNING_CORE_CONFIGURATION_SHA256,
            "learning_core_component_sha256": self._core_component_sha256(),
            "learning_table_identity_sha256": _learning_table_identity_sha256(labeled.table),
            "labeled_row_count": int(len(labeled.table)),
            "asset_label_diagnostics": labeled.diagnostics,
            "fold_support": support,
            "minimum_training_class_count": MINIMUM_TRAINING_CLASS_COUNT,
            "minimum_validation_class_count": MINIMUM_VALIDATION_CLASS_COUNT,
            "predictive_metrics": _json_ready(metrics),
            "trained_model_count": len(model_manifest),
            "model_artifacts": model_manifest,
            "out_of_fold_prediction_count": int(len(predictions)),
            "prediction_artifact": {
                "path": PREDICTIONS_FILENAME,
                "checksum_path": PREDICTIONS_SHA256_FILENAME,
                "bytes": len(prediction_bytes),
                "sha256": prediction_sha256,
            },
            "source_archive_opened": True,
            "development_data_opened": True,
            "nondevelopment_ohlcvt_values_parsed": False,
            "labels_generated": True,
            "model_training_authorized": True,
            "model_training_executed": training_executed,
            "walk_forward_executed": training_executed,
            "automatic_model_selection": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
            "next_stage": "READ_ONLY_DEVELOPMENT_LEARNING_EVIDENCE_REVIEW",
        }
        report_bytes = canonical_json_bytes(_json_ready(payload))
        report_sha256 = hashlib.sha256(report_bytes).hexdigest()

        (staging / REPORT_FILENAME).write_bytes(report_bytes)
        (staging / REPORT_SHA256_FILENAME).write_text(
            f"{report_sha256}  {REPORT_FILENAME}\n", encoding="ascii"
        )
        (staging / PREDICTIONS_FILENAME).write_bytes(prediction_bytes)
        (staging / PREDICTIONS_SHA256_FILENAME).write_text(
            f"{prediction_sha256}  {PREDICTIONS_FILENAME}\n", encoding="ascii"
        )
        if model_manifest:
            model_directory = staging / MODEL_DIRECTORY_NAME
            model_directory.mkdir(exist_ok=False)
            for artifact in model_manifest:
                key = artifact["artifact_id"]
                (staging / artifact["path"]).write_bytes(model_bytes[key])
        staging.rename(final)
        locked = KrakenAIDrivenV212hLearningEvidenceLock().lock(final)
        return RecordedLearningEvidence(
            locked.report_path,
            locked.checksum_path,
            locked.report_sha256,
            learning_status,
            int(len(labeled.table)),
            len(model_manifest),
            int(len(predictions)),
        )


def runner_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "protocol_id": PROTOCOL_ID,
        "run_id": RUN_ID,
        "parent_commit": PARENT_COMMIT,
        "recovery_attempt": 3,
        "prior_attempt_staging_count_required": 2,
        "boundary_missing_bucket_validation_implemented": True,
        "mandatory_endpoint_presence_assumption_active": False,
        "authorization_phrase": AUTHORIZATION_PHRASE,
        "authorization_phrase_active": False,
        "active_resolution": "12h",
        "partition": "DEVELOPMENT",
        "asset_order": list(ASSET_ORDER),
        "model_order": list(MODEL_SPECS),
        "model_artifact_count_if_supported": len(FOLD_PLAN) * len(MODEL_SPECS),
        "real_model_artifact_persistence_implemented": True,
        "out_of_fold_prediction_artifact_implemented": True,
        "class_support_hold_cash_branch_implemented": True,
        "independent_evidence_lock_implemented": True,
        "one_shot_atomic_evidence_implemented": True,
        "source_archive_opened": False,
        "development_data_opened": False,
        "labels_generated": False,
        "model_training_authorized": False,
        "model_training_executed": False,
        "automatic_model_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_12H_DEVELOPMENT_LEARNING_RECOVERY_ATTEMPT_3",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Execute one authorized Kraken V2 12h Development learning run."
    )
    parser.add_argument("--complete-archive", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--attempt-1-staging", required=True)
    parser.add_argument("--attempt-2-staging", required=True)
    parser.add_argument("--authorization-phrase", required=True)
    args = parser.parse_args(argv)
    recorded = KrakenAIDrivenV212hDevelopmentLearningRunner().run(
        args.complete_archive,
        args.evidence_root,
        args.attempt_1_staging,
        args.attempt_2_staging,
        args.authorization_phrase,
    )
    print(json.dumps(recorded.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
