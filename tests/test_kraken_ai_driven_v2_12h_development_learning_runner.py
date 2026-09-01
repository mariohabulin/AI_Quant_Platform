import hashlib
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import zipfile

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_12h_development_learning_runner as runner_module
from kraken_ai_driven_v2_12h_development_learning_runner import (
    ASSET_ORDER,
    AUTHORIZATION_PHRASE,
    CLASS_ORDER,
    EVIDENCE_DIRECTORY_NAME,
    EXPECTED_DEVELOPMENT_ROWS,
    EXPECTED_MISSING_BUCKETS,
    FEATURE_COLUMNS,
    FOLD_PLAN,
    INSUFFICIENT_SUPPORT_STATUS,
    KrakenAIDrivenV212hDevelopmentLearningRunner,
    KrakenAIDrivenV212hLearningEvidenceLock,
    MODEL_SPECS,
    PREDICTIONS_FILENAME,
    PROTOCOL_ID,
    REPORT_FILENAME,
    REVIEW_REQUIRED_STATUS,
    RUN_ID,
    STAGING_DIRECTORY_NAME,
    fold_support,
    runner_declaration,
)


def _complete_timestamps():
    return pd.date_range(
        "2019-01-01T00:00:00Z",
        "2024-03-31T12:00:00Z",
        freq="12h",
        tz="UTC",
    )


def _write_complete_12h_archive(path, *, include_vwap=False):
    stems = {"BTC-USD": "XBTUSD", "ETH-USD": "ETHUSD", "XRP-USD": "XRPUSD"}
    full = _complete_timestamps()
    removed = {
        # The locked source's single BTC omission is at the right Development edge.
        "BTC-USD": {len(full) - 1},
        "ETH-USD": set(),
        "XRP-USD": {1000, 1001, 1002, 1003},
    }
    boundary = int(pd.Timestamp("2024-04-01T00:00:00Z").timestamp())
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for asset in ASSET_ORDER:
            lines = []
            for number, timestamp in enumerate(full):
                if number in removed[asset]:
                    continue
                open_ = 100.0 + number * 0.01
                values = [
                    int(timestamp.timestamp()),
                    open_,
                    open_ + 1,
                    open_ - 1,
                    open_ + 0.2,
                ]
                if include_vwap:
                    values.append(open_ + 0.1)
                values.extend((1000, 10))
                lines.append(",".join(str(value) for value in values) + "\n")
            # These values are intentionally invalid.  Only their timestamps may be read.
            lines.append(f"{boundary},NOT_PARSED,NOT_PARSED,NOT_PARSED,NOT_PARSED,x,x\n")
            lines.append(f"{boundary + 43200},STILL_NOT_PARSED,x,x,x,x,x\n")
            archive.writestr(f"nested/{stems[asset]}_720.csv", "".join(lines))
    return path


def _learning_table(all_classes=True):
    timestamps = pd.date_range(
        "2019-04-01T00:00:00Z",
        "2024-02-01T00:00:00Z",
        freq="7D",
        tz="UTC",
    )
    rows = []
    for asset_number, asset in enumerate(ASSET_ORDER):
        for number, timestamp in enumerate(timestamps):
            label = CLASS_ORDER[number % 3] if all_classes else CLASS_ORDER[0]
            row = {
                "asset": asset,
                "decision_timestamp": timestamp,
                "entry_timestamp": timestamp + pd.Timedelta(hours=12),
                "event_end_timestamp": timestamp + pd.Timedelta(days=1),
                "label": label,
                "outcome_net_r": {CLASS_ORDER[0]: 3.0, CLASS_ORDER[1]: -1.0, CLASS_ORDER[2]: 0.0}[label],
            }
            for feature_number, feature in enumerate(FEATURE_COLUMNS):
                row[feature] = math.sin(number / 5.0 + asset_number) + feature_number / 100.0
            rows.append(row)
    return pd.DataFrame(rows)


def _diagnostics(table):
    result = {}
    for asset in ASSET_ORDER:
        labels = table.loc[table["asset"] == asset, "label"].value_counts()
        result[asset] = {
            "feature_rows": int((table["asset"] == asset).sum()),
            "labeled_rows": int((table["asset"] == asset).sum()),
            "invalid_reason_counts": {},
            "label_counts": {label: int(labels.get(label, 0)) for label in CLASS_ORDER},
        }
    return result


