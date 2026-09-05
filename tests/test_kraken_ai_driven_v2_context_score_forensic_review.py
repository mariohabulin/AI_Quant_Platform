import hashlib
import json
import os
from pathlib import Path
import pickle
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_context_score_forensic_review as forensic
import kraken_ai_driven_v2_derivatives_context_development_learning_runner as runner
from kraken_ai_driven_v2_derivatives_context_hypothesis import (
    ASSET_ORDER,
    FOLD_PLAN,
    MATCHED_CONTROL,
    VARIANT_SPECS,
)
from kraken_ai_driven_v2_learning_core import CLASS_ORDER


def _predictions():
    rows = []
    for variant_number, variant_id in enumerate(VARIANT_SPECS):
        is_context = variant_id in MATCHED_CONTROL
        for fold_number, fold in enumerate(FOLD_PLAN):
            start = forensic.pd.Timestamp(fold["validation_start_utc"])
            for number in range(30):
                label = CLASS_ORDER[number % 3]
                outcome = {CLASS_ORDER[0]: 3.0, CLASS_ORDER[1]: -1.0, CLASS_ORDER[2]: 0.0}[label]
                if is_context:
                    score = outcome - 4.0 + number / 1000.0
                else:
                    score = -outcome - 2.0 + number / 1000.0
                decision = start + forensic.pd.Timedelta(days=number)
                rows.append(
                    {
                        "variant_id": variant_id,
                        "fold_id": fold["fold_id"],
                        "asset": ASSET_ORDER[number % len(ASSET_ORDER)],
                        "decision_timestamp": decision.isoformat().replace("+00:00", "Z"),
                        "event_end_timestamp": (decision + forensic.pd.Timedelta(days=number % 5 + 1)).isoformat().replace("+00:00", "Z"),
                        "label": label,
                        "outcome_net_r": outcome,
                        "score": score,
                        "eligible": score > 0.0,
                    }
                )
    return rows


def _report(prediction_count):
    return {
        "variant_reviews": [
            {
                "variant_id": variant_id,
                "objective": VARIANT_SPECS[variant_id]["objective"],
                "development_viable": False,
                "incremental_gates": (
                    {"predictive_fold_win_count": 3}
                    if variant_id in MATCHED_CONTROL
                    else None
                ),
            }
            for variant_id in VARIANT_SPECS
        ],
        "labeled_row_count": prediction_count // len(VARIANT_SPECS),
        "out_of_fold_prediction_count": prediction_count,
    }


def _write_evidence(root, predictions):
    root.mkdir()
    model_directory = root / runner.MODEL_DIRECTORY_NAME
    model_directory.mkdir()
    artifacts = []
    for variant_id in VARIANT_SPECS:
        for fold in FOLD_PLAN:
            artifact_id = f"{variant_id}|{fold['fold_id']}"
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
    prediction_bytes = runner.canonical_json_bytes(predictions)
    prediction_digest = hashlib.sha256(prediction_bytes).hexdigest()
    (root / runner.PREDICTIONS_FILENAME).write_bytes(prediction_bytes)
    (root / runner.PREDICTIONS_SHA256_FILENAME).write_bytes(
        f"{prediction_digest}  {runner.PREDICTIONS_FILENAME}\n".encode("ascii")
    )
    report = {
        **_report(len(predictions)),
        "protocol_id": runner.PROTOCOL_ID,
        "run_id": runner.RUN_ID,
        "learning_status": runner.STATUS_HOLD,
        "action": "HOLD_CASH",
        "trained_model_count": 12,
        "model_artifacts": artifacts,
        "prediction_artifact": {
            "path": runner.PREDICTIONS_FILENAME,
            "checksum_path": runner.PREDICTIONS_SHA256_FILENAME,
            "bytes": len(prediction_bytes),
            "sha256": prediction_digest,
        },
    }
    report_bytes = runner.canonical_json_bytes(report)
    report_digest = hashlib.sha256(report_bytes).hexdigest()
    (root / runner.REPORT_FILENAME).write_bytes(report_bytes)
    (root / runner.REPORT_SHA256_FILENAME).write_bytes(
        f"{report_digest}  {runner.REPORT_FILENAME}\n".encode("ascii")
    )
    return report_digest, report


