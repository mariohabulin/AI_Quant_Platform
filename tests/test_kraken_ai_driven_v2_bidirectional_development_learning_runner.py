import hashlib
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_bidirectional_development_learning_runner as runner
from kraken_ai_driven_v2_bidirectional_development_learning_runner import (
    AUTHORIZATION_PHRASE,
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
    _combine_direction_predictions,
    _nonoverlapping,
    canonical_json_bytes,
    read_bidirectional_learning_evidence,
    run_bidirectional_experiment,
    runner_declaration,
)
from kraken_ai_driven_v2_bidirectional_hypothesis import (
    ALL_NUMERIC_FEATURE_COLUMNS,
    ASSET_ORDER,
    CONTEXT_FEATURE_COLUMNS,
    DIRECTION_ORDER,
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
    rows = []
    for asset_number, asset in enumerate(ASSET_ORDER):
        for number, timestamp in enumerate(dates):
            wave = np.sin(number / 9.0 + asset_number)
            row = {
                "asset": asset,
                "decision_timestamp": timestamp,
                "entry_timestamp": timestamp + pd.Timedelta(hours=12),
                "long_event_end_timestamp": timestamp + pd.Timedelta(days=1),
                "short_event_end_timestamp": timestamp + pd.Timedelta(days=1),
                "long_label": CLASS_ORDER[number % 3],
                "short_label": CLASS_ORDER[(number + 1) % 3],
                "long_outcome_net_r": float(wave),
                "short_outcome_net_r": float(-wave - 0.05),
            }
            for feature_number, feature in enumerate(ALL_NUMERIC_FEATURE_COLUMNS):
                row[feature] = float(
                    wave + np.cos(number / 13.0) + feature_number * 0.002
                )
            rows.append(row)
    return pd.DataFrame(rows)


def _market_frames_and_sources(periods=500):
    index = pd.date_range(
        "2021-12-01T00:00:00Z", periods=periods, freq="12h", tz="UTC"
    )
    frames = {}
    sources = {}
    for asset_number, asset in enumerate(ASSET_ORDER):
        x = np.arange(periods, dtype=float)
        close = 100.0 + x * 0.02 + 3.0 * np.sin(x / 11.0 + asset_number)
        open_ = close * (1.0 + 0.001 * np.cos(x / 7.0))
        frames[asset] = pd.DataFrame(
            {
                "Open": open_,
                "High": np.maximum(open_, close) + 1.0,
                "Low": np.minimum(open_, close) - 1.0,
                "Close": close,
                "Volume": 1000.0 + x + asset_number * 10.0,
            },
            index=index,
        )
        funding_index = pd.date_range(
            index[0], index[-1] + pd.Timedelta(hours=12), freq="8h", tz="UTC"
        )
        open_interest_index = pd.date_range(
            index[0], index[-1] + pd.Timedelta(hours=12), freq="30min", tz="UTC"
        )
        basis = 0.001 + np.sin(x / 17.0) * 0.0002
        index_close = 100.0 + x * 0.01 + asset_number
        sources[asset] = {
            "funding": pd.DataFrame(
                {
                    "funding_rate": 0.0001
                    + np.sin(np.arange(len(funding_index)) / 13.0) * 0.00001
                },
                index=funding_index,
            ),
            "open_interest": pd.DataFrame(
                {
                    "open_interest": 10000.0
                    + asset_number * 100.0
                    + np.arange(len(open_interest_index), dtype=float) * 0.2
                },
                index=open_interest_index,
            ),
            "mark_index_12h": pd.DataFrame(
                {
                    "mark_close": index_close * (1.0 + basis),
                    "index_close": index_close,
                },
                index=index,
            ),
        }
    return frames, sources


def _comparison_predictions(good):
    rows = []
    for fold in FOLD_PLAN:
        start = pd.Timestamp(fold["validation_start_utc"])
        for number in range(45):
            timestamp = start + pd.Timedelta(days=number)
            long_score, short_score = ((0.7, -0.2) if good else (-0.2, 0.7))
            rows.append(
                {
                    "fold_id": fold["fold_id"],
                    "variant_id": "fixture",
                    "asset": ASSET_ORDER[number % 3],
                    "decision_timestamp": timestamp,
                    "entry_timestamp": timestamp + pd.Timedelta(hours=12),
                    "long_event_end_timestamp": timestamp + pd.Timedelta(hours=18),
                    "short_event_end_timestamp": timestamp + pd.Timedelta(hours=18),
                    "long_label": CLASS_ORDER[0],
                    "short_label": CLASS_ORDER[1],
                    "long_outcome_net_r": 1.0,
                    "short_outcome_net_r": -1.0,
                    "long_predicted_net_r": long_score,
                    "short_predicted_net_r": short_score,
                    "action": "LONG" if good else "SHORT",
                    "selected_outcome_net_r": 1.0 if good else -1.0,
                }
            )
    return pd.DataFrame(rows)


def _fold_metadata():
    return {
        fold["fold_id"]: {
            "fold_id": fold["fold_id"],
            "training_rows": 300,
            "validation_rows": 45,
            "training_latest_event_end_utc": pd.Timestamp(
                fold["training_end_exclusive_utc"]
            )
            - pd.Timedelta(days=1),
            "validation_latest_event_end_utc": pd.Timestamp(
                fold["validation_end_exclusive_utc"]
            )
            - pd.Timedelta(days=1),
            "validation_row_identity_sha256": "a" * 64,
            "direction_predictive_metrics": {
                direction: {"mean_absolute_error_net_r": 0.5}
                for direction in DIRECTION_ORDER
            },
        }
        for fold in FOLD_PLAN
    }


def test_declaration_freezes_exact_two_by_two_by_three_run():
    declaration = runner_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["parent_commit"] == PARENT_COMMIT
    assert declaration["parent_commit"].startswith("82ea7f1")
    assert declaration["authorization_phrase"] == AUTHORIZATION_PHRASE
    assert declaration["authorization_phrase_active"] is False
    assert declaration["variant_order"] == list(VARIANT_SPECS)
    assert declaration["direction_order"] == list(DIRECTION_ORDER)
    assert declaration["matched_control"] == MATCHED_CONTROL
    assert declaration["maximum_fold_model_fits"] == 12
    assert declaration["maximum_numeric_feature_count"] == 25


def test_declaration_keeps_all_later_boundaries_closed():
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
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        assert declaration[field] is False


def test_table_validation_rejects_missing_schema_and_duplicate_decisions():
    table = _learning_table()
    with pytest.raises(ValueError, match="schema mismatch"):
        runner._validate_bidirectional_table(
            table.drop(columns=[CONTEXT_FEATURE_COLUMNS[0]])
        )
    duplicate = pd.concat([table, table.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        runner._validate_bidirectional_table(duplicate)


def test_table_validation_rejects_noncausal_directional_outcome():
    table = _learning_table()
    table.loc[0, "short_event_end_timestamp"] = table.loc[0, "decision_timestamp"]
    with pytest.raises(ValueError, match="SHORT outcomes are not causal"):
        runner._validate_bidirectional_table(table)


def test_table_builder_integrates_real_causal_features_and_paired_labels():
    frames, sources = _market_frames_and_sources()
    table, diagnostics = runner.build_bidirectional_context_learning_table(
        frames, sources
    )

    assert len(table) > 0
    assert table["entry_timestamp"].gt(table["decision_timestamp"]).all()
    assert tuple(table.loc[:, CONTEXT_FEATURE_COLUMNS].columns) == tuple(
        CONTEXT_FEATURE_COLUMNS
    )
    assert all(
        diagnostics[asset]["context_complete_decisions"] > 0
        for asset in ASSET_ORDER
    )


def test_fold_slices_purge_until_both_directional_outcomes_are_complete():
    table = runner._validate_bidirectional_table(_learning_table())
    for fold in FOLD_PLAN:
        training, validation = runner._fold_slices(table, fold)
        assert training["latest_event_end_timestamp"].max() < pd.Timestamp(
            fold["training_end_exclusive_utc"]
        )
        assert validation["decision_timestamp"].min() >= pd.Timestamp(
            fold["validation_start_utc"]
        )
        assert validation["latest_event_end_timestamp"].max() < pd.Timestamp(
            fold["validation_end_exclusive_utc"]
        )


def test_combined_predictions_apply_positive_maximum_and_cash_tie():
    validation = runner._validate_bidirectional_table(_learning_table().iloc[:4])
    observed = _combine_direction_predictions(
        validation,
        np.array([0.2, -0.1, 0.3, 0.2]),
        np.array([-0.1, 0.2, 0.3, 0.4]),
    )
    assert list(observed["action"]) == ["LONG", "SHORT", "HOLD_CASH", "SHORT"]
    assert observed.iloc[2]["selected_outcome_net_r"] == 0.0


def test_nonoverlap_uses_the_selected_direction_event_end():
    start = pd.Timestamp("2023-01-01T00:00:00Z")
    rows = []
    for offset in (0, 12, 24, 36):
        rows.append(
            {
                "asset": "BTC-USD",
                "decision_timestamp": start + pd.Timedelta(hours=offset),
                "event_end_timestamp": start + pd.Timedelta(hours=offset + 24),
                "outcome_net_r": 1.0,
                "action": "LONG",
            }
        )
    observed = _nonoverlapping(pd.DataFrame(rows))
    assert list(observed["decision_timestamp"]) == [
        start,
        start + pd.Timedelta(hours=24),
    ]


def test_absolute_gates_allow_positive_spot_control_evidence():
    control_id = "SPOT_ONLY_BIDIRECTIONAL_HIST_GBT_NET_R_CONTROL"
    review = _absolute_review(
        control_id, _comparison_predictions(True), _fold_metadata()
    )
    assert review["absolute_gates_passed"] is True
    assert review["development_viable"] is True
    assert review["incremental_gates"] is None


def test_context_incremental_gates_require_three_fixed_economic_comparisons():
    control_id = "SPOT_ONLY_BIDIRECTIONAL_HIST_GBT_NET_R_CONTROL"
    context_id = "SPOT_CONTEXT_BIDIRECTIONAL_HIST_GBT_NET_R"
    control = _absolute_review(
        control_id, _comparison_predictions(False), _fold_metadata()
    )
    context = _absolute_review(
        context_id, _comparison_predictions(True), _fold_metadata()
    )
    _apply_incremental_gates([control, context])

    incremental = context["incremental_gates"]
    assert incremental["higher_overall_mean_net_r_pass"] is True
    assert incremental["higher_worst_fold_mean_net_r_pass"] is True
    assert incremental["fold_mean_win_count"] == 3
    assert incremental["fold_mean_wins_pass"] is True
    assert context["development_viable"] is True


def test_context_incremental_tie_fails_closed():
    control_id = "SPOT_ONLY_BIDIRECTIONAL_HIST_GBT_NET_R_CONTROL"
    context_id = "SPOT_CONTEXT_BIDIRECTIONAL_HIST_GBT_NET_R"
    shared = _comparison_predictions(True)
    control = _absolute_review(control_id, shared.copy(), _fold_metadata())
    context = _absolute_review(context_id, shared.copy(), _fold_metadata())
    _apply_incremental_gates([control, context])
    assert context["incremental_gates"]["fold_mean_win_count"] == 0
    assert context["development_viable"] is False


def test_real_experiment_fits_twelve_directional_models_on_matched_rows():
    result, predictions, artifacts = run_bidirectional_experiment(_learning_table())

    assert result["status"] in {STATUS_PASS, STATUS_HOLD}
    assert len(artifacts) == 12
    assert len(predictions) > 0
    assert predictions.groupby(["variant_id", "fold_id"]).size().size == 6
    assert set(predictions["action"]).issubset({"LONG", "SHORT", "HOLD_CASH"})
    reviews = {item["variant_id"]: item for item in result["variant_reviews"]}
    context_id, control_id = next(iter(MATCHED_CONTROL.items()))
    assert (
        reviews[context_id]["prediction_row_identity_sha256"]
        == reviews[control_id]["prediction_row_identity_sha256"]
    )
    assert result["automatic_model_selection"] is False
    assert result["candidate_v2_authorized"] is False


def _write_locked_evidence(root):
    root.mkdir()
    model_directory = root / runner.MODEL_DIRECTORY_NAME
    model_directory.mkdir()
    model_artifacts = []
    for variant_id in VARIANT_SPECS:
        for fold in FOLD_PLAN:
            for direction in DIRECTION_ORDER:
                artifact_id = f"{variant_id}|{fold['fold_id']}|{direction}"
                raw = artifact_id.encode("ascii")
                path = (
                    f"{runner.MODEL_DIRECTORY_NAME}/"
                    f"{runner._artifact_filename(artifact_id)}"
                )
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
    digest = hashlib.sha256(report_bytes).hexdigest()
    (root / REPORT_FILENAME).write_bytes(report_bytes)
    (root / REPORT_SHA256_FILENAME).write_bytes(
        f"{digest}  {REPORT_FILENAME}\n".encode("ascii")
    )
    return digest


def test_independent_reader_verifies_all_artifacts_without_unpickling(tmp_path):
    root = tmp_path / FINAL_DIRECTORY_NAME
    digest = _write_locked_evidence(root)
    result = read_bidirectional_learning_evidence(root)

    assert result["status"] == READER_PASS_STATUS
    assert result["report_sha256"] == digest
    assert result["trained_model_count"] == 12
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False
    assert not (root / REPORT_SHA256_FILENAME).read_bytes().endswith(b"\r\n")


def test_independent_reader_rejects_model_tamper(tmp_path):
    root = tmp_path / FINAL_DIRECTORY_NAME
    _write_locked_evidence(root)
    first = next((root / runner.MODEL_DIRECTORY_NAME).iterdir())
    first.write_bytes(first.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="model artifact mismatch"):
        read_bidirectional_learning_evidence(root)


def test_protocol_freezes_no_search_and_separate_authorization():
    protocol = (
        ROOT
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(protocol.split())
    for marker in (
        "exactly twelve model fits",
        "A nonpositive maximum or exact positive LONG/SHORT tie is `HOLD_CASH`",
        "There is no feature, learner, hyperparameter or threshold sweep",
        "The spot-only control may pass as independent Development evidence",
        "Calibration, Evaluation, Candidate v2",
    ):
        assert marker in normalized


def test_runner_requires_exact_separate_authorization(tmp_path):
    with pytest.raises(PermissionError, match="Exact one-shot"):
        runner.KrakenAIDrivenV2BidirectionalDevelopmentLearningRunner().run(
            tmp_path / "archive.zip",
            tmp_path / "context",
            tmp_path / "evidence",
            "WRONG",
        )
