import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_data_sufficiency_audit as audit_module
from kraken_ai_driven_v2_data_sufficiency_audit import (
    ASSET_ORDER,
    AUDIT_GATES,
    AUDIT_STATUS_NO_SELECTION,
    AUDIT_STATUS_RESOLUTION_SELECTED,
    AUTHORIZATION_PHRASE,
    CANDIDATE_RESOLUTIONS,
    DEVELOPMENT_END_EXCLUSIVE_UTC,
    DEVELOPMENT_START_UTC,
    EVIDENCE_DIRECTORY_NAME,
    FEATURE_WARMUP_DAYS,
    FOLD_PLAN,
    KrakenAIDrivenV2DataSufficiencyAuditor,
    KrakenAIDrivenV2DataSufficiencyEvidenceLock,
    LABEL_HORIZON_DAYS,
    REPORT_FILENAME,
    STAGE_1_COMMIT,
    STAGING_DIRECTORY_NAME,
    audit_declaration,
    audit_resolution_candidates,
    canonical_json_bytes,
)


def _utc(value):
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def _timestamps(interval_minutes, start=DEVELOPMENT_START_UTC, end=DEVELOPMENT_END_EXCLUSIVE_UTC):
    current = _utc(start)
    stop = _utc(end)
    step = interval_minutes * 60
    values = []
    while current < stop:
        values.append(current)
        current += step
    return values


def _candidate_inputs():
    return {
        item["resolution_id"]: {
            asset: _timestamps(item["interval_minutes"]) for asset in ASSET_ORDER
        }
        for item in CANDIDATE_RESOLUTIONS
    }


def _write_archive(path, candidate_inputs):
    stems = {"BTC-USD": "XBTUSD", "ETH-USD": "ETHUSD", "XRP-USD": "XRPUSD"}
    by_id = {item["resolution_id"]: item for item in CANDIDATE_RESOLUTIONS}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for resolution_id, assets in candidate_inputs.items():
            minutes = by_id[resolution_id]["interval_minutes"]
            for asset, timestamps in assets.items():
                rows = "".join(
                    f"{timestamp},1,1,1,1,1,1,1\n" for timestamp in timestamps
                )
                archive.writestr(f"nested/{stems[asset]}_{minutes}.csv", rows)
    return path