def _fake_learning_result():
    artifacts = {}
    rows = []
    metrics = {}
    for fold in FOLD_PLAN:
        validation_timestamp = pd.Timestamp(fold["validation_start_utc"]) + pd.Timedelta(days=1)
        for model_id in MODEL_SPECS:
            key = f"{fold['fold_id']}|{model_id}"
            artifacts[key] = f"learned-{key}".encode("ascii")
            metrics[key] = {
                "fold_id": fold["fold_id"],
                "model_id": model_id,
                "multiclass_log_loss": 1.0,
            }
            rows.append(
                {
                    "fold_id": fold["fold_id"],
                    "model_id": model_id,
                    "asset": "BTC-USD",
                    "decision_timestamp": validation_timestamp,
                    "event_end_timestamp": validation_timestamp + pd.Timedelta(days=1),
                    "training_end_timestamp": pd.Timestamp(fold["training_end_exclusive_utc"]),
                    "actual_label": CLASS_ORDER[0],
                    "actual_outcome_net_r": 3.0,
                    "p_target_3r_first": 0.6,
                    "p_stop_1r_first": 0.2,
                    "p_timeout_no_barrier": 0.2,
                }
            )
    return SimpleNamespace(
        predictions=pd.DataFrame(rows),
        metrics=metrics,
        model_artifact_bytes=artifacts,
        model_artifact_sha256={
            key: hashlib.sha256(value).hexdigest() for key, value in artifacts.items()
        },
    )


def _patch_synthetic_run(monkeypatch, table, training_result=None):
    source = runner_module.FROZEN_COMPLETE_ARCHIVE_SPEC
    monkeypatch.setattr(
        KrakenAIDrivenV212hDevelopmentLearningRunner,
        "_validate_archive",
        staticmethod(lambda _path: dict(source)),
    )
    dummy_frames = {asset: pd.DataFrame() for asset in ASSET_ORDER}
    monkeypatch.setattr(
        KrakenAIDrivenV212hDevelopmentLearningRunner,
        "_load_frames",
        lambda self, _path: (
            dummy_frames,
            [
                {
                    "asset": asset,
                    "development_rows": EXPECTED_DEVELOPMENT_ROWS[asset],
                    "missing_calendar_buckets": EXPECTED_MISSING_BUCKETS[asset],
                    "missing_development_timestamps_utc": [
                        f"synthetic-missing-{number}"
                        for number in range(EXPECTED_MISSING_BUCKETS[asset])
                    ],
                    "development_trade_counts_validated": True,
                    "nondevelopment_ohlcvt_values_parsed": False,
                }
                for asset in ASSET_ORDER
            ],
        ),
    )
    monkeypatch.setattr(
        runner_module,
        "build_labeled_learning_data",
        lambda _frames: SimpleNamespace(table=table, diagnostics=_diagnostics(table)),
    )
    if training_result is not None:
        monkeypatch.setattr(
            runner_module,
            "train_walk_forward",
            lambda *args, **kwargs: training_result,
        )


def _prior_attempt_stagings(tmp_path):
    paths = []
    for attempt in (1, 2):
        path = tmp_path / f"attempt_{attempt}" / STAGING_DIRECTORY_NAME
        path.mkdir(parents=True)
        paths.append(path)
    return tuple(paths)


