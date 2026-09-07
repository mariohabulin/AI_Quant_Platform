"""Hash-bound, checkout-stable regime-gated selective Development runner V1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from kraken_ai_driven_v2_12h_development_learning_runner import (
        FROZEN_COMPLETE_ARCHIVE_SPEC,
        KrakenAIDrivenV212hDevelopmentLearningRunner,
    )
    from kraken_ai_driven_v2_bidirectional_development_learning_runner import (
        build_bidirectional_context_learning_table,
    )
    from kraken_ai_driven_v2_derivatives_context_dataset import (
        ATTEMPT_4_MANIFEST_SHA256,
        read_locked_derivatives_context_dataset,
    )
    from kraken_ai_driven_v2_derivatives_context_hypothesis import (
        COMMON_END_EXCLUSIVE_UTC,
        COMMON_START_UTC,
    )
    from kraken_ai_driven_v2_learning_core import ASSET_ORDER
    from kraken_ai_driven_v2_regime_gated_selective_hypothesis import (
        CONTEXT_FEATURE_COLUMNS,
        DIRECTION_ORDER,
        FOLD_PLAN,
        INNER_BASE_FIT_FRACTION,
        LOGISTIC_PARAMETERS,
        MATCHED_CONTROL,
        MINIMUM_BASE_CLASS_COUNT,
        MINIMUM_CALIBRATION_CLASS_COUNT,
        MINIMUM_CONTEXT_FOLD_WINS,
        MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        MINIMUM_POSITIVE_ASSETS,
        MINIMUM_RAW_SELECTIONS_PER_FOLD,
        PROBABILITY_SAFETY_BUFFER,
        REGIME_FEATURE_COLUMNS,
        SPOT_FEATURE_COLUMNS,
        TERMINAL_FAILURE_STATUS,
        VARIANT_SPECS,
        classify_spot_regime,
        context_confirms_direction,
        required_positive_probability,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_12h_development_learning_runner import (
        FROZEN_COMPLETE_ARCHIVE_SPEC,
        KrakenAIDrivenV212hDevelopmentLearningRunner,
    )
    from .kraken_ai_driven_v2_bidirectional_development_learning_runner import (
        build_bidirectional_context_learning_table,
    )
    from .kraken_ai_driven_v2_derivatives_context_dataset import (
        ATTEMPT_4_MANIFEST_SHA256,
        read_locked_derivatives_context_dataset,
    )
    from .kraken_ai_driven_v2_derivatives_context_hypothesis import (
        COMMON_END_EXCLUSIVE_UTC,
        COMMON_START_UTC,
    )
    from .kraken_ai_driven_v2_learning_core import ASSET_ORDER
    from .kraken_ai_driven_v2_regime_gated_selective_hypothesis import (
        CONTEXT_FEATURE_COLUMNS,
        DIRECTION_ORDER,
        FOLD_PLAN,
        INNER_BASE_FIT_FRACTION,
        LOGISTIC_PARAMETERS,
        MATCHED_CONTROL,
        MINIMUM_BASE_CLASS_COUNT,
        MINIMUM_CALIBRATION_CLASS_COUNT,
        MINIMUM_CONTEXT_FOLD_WINS,
        MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        MINIMUM_POSITIVE_ASSETS,
        MINIMUM_RAW_SELECTIONS_PER_FOLD,
        PROBABILITY_SAFETY_BUFFER,
        REGIME_FEATURE_COLUMNS,
        SPOT_FEATURE_COLUMNS,
        TERMINAL_FAILURE_STATUS,
        VARIANT_SPECS,
        classify_spot_regime,
        context_confirms_direction,
        required_positive_probability,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-v2-regime-gated-selective-development-runner-v1"
)
RUN_ID = "kraken-ai-v2-regime-gated-selective-development-v1"
COMPONENT_ID = "kraken-ai-v2-regime-gated-selective-development-runner-v1"
PARENT_COMMIT = "87927efa5f99e52ec0b6dba1fb2b10c4711e43f2"
AUTHORIZATION_PHRASE = (
    "EXECUTE_KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_ONCE"
)

DATASET_MANIFEST_SHA256 = (
    "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916"
)
SOURCE_BINDING_SHA256 = {
    "line_ending_policy": (
        "0cc450c4a2fe9a9fdf974fba4a75e7cd5d63b5897469b4f28e888d7c1bc1185e"
    ),
    "learning_core_component": (
        "467f2a1913371ef11c9a828770bb6a260708032a9ba2aec142d88cfe7ab79207"
    ),
    "spot_reader_component": (
        "8cbeb478b2d78bccbe33ebb96ab8a1e2838492b10f52e7e42b363c1c9e545082"
    ),
    "bidirectional_runner_component": (
        "6b37f6a1df2c40941202216179b38c25997ac16d3cf5fb261809c579222ea6c4"
    ),
    "context_dataset_component": (
        "718167d72b229f1e48af3e81a0835cf367003f81ca433b1bb0eb19035ed5eda0"
    ),
    "context_hypothesis_component": (
        "5355bb5d8e672d539776fc88705f2864b4974a767b12aaabfd4615aeb42288b3"
    ),
    "regime_hypothesis_protocol": (
        "788338f8c66f3bdf326086e03ea91123346fe48d69cc5161b2b1dc1f156e3553"
    ),
    "regime_hypothesis_component": (
        "1bb60a99b2b29741b89ab048b8a5942014c3d41eaa4e5b9a5ac4a760732d4594"
    ),
    "regime_hypothesis_review": (
        "191ab6770f900e28b0fa2a5309cc0f86c6b4710c9b2de8ab6f5b05a594f8e633"
    ),
}

FINAL_DIRECTORY_NAME = "v2_regime_gated_selective_development_v1"
STAGING_DIRECTORY_NAME = FINAL_DIRECTORY_NAME + ".staging"
REPORT_FILENAME = "kraken_ai_v2_regime_gated_selective_development_report.json"
REPORT_SHA256_FILENAME = REPORT_FILENAME + ".sha256"
PREDICTIONS_FILENAME = "out_of_fold_predictions.json"
PREDICTIONS_SHA256_FILENAME = PREDICTIONS_FILENAME + ".sha256"
MODEL_DIRECTORY_NAME = "models"
STATUS_REVIEW_REQUIRED = (
    "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_COMPLETED_REVIEW_REQUIRED"
)
STATUS_HOLD = TERMINAL_FAILURE_STATUS
STATUS_PASS = "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_PASS_REVIEW_REQUIRED"
READER_PASS_STATUS = "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_EVIDENCE_READER_PASS"

ALL_NUMERIC_FEATURE_COLUMNS = (*SPOT_FEATURE_COLUMNS, *CONTEXT_FEATURE_COLUMNS)


@dataclass(frozen=True)
class RecordedRegimeGatedSelectiveEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    learning_status: str
    labeled_decision_count: int
    trained_base_model_count: int
    trained_calibrator_count: int
    out_of_fold_prediction_count: int


def _utc(value):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Regime-gated timestamps must be timezone-aware.")
    return timestamp.tz_convert("UTC")


def _json_ready(value):
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Regime-gated evidence cannot contain non-finite values.")
        return value
    if isinstance(value, pd.Timestamp):
        return value.isoformat().replace("+00:00", "Z")
    return value


def canonical_json_bytes(value):
    return (
        json.dumps(
            _json_ready(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _direction_column(direction, suffix):
    return f"{direction.lower()}_{suffix}"


def _feature_names(variant_id):
    names = list(SPOT_FEATURE_COLUMNS)
    if VARIANT_SPECS[variant_id]["feature_set"] == "SPOT_PLUS_DERIVATIVES_CONTEXT":
        names.extend(CONTEXT_FEATURE_COLUMNS)
    return names


def _base_pipeline(feature_names):
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]
    )
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric, list(feature_names)),
            (
                "asset",
                OneHotEncoder(
                    categories=[list(ASSET_ORDER)],
                    handle_unknown="error",
                    sparse_output=False,
                ),
                ["asset"],
            ),
        ],
        sparse_threshold=0.0,
    )
    return Pipeline(
        [
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(**LOGISTIC_PARAMETERS)),
        ]
    )


def _validate_regime_table(table):
    if not isinstance(table, pd.DataFrame) or table.empty:
        raise ValueError("Regime-gated learning table must be nonempty.")
    required = {
        "asset",
        "decision_timestamp",
        "entry_timestamp",
        "long_event_end_timestamp",
        "short_event_end_timestamp",
        "long_label",
        "short_label",
        "long_outcome_net_r",
        "short_outcome_net_r",
        *ALL_NUMERIC_FEATURE_COLUMNS,
    }
    missing = sorted(required - set(table.columns))
    if missing:
        raise ValueError(f"Regime-gated learning table schema mismatch: {missing}.")
    candidate = table.copy()
    for column in (
        "decision_timestamp",
        "entry_timestamp",
        "long_event_end_timestamp",
        "short_event_end_timestamp",
    ):
        candidate[column] = pd.to_datetime(candidate[column], utc=True)
    if not set(candidate["asset"]).issubset(set(ASSET_ORDER)):
        raise ValueError("Regime-gated learning table asset mismatch.")
    if candidate.duplicated(["asset", "decision_timestamp"]).any():
        raise ValueError("Regime-gated learning table has duplicate decisions.")
    if (candidate["entry_timestamp"] <= candidate["decision_timestamp"]).any():
        raise ValueError("Regime-gated entries are not causal.")
    for direction in DIRECTION_ORDER:
        if (
            candidate[_direction_column(direction, "event_end_timestamp")]
            < candidate["entry_timestamp"]
        ).any():
            raise ValueError(f"{direction} outcomes are not causal.")
    numeric_columns = [
        *ALL_NUMERIC_FEATURE_COLUMNS,
        "long_outcome_net_r",
        "short_outcome_net_r",
    ]
    numeric = candidate[numeric_columns].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Regime-gated features and outcomes must be finite.")
    candidate.loc[:, numeric_columns] = numeric.astype(float)
    start = _utc(COMMON_START_UTC)
    end = _utc(COMMON_END_EXCLUSIVE_UTC)
    if (
        (candidate["decision_timestamp"] < start).any()
        or (candidate["decision_timestamp"] >= end).any()
    ):
        raise ValueError("Regime-gated decisions exceed the common interval.")
    candidate["latest_event_end_timestamp"] = candidate[
        ["long_event_end_timestamp", "short_event_end_timestamp"]
    ].max(axis=1)
    if (candidate["latest_event_end_timestamp"] >= end).any():
        raise ValueError("Regime-gated outcomes exceed the Development boundary.")
    candidate["regime"] = [
        classify_spot_regime(row) for row in candidate.to_dict("records")
    ]
    candidate["regime_direction"] = candidate["regime"].map(
        {"LONG_REGIME": "LONG", "SHORT_REGIME": "SHORT"}
    )
    candidate["context_confirmed"] = [
        False
        if pd.isna(direction)
        else context_confirms_direction(row, direction)
        for row, direction in zip(
            candidate.to_dict("records"), candidate["regime_direction"], strict=True
        )
    ]
    return candidate.sort_values(
        ["decision_timestamp", "asset"], kind="stable"
    ).reset_index(drop=True)


def build_regime_gated_selective_learning_table(frames, sources_by_asset):
    table, diagnostics = build_bidirectional_context_learning_table(
        frames, sources_by_asset
    )
    table = _validate_regime_table(table)
    diagnostics["regime_counts"] = {
        regime: int((table["regime"] == regime).sum())
        for regime in ("LONG_REGIME", "SHORT_REGIME", "NEUTRAL")
    }
    diagnostics["context_confirmed_counts"] = {
        direction: int(
            (
                (table["regime_direction"] == direction)
                & table["context_confirmed"]
            ).sum()
        )
        for direction in DIRECTION_ORDER
    }
    return table, diagnostics


def _direction_rows(table, direction, require_context):
    if direction not in DIRECTION_ORDER:
        raise ValueError(f"Direction must be one of {DIRECTION_ORDER}.")
    rows = table.loc[table["regime_direction"] == direction].copy()
    if require_context:
        rows = rows.loc[rows["context_confirmed"]].copy()
    rows["event_end_timestamp"] = rows[
        _direction_column(direction, "event_end_timestamp")
    ]
    rows["label"] = rows[_direction_column(direction, "label")]
    rows["outcome_net_r"] = rows[_direction_column(direction, "outcome_net_r")]
    rows["positive_outcome"] = rows["outcome_net_r"] > 0.0
    return rows


def _class_counts(values):
    observed = pd.Series(values).value_counts()
    return {
        "NONPOSITIVE": int(observed.get(False, 0)),
        "POSITIVE": int(observed.get(True, 0)),
    }


def _inner_direction_slices(table, fold, direction, require_context):
    candidate = _direction_rows(_validate_regime_table(table), direction, require_context)
    training_end = _utc(fold["training_end_exclusive_utc"])
    validation_start = _utc(fold["validation_start_utc"])
    validation_end = _utc(fold["validation_end_exclusive_utc"])
    outer_training = candidate.loc[
        (candidate["decision_timestamp"] < training_end)
        & (candidate["event_end_timestamp"] < training_end)
    ].copy()
    validation = candidate.loc[
        (candidate["decision_timestamp"] >= validation_start)
        & (candidate["decision_timestamp"] < validation_end)
        & (candidate["event_end_timestamp"] < validation_end)
    ].copy()
    unique_times = pd.DatetimeIndex(
        outer_training["decision_timestamp"].drop_duplicates().sort_values()
    )
    if len(unique_times) < 8:
        raise ValueError(f"{fold['fold_id']} {direction} has insufficient timestamps.")
    split = max(
        1,
        min(
            len(unique_times) - 1,
            int(len(unique_times) * INNER_BASE_FIT_FRACTION),
        ),
    )
    boundary = unique_times[split]
    inner_fit = outer_training.loc[
        (outer_training["decision_timestamp"] < boundary)
        & (outer_training["event_end_timestamp"] < boundary)
    ].copy()
    inner_calibration = outer_training.loc[
        (outer_training["decision_timestamp"] >= boundary)
        & (outer_training["event_end_timestamp"] < training_end)
    ].copy()
    if validation.empty:
        raise ValueError(f"{fold['fold_id']} {direction} has no validation rows.")
    for name, frame, minimum in (
        ("base fit", inner_fit, MINIMUM_BASE_CLASS_COUNT),
        ("calibration", inner_calibration, MINIMUM_CALIBRATION_CLASS_COUNT),
    ):
        counts = _class_counts(frame["positive_outcome"])
        if min(counts.values()) < minimum:
            raise ValueError(
                f"{fold['fold_id']} {direction} {name} lacks frozen class support: {counts}."
            )
    return inner_fit, inner_calibration, validation, boundary


def _fit_direction(variant_id, direction, inner_fit, inner_calibration, validation):
    numeric_features = _feature_names(variant_id)
    feature_names = [*numeric_features, "asset"]
    base = _base_pipeline(numeric_features)
    base.fit(inner_fit[feature_names], inner_fit["positive_outcome"])
    calibration_score = np.asarray(
        base.decision_function(inner_calibration[feature_names]), dtype=float
    ).reshape(-1, 1)
    calibrator = LogisticRegression(
        C=1.0,
        class_weight=None,
        solver="lbfgs",
        max_iter=2000,
        random_state=LOGISTIC_PARAMETERS["random_state"],
    )
    calibrator.fit(calibration_score, inner_calibration["positive_outcome"])
    validation_score = np.asarray(
        base.decision_function(validation[feature_names]), dtype=float
    ).reshape(-1, 1)
    probabilities = np.asarray(
        calibrator.predict_proba(validation_score)[:, list(calibrator.classes_).index(True)],
        dtype=float,
    )
    base_positive = inner_fit.loc[inner_fit["positive_outcome"], "outcome_net_r"]
    base_nonpositive = inner_fit.loc[
        ~inner_fit["positive_outcome"], "outcome_net_r"
    ]
    required = required_positive_probability(
        float(base_positive.mean()), float(base_nonpositive.mean())
    )
    actual = validation["positive_outcome"].to_numpy(dtype=float)
    outer_training = pd.concat([inner_fit, inner_calibration], ignore_index=True)
    prevalence = float(outer_training["positive_outcome"].mean())
    calibrated_brier = float(np.mean((actual - probabilities) ** 2))
    prevalence_brier = float(np.mean((actual - prevalence) ** 2))
    prediction = validation[
        [
            "asset",
            "decision_timestamp",
            "entry_timestamp",
            "event_end_timestamp",
            "label",
            "outcome_net_r",
            "regime",
            "context_confirmed",
        ]
    ].copy()
    prediction["direction"] = direction
    prediction["positive_outcome"] = validation["positive_outcome"].to_numpy(bool)
    prediction["positive_probability"] = probabilities
    prediction["required_probability"] = required
    prediction["action"] = np.where(probabilities > required, direction, "HOLD_CASH")
    metrics = {
        "inner_fit_rows": int(len(inner_fit)),
        "inner_calibration_rows": int(len(inner_calibration)),
        "outer_validation_rows": int(len(validation)),
        "inner_fit_class_counts": _class_counts(inner_fit["positive_outcome"]),
        "inner_calibration_class_counts": _class_counts(
            inner_calibration["positive_outcome"]
        ),
        "outer_training_positive_prevalence": prevalence,
        "mean_positive_net_r_base_fit": float(base_positive.mean()),
        "mean_nonpositive_net_r_base_fit": float(base_nonpositive.mean()),
        "required_positive_probability": required,
        "calibrated_brier_score": calibrated_brier,
        "prevalence_brier_score": prevalence_brier,
        "brier_skill_pass": calibrated_brier < prevalence_brier,
        "supported": True,
    }
    base_artifact = pickle.dumps(
        {
            "variant_id": variant_id,
            "direction": direction,
            "feature_names": feature_names,
            "estimator": base,
        },
        protocol=5,
    )
    calibrator_artifact = pickle.dumps(
        {
            "variant_id": variant_id,
            "direction": direction,
            "input": "BASE_DECISION_FUNCTION",
            "calibrator": calibrator,
            "required_positive_probability": required,
        },
        protocol=5,
    )
    return prediction, metrics, base_artifact, calibrator_artifact


def _nonoverlapping(frame):
    selected = []
    busy_until = {}
    ordered = frame.sort_values(["decision_timestamp", "asset"], kind="stable")
    for index, row in ordered.iterrows():
        asset = row["asset"]
        if asset not in busy_until or row["decision_timestamp"] >= busy_until[asset]:
            selected.append(index)
            busy_until[asset] = row["event_end_timestamp"]
    return frame.loc[selected].sort_values(
        ["decision_timestamp", "asset"], kind="stable"
    )


def _selected(predictions):
    return predictions.loc[predictions["action"] != "HOLD_CASH"].copy()


def _summary(frame):
    values = frame["outcome_net_r"].to_numpy(dtype=float)
    count = int(len(frame))
    directions = frame["direction"].value_counts() if "direction" in frame else pd.Series()
    return {
        "count": count,
        "direction_counts": {
            direction: int(directions.get(direction, 0)) for direction in DIRECTION_ORDER
        },
        "cumulative_net_r": float(values.sum()),
        "mean_net_r": float(values.mean()) if count else None,
        "median_net_r": float(np.median(values)) if count else None,
        "positive_outcome_count": int((values > 0.0).sum()),
    }


def _prediction_identity_sha256(predictions):
    columns = (
        "fold_id",
        "asset",
        "decision_timestamp",
        "entry_timestamp",
        "event_end_timestamp",
        "direction",
        "label",
        "outcome_net_r",
    )
    return hashlib.sha256(
        canonical_json_bytes(predictions.loc[:, columns].to_dict("records"))
    ).hexdigest()


def _empty_predictions():
    return pd.DataFrame(
        columns=[
            "variant_id",
            "fold_id",
            "asset",
            "decision_timestamp",
            "entry_timestamp",
            "event_end_timestamp",
            "direction",
            "label",
            "outcome_net_r",
            "regime",
            "context_confirmed",
            "positive_outcome",
            "positive_probability",
            "required_probability",
            "action",
        ]
    )


def _absolute_review(variant_id, predictions, fold_metadata):
    raw_selected = _selected(predictions)
    nonoverlap = _nonoverlapping(raw_selected)
    folds = []
    for fold in FOLD_PLAN:
        fold_id = fold["fold_id"]
        raw_summary = _summary(raw_selected.loc[raw_selected["fold_id"] == fold_id])
        separate_summary = _summary(
            nonoverlap.loc[nonoverlap["fold_id"] == fold_id]
        )
        direction_support = fold_metadata[fold_id]["direction_support"]
        folds.append(
            {
                **fold_metadata[fold_id],
                "raw_selected": raw_summary,
                "nonoverlapping_selected": separate_summary,
                "raw_support_pass": (
                    raw_summary["count"] >= MINIMUM_RAW_SELECTIONS_PER_FOLD
                ),
                "nonoverlap_support_pass": (
                    separate_summary["count"]
                    >= MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD
                ),
                "positive_net_r_pass": (
                    separate_summary["mean_net_r"] is not None
                    and separate_summary["mean_net_r"] > 0.0
                    and separate_summary["cumulative_net_r"] > 0.0
                ),
                "all_direction_brier_skill_pass": all(
                    item["supported"] and item["brier_skill_pass"]
                    for item in direction_support.values()
                ),
            }
        )
    assets = []
    for asset in ASSET_ORDER:
        summary = _summary(nonoverlap.loc[nonoverlap["asset"] == asset])
        assets.append(
            {
                "asset": asset,
                "nonoverlapping_selected": summary,
                "positive_net_r_pass": summary["cumulative_net_r"] > 0.0,
            }
        )
    overall = _summary(nonoverlap)
    positive_asset_count = sum(item["positive_net_r_pass"] for item in assets)
    gates = {
        "all_fold_raw_support_pass": all(item["raw_support_pass"] for item in folds),
        "all_fold_nonoverlap_support_pass": all(
            item["nonoverlap_support_pass"] for item in folds
        ),
        "all_fold_positive_net_r_pass": all(
            item["positive_net_r_pass"] for item in folds
        ),
        "all_direction_fold_brier_skill_pass": all(
            item["all_direction_brier_skill_pass"] for item in folds
        ),
        "positive_asset_count": positive_asset_count,
        "asset_breadth_pass": positive_asset_count >= MINIMUM_POSITIVE_ASSETS,
        "overall_positive_net_r_pass": (
            overall["mean_net_r"] is not None
            and overall["mean_net_r"] > 0.0
            and overall["cumulative_net_r"] > 0.0
        ),
    }
    absolute_pass = all(
        value for key, value in gates.items() if key.endswith("_pass")
    )
    requires_incremental = VARIANT_SPECS[variant_id][
        "incremental_context_gate_required"
    ]
    return {
        "variant_id": variant_id,
        "objective": VARIANT_SPECS[variant_id]["objective"],
        "feature_set": VARIANT_SPECS[variant_id]["feature_set"],
        "folds": folds,
        "assets": assets,
        "raw_selected_overall": _summary(raw_selected),
        "nonoverlapping_selected_overall": overall,
        "absolute_gates": gates,
        "absolute_gates_passed": absolute_pass,
        "incremental_gates": None,
        "development_viable": bool(absolute_pass and not requires_incremental),
        "prediction_row_identity_sha256": _prediction_identity_sha256(predictions),
    }


def _mean_or_zero(summary):
    return 0.0 if summary["mean_net_r"] is None else summary["mean_net_r"]


def _apply_incremental_gates(reviews):
    registry = {review["variant_id"]: review for review in reviews}
    for context_id, control_id in MATCHED_CONTROL.items():
        if context_id not in registry or control_id not in registry:
            raise RuntimeError("Regime-gated matched review pair is incomplete.")
        context = registry[context_id]
        control = registry[control_id]
        context_overall = _mean_or_zero(context["nonoverlapping_selected_overall"])
        control_overall = _mean_or_zero(control["nonoverlapping_selected_overall"])
        context_fold_means = {
            item["fold_id"]: _mean_or_zero(item["nonoverlapping_selected"])
            for item in context["folds"]
        }
        control_fold_means = {
            item["fold_id"]: _mean_or_zero(item["nonoverlapping_selected"])
            for item in control["folds"]
        }
        fold_wins = sum(
            context_fold_means[fold_id] > control_fold_means[fold_id]
            for fold_id in context_fold_means
        )
        incremental = {
            "matched_control": control_id,
            "overall_mean_net_r": context_overall,
            "control_overall_mean_net_r": control_overall,
            "higher_overall_mean_net_r_pass": context_overall > control_overall,
            "worst_fold_mean_net_r": min(context_fold_means.values()),
            "control_worst_fold_mean_net_r": min(control_fold_means.values()),
            "higher_worst_fold_mean_net_r_pass": (
                min(context_fold_means.values()) > min(control_fold_means.values())
            ),
            "fold_mean_win_count": fold_wins,
            "minimum_fold_mean_wins": MINIMUM_CONTEXT_FOLD_WINS,
            "fold_mean_wins_pass": fold_wins >= MINIMUM_CONTEXT_FOLD_WINS,
        }
        incremental_pass = all(
            value for key, value in incremental.items() if key.endswith("_pass")
        )
        incremental["all_incremental_gates_passed"] = incremental_pass
        context["incremental_gates"] = incremental
        context["development_viable"] = bool(
            context["absolute_gates_passed"] and incremental_pass
        )
    return reviews


def run_regime_gated_selective_experiment(table):
    candidate = _validate_regime_table(table)
    reviews = []
    artifacts = {}
    prediction_frames = []
    for variant_id, spec in VARIANT_SPECS.items():
        require_context = spec["derivatives_confirmation_required"]
        fold_predictions = []
        fold_metadata = {}
        for fold in FOLD_PLAN:
            fold_id = fold["fold_id"]
            direction_support = {}
            for direction in DIRECTION_ORDER:
                try:
                    inner_fit, inner_calibration, validation, boundary = (
                        _inner_direction_slices(
                            candidate, fold, direction, require_context=require_context
                        )
                    )
                except ValueError as exc:
                    direction_support[direction] = {
                        "supported": False,
                        "support_failure": str(exc),
                        "calibrated_brier_score": None,
                        "prevalence_brier_score": None,
                        "brier_skill_pass": False,
                    }
                    continue
                prediction, metrics, base_artifact, calibrator_artifact = (
                    _fit_direction(
                        variant_id,
                        direction,
                        inner_fit,
                        inner_calibration,
                        validation,
                    )
                )
                prediction["fold_id"] = fold_id
                prediction["variant_id"] = variant_id
                fold_predictions.append(prediction)
                direction_support[direction] = {
                    **metrics,
                    "inner_boundary_utc": boundary,
                }
                prefix = f"{variant_id}|{fold_id}|{direction}"
                artifacts[f"{prefix}|BASE"] = base_artifact
                artifacts[f"{prefix}|CALIBRATOR"] = calibrator_artifact
            fold_metadata[fold_id] = {
                "fold_id": fold_id,
                "direction_support": direction_support,
            }
        predictions = (
            pd.concat(fold_predictions, ignore_index=True)
            if fold_predictions
            else _empty_predictions()
        )
        predictions = predictions.sort_values(
            ["fold_id", "decision_timestamp", "asset", "direction"], kind="stable"
        ).reset_index(drop=True)
        prediction_frames.append(predictions)
        reviews.append(_absolute_review(variant_id, predictions, fold_metadata))
    reviews = _apply_incremental_gates(reviews)
    passing = [
        review["variant_id"] for review in reviews if review["development_viable"]
    ]
    all_predictions = pd.concat(prediction_frames, ignore_index=True).sort_values(
        ["variant_id", "fold_id", "decision_timestamp", "asset", "direction"],
        kind="stable",
    ).reset_index(drop=True)
    return (
        {
            "status": STATUS_PASS if passing else STATUS_HOLD,
            "action": (
                "REVIEW_PASSING_DEVELOPMENT_HYPOTHESES" if passing else "HOLD_CASH"
            ),
            "passing_development_hypotheses": passing,
            "automatic_model_selection": False,
            "automatic_successor_authorized": False,
            "candidate_v2_authorized": False,
            "variant_reviews": reviews,
        },
        all_predictions,
        artifacts,
    )


def _prediction_payload(predictions):
    columns = (
        "variant_id",
        "fold_id",
        "asset",
        "decision_timestamp",
        "entry_timestamp",
        "event_end_timestamp",
        "direction",
        "label",
        "outcome_net_r",
        "regime",
        "context_confirmed",
        "positive_outcome",
        "positive_probability",
        "required_probability",
        "action",
    )
    return [
        {column: row[column] for column in columns}
        for _, row in predictions.iterrows()
    ]


def _artifact_filename(artifact_id):
    return artifact_id.lower().replace("|", "__") + ".pkl"


def read_regime_gated_selective_evidence(evidence_directory):
    root = Path(evidence_directory).resolve()
    report_path = root / REPORT_FILENAME
    sidecar_path = root / REPORT_SHA256_FILENAME
    if not report_path.is_file() or not sidecar_path.is_file():
        raise RuntimeError("Regime-gated report lock is incomplete.")
    report_bytes = report_path.read_bytes()
    digest = hashlib.sha256(report_bytes).hexdigest()
    if sidecar_path.read_bytes() != f"{digest}  {REPORT_FILENAME}\n".encode("ascii"):
        raise RuntimeError("Regime-gated report sidecar mismatch.")
    report = json.loads(report_bytes)
    if canonical_json_bytes(report) != report_bytes:
        raise RuntimeError("Regime-gated report is not canonical JSON.")
    if report.get("protocol_id") != PROTOCOL_ID or report.get("run_id") != RUN_ID:
        raise RuntimeError("Regime-gated report identity mismatch.")
    prediction = report.get("prediction_artifact", {})
    prediction_path = root / prediction.get("path", "")
    prediction_sidecar = root / prediction.get("checksum_path", "")
    if not prediction_path.is_file() or not prediction_sidecar.is_file():
        raise RuntimeError("Regime-gated prediction artifact is incomplete.")
    prediction_bytes = prediction_path.read_bytes()
    prediction_digest = hashlib.sha256(prediction_bytes).hexdigest()
    if (
        prediction_digest != prediction.get("sha256")
        or len(prediction_bytes) != prediction.get("bytes")
        or prediction_sidecar.read_bytes()
        != f"{prediction_digest}  {PREDICTIONS_FILENAME}\n".encode("ascii")
    ):
        raise RuntimeError("Regime-gated prediction artifact mismatch.")
    rows = json.loads(prediction_bytes)
    if canonical_json_bytes(rows) != prediction_bytes:
        raise RuntimeError("Regime-gated predictions are not canonical JSON.")
    if len(rows) != report.get("out_of_fold_prediction_count"):
        raise RuntimeError("Regime-gated prediction count mismatch.")
    allowed_ids = {
        f"{variant}|{fold['fold_id']}|{direction}|{kind}"
        for variant in VARIANT_SPECS
        for fold in FOLD_PLAN
        for direction in DIRECTION_ORDER
        for kind in ("BASE", "CALIBRATOR")
    }
    observed_ids = set()
    for artifact in report.get("model_artifacts", []):
        observed_ids.add(artifact["artifact_id"])
        path = root / artifact["path"]
        if (
            not path.is_file()
            or path.stat().st_size != artifact["bytes"]
            or _sha256(path) != artifact["sha256"]
        ):
            raise RuntimeError(
                f"Regime-gated artifact mismatch: {artifact['artifact_id']}."
            )
    if not observed_ids.issubset(allowed_ids):
        raise RuntimeError("Regime-gated artifact registry mismatch.")
    base_count = sum(item.endswith("|BASE") for item in observed_ids)
    calibrator_count = sum(item.endswith("|CALIBRATOR") for item in observed_ids)
    if report.get("trained_base_model_count") != base_count or base_count > 12:
        raise RuntimeError("Regime-gated base-model count mismatch.")
    if (
        report.get("trained_calibrator_count") != calibrator_count
        or calibrator_count > 12
    ):
        raise RuntimeError("Regime-gated calibrator count mismatch.")
    if report.get("trained_artifact_count") != len(observed_ids):
        raise RuntimeError("Regime-gated total artifact count mismatch.")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": READER_PASS_STATUS,
        "report_sha256": digest,
        "learning_status": report["learning_status"],
        "action": report["action"],
        "trained_base_model_count": base_count,
        "trained_calibrator_count": calibrator_count,
        "trained_artifact_count": len(observed_ids),
        "out_of_fold_prediction_count": report["out_of_fold_prediction_count"],
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "real_orders_submitted": False,
    }


class KrakenAIDrivenV2RegimeGatedSelectiveDevelopmentRunner:
    @staticmethod
    def _external_paths(archive_path, context_lock, evidence_root):
        project_root = Path(__file__).resolve().parents[1]
        paths = tuple(
            Path(path).resolve()
            for path in (archive_path, context_lock, evidence_root)
        )
        for path in paths:
            if path == project_root or path.is_relative_to(project_root):
                raise ValueError("Learning inputs and evidence must remain external.")
        if len(set(paths)) != len(paths):
            raise ValueError("Learning archive, context lock and evidence must differ.")
        return paths

    @staticmethod
    def _assert_one_shot(evidence_root):
        final = evidence_root / FINAL_DIRECTORY_NAME
        staging = evidence_root / STAGING_DIRECTORY_NAME
        if final.exists():
            raise FileExistsError("Regime-gated evidence exists; refusing repeat.")
        if staging.exists():
            raise FileExistsError("Incomplete regime-gated staging evidence exists.")
        return final, staging

    def run(self, archive_path, context_lock, evidence_root, authorization_phrase):
        if authorization_phrase != AUTHORIZATION_PHRASE:
            raise PermissionError("Exact one-shot regime-gated authorization is required.")
        archive_path, context_lock, evidence_root = self._external_paths(
            archive_path, context_lock, evidence_root
        )
        final, staging = self._assert_one_shot(evidence_root)
        evidence_root.mkdir(parents=True, exist_ok=True)
        staging.mkdir(exist_ok=False)

        spot_reader = KrakenAIDrivenV212hDevelopmentLearningRunner()
        archive_evidence = spot_reader._validate_archive(archive_path)
        frames, member_evidence = spot_reader._load_frames(archive_path)
        sources, context_manifest, context_digest = (
            read_locked_derivatives_context_dataset(
                context_lock,
                expected_manifest_sha256=DATASET_MANIFEST_SHA256,
                verify_raw=True,
            )
        )
        if context_digest != ATTEMPT_4_MANIFEST_SHA256:
            raise RuntimeError("Attempt 4 context-lock binding mismatch.")
        table, diagnostics = build_regime_gated_selective_learning_table(
            frames, sources
        )
        experiment, predictions, artifacts = run_regime_gated_selective_experiment(
            table
        )
        if len(artifacts) > 24:
            raise RuntimeError("Frozen regime-gated artifact budget exceeded.")

        prediction_bytes = canonical_json_bytes(_prediction_payload(predictions))
        prediction_sha256 = hashlib.sha256(prediction_bytes).hexdigest()
        model_manifest = []
        for artifact_id in sorted(artifacts):
            raw = artifacts[artifact_id]
            filename = _artifact_filename(artifact_id)
            model_manifest.append(
                {
                    "artifact_id": artifact_id,
                    "path": f"{MODEL_DIRECTORY_NAME}/{filename}",
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
        payload = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "component_id": COMPONENT_ID,
            "run_id": RUN_ID,
            "implementation_parent_commit": PARENT_COMMIT,
            "source_binding_sha256": dict(SOURCE_BINDING_SHA256),
            "learning_status": experiment["status"],
            "action": experiment["action"],
            "terminal_failure_status": TERMINAL_FAILURE_STATUS,
            "partition": "DEVELOPMENT",
            "resolution": "12h",
            "common_start_utc": COMMON_START_UTC,
            "common_end_exclusive_utc": COMMON_END_EXCLUSIVE_UTC,
            "source_archive": archive_evidence,
            "source_member_evidence": member_evidence,
            "context_dataset_id": context_manifest["dataset_id"],
            "context_dataset_manifest_sha256": context_digest,
            "context_dataset_object_count": context_manifest["object_count"],
            "context_dataset_recovery_attempt": context_manifest["recovery_attempt"],
            "asset_order": list(ASSET_ORDER),
            "direction_order": list(DIRECTION_ORDER),
            "regime_feature_columns": list(REGIME_FEATURE_COLUMNS),
            "spot_feature_columns": list(SPOT_FEATURE_COLUMNS),
            "context_feature_columns": list(CONTEXT_FEATURE_COLUMNS),
            "variant_order": list(VARIANT_SPECS),
            "matched_control": dict(MATCHED_CONTROL),
            "fold_plan": [dict(fold) for fold in FOLD_PLAN],
            "labeled_decision_count": int(len(table)),
            "label_diagnostics": diagnostics,
            "probability_safety_buffer": PROBABILITY_SAFETY_BUFFER,
            "variant_reviews": experiment["variant_reviews"],
            "passing_development_hypotheses": experiment[
                "passing_development_hypotheses"
            ],
            "trained_base_model_count": sum(
                key.endswith("|BASE") for key in artifacts
            ),
            "trained_calibrator_count": sum(
                key.endswith("|CALIBRATOR") for key in artifacts
            ),
            "trained_artifact_count": len(artifacts),
            "model_artifacts": model_manifest,
            "out_of_fold_prediction_count": int(len(predictions)),
            "prediction_artifact": {
                "path": PREDICTIONS_FILENAME,
                "checksum_path": PREDICTIONS_SHA256_FILENAME,
                "bytes": len(prediction_bytes),
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
            "next_stage": (
                "RUN_INDEPENDENT_READ_ONLY_REGIME_GATED_SELECTIVE_EVIDENCE_REVIEW"
            ),
        }
        report_bytes = canonical_json_bytes(payload)
        report_sha256 = hashlib.sha256(report_bytes).hexdigest()
        (staging / REPORT_FILENAME).write_bytes(report_bytes)
        (staging / REPORT_SHA256_FILENAME).write_bytes(
            f"{report_sha256}  {REPORT_FILENAME}\n".encode("ascii")
        )
        (staging / PREDICTIONS_FILENAME).write_bytes(prediction_bytes)
        (staging / PREDICTIONS_SHA256_FILENAME).write_bytes(
            f"{prediction_sha256}  {PREDICTIONS_FILENAME}\n".encode("ascii")
        )
        model_directory = staging / MODEL_DIRECTORY_NAME
        model_directory.mkdir(exist_ok=False)
        for artifact in model_manifest:
            (staging / artifact["path"]).write_bytes(
                artifacts[artifact["artifact_id"]]
            )
        os.replace(staging, final)
        locked = read_regime_gated_selective_evidence(final)
        return RecordedRegimeGatedSelectiveEvidence(
            report_path=final / REPORT_FILENAME,
            checksum_path=final / REPORT_SHA256_FILENAME,
            report_sha256=locked["report_sha256"],
            learning_status=locked["learning_status"],
            labeled_decision_count=int(len(table)),
            trained_base_model_count=locked["trained_base_model_count"],
            trained_calibrator_count=locked["trained_calibrator_count"],
            out_of_fold_prediction_count=int(len(predictions)),
        )


def runner_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "run_id": RUN_ID,
        "parent_commit": PARENT_COMMIT,
        "authorization_phrase": AUTHORIZATION_PHRASE,
        "authorization_phrase_active": False,
        "partition": "DEVELOPMENT",
        "active_resolution": "12h",
        "common_start_utc": COMMON_START_UTC,
        "common_end_exclusive_utc": COMMON_END_EXCLUSIVE_UTC,
        "asset_order": list(ASSET_ORDER),
        "direction_order": list(DIRECTION_ORDER),
        "variant_order": list(VARIANT_SPECS),
        "matched_control": dict(MATCHED_CONTROL),
        "regime_feature_order": list(REGIME_FEATURE_COLUMNS),
        "probability_safety_buffer": PROBABILITY_SAFETY_BUFFER,
        "maximum_base_model_fits": 12,
        "maximum_calibrator_fits": 12,
        "maximum_total_fits": 24,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "source_binding_sha256": dict(SOURCE_BINDING_SHA256),
        "frozen_archive_sha256": FROZEN_COMPLETE_ARCHIVE_SPEC["sha256"],
        "strict_regime_filter_implemented": True,
        "directional_context_confirmation_implemented": True,
        "chronological_inner_calibration_implemented": True,
        "payoff_break_even_threshold_implemented": True,
        "brier_prevalence_skill_gate_implemented": True,
        "absolute_and_incremental_gates_implemented": True,
        "terminal_research_stop_implemented": True,
        "real_model_artifact_persistence_implemented": True,
        "out_of_fold_prediction_artifact_implemented": True,
        "canonical_binary_lf_sidecars_implemented": True,
        "one_shot_atomic_evidence_implemented": True,
        "independent_evidence_reader_implemented": True,
        "network_download_authorized": False,
        "source_archive_opened": False,
        "context_dataset_opened": False,
        "development_data_opened": False,
        "labels_generated": False,
        "model_training_authorized": False,
        "model_training_executed": False,
        "feature_search_authorized": False,
        "hyperparameter_sweep_authorized": False,
        "threshold_sweep_authorized": False,
        "automatic_model_selection": False,
        "automatic_successor_authorized": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": (
            "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_RUNNER_REVIEW_REQUIRED"
        ),
        "next_stage": (
            "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_REGIME_GATED_SELECTIVE_"
            "DEVELOPMENT_RUN"
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Execute or review frozen regime-gated selective Development learning."
    )
    parser.add_argument("--declaration-only", action="store_true")
    parser.add_argument("--complete-archive")
    parser.add_argument("--context-lock")
    parser.add_argument("--evidence-root")
    parser.add_argument("--authorization-phrase")
    parser.add_argument("--review-evidence")
    args = parser.parse_args(argv)
    if args.declaration_only:
        result = runner_declaration()
    elif args.review_evidence:
        result = read_regime_gated_selective_evidence(args.review_evidence)
    elif all(
        (
            args.complete_archive,
            args.context_lock,
            args.evidence_root,
            args.authorization_phrase,
        )
    ):
        recorded = KrakenAIDrivenV2RegimeGatedSelectiveDevelopmentRunner().run(
            args.complete_archive,
            args.context_lock,
            args.evidence_root,
            args.authorization_phrase,
        )
        result = {
            "status": "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_EVIDENCE_RECORDED",
            "learning_status": recorded.learning_status,
            "report_path": str(recorded.report_path),
            "checksum_path": str(recorded.checksum_path),
            "report_sha256": recorded.report_sha256,
            "labeled_decision_count": recorded.labeled_decision_count,
            "trained_base_model_count": recorded.trained_base_model_count,
            "trained_calibrator_count": recorded.trained_calibrator_count,
            "out_of_fold_prediction_count": recorded.out_of_fold_prediction_count,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "candidate_v2_authorized": False,
            "real_orders_submitted": False,
        }
    else:
        parser.error(
            "Use --declaration-only, --review-evidence, or all four execution arguments."
        )
    print(json.dumps(_json_ready(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
