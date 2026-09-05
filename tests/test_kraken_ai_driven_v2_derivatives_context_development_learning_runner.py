import hashlib
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_derivatives_context_development_learning_runner as runner
from kraken_ai_driven_v2_derivatives_context_development_learning_runner import (
    AUTHORIZATION_PHRASE,
    DATASET_MANIFEST_SHA256,
    FINAL_DIRECTORY_NAME,
    PARENT_COMMIT,
    PROTOCOL_ID,
    READER_PASS_STATUS,
    REPORT_FILENAME,
    REPORT_SHA256_FILENAME,
    STATUS_HOLD,
    STATUS_PASS,
    _absolute_review,
    _apply_incremental_gates,
    _nonoverlapping,
    canonical_json_bytes,
    read_context_learning_evidence,
    run_matched_context_experiment,
    runner_declaration,
)
from kraken_ai_driven_v2_derivatives_context_hypothesis import (
    ASSET_ORDER,
    CONTEXT_FEATURE_COLUMNS,
    FOLD_PLAN,
    MATCHED_CONTROL,
    SPOT_FEATURE_COLUMNS,
    VARIANT_SPECS,
)
from kraken_ai_driven_v2_learning_core import CLASS_ORDER


ROOT = Path(__file__).resolve().parents[1]


def _learning_table():
    dates = pd.date_range(
        "2021-12-05T00:00:00Z",
        "2024-03-20T00:00:00Z",
        freq="2D",
        tz="UTC",
    )
    outcomes = {CLASS_ORDER[0]: 3.0, CLASS_ORDER[1]: -1.0, CLASS_ORDER[2]: 0.0}
    rows = []
    for asset_number, asset in enumerate(ASSET_ORDER):
        for number, timestamp in enumerate(dates):
            label = CLASS_ORDER[number % 3]
            row = {
                "asset": asset,
                "decision_timestamp": timestamp,
                "entry_timestamp": timestamp + pd.Timedelta(hours=12),
                "event_end_timestamp": timestamp + pd.Timedelta(days=1),
                "label": label,
                "outcome_net_r": outcomes[label],
            }
            for feature_number, feature in enumerate(SPOT_FEATURE_COLUMNS):
                row[feature] = (
                    np.sin(number / 7.0 + asset_number)
                    + feature_number * 0.01
                )
            for feature_number, feature in enumerate(CONTEXT_FEATURE_COLUMNS):
                row[feature] = (
                    np.cos(number / 11.0 + asset_number)
                    + feature_number * 0.005
                )
            rows.append(row)
    return pd.DataFrame(rows)


def _comparison_predictions(context):
    rows = []
    for fold in FOLD_PLAN:
        start = pd.Timestamp(fold["validation_start_utc"])
        for number in range(72):
            target = number % 2 == 0
            timestamp = start + pd.Timedelta(days=number)
            rows.append(
                {
                    "fold_id": fold["fold_id"],
                    "asset": ASSET_ORDER[number % 3],
                    "decision_timestamp": timestamp,
                    "event_end_timestamp": timestamp + pd.Timedelta(hours=12),
                    "label": CLASS_ORDER[0] if target else CLASS_ORDER[1],
                    "outcome_net_r": 3.0 if target else -1.0,
                    "score": 1.0 if target == context else -1.0,
                    "eligible": target == context,
                }
            )
    return pd.DataFrame(rows)


def _fold_metadata(metric, value):
    return {
        fold["fold_id"]: {
            "fold_id": fold["fold_id"],
            "inner_boundary_utc": pd.Timestamp(fold["training_end_exclusive_utc"]),
            "inner_fit_rows": 300,
            "inner_calibration_rows": 100,
            "outer_validation_rows": 72,
            "inner_fit_class_counts": {label: 100 for label in CLASS_ORDER},
            "inner_calibration_class_counts": {label: 33 for label in CLASS_ORDER},
            "outer_validation_class_counts": {label: 24 for label in CLASS_ORDER},
            "validation_row_identity_sha256": "a" * 64,
            "predictive_metrics": {metric: value},
        }
        for fold in FOLD_PLAN
    }


