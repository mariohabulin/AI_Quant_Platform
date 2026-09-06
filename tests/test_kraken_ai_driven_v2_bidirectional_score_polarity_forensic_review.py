import hashlib
import os
from pathlib import Path
import pickle
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_bidirectional_development_learning_runner as runner
import kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review as forensic
from kraken_ai_driven_v2_bidirectional_hypothesis import (
    DIRECTION_ORDER,
    FOLD_PLAN,
    MATCHED_CONTROL,
    VARIANT_SPECS,
    select_bidirectional_action,
)
from kraken_ai_driven_v2_learning_core import ASSET_ORDER, CLASS_ORDER


def _outcome(label, direction):
    values = {
        "TARGET_3R_FIRST": 2.8 if direction == "LONG" else 2.7,
        "STOP_1R_FIRST": -1.1 if direction == "LONG" else -1.2,
        "TIMEOUT_NO_BARRIER": 0.15 if direction == "LONG" else -0.05,
    }
    return values[label]


def _predictions():
    rows = []
    for variant_number, variant_id in enumerate(VARIANT_SPECS):
        for fold_number, fold in enumerate(FOLD_PLAN):
            start = forensic.pd.Timestamp(fold["validation_start_utc"])
            for number in range(30):
                long_label = CLASS_ORDER[number % len(CLASS_ORDER)]
                short_label = CLASS_ORDER[(number + 1) % len(CLASS_ORDER)]
                long_outcome = _outcome(long_label, "LONG")
                short_outcome = _outcome(short_label, "SHORT")
                slope = 0.8 if variant_number else 0.5
                offset = number / 1000.0 + fold_number / 10000.0
                long_score = long_outcome * slope + offset
                short_score = short_outcome * slope - offset - 0.01
                action = select_bidirectional_action(long_score, short_score)
                selected = {
                    "LONG": long_outcome,
                    "SHORT": short_outcome,
                    "HOLD_CASH": 0.0,
                }[action]
                decision = start + forensic.pd.Timedelta(hours=12 * number)
                entry = decision + forensic.pd.Timedelta(hours=12)
                rows.append(
                    {
                        "variant_id": variant_id,
                        "fold_id": fold["fold_id"],
                        "asset": ASSET_ORDER[number % len(ASSET_ORDER)],
                        "decision_timestamp": decision.isoformat().replace("+00:00", "Z"),
                        "entry_timestamp": entry.isoformat().replace("+00:00", "Z"),
                        "long_event_end_timestamp": (
                            entry + forensic.pd.Timedelta(hours=12 * (number % 4 + 1))
                        ).isoformat().replace("+00:00", "Z"),
                        "short_event_end_timestamp": (
                            entry + forensic.pd.Timedelta(hours=12 * (number % 5 + 1))
                        ).isoformat().replace("+00:00", "Z"),
                        "long_label": long_label,
                        "short_label": short_label,
                        "long_outcome_net_r": long_outcome,
                        "short_outcome_net_r": short_outcome,
                        "long_predicted_net_r": long_score,
                        "short_predicted_net_r": short_score,
                        "action": action,
                        "selected_outcome_net_r": selected,
                    }
                )
    return rows


def _report(predictions):
    labeled = len(predictions) // len(VARIANT_SPECS)
    return {
        "variant_reviews": [
            {
                "variant_id": variant_id,
                "feature_set": VARIANT_SPECS[variant_id]["feature_set"],
                "development_viable": False,
            }
            for variant_id in VARIANT_SPECS
        ],
        "labeled_decision_count": labeled,
        "directional_label_count": labeled * len(DIRECTION_ORDER),
        "out_of_fold_prediction_count": len(predictions),
    }


def _write_evidence(root, predictions):
    root.mkdir()
    model_directory = root / runner.MODEL_DIRECTORY_NAME
    model_directory.mkdir()
    artifacts = []
    for variant_id in VARIANT_SPECS:
        for fold in FOLD_PLAN:
            for direction in DIRECTION_ORDER:
                artifact_id = f"{variant_id}|{fold['fold_id']}|{direction}"
                raw = artifact_id.encode("ascii")
                relative = (
                    f"{runner.MODEL_DIRECTORY_NAME}/"
                    f"{runner._artifact_filename(artifact_id)}"
                )
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
        **_report(predictions),
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


def test_declaration_is_inert_and_freezes_bidirectional_diagnostics():
    declaration = forensic.forensic_declaration()
    assert declaration["fixed_decile_count"] == 10
    assert declaration["variant_order"] == list(VARIANT_SPECS)
    assert declaration["direction_order"] == list(DIRECTION_ORDER)
    assert declaration["matched_control"] == MATCHED_CONTROL
    for field in (
        "action_reconstruction_implemented",
        "matched_row_validation_implemented",
        "label_polarity_validation_implemented",
        "direction_calibration_diagnostics_implemented",
        "fixed_score_deciles_implemented",
        "selected_policy_economics_implemented",
        "read_only_forensics_implemented",
    ):
        assert declaration[field] is True
    for field in (
        "external_evidence_opened",
        "model_artifacts_unpickled",
        "labels_generated",
        "model_training_executed",
        "retrospective_threshold_search_authorized",
        "polarity_flip_authorized",
        "automatic_next_experiment_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "real_orders_submitted",
    ):
        assert declaration[field] is False