def test_runner_declaration_is_inert_and_does_not_select_a_model():
    declaration = runner_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["run_id"] == RUN_ID
    assert declaration["parent_commit"] == "203b4c5b81434be3edab7ec5372448cd12472288"
    assert declaration["recovery_attempt"] == 3
    assert declaration["prior_attempt_staging_count_required"] == 2
    assert declaration["boundary_missing_bucket_validation_implemented"] is True
    assert declaration["mandatory_endpoint_presence_assumption_active"] is False
    assert declaration["active_resolution"] == "12h"
    assert declaration["partition"] == "DEVELOPMENT"
    assert declaration["model_artifact_count_if_supported"] == 6
    assert declaration["real_model_artifact_persistence_implemented"] is True
    assert declaration["authorization_phrase_active"] is False
    assert declaration["source_archive_opened"] is False
    assert declaration["model_training_executed"] is False
    assert declaration["automatic_model_selection"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_reader_opens_only_development_values_and_hashes_whole_members(tmp_path):
    archive_path = _write_complete_12h_archive(tmp_path / "source.zip")
    frames, evidence = KrakenAIDrivenV212hDevelopmentLearningRunner()._load_frames(
        archive_path
    )

    assert {asset: len(frame) for asset, frame in frames.items()} == EXPECTED_DEVELOPMENT_ROWS
    assert all(frame.index.min() == pd.Timestamp("2019-01-01T00:00:00Z") for frame in frames.values())
    assert frames["BTC-USD"].index.max() == pd.Timestamp("2024-03-31T00:00:00Z")
    assert frames["ETH-USD"].index.max() == pd.Timestamp("2024-03-31T12:00:00Z")
    assert frames["XRP-USD"].index.max() == pd.Timestamp("2024-03-31T12:00:00Z")
    btc = next(item for item in evidence if item["asset"] == "BTC-USD")
    assert btc["missing_calendar_buckets"] == 1
    assert btc["missing_development_timestamps_utc"] == ["2024-03-31T12:00:00Z"]
    assert all(item["nondevelopment_ohlcvt_values_parsed"] is False for item in evidence)
    assert all(item["development_trade_counts_validated"] is True for item in evidence)
    assert all(len(item["member_uncompressed_sha256"]) == 64 for item in evidence)


def test_reader_rejects_the_attempt_one_eight_column_assumption(tmp_path):
    archive_path = _write_complete_12h_archive(
        tmp_path / "wrong-eight-column-source.zip", include_vwap=True
    )

    with pytest.raises(RuntimeError, match="seven columns"):
        KrakenAIDrivenV212hDevelopmentLearningRunner()._load_frames(archive_path)


def test_reader_rejects_an_unexpected_development_row_count(tmp_path):
    archive_path = _write_complete_12h_archive(tmp_path / "source.zip")
    with zipfile.ZipFile(archive_path, "a") as archive:
        archive.writestr("nested/XBTUSD_720_DUPLICATE.csv", "1,1,1,1,1,1,1\n")

    # The duplicate has a different basename and is ignored; mutate the expected count instead.
    monkey = dict(EXPECTED_DEVELOPMENT_ROWS)
    runner_module.EXPECTED_DEVELOPMENT_ROWS = {**monkey, "BTC-USD": monkey["BTC-USD"] + 1}
    try:
        with pytest.raises(RuntimeError, match="row count"):
            KrakenAIDrivenV212hDevelopmentLearningRunner()._load_frames(archive_path)
    finally:
        runner_module.EXPECTED_DEVELOPMENT_ROWS = monkey


def test_fold_support_is_measured_before_training():
    supported = fold_support(_learning_table(all_classes=True))
    insufficient = fold_support(_learning_table(all_classes=False))

    assert supported["all_folds_supported"] is True
    assert all(item["all_class_support_passed"] for item in supported["folds"])
    assert insufficient["all_folds_supported"] is False


def test_wrong_authorization_cannot_open_source_or_create_evidence(tmp_path):
    with pytest.raises(PermissionError, match="authorization phrase"):
        KrakenAIDrivenV212hDevelopmentLearningRunner().run(
            tmp_path / "missing.zip",
            tmp_path / "evidence",
            tmp_path / "missing-attempt-1-staging",
            tmp_path / "missing-attempt-2-staging",
            "WRONG",
        )
    assert not (tmp_path / "evidence").exists()


def test_recovery_requires_the_preserved_empty_attempt_one_staging_marker(tmp_path):
    evidence_root = tmp_path / "attempt_2"
    marker = tmp_path / "attempt_1" / STAGING_DIRECTORY_NAME
    runner = KrakenAIDrivenV212hDevelopmentLearningRunner()

    with pytest.raises(FileNotFoundError, match="Attempt 1 staging marker"):
        runner._validate_prior_attempt_staging(
            marker,
            evidence_root,
            attempt=1,
            execution_commit="cc8ae44c45d41182af3bc91ee21cf075e65011b5",
        )

    marker.mkdir(parents=True)
    (marker / "unexpected.txt").write_text("not empty", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not the preserved empty incident marker"):
        runner._validate_prior_attempt_staging(
            marker,
            evidence_root,
            attempt=1,
            execution_commit="cc8ae44c45d41182af3bc91ee21cf075e65011b5",
        )


def test_recovery_requires_two_distinct_prior_attempt_markers(tmp_path):
    marker = tmp_path / "attempt" / STAGING_DIRECTORY_NAME
    marker.mkdir(parents=True)

    with pytest.raises(ValueError, match="must be distinct"):
        KrakenAIDrivenV212hDevelopmentLearningRunner._validate_prior_attempt_stagings(
            marker,
            marker,
            tmp_path / "attempt_3",
        )


def test_authorized_failure_leaves_staging_and_blocks_silent_retry(tmp_path, monkeypatch):
    archive_path = tmp_path / "Kraken_OHLCVT.zip"
    archive_path.write_bytes(b"wrong-source")
    evidence_root = tmp_path / "evidence"
    attempt_1_staging, attempt_2_staging = _prior_attempt_stagings(tmp_path)
    monkeypatch.setattr(
        KrakenAIDrivenV212hDevelopmentLearningRunner,
        "_validate_archive",
        staticmethod(lambda _path: (_ for _ in ()).throw(RuntimeError("source failure"))),
    )

    with pytest.raises(RuntimeError, match="source failure"):
        KrakenAIDrivenV212hDevelopmentLearningRunner().run(
            archive_path,
            evidence_root,
            attempt_1_staging,
            attempt_2_staging,
            AUTHORIZATION_PHRASE,
        )
    assert (evidence_root / STAGING_DIRECTORY_NAME).is_dir()
    with pytest.raises(FileExistsError, match="staging evidence"):
        KrakenAIDrivenV212hDevelopmentLearningRunner().run(
            archive_path,
            evidence_root,
            attempt_1_staging,
            attempt_2_staging,
            AUTHORIZATION_PHRASE,
        )


def test_successful_run_atomically_records_six_models_and_oof_predictions(tmp_path, monkeypatch):
    table = _learning_table(all_classes=True)
    _patch_synthetic_run(monkeypatch, table, _fake_learning_result())
    archive_path = tmp_path / "Kraken_OHLCVT.zip"
    archive_path.write_bytes(b"opaque-test-source")
    evidence_root = tmp_path / "evidence"
    attempt_1_staging, attempt_2_staging = _prior_attempt_stagings(tmp_path)

    recorded = KrakenAIDrivenV212hDevelopmentLearningRunner().run(
        archive_path,
        evidence_root,
        attempt_1_staging,
        attempt_2_staging,
        AUTHORIZATION_PHRASE,
    )
    final = evidence_root / EVIDENCE_DIRECTORY_NAME
    locked = KrakenAIDrivenV212hLearningEvidenceLock().lock(final)

    assert recorded.learning_status == REVIEW_REQUIRED_STATUS
    assert recorded.trained_model_count == 6
    assert recorded.prediction_count == 6
    assert locked.payload["model_training_executed"] is True
    assert locked.payload["automatic_model_selection"] is False
    assert len(locked.payload["model_artifacts"]) == 6
    assert (final / PREDICTIONS_FILENAME).is_file()
    assert not (evidence_root / STAGING_DIRECTORY_NAME).exists()

    with pytest.raises(FileExistsError, match="refusing repeat"):
        KrakenAIDrivenV212hDevelopmentLearningRunner().run(
            archive_path,
            evidence_root,
            attempt_1_staging,
            attempt_2_staging,
            AUTHORIZATION_PHRASE,
        )


def test_insufficient_class_support_records_hold_cash_without_model_files(tmp_path, monkeypatch):
    table = _learning_table(all_classes=False)
    _patch_synthetic_run(monkeypatch, table)
    archive_path = tmp_path / "Kraken_OHLCVT.zip"
    archive_path.write_bytes(b"opaque-test-source")
    evidence_root = tmp_path / "evidence"
    attempt_1_staging, attempt_2_staging = _prior_attempt_stagings(tmp_path)

    recorded = KrakenAIDrivenV212hDevelopmentLearningRunner().run(
        archive_path,
        evidence_root,
        attempt_1_staging,
        attempt_2_staging,
        AUTHORIZATION_PHRASE,
    )
    locked = KrakenAIDrivenV212hLearningEvidenceLock().lock(
        evidence_root / EVIDENCE_DIRECTORY_NAME
    )

    assert recorded.learning_status == INSUFFICIENT_SUPPORT_STATUS
    assert recorded.trained_model_count == 0
    assert recorded.prediction_count == 0
    assert locked.payload["model_training_executed"] is False
    assert locked.payload["model_artifacts"] == []
    assert locked.payload["next_stage"] == "READ_ONLY_DEVELOPMENT_LEARNING_EVIDENCE_REVIEW"


def test_evidence_lock_detects_model_tampering(tmp_path, monkeypatch):
    table = _learning_table(all_classes=True)
    _patch_synthetic_run(monkeypatch, table, _fake_learning_result())
    archive_path = tmp_path / "Kraken_OHLCVT.zip"
    archive_path.write_bytes(b"opaque-test-source")
    evidence_root = tmp_path / "evidence"
    attempt_1_staging, attempt_2_staging = _prior_attempt_stagings(tmp_path)
    KrakenAIDrivenV212hDevelopmentLearningRunner().run(
        archive_path,
        evidence_root,
        attempt_1_staging,
        attempt_2_staging,
        AUTHORIZATION_PHRASE,
    )
    final = evidence_root / EVIDENCE_DIRECTORY_NAME
    report = json.loads((final / REPORT_FILENAME).read_text(encoding="utf-8"))
    model_path = final / report["model_artifacts"][0]["path"]
    model_path.write_bytes(model_path.read_bytes() + b"tamper")

    with pytest.raises(RuntimeError, match="model artifact checksum"):
        KrakenAIDrivenV212hLearningEvidenceLock().lock(final)