def test_declaration_is_inert_and_freezes_exact_four_variant_run():
    declaration = runner_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["parent_commit"] == PARENT_COMMIT
    assert declaration["authorization_phrase"] == AUTHORIZATION_PHRASE
    assert declaration["authorization_phrase_active"] is False
    assert declaration["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert declaration["variant_order"] == list(VARIANT_SPECS)
    assert declaration["matched_control"] == MATCHED_CONTROL
    assert declaration["maximum_fold_model_fits"] == 12
    assert declaration["identical_context_complete_rows_implemented"] is True
    assert declaration["absolute_and_incremental_gates_implemented"] is True


def test_declaration_keeps_every_later_boundary_closed():
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
        "hyperparameter_sweep_authorized",
        "threshold_sweep_authorized",
        "automatic_model_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        assert declaration[field] is False


def test_matched_learning_table_rejects_missing_context_and_duplicate_rows():
    table = _learning_table()
    with pytest.raises(ValueError, match="schema mismatch"):
        runner._validate_matched_table(table.drop(columns=[CONTEXT_FEATURE_COLUMNS[0]]))
    duplicate = pd.concat([table, table.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        runner._validate_matched_table(duplicate)


def test_nested_split_uses_only_completed_prior_outcomes():
    table = _learning_table()
    for fold in FOLD_PLAN:
        inner_fit, inner_calibration, validation, boundary = runner._outer_and_inner_slices(
            table, fold
        )
        assert inner_fit["decision_timestamp"].max() < boundary
        assert inner_fit["event_end_timestamp"].max() < boundary
        assert inner_calibration["decision_timestamp"].min() >= boundary
        assert inner_calibration["event_end_timestamp"].max() < pd.Timestamp(
            fold["training_end_exclusive_utc"]
        )
        assert validation["decision_timestamp"].min() >= pd.Timestamp(
            fold["validation_start_utc"]
        )


def test_nonoverlap_allows_only_one_live_event_per_asset():
    start = pd.Timestamp("2023-01-01T00:00:00Z")
    rows = [
        {
            "asset": "BTC-USD",
            "decision_timestamp": start + pd.Timedelta(hours=offset),
            "event_end_timestamp": start + pd.Timedelta(hours=offset + 24),
            "label": CLASS_ORDER[0],
            "outcome_net_r": 3.0,
        }
        for offset in (0, 12, 24, 36)
    ]
    selected = _nonoverlapping(pd.DataFrame(rows))
    assert list(selected["decision_timestamp"]) == [
        start,
        start + pd.Timedelta(hours=24),
    ]


@pytest.mark.parametrize(
    "context_id,control_id,metric",
    [
        (
            "SPOT_CONTEXT_HIST_GBT_CLASSIFIER",
            "SPOT_ONLY_HIST_GBT_CLASSIFIER_CONTROL",
            "multiclass_log_loss",
        ),
        (
            "SPOT_CONTEXT_HIST_GBT_NET_R",
            "SPOT_ONLY_HIST_GBT_NET_R_CONTROL",
            "mean_absolute_error_net_r",
        ),
    ],
)
def test_incremental_gates_require_context_to_beat_matched_control(
    context_id, control_id, metric
):
    context = _absolute_review(
        context_id, _comparison_predictions(True), _fold_metadata(metric, 0.4)
    )
    control = _absolute_review(
        control_id, _comparison_predictions(False), _fold_metadata(metric, 0.8)
    )
    reviews = _apply_incremental_gates([control, context])
    observed = {review["variant_id"]: review for review in reviews}[context_id]

    assert observed["absolute_gates_passed"] is True
    assert observed["incremental_gates"]["higher_overall_mean_net_r_pass"] is True
    assert observed["incremental_gates"]["higher_worst_fold_mean_net_r_pass"] is True
    assert observed["incremental_gates"]["predictive_fold_win_count"] == 3
    assert observed["development_viable"] is True


def test_incremental_gate_rejects_predictive_tie():
    context = _absolute_review(
        "SPOT_CONTEXT_HIST_GBT_CLASSIFIER",
        _comparison_predictions(True),
        _fold_metadata("multiclass_log_loss", 0.8),
    )
    control = _absolute_review(
        "SPOT_ONLY_HIST_GBT_CLASSIFIER_CONTROL",
        _comparison_predictions(False),
        _fold_metadata("multiclass_log_loss", 0.8),
    )
    _apply_incremental_gates([control, context])
    assert context["incremental_gates"]["predictive_fold_win_count"] == 0
    assert context["development_viable"] is False


def test_real_nested_experiment_fits_exactly_twelve_matched_models():
    result, predictions, artifacts = run_matched_context_experiment(_learning_table())

    assert result["status"] in {STATUS_PASS, STATUS_HOLD}
    assert [review["variant_id"] for review in result["variant_reviews"]] == list(
        VARIANT_SPECS
    )
    assert len(artifacts) == 12
    assert len(predictions) > 0
    assert predictions.groupby(["variant_id", "fold_id"]).size().size == 12
    for context_id, control_id in MATCHED_CONTROL.items():
        reviews = {item["variant_id"]: item for item in result["variant_reviews"]}
        assert (
            reviews[context_id]["prediction_row_identity_sha256"]
            == reviews[control_id]["prediction_row_identity_sha256"]
        )
    assert result["automatic_model_selection"] is False
    assert result["candidate_v2_authorized"] is False


def _write_locked_evidence(root):
    root.mkdir()
    model_artifacts = []
    model_directory = root / runner.MODEL_DIRECTORY_NAME
    model_directory.mkdir()
    for variant_id in VARIANT_SPECS:
        for fold in FOLD_PLAN:
            artifact_id = f"{variant_id}|{fold['fold_id']}"
            raw = artifact_id.encode("ascii")
            path = f"{runner.MODEL_DIRECTORY_NAME}/{runner._artifact_filename(artifact_id)}"
            (root / path).write_bytes(raw)
            model_artifacts.append(
                {
                    "artifact_id": artifact_id,
                    "path": path,
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
    prediction_bytes = canonical_json_bytes([])
    (root / runner.PREDICTIONS_FILENAME).write_bytes(prediction_bytes)
    prediction_digest = hashlib.sha256(prediction_bytes).hexdigest()
    (root / runner.PREDICTIONS_SHA256_FILENAME).write_bytes(
        f"{prediction_digest}  {runner.PREDICTIONS_FILENAME}\n".encode("ascii")
    )
    report = {
        "protocol_id": PROTOCOL_ID,
        "run_id": runner.RUN_ID,
        "learning_status": STATUS_HOLD,
        "action": "HOLD_CASH",
        "trained_model_count": 12,
        "out_of_fold_prediction_count": 0,
        "model_artifacts": model_artifacts,
        "prediction_artifact": {
            "path": runner.PREDICTIONS_FILENAME,
            "checksum_path": runner.PREDICTIONS_SHA256_FILENAME,
            "bytes": len(prediction_bytes),
            "sha256": prediction_digest,
        },
    }
    report_bytes = canonical_json_bytes(report)
    (root / REPORT_FILENAME).write_bytes(report_bytes)
    report_digest = hashlib.sha256(report_bytes).hexdigest()
    (root / REPORT_SHA256_FILENAME).write_bytes(
        f"{report_digest}  {REPORT_FILENAME}\n".encode("ascii")
    )
    return report_digest


def test_independent_evidence_reader_verifies_every_artifact_without_unpickling(tmp_path):
    root = tmp_path / FINAL_DIRECTORY_NAME
    digest = _write_locked_evidence(root)
    result = read_context_learning_evidence(root)
    assert result["status"] == READER_PASS_STATUS
    assert result["report_sha256"] == digest
    assert result["trained_model_count"] == 12
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False
    assert (root / REPORT_SHA256_FILENAME).read_bytes().endswith(b"\n")
    assert not (root / REPORT_SHA256_FILENAME).read_bytes().endswith(b"\r\n")
    assert (root / runner.PREDICTIONS_SHA256_FILENAME).read_bytes().endswith(b"\n")
    assert not (root / runner.PREDICTIONS_SHA256_FILENAME).read_bytes().endswith(b"\r\n")


def test_independent_evidence_reader_rejects_model_tamper(tmp_path):
    root = tmp_path / FINAL_DIRECTORY_NAME
    _write_locked_evidence(root)
    first = next((root / runner.MODEL_DIRECTORY_NAME).iterdir())
    first.write_bytes(first.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="model artifact mismatch"):
        read_context_learning_evidence(root)


def test_protocol_freezes_stop_conditions_and_no_sweep():
    protocol = (
        ROOT
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    for marker in (
        "Exactly four variants execute",
        "identical ordered",
        "There is no hyperparameter, feature, learner or threshold sweep",
        "Controls are never eligible for promotion",
        "HOLD_CASH",
        "Calibration and Evaluation remain unopened",
    ):
        assert marker in protocol


def test_runner_requires_exact_separate_authorization(tmp_path):
    with pytest.raises(PermissionError, match="Exact one-shot"):
        runner.KrakenAIDrivenV2DerivativesContextDevelopmentLearningRunner().run(
            tmp_path / "archive.zip",
            tmp_path / "context",
            tmp_path / "evidence",
            "WRONG",
        )