def test_forensics_reconstruct_actions_and_measure_both_directions():
    predictions = _predictions()
    result = forensic.analyze_bidirectional_scores(_report(predictions), predictions)
    assert result["action_rule_reconstructed"] is True
    assert result["label_polarity_validated"] is True
    assert result["automatic_next_experiment_selection"] is False
    assert len(result["variant_forensics"]) == 2
    assert len(result["matched_pair_forensics"]) == 1
    context = next(
        item
        for item in result["variant_forensics"]
        if item["variant_id"] in MATCHED_CONTROL
    )
    assert len(context["direction_forensics"]) == 2
    for direction in context["direction_forensics"]:
        assert direction["overall"]["spearman"] > 0.8
        assert len(direction["score_decile_forensics"]["deciles"]) == 10
        assert len(direction["score_decile_forensics"]["top_decile_by_fold"]) == 3
        assert len(direction["label_support"]) == 3
    actions = context["frozen_action_forensics"]
    assert sum(actions["action_counts"].values()) == 90
    assert actions["raw_selected"]["count"] > 0


def test_forensics_rejects_action_rule_drift():
    predictions = _predictions()
    predictions[0]["action"] = "SHORT"
    predictions[0]["selected_outcome_net_r"] = predictions[0]["short_outcome_net_r"]
    with pytest.raises(RuntimeError, match="action-rule mismatch"):
        forensic.analyze_bidirectional_scores(_report(predictions), predictions)


def test_forensics_rejects_target_label_polarity_drift():
    predictions = _predictions()
    row = next(row for row in predictions if row["long_label"] == "TARGET_3R_FIRST")
    row["long_outcome_net_r"] = -0.1
    with pytest.raises(RuntimeError, match="LONG target-label polarity mismatch"):
        forensic.analyze_bidirectional_scores(_report(predictions), predictions)


def test_forensics_rejects_matched_outcome_row_drift():
    predictions = _predictions()
    row = next(
        row
        for row in predictions
        if row["variant_id"] in MATCHED_CONTROL
        and row["long_label"] == "TIMEOUT_NO_BARRIER"
        and row["action"] != "LONG"
    )
    row["long_outcome_net_r"] += 0.01
    with pytest.raises(RuntimeError, match="matched-row mismatch"):
        forensic.analyze_bidirectional_scores(_report(predictions), predictions)


def test_external_read_hashes_models_without_unpickling_or_writing(tmp_path, monkeypatch):
    root = tmp_path / runner.FINAL_DIRECTORY_NAME
    predictions = _predictions()
    digest, report = _write_evidence(root, predictions)
    monkeypatch.setattr(forensic, "EXPECTED_REPORT_SHA256", digest)
    monkeypatch.setattr(
        forensic, "EXPECTED_LABELED_DECISION_COUNT", report["labeled_decision_count"]
    )
    monkeypatch.setattr(
        forensic, "EXPECTED_DIRECTIONAL_LABEL_COUNT", report["directional_label_count"]
    )
    monkeypatch.setattr(forensic, "EXPECTED_PREDICTION_COUNT", len(predictions))
    monkeypatch.setattr(pickle, "loads", lambda *_: pytest.fail("model was unpickled"))
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    result = forensic.read_bidirectional_score_polarity_forensics(root)
    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert result["status"] == forensic.STATUS
    assert result["development_evidence_opened"] is True
    assert result["model_artifacts_unpickled"] is False
    assert result["model_training_executed"] is False
    assert result["evidence_modified"] is False
    assert before == after


def test_external_read_rejects_prediction_tamper(tmp_path, monkeypatch):
    root = tmp_path / runner.FINAL_DIRECTORY_NAME
    predictions = _predictions()
    digest, report = _write_evidence(root, predictions)
    monkeypatch.setattr(forensic, "EXPECTED_REPORT_SHA256", digest)
    monkeypatch.setattr(
        forensic, "EXPECTED_LABELED_DECISION_COUNT", report["labeled_decision_count"]
    )
    monkeypatch.setattr(
        forensic, "EXPECTED_DIRECTIONAL_LABEL_COUNT", report["directional_label_count"]
    )
    monkeypatch.setattr(forensic, "EXPECTED_PREDICTION_COUNT", len(predictions))
    path = root / runner.PREDICTIONS_FILENAME
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="prediction artifact mismatch"):
        forensic.read_bidirectional_score_polarity_forensics(root)


def test_protocol_prohibits_retrospective_search_and_automatic_choice():
    root = Path(__file__).resolve().parents[1]
    text = (
        root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    for marker in (
        "not a threshold, top-k, polarity-flip or model search",
        "does not make that decision automatically",
        "without unpickling",
        "cost decomposition is unavailable",
        "Calibration and Evaluation remain unopened",
    ):
        assert marker in normalized