def test_stage_two_identity_candidate_order_and_nonperformance_boundary():
    declaration = audit_declaration()

    assert STAGE_1_COMMIT == "796c8de"
    assert declaration["status"] == (
        "KRAKEN_AI_V2_STAGE_2_DATA_SUFFICIENCY_AUDIT_IMPLEMENTED_NO_RUN_AUTHORIZATION"
    )
    assert [item["interval_minutes"] for item in CANDIDATE_RESOLUTIONS] == [1440, 720, 240]
    assert [item["timeframe"] for item in CANDIDATE_RESOLUTIONS] == ["1d", "12h", "4h"]
    assert declaration["candidate_resolution_count"] == 3
    assert declaration["selected_resolution"] is None
    assert declaration["selection_uses_performance"] is False
    assert declaration["timestamp_column_only_reader_implemented"] is True
    assert declaration["ohlcvt_value_columns_permitted"] is False
    assert declaration["source_archive_opened"] is False
    assert declaration["audit_run_authorized"] is False
    assert declaration["audit_run_executed"] is False
    assert declaration["labels_generated"] is False
    assert declaration["model_training_executed"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["live_execution_authorized"] is False


def test_support_gates_and_calendar_fold_plan_are_frozen_before_data_access():
    assert FEATURE_WARMUP_DAYS == 90
    assert LABEL_HORIZON_DAYS == 30
    assert AUDIT_GATES == {
        "minimum_observed_coverage_fraction_per_asset": 0.995,
        "minimum_valid_examples_per_asset": 9000,
        "minimum_nonoverlapping_horizons_per_asset": 48,
        "minimum_largest_continuous_segment_days_per_asset": 730,
        "maximum_gap_utc_days_per_asset": 7,
        "minimum_training_examples_per_asset_per_fold": 3000,
        "minimum_validation_examples_per_asset_per_fold": 900,
    }
    assert len(FOLD_PLAN) == 3
    assert [item["fold_id"] for item in FOLD_PLAN] == ["FOLD_1", "FOLD_2", "FOLD_3"]
    assert all(item["purge_utc_days"] == 30 for item in FOLD_PLAN)
    assert all(item["embargo_utc_days"] == 30 for item in FOLD_PLAN)
    assert FOLD_PLAN[-1]["validation_end_exclusive_utc"] == DEVELOPMENT_END_EXCLUSIVE_UTC


def test_full_synthetic_inventory_selects_four_hour_without_performance():
    report = audit_resolution_candidates(_candidate_inputs())

    assert report["status"] == AUDIT_STATUS_RESOLUTION_SELECTED
    assert report["selected_resolution"] == {
        "resolution_id": "KRAKEN_NATIVE_4H",
        "timeframe": "4h",
        "interval_minutes": 240,
    }
    assert report["selection_policy"] == "COARSEST_PASSING_CANDIDATE"
    assert report["candidate_results"][0]["all_gates_passed"] is False
    assert report["candidate_results"][1]["all_gates_passed"] is False
    assert report["candidate_results"][2]["all_gates_passed"] is True
    assert report["candidate_results"][2]["minimum_valid_examples_per_asset"] > 9000
    assert report["performance_fields_opened"] is False
    assert report["labels_generated"] is False
    assert report["model_training_executed"] is False


def test_gap_segmentation_warmup_and_right_censoring_are_counted():
    inputs = _candidate_inputs()
    four_hour = inputs["KRAKEN_NATIVE_4H"]
    removed = _utc("2022-05-11T00:00:00Z")
    four_hour["XRP-USD"] = [value for value in four_hour["XRP-USD"] if value != removed]

    report = audit_resolution_candidates(inputs)
    xrp = report["candidate_results"][2]["per_asset"]["XRP-USD"]

    assert xrp["missing_bucket_count"] == 1
    assert xrp["gap_count"] == 1
    assert xrp["maximum_gap_buckets"] == 1
    assert len(xrp["continuous_segment_rows"]) == 2
    assert xrp["feature_warmup_loss_count"] == FEATURE_WARMUP_DAYS * 6 * 2
    assert xrp["horizon_right_censored_count"] == LABEL_HORIZON_DAYS * 6 * 2


@pytest.mark.parametrize(
    "mutator,message",
    [
        (lambda values: values.__setitem__(1, values[0]), "strictly increasing"),
        (lambda values: values.__setitem__(1, values[1] + 60), "alignment"),
        (lambda values: values.__setitem__(0, _utc("2018-12-31T20:00:00Z")), "Development"),
    ],
)
def test_timestamp_inventory_fails_closed(mutator, message):
    inputs = _candidate_inputs()
    values = inputs["KRAKEN_NATIVE_4H"]["BTC-USD"]
    mutator(values)

    with pytest.raises(ValueError, match=message):
        audit_resolution_candidates(inputs)


def test_no_resolution_is_selected_when_a_required_asset_is_insufficient():
    inputs = _candidate_inputs()
    for resolution_id in inputs:
        inputs[resolution_id]["XRP-USD"] = inputs[resolution_id]["XRP-USD"][:100]

    report = audit_resolution_candidates(inputs)

    assert report["status"] == AUDIT_STATUS_NO_SELECTION
    assert report["selected_resolution"] is None
    assert report["next_stage"] == "EXTEND_OR_RELOCK_SOURCE_DATA_BEFORE_STAGE_3"


def test_archive_runner_reads_timestamps_only_and_records_atomic_evidence(tmp_path, monkeypatch):
    project_root = Path(audit_module.__file__).resolve().parents[1]
    external = tmp_path / "external"
    external.mkdir()
    archive_path = _write_archive(external / "Kraken_OHLCVT.zip", _candidate_inputs())
    archive_bytes = archive_path.read_bytes()
    monkeypatch.setattr(
        audit_module,
        "FROZEN_COMPLETE_ARCHIVE_SPEC",
        {
            "filename": "Kraken_OHLCVT.zip",
            "bytes": len(archive_bytes),
            "sha256": hashlib.sha256(archive_bytes).hexdigest(),
        },
    )
    evidence_root = external / "evidence"

    recorded = KrakenAIDrivenV2DataSufficiencyAuditor().run(
        archive_path, evidence_root, AUTHORIZATION_PHRASE
    )

    assert recorded.selected_resolution_minutes == 240
    assert recorded.audit_status == AUDIT_STATUS_RESOLUTION_SELECTED
    final = evidence_root / EVIDENCE_DIRECTORY_NAME
    assert final.is_dir()
    assert not (evidence_root / STAGING_DIRECTORY_NAME).exists()
    locked = KrakenAIDrivenV2DataSufficiencyEvidenceLock().lock(final)
    payload = json.loads((final / REPORT_FILENAME).read_text(encoding="utf-8"))
    assert locked.report_sha256 == recorded.report_sha256
    assert payload["source_archive_opened"] is True
    assert payload["timestamp_columns_opened"] is True
    assert payload["ohlcvt_value_columns_opened"] is False
    assert payload["development_market_values_opened"] is False
    assert payload["calibration_data_opened"] is False
    assert payload["evaluation_data_opened"] is False
    assert payload["performance_fields_opened"] is False
    assert payload["selected_resolution"]["interval_minutes"] == 240
    assert Path(recorded.report_path).is_relative_to(external)
    assert not Path(recorded.report_path).is_relative_to(project_root)


def test_runner_requires_exact_phrase_external_paths_and_one_shot(tmp_path, monkeypatch):
    inputs = _candidate_inputs()
    external = tmp_path / "external"
    external.mkdir()
    archive_path = _write_archive(external / "Kraken_OHLCVT.zip", inputs)
    raw = archive_path.read_bytes()
    monkeypatch.setattr(
        audit_module,
        "FROZEN_COMPLETE_ARCHIVE_SPEC",
        {"filename": archive_path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
    )
    evidence_root = external / "evidence"
    runner = KrakenAIDrivenV2DataSufficiencyAuditor()

    with pytest.raises(PermissionError, match="authorization phrase"):
        runner.run(archive_path, evidence_root, "WRONG")
    runner.run(archive_path, evidence_root, AUTHORIZATION_PHRASE)
    with pytest.raises(FileExistsError, match="already exists"):
        runner.run(archive_path, evidence_root, AUTHORIZATION_PHRASE)


def test_evidence_lock_rejects_tampering_and_performance_fields(tmp_path):
    final = tmp_path / EVIDENCE_DIRECTORY_NAME
    final.mkdir()
    payload = {
        "schema_version": 1,
        "protocol_id": audit_module.PROTOCOL_ID,
        "audit_id": audit_module.AUDIT_ID,
        "status": AUDIT_STATUS_NO_SELECTION,
        "candidate_results": [],
        "selected_resolution": None,
        "source_archive_opened": True,
        "timestamp_columns_opened": True,
        "ohlcvt_value_columns_opened": False,
        "development_market_values_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "performance_fields_opened": False,
        "labels_generated": False,
        "model_training_executed": False,
        "candidate_v2_authorized": False,
        "live_execution_authorized": False,
    }
    raw = canonical_json_bytes(payload)
    digest = hashlib.sha256(raw).hexdigest()
    (final / REPORT_FILENAME).write_bytes(raw)
    (final / audit_module.REPORT_SHA256_FILENAME).write_text(
        f"{digest}  {REPORT_FILENAME}\n", encoding="ascii"
    )
    assert KrakenAIDrivenV2DataSufficiencyEvidenceLock().lock(final).report_sha256 == digest

    changed = copy.deepcopy(payload)
    changed["returns"] = [1.0]
    raw = canonical_json_bytes(changed)
    digest = hashlib.sha256(raw).hexdigest()
    (final / REPORT_FILENAME).write_bytes(raw)
    (final / audit_module.REPORT_SHA256_FILENAME).write_text(
        f"{digest}  {REPORT_FILENAME}\n", encoding="ascii"
    )
    with pytest.raises(RuntimeError, match="performance field"):
        KrakenAIDrivenV2DataSufficiencyEvidenceLock().lock(final)