def test_declaration_is_inert_and_freezes_diagnostics():
    declaration = forensic.forensic_declaration()
    assert declaration["fixed_decile_count"] == 10
    assert declaration["variant_order"] == list(VARIANT_SPECS)
    assert declaration["matched_control"] == MATCHED_CONTROL
    assert declaration["read_only_forensics_implemented"] is True
    assert declaration["cost_decomposition_available"] is False
    for field in (
        "external_evidence_opened",
        "model_artifacts_unpickled",
        "labels_generated",
        "model_training_executed",
        "threshold_sweep_authorized",
        "automatic_experiment_2_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "real_orders_submitted",
    ):
        assert declaration[field] is False


def test_forensics_measure_rank_deciles_folds_assets_and_durations():
    predictions = _predictions()
    result = forensic.analyze_context_scores(_report(len(predictions)), predictions)
    assert len(result["variant_forensics"]) == 4
    assert len(result["matched_pair_forensics"]) == 2
    assert result["automatic_experiment_2_selection"] is False
    assert result["cost_decomposition_available"] is False
    context = next(
        item
        for item in result["variant_forensics"]
        if item["variant_id"] == "SPOT_CONTEXT_HIST_GBT_CLASSIFIER"
    )
    assert context["score_statistics"]["maximum"] < 0.0
    assert context["score_statistics"]["positive_count"] == 0
    assert context["score_outcome_relationship"]["overall"]["score_outcome_spearman"] > 0.8
    assert len(context["score_decile_forensics"]["deciles"]) == 10
    assert context["score_decile_forensics"]["top_decile"]["positive_nonoverlapping_mean_in_every_fold"] is True
    assert len(context["class_support_by_fold"]) == 3
    assert len(context["event_duration"]["by_label"]) == 3


def test_forensics_rejects_eligibility_redefinition():
    predictions = _predictions()
    predictions[0]["eligible"] = not predictions[0]["eligible"]
    with pytest.raises(RuntimeError, match="eligibility rule"):
        forensic.analyze_context_scores(_report(len(predictions)), predictions)


def test_forensics_rejects_matched_row_drift():
    predictions = _predictions()
    target = next(
        row
        for row in predictions
        if row["variant_id"] == "SPOT_CONTEXT_HIST_GBT_CLASSIFIER"
    )
    target["outcome_net_r"] += 0.1
    with pytest.raises(RuntimeError, match="matched row mismatch"):
        forensic.analyze_context_scores(_report(len(predictions)), predictions)


def test_external_read_verifies_all_bytes_without_unpickling_or_writing(tmp_path, monkeypatch):
    root = tmp_path / runner.FINAL_DIRECTORY_NAME
    predictions = _predictions()
    digest, report = _write_evidence(root, predictions)
    monkeypatch.setattr(forensic, "EXPECTED_REPORT_SHA256", digest)
    monkeypatch.setattr(forensic, "EXPECTED_PREDICTION_COUNT", len(predictions))
    monkeypatch.setattr(forensic, "EXPECTED_LABELED_ROW_COUNT", report["labeled_row_count"])
    monkeypatch.setattr(pickle, "loads", lambda *_: pytest.fail("model was unpickled"))
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    result = forensic.read_context_score_forensics(root)
    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert result["status"] == forensic.STATUS
    assert result["model_artifacts_unpickled"] is False
    assert result["model_training_executed"] is False
    assert result["evidence_modified"] is False
    assert before == after


def test_external_read_rejects_prediction_tamper(tmp_path, monkeypatch):
    root = tmp_path / runner.FINAL_DIRECTORY_NAME
    predictions = _predictions()
    digest, report = _write_evidence(root, predictions)
    monkeypatch.setattr(forensic, "EXPECTED_REPORT_SHA256", digest)
    monkeypatch.setattr(forensic, "EXPECTED_PREDICTION_COUNT", len(predictions))
    monkeypatch.setattr(forensic, "EXPECTED_LABELED_ROW_COUNT", report["labeled_row_count"])
    path = root / runner.PREDICTIONS_FILENAME
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="prediction artifact mismatch"):
        forensic.read_context_score_forensics(root)


def test_protocol_prohibits_retrospective_search_and_automatic_choice():
    root = Path(__file__).resolve().parents[1]
    text = (
        root / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_CONTEXT_SCORE_FORENSIC_REVIEW_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    for marker in (
        "not a threshold search",
        "It does not simulate",
        "automatically",
        "Calibration, Evaluation",
        "cannot be decomposed",
    ):
        assert marker in text
