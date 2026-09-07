import hashlib
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_regime_gated_selective_development_runner as runner
from kraken_ai_driven_v2_regime_gated_selective_development_runner import (
    AUTHORIZATION_PHRASE,
    FINAL_DIRECTORY_NAME,
    PARENT_COMMIT,
    PROTOCOL_ID,
    READER_PASS_STATUS,
    STATUS_HOLD,
    STATUS_PASS,
    _absolute_review,
    _apply_incremental_gates,
    _inner_direction_slices,
    _nonoverlapping,
    _validate_regime_table,
    canonical_json_bytes,
    read_regime_gated_selective_evidence,
    run_regime_gated_selective_experiment,
    runner_declaration,
)
from kraken_ai_driven_v2_regime_gated_selective_hypothesis import (
    CONTEXT_FEATURE_COLUMNS,
    DIRECTION_ORDER,
    FOLD_PLAN,
    MATCHED_CONTROL,
    REGIME_FEATURE_COLUMNS,
    SPOT_FEATURE_COLUMNS,
    VARIANT_SPECS,
)
from kraken_ai_driven_v2_learning_core import ASSET_ORDER, CLASS_ORDER


ROOT = Path(__file__).resolve().parents[1]


def _learning_table():
    dates = pd.date_range(
        "2021-12-05T00:00:00Z", "2024-03-20T00:00:00Z", freq="2D", tz="UTC"
    )
    rows = []
    for asset_number, asset in enumerate(ASSET_ORDER):
        for number, timestamp in enumerate(dates):
            direction = "LONG" if number % 2 == 0 else "SHORT"
            sign = 1.0 if direction == "LONG" else -1.0
            positive = (number // 2 + asset_number) % 2 == 0
            row = {
                "asset": asset,
                "decision_timestamp": timestamp,
                "entry_timestamp": timestamp + pd.Timedelta(hours=12),
                "long_event_end_timestamp": timestamp + pd.Timedelta(hours=18),
                "short_event_end_timestamp": timestamp + pd.Timedelta(hours=18),
                "long_label": CLASS_ORDER[number % 3],
                "short_label": CLASS_ORDER[(number + 1) % 3],
                "long_outcome_net_r": 1.0 if direction == "LONG" and positive else -1.0,
                "short_outcome_net_r": 1.0 if direction == "SHORT" and positive else -1.0,
            }
            for feature_number, feature in enumerate(
                (*SPOT_FEATURE_COLUMNS, *CONTEXT_FEATURE_COLUMNS)
            ):
                row[feature] = float(
                    np.sin(number / 7.0 + asset_number) + feature_number * 0.001
                )
            for feature in REGIME_FEATURE_COLUMNS:
                row[feature] = sign
            row["open_interest_log_change_6"] = 0.02
            row["basis_change_1"] = sign * 0.001
            row["funding_rate_zscore_60"] = sign * 0.25
            rows.append(row)
    return pd.DataFrame(rows)


def _selected_predictions(net_r):
    rows = []
    for fold in FOLD_PLAN:
        start = pd.Timestamp(fold["validation_start_utc"])
        for number in range(45):
            direction = "LONG" if number % 2 == 0 else "SHORT"
            rows.append(
                {
                    "fold_id": fold["fold_id"],
                    "variant_id": "fixture",
                    "asset": ASSET_ORDER[number % 3],
                    "decision_timestamp": start + pd.Timedelta(days=number),
                    "entry_timestamp": start + pd.Timedelta(days=number, hours=12),
                    "event_end_timestamp": start + pd.Timedelta(days=number, hours=18),
                    "direction": direction,
                    "label": "TARGET_3R_FIRST" if net_r > 0.0 else "STOP_1R_FIRST",
                    "action": direction,
                    "positive_probability": 0.8,
                    "required_probability": 0.6,
                    "outcome_net_r": float(net_r),
                }
            )
    return pd.DataFrame(rows)


def _fold_metadata(brier_pass=True):
    return {
        fold["fold_id"]: {
            "fold_id": fold["fold_id"],
            "direction_support": {
                direction: {
                    "supported": True,
                    "calibrated_brier_score": 0.20 if brier_pass else 0.30,
                    "prevalence_brier_score": 0.25,
                    "brier_skill_pass": brier_pass,
                }
                for direction in DIRECTION_ORDER
            },
        }
        for fold in FOLD_PLAN
    }


def test_declaration_freezes_two_by_two_by_three_base_and_calibrator_budget():
    declaration = runner_declaration()
    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["parent_commit"] == PARENT_COMMIT
    assert declaration["parent_commit"].startswith("87927ef")
    assert declaration["authorization_phrase"] == AUTHORIZATION_PHRASE
    assert declaration["authorization_phrase_active"] is False
    assert declaration["variant_order"] == list(VARIANT_SPECS)
    assert declaration["direction_order"] == list(DIRECTION_ORDER)
    assert declaration["matched_control"] == MATCHED_CONTROL
    assert declaration["maximum_base_model_fits"] == 12
    assert declaration["maximum_calibrator_fits"] == 12
    assert declaration["maximum_total_fits"] == 24


def test_declaration_keeps_real_run_and_every_later_boundary_closed():
    declaration = runner_declaration()
    for field in (
        "authorization_phrase_active",
        "network_download_authorized",
        "source_archive_opened",
        "context_dataset_opened",
        "development_data_opened",
        "labels_generated",
        "model_training_authorized",
        "model_training_executed",
        "feature_search_authorized",
        "hyperparameter_sweep_authorized",
        "threshold_sweep_authorized",
        "automatic_model_selection",
        "automatic_successor_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        assert declaration[field] is False


def test_table_validation_derives_strict_regime_and_context_confirmation():
    table = _validate_regime_table(_learning_table())
    assert set(table["regime"]) == {"LONG_REGIME", "SHORT_REGIME"}
    assert table["context_confirmed"].all()
    assert set(table["regime_direction"]) == {"LONG", "SHORT"}
    duplicate = pd.concat([table, table.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        _validate_regime_table(duplicate)


def test_nested_direction_slices_are_chronological_purged_and_class_supported():
    table = _validate_regime_table(_learning_table())
    for fold in FOLD_PLAN:
        for direction in DIRECTION_ORDER:
            inner_fit, inner_calibration, validation, boundary = _inner_direction_slices(
                table, fold, direction, require_context=True
            )
            assert inner_fit["decision_timestamp"].max() < boundary
            assert inner_fit["event_end_timestamp"].max() < boundary
            assert inner_calibration["decision_timestamp"].min() >= boundary
            assert validation["decision_timestamp"].min() >= pd.Timestamp(
                fold["validation_start_utc"]
            )
            assert set(inner_fit["positive_outcome"]) == {False, True}
            assert set(inner_calibration["positive_outcome"]) == {False, True}


def test_nonoverlap_is_per_asset_and_uses_selected_event_end():
    start = pd.Timestamp("2023-01-01T00:00:00Z")
    frame = pd.DataFrame(
        [
            {
                "asset": "BTC-USD",
                "decision_timestamp": start + pd.Timedelta(hours=offset),
                "event_end_timestamp": start + pd.Timedelta(hours=offset + 24),
            }
            for offset in (0, 12, 24, 36)
        ]
    )
    assert list(_nonoverlapping(frame)["decision_timestamp"]) == [
        start,
        start + pd.Timedelta(hours=24),
    ]


def test_absolute_gates_require_brier_skill_in_every_direction_fold():
    variant = "SPOT_REGIME_CALIBRATED_LOGISTIC_CONTROL"
    passing = _absolute_review(variant, _selected_predictions(1.0), _fold_metadata())
    failing = _absolute_review(
        variant, _selected_predictions(1.0), _fold_metadata(brier_pass=False)
    )
    assert passing["absolute_gates_passed"] is True
    assert passing["development_viable"] is True
    assert failing["absolute_gates"]["all_direction_fold_brier_skill_pass"] is False
    assert failing["development_viable"] is False


def test_context_incremental_gates_are_strict_and_terminal_failure_is_fixed():
    control_id = "SPOT_REGIME_CALIBRATED_LOGISTIC_CONTROL"
    context_id = "SPOT_CONTEXT_REGIME_CALIBRATED_LOGISTIC"
    control = _absolute_review(
        control_id, _selected_predictions(-0.5), _fold_metadata()
    )
    context = _absolute_review(context_id, _selected_predictions(1.0), _fold_metadata())
    _apply_incremental_gates([control, context])
    assert context["incremental_gates"]["higher_overall_mean_net_r_pass"] is True
    assert context["incremental_gates"]["higher_worst_fold_mean_net_r_pass"] is True
    assert context["incremental_gates"]["fold_mean_win_count"] == 3
    assert context["development_viable"] is True
    assert runner.TERMINAL_FAILURE_STATUS.endswith("STOP_KRAKEN_12H_RESEARCH")


def test_synthetic_experiment_fits_exactly_twelve_base_and_twelve_calibrators():
    result, predictions, artifacts = run_regime_gated_selective_experiment(
        _learning_table()
    )
    assert result["status"] in {STATUS_PASS, STATUS_HOLD}
    assert len(artifacts) == 24
    assert len(predictions) > 0
    assert predictions.groupby(["variant_id", "fold_id", "direction"]).size().size == 12
    assert set(predictions["action"]).issubset({"LONG", "SHORT", "HOLD_CASH"})
    assert result["automatic_model_selection"] is False
    assert result["candidate_v2_authorized"] is False


def test_missing_direction_class_support_fails_closed_without_exceeding_fit_budget():
    table = _learning_table()
    long_rows = table["return_14"] > 0.0
    table.loc[long_rows, "long_outcome_net_r"] = -1.0
    result, predictions, artifacts = run_regime_gated_selective_experiment(table)
    assert result["status"] == STATUS_HOLD
    assert result["passing_development_hypotheses"] == []
    assert len(artifacts) < 24
    assert all(
        not review["absolute_gates"]["all_direction_fold_brier_skill_pass"]
        for review in result["variant_reviews"]
    )
    assert set(predictions["action"]).issubset({"SHORT", "HOLD_CASH"})


def _write_locked_evidence(root):
    root.mkdir()
    model_directory = root / runner.MODEL_DIRECTORY_NAME
    model_directory.mkdir()
    artifacts = []
    for variant in VARIANT_SPECS:
        for fold in FOLD_PLAN:
            for direction in DIRECTION_ORDER:
                for kind in ("BASE", "CALIBRATOR"):
                    artifact_id = f"{variant}|{fold['fold_id']}|{direction}|{kind}"
                    raw = artifact_id.encode("ascii")
                    relative = f"{runner.MODEL_DIRECTORY_NAME}/{runner._artifact_filename(artifact_id)}"
                    (root / relative).write_bytes(raw)
                    artifacts.append(
                        {
                            "artifact_id": artifact_id,
                            "path": relative,
                            "bytes": len(raw),
                            "sha256": hashlib.sha256(raw).hexdigest(),
                        }
                    )
    prediction_bytes = canonical_json_bytes([])
    prediction_digest = hashlib.sha256(prediction_bytes).hexdigest()
    (root / runner.PREDICTIONS_FILENAME).write_bytes(prediction_bytes)
    (root / runner.PREDICTIONS_SHA256_FILENAME).write_bytes(
        f"{prediction_digest}  {runner.PREDICTIONS_FILENAME}\n".encode("ascii")
    )
    report = {
        "protocol_id": PROTOCOL_ID,
        "run_id": runner.RUN_ID,
        "learning_status": STATUS_HOLD,
        "action": "HOLD_CASH",
        "trained_base_model_count": 12,
        "trained_calibrator_count": 12,
        "trained_artifact_count": 24,
        "out_of_fold_prediction_count": 0,
        "model_artifacts": artifacts,
        "prediction_artifact": {
            "path": runner.PREDICTIONS_FILENAME,
            "checksum_path": runner.PREDICTIONS_SHA256_FILENAME,
            "bytes": len(prediction_bytes),
            "sha256": prediction_digest,
        },
    }
    report_bytes = canonical_json_bytes(report)
    digest = hashlib.sha256(report_bytes).hexdigest()
    (root / runner.REPORT_FILENAME).write_bytes(report_bytes)
    (root / runner.REPORT_SHA256_FILENAME).write_bytes(
        f"{digest}  {runner.REPORT_FILENAME}\n".encode("ascii")
    )
    return digest


def test_reader_hash_verifies_all_24_artifacts_without_unpickling(tmp_path):
    root = tmp_path / FINAL_DIRECTORY_NAME
    digest = _write_locked_evidence(root)
    result = read_regime_gated_selective_evidence(root)
    assert result["status"] == READER_PASS_STATUS
    assert result["report_sha256"] == digest
    assert result["trained_artifact_count"] == 24
    assert result["evaluation_data_opened"] is False
    first = next((root / runner.MODEL_DIRECTORY_NAME).iterdir())
    first.write_bytes(first.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="artifact mismatch"):
        read_regime_gated_selective_evidence(root)


def test_protocol_freezes_one_shot_authorization_and_terminal_stop():
    protocol = (
        ROOT
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_RUNNER_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(protocol.split())
    for marker in (
        "at most twelve base-model fits and twelve sigmoid-calibrator fits",
        "payoff break-even probability plus `0.05`",
        "There is no feature, learner, class-weight, parameter or threshold sweep",
        "separate exact authorization phrase",
        "STOP_KRAKEN_12H_RESEARCH",
        "Calibration, Evaluation, Candidate v2",
    ):
        assert marker in normalized


def test_runner_requires_exact_separate_authorization_before_any_path_access(tmp_path):
    with pytest.raises(PermissionError, match="Exact one-shot"):
        runner.KrakenAIDrivenV2RegimeGatedSelectiveDevelopmentRunner().run(
            tmp_path / "archive.zip",
            tmp_path / "context",
            tmp_path / "evidence",
            "WRONG",
        )
