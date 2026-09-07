import copy
from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
import pickle
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_regime_gated_selective_development_result_review as review
import kraken_ai_driven_v2_regime_gated_selective_development_runner as runner
from kraken_ai_driven_v2_regime_gated_selective_hypothesis import (
    DIRECTION_ORDER,
    FOLD_PLAN,
    VARIANT_SPECS,
)
from kraken_ai_driven_v2_learning_core import ASSET_ORDER


CONTROL = "SPOT_REGIME_CALIBRATED_LOGISTIC_CONTROL"
CONTEXT = "SPOT_CONTEXT_REGIME_CALIBRATED_LOGISTIC"


def _timestamp(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _predictions():
    rows = []
    specs = (("FOLD_1", 134, 11, 0.30), ("FOLD_2", 157, 1, 0.32))
    for fold_id, count, positive_count, required in specs:
        fold = next(item for item in FOLD_PLAN if item["fold_id"] == fold_id)
        start = datetime.fromisoformat(
            fold["validation_start_utc"].replace("Z", "+00:00")
        )
        for number in range(count):
            decision = start + timedelta(hours=12 * number)
            entry = decision + timedelta(hours=12)
            positive = number < positive_count
            probability = 0.04 + number / 2000.0
            rows.append(
                {
                    "action": "HOLD_CASH",
                    "asset": ASSET_ORDER[number % len(ASSET_ORDER)],
                    "context_confirmed": number % 2 == 0,
                    "decision_timestamp": _timestamp(decision),
                    "direction": "SHORT",
                    "entry_timestamp": _timestamp(entry),
                    "event_end_timestamp": _timestamp(entry + timedelta(hours=12)),
                    "fold_id": fold_id,
                    "label": "TIMEOUT_NO_BARRIER" if positive else "STOP_1R_FIRST",
                    "outcome_net_r": 0.2 if positive else -1.0,
                    "positive_outcome": positive,
                    "positive_probability": probability,
                    "regime": "SHORT_REGIME",
                    "required_probability": required,
                    "variant_id": CONTROL,
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            row["variant_id"],
            row["fold_id"],
            row["decision_timestamp"],
            row["asset"],
            row["direction"],
        ),
    )


def _empty_summary():
    return {
        "count": 0,
        "direction_counts": {direction: 0 for direction in DIRECTION_ORDER},
        "cumulative_net_r": 0.0,
        "mean_net_r": None,
        "median_net_r": None,
        "positive_outcome_count": 0,
    }


def _supported_metrics(rows):
    actual = [1.0 if row["positive_outcome"] else 0.0 for row in rows]
    probabilities = [row["positive_probability"] for row in rows]
    prevalence = 0.2
    calibrated_brier = sum(
        (observed - probability) ** 2
        for observed, probability in zip(actual, probabilities, strict=True)
    ) / len(rows)
    prevalence_brier = sum(
        (observed - prevalence) ** 2 for observed in actual
    ) / len(rows)
    return {
        "supported": True,
        "outer_validation_rows": len(rows),
        "outer_training_positive_prevalence": prevalence,
        "required_positive_probability": rows[0]["required_probability"],
        "calibrated_brier_score": calibrated_brier,
        "prevalence_brier_score": prevalence_brier,
        "brier_skill_pass": calibrated_brier < prevalence_brier,
    }


def _unsupported():
    return {
        "supported": False,
        "support_failure": "synthetic frozen class support failure",
        "calibrated_brier_score": None,
        "prevalence_brier_score": None,
        "brier_skill_pass": False,
    }


def _report(predictions, prediction_sha256):
    rows_by_fold = {
        fold["fold_id"]: [
            row for row in predictions if row["fold_id"] == fold["fold_id"]
        ]
        for fold in FOLD_PLAN
    }
    reviews = []
    for variant_id in VARIANT_SPECS:
        folds = []
        for fold in FOLD_PLAN:
            fold_id = fold["fold_id"]
            direction_support = {}
            for direction in DIRECTION_ORDER:
                cell = f"{variant_id}|{fold_id}|{direction}"
                direction_support[direction] = (
                    _supported_metrics(rows_by_fold[fold_id])
                    if cell in review.EXPECTED_SUPPORTED_CELLS
                    else _unsupported()
                )
            folds.append(
                {
                    "fold_id": fold_id,
                    "direction_support": direction_support,
                    "raw_selected": _empty_summary(),
                    "nonoverlapping_selected": _empty_summary(),
                    "raw_support_pass": False,
                    "nonoverlap_support_pass": False,
                    "positive_net_r_pass": False,
                    "all_direction_brier_skill_pass": False,
                }
            )
        variant_rows = [
            row for row in predictions if row["variant_id"] == variant_id
        ]
        identities = [
            {column: row[column] for column in review.IDENTITY_COLUMNS}
            for row in variant_rows
        ]
        reviews.append(
            {
                "variant_id": variant_id,
                "folds": folds,
                "assets": [
                    {
                        "asset": asset,
                        "nonoverlapping_selected": _empty_summary(),
                        "positive_net_r_pass": False,
                    }
                    for asset in ASSET_ORDER
                ],
                "raw_selected_overall": _empty_summary(),
                "nonoverlapping_selected_overall": _empty_summary(),
                "absolute_gates": {
                    "all_fold_raw_support_pass": False,
                    "all_fold_nonoverlap_support_pass": False,
                    "all_fold_positive_net_r_pass": False,
                    "all_direction_fold_brier_skill_pass": False,
                    "asset_breadth_pass": False,
                    "overall_positive_net_r_pass": False,
                    "positive_asset_count": 0,
                },
                "absolute_gates_passed": False,
                "incremental_gates": None
                if variant_id == CONTROL
                else {
                    "higher_overall_mean_net_r_pass": False,
                    "higher_worst_fold_mean_net_r_pass": False,
                    "fold_mean_wins_pass": False,
                    "all_incremental_gates_passed": False,
                    "fold_mean_win_count": 0,
                },
                "development_viable": False,
                "prediction_row_identity_sha256": hashlib.sha256(
                    runner.canonical_json_bytes(identities)
                ).hexdigest(),
            }
        )
    artifacts = []
    for cell in review.EXPECTED_SUPPORTED_CELLS:
        for kind in ("BASE", "CALIBRATOR"):
            artifact_id = f"{cell}|{kind}"
            relative = f"{runner.MODEL_DIRECTORY_NAME}/{runner._artifact_filename(artifact_id)}"
            raw = artifact_id.encode("ascii")
            artifacts.append(
                {
                    "artifact_id": artifact_id,
                    "path": relative,
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
    return {
        "protocol_id": runner.PROTOCOL_ID,
        "run_id": runner.RUN_ID,
        "learning_status": runner.STATUS_HOLD,
        "terminal_failure_status": runner.STATUS_HOLD,
        "action": "HOLD_CASH",
        "partition": "DEVELOPMENT",
        "resolution": "12h",
        "common_start_utc": "2021-12-01T00:00:00Z",
        "common_end_exclusive_utc": "2024-04-01T00:00:00Z",
        "labeled_decision_count": review.EXPECTED_LABELED_DECISION_COUNT,
        "trained_base_model_count": review.EXPECTED_BASE_MODEL_COUNT,
        "trained_calibrator_count": review.EXPECTED_CALIBRATOR_COUNT,
        "trained_artifact_count": 4,
        "out_of_fold_prediction_count": len(predictions),
        "passing_development_hypotheses": [],
        "variant_order": list(VARIANT_SPECS),
        "direction_order": list(DIRECTION_ORDER),
        "source_archive": {
            "filename": "Kraken_OHLCVT.zip",
            "bytes": 7885068519,
            "sha256": review.EXPECTED_ARCHIVE_SHA256,
        },
        "context_dataset_manifest_sha256": review.EXPECTED_CONTEXT_MANIFEST_SHA256,
        "context_dataset_object_count": 2808,
        "context_dataset_recovery_attempt": 4,
        "label_diagnostics": {
            "regime_counts": {
                "LONG_REGIME": 933,
                "NEUTRAL": 1660,
                "SHORT_REGIME": 1200,
            },
            "context_confirmed_counts": {"LONG": 201, "SHORT": 237},
        },
        "variant_reviews": reviews,
        "model_artifacts": artifacts,
        "prediction_artifact": {
            "path": runner.PREDICTIONS_FILENAME,
            "checksum_path": runner.PREDICTIONS_SHA256_FILENAME,
            "bytes": len(runner.canonical_json_bytes(predictions)),
            "sha256": prediction_sha256,
        },
        "source_archive_opened": True,
        "context_dataset_opened": True,
        "development_data_opened": True,
        "labels_generated": True,
        "model_training_authorized": True,
        "model_training_executed": True,
        "feature_search_executed": False,
        "hyperparameter_sweep_executed": False,
        "threshold_sweep_executed": False,
        "automatic_model_selection": False,
        "automatic_successor_authorized": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
    }


def _synthetic(monkeypatch):
    predictions = _predictions()
    prediction_sha256 = hashlib.sha256(
        runner.canonical_json_bytes(predictions)
    ).hexdigest()
    monkeypatch.setattr(review, "EXPECTED_PREDICTION_SHA256", prediction_sha256)
    report = _report(predictions, prediction_sha256)
    analysis = review.analyze_terminal_result(report, predictions)
    monkeypatch.setattr(
        review, "EXPECTED_SUPPORTED_CELL_RESULTS", analysis["cell_diagnostics"]
    )
    return report, predictions


def _write_evidence(root, report, predictions):
    root.mkdir()
    (root / runner.MODEL_DIRECTORY_NAME).mkdir()
    for artifact in report["model_artifacts"]:
        raw = artifact["artifact_id"].encode("ascii")
        (root / artifact["path"]).write_bytes(raw)
    prediction_bytes = runner.canonical_json_bytes(predictions)
    prediction_digest = hashlib.sha256(prediction_bytes).hexdigest()
    (root / runner.PREDICTIONS_FILENAME).write_bytes(prediction_bytes)
    (root / runner.PREDICTIONS_SHA256_FILENAME).write_bytes(
        f"{prediction_digest}  {runner.PREDICTIONS_FILENAME}\n".encode("ascii")
    )
    report_bytes = runner.canonical_json_bytes(report)
    report_digest = hashlib.sha256(report_bytes).hexdigest()
    (root / runner.REPORT_FILENAME).write_bytes(report_bytes)
    (root / runner.REPORT_SHA256_FILENAME).write_bytes(
        f"{report_digest}  {runner.REPORT_FILENAME}\n".encode("ascii")
    )
    return report_digest


def test_declaration_is_inert_and_freezes_terminal_boundary():
    declaration = review.result_review_declaration()
    assert declaration["terminal_status"] == runner.STATUS_HOLD
    assert declaration["terminal_action"] == "HOLD_CASH"
    assert declaration["expected_supported_cells"] == list(
        review.EXPECTED_SUPPORTED_CELLS
    )
    for field in (
        "external_evidence_opened",
        "model_artifacts_unpickled",
        "labels_generated",
        "model_training_executed",
        "retry_authorized",
        "threshold_rescue_authorized",
        "automatic_successor_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        assert declaration[field] is False


def test_terminal_review_reconstructs_thresholds_brier_and_support(monkeypatch):
    report, predictions = _synthetic(monkeypatch)
    result = review.analyze_terminal_result(report, predictions)
    assert result["terminal_status_validated"] is True
    assert result["threshold_actions_reconstructed"] is True
    assert result["brier_scores_recomputed"] is True
    assert result["supported_direction_fold_count"] == 2
    assert result["unsupported_direction_fold_count"] == 10
    assert result["selected_prediction_count"] == 0
    assert result["terminal_kraken_12h_research_stop"] is True


def test_terminal_review_rejects_threshold_action_tamper(monkeypatch):
    report, predictions = _synthetic(monkeypatch)
    predictions[0]["action"] = "SHORT"
    with pytest.raises(RuntimeError, match="threshold-action mismatch"):
        review.analyze_terminal_result(report, predictions)


def test_terminal_review_rejects_brier_tamper(monkeypatch):
    report, predictions = _synthetic(monkeypatch)
    report["variant_reviews"][0]["folds"][0]["direction_support"]["SHORT"][
        "calibrated_brier_score"
    ] += 0.01
    with pytest.raises(RuntimeError, match="Brier gate mismatch"):
        review.analyze_terminal_result(report, predictions)


def test_terminal_review_rejects_supported_cell_expansion(monkeypatch):
    report, predictions = _synthetic(monkeypatch)
    report["variant_reviews"][1]["folds"][0]["direction_support"]["LONG"] = (
        copy.deepcopy(
            report["variant_reviews"][0]["folds"][0]["direction_support"]["SHORT"]
        )
    )
    with pytest.raises(RuntimeError, match="supported-cell registry mismatch"):
        review.analyze_terminal_result(report, predictions)


def test_external_review_hashes_without_unpickling_or_writing(
    tmp_path, monkeypatch
):
    report, predictions = _synthetic(monkeypatch)
    root = tmp_path / runner.FINAL_DIRECTORY_NAME
    report_digest = _write_evidence(root, report, predictions)
    monkeypatch.setattr(review, "EXPECTED_REPORT_SHA256", report_digest)
    monkeypatch.setattr(
        pickle, "loads", lambda *_: pytest.fail("model artifact was unpickled")
    )
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    result = review.read_regime_gated_selective_terminal_result(root)
    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert before == after
    assert result["status"] == review.STATUS
    assert result["evidence_unchanged"] is True
    assert result["model_artifacts_unpickled"] is False
    assert result["terminal_kraken_12h_research_stop"] is True
    assert result["retry_authorized"] is False
