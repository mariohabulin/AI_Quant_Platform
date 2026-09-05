"""Hash-bound four-variant Development runner for derivatives context V1."""

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
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import average_precision_score, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from kraken_ai_driven_v2_12h_development_learning_runner import (
        FROZEN_COMPLETE_ARCHIVE_SPEC,
        KrakenAIDrivenV212hDevelopmentLearningRunner,
    )
    from kraken_ai_driven_v2_derivatives_context_dataset import (
        ATTEMPT_4_MANIFEST_SHA256,
        read_locked_derivatives_context_dataset,
    )
    from kraken_ai_driven_v2_derivatives_context_hypothesis import (
        ASSET_ORDER,
        CLASSIFIER_PARAMETERS,
        COMMON_END_EXCLUSIVE_UTC,
        COMMON_START_UTC,
        CONTEXT_FEATURE_COLUMNS,
        FOLD_PLAN,
        INNER_FIT_FRACTION,
        MATCHED_CONTROL,
        MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        MINIMUM_POSITIVE_ASSETS,
        MINIMUM_PREDICTIVE_FOLD_WINS,
        MINIMUM_RAW_SELECTIONS_PER_FOLD,
        REGRESSOR_PARAMETERS,
        SPOT_FEATURE_COLUMNS,
        VARIANT_SPECS,
        build_derivatives_context_feature_table,
    )
    from kraken_ai_driven_v2_learning_core import (
        CLASS_ORDER,
        build_labeled_learning_data,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_12h_development_learning_runner import (
        FROZEN_COMPLETE_ARCHIVE_SPEC,
        KrakenAIDrivenV212hDevelopmentLearningRunner,
    )
    from .kraken_ai_driven_v2_derivatives_context_dataset import (
        ATTEMPT_4_MANIFEST_SHA256,
        read_locked_derivatives_context_dataset,
    )
    from .kraken_ai_driven_v2_derivatives_context_hypothesis import (
        ASSET_ORDER,
        CLASSIFIER_PARAMETERS,
        COMMON_END_EXCLUSIVE_UTC,
        COMMON_START_UTC,
        CONTEXT_FEATURE_COLUMNS,
        FOLD_PLAN,
        INNER_FIT_FRACTION,
        MATCHED_CONTROL,
        MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        MINIMUM_POSITIVE_ASSETS,
        MINIMUM_PREDICTIVE_FOLD_WINS,
        MINIMUM_RAW_SELECTIONS_PER_FOLD,
        REGRESSOR_PARAMETERS,
        SPOT_FEATURE_COLUMNS,
        VARIANT_SPECS,
        build_derivatives_context_feature_table,
    )
    from .kraken_ai_driven_v2_learning_core import (
        CLASS_ORDER,
        build_labeled_learning_data,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-derivatives-context-development-learning-runner-v1"
)
RUN_ID = "kraken-ai-v2-derivatives-context-development-learning-v1"
COMPONENT_ID = "kraken-ai-v2-derivatives-context-development-learning-runner-v1"
PARENT_COMMIT = "9b23d05eed043c92205e7a2ca62c70312f6b6e8f"
AUTHORIZATION_PHRASE = (
    "EXECUTE_KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_ONCE"
)
DATASET_MANIFEST_SHA256 = (
    "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916"
)
DATASET_RESULT_DOCUMENT_SHA256 = (
    "753ff82a36d93382eed5ead23ecabbd884e850dd6ac72f3e2728df32d8c33922"
)
WINDOWS_SIDECAR_INCIDENT_SHA256 = (
    "8bd88c1129a449b2dd1670a663be49cf7ea3091691dbed123dc54f5280504c3d"
)
HYPOTHESIS_PROTOCOL_SHA256 = (
    "81074ffcd8213fcf86c44e5f118293936632b279602b5750a67332848d6fd865"
)
HYPOTHESIS_COMPONENT_SHA256 = (
    "5355bb5d8e672d539776fc88705f2864b4974a767b12aaabfd4615aeb42288b3"
)
HYPOTHESIS_REVIEW_SHA256 = (
    "48cff3f16d576a77a993694fb37d7410027daaecc87f3f010f910e2b6111fb05"
)
DATASET_PROTOCOL_SHA256 = (
    "d440ecf75822dcef6c0517402cf3586ae1006452c51f317eb207e89213d8725b"
)
DATASET_COMPONENT_SHA256 = (
    "718167d72b229f1e48af3e81a0835cf367003f81ca433b1bb0eb19035ed5eda0"
)
DATASET_REVIEW_SHA256 = (
    "63cbf24db6d402f2cc88eec6538690e55f6648a0409edf5f2c0c2caa1a2d4169"
)
RANDOM_STATE = 1729
FINAL_DIRECTORY_NAME = "v2_derivatives_context_development_learning_v1"
STAGING_DIRECTORY_NAME = FINAL_DIRECTORY_NAME + ".staging"
REPORT_FILENAME = "kraken_ai_v2_derivatives_context_development_learning_report.json"
REPORT_SHA256_FILENAME = REPORT_FILENAME + ".sha256"
PREDICTIONS_FILENAME = "out_of_fold_predictions.json"
PREDICTIONS_SHA256_FILENAME = PREDICTIONS_FILENAME + ".sha256"
MODEL_DIRECTORY_NAME = "models"
STATUS_REVIEW_REQUIRED = (
    "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_COMPLETED_REVIEW_REQUIRED"
)
STATUS_HOLD = "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_NO_VIABLE_HYPOTHESIS_HOLD_CASH"
STATUS_PASS = "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_HYPOTHESIS_PASS_REVIEW_REQUIRED"
READER_PASS_STATUS = "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_LEARNING_EVIDENCE_READER_PASS"


@dataclass(frozen=True)
class RecordedContextLearningEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    learning_status: str
    labeled_row_count: int
    trained_model_count: int
    out_of_fold_prediction_count: int


def _utc(value):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Context-learning timestamps must be timezone-aware.")
    return timestamp.tz_convert("UTC")


def _json_ready(value):
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Context-learning output cannot contain non-finite values.")
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


def _row_identity_records(table):
    columns = (
        "asset",
        "decision_timestamp",
        "entry_timestamp",
        "event_end_timestamp",
        "label",
        "outcome_net_r",
    )
    return [
        {column: row[column] for column in columns}
        for _, row in table.sort_values(
            ["decision_timestamp", "asset"], kind="stable"
        ).iterrows()
    ]


def _row_identity_sha256(table):
    return hashlib.sha256(canonical_json_bytes(_row_identity_records(table))).hexdigest()


def build_matched_context_learning_table(frames, sources_by_asset):
    """Create one context-complete table shared by all four frozen variants."""

    labeled = build_labeled_learning_data(frames)
    table = labeled.table.copy()
    start = _utc(COMMON_START_UTC)
    end = _utc(COMMON_END_EXCLUSIVE_UTC)
    table = table.loc[
        (table["decision_timestamp"] >= start)
        & (table["decision_timestamp"] < end)
    ].copy()
    decision_indices = {
        asset: pd.DatetimeIndex(
            table.loc[table["asset"] == asset, "decision_timestamp"]
        )
        for asset in ASSET_ORDER
    }
    context = build_derivatives_context_feature_table(
        sources_by_asset, decision_indices
    )
    matched = table.merge(
        context,
        on=["asset", "decision_timestamp"],
        how="inner",
        validate="one_to_one",
        sort=False,
    )
    matched = matched.sort_values(
        ["decision_timestamp", "asset"], kind="stable"
    ).reset_index(drop=True)
    matched = _validate_matched_table(matched)
    diagnostics = {}
    for asset in ASSET_ORDER:
        spot_count = int((table["asset"] == asset).sum())
        context_count = int((matched["asset"] == asset).sum())
        diagnostics[asset] = {
            "common_interval_spot_labeled_rows": spot_count,
            "context_complete_labeled_rows": context_count,
            "rows_removed_by_context_completeness": spot_count - context_count,
        }
    return matched, labeled.diagnostics, diagnostics


def _validate_matched_table(table):
    if not isinstance(table, pd.DataFrame) or table.empty:
        raise ValueError("Matched context learning table must be nonempty.")
    required = {
        "asset",
        "decision_timestamp",
        "entry_timestamp",
        "event_end_timestamp",
        "label",
        "outcome_net_r",
        *SPOT_FEATURE_COLUMNS,
        *CONTEXT_FEATURE_COLUMNS,
    }
    if not required.issubset(table.columns):
        raise ValueError("Matched context learning table schema mismatch.")
    candidate = table.copy()
    for column in ("decision_timestamp", "entry_timestamp", "event_end_timestamp"):
        if not isinstance(candidate[column].dtype, pd.DatetimeTZDtype):
            candidate[column] = pd.to_datetime(candidate[column], utc=True)
        if candidate[column].dt.tz is None:
            raise ValueError(f"{column} must be timezone-aware.")
        candidate[column] = candidate[column].dt.tz_convert("UTC")
    if not set(candidate["asset"]).issubset(set(ASSET_ORDER)):
        raise ValueError("Matched context learning table asset mismatch.")
    if set(candidate["label"]) - set(CLASS_ORDER):
        raise ValueError("Matched context learning table label mismatch.")
    if candidate.duplicated(["asset", "decision_timestamp"]).any():
        raise ValueError("Matched context learning table has duplicate decisions.")
    if (candidate["entry_timestamp"] <= candidate["decision_timestamp"]).any():
        raise ValueError("Matched context learning entries are not causal.")
    if (candidate["event_end_timestamp"] < candidate["entry_timestamp"]).any():
        raise ValueError("Matched context learning outcomes are not causal.")
    start = _utc(COMMON_START_UTC)
    end = _utc(COMMON_END_EXCLUSIVE_UTC)
    if (
        candidate["decision_timestamp"].min() < start
        or candidate["decision_timestamp"].max() >= end
    ):
        raise ValueError("Matched context rows exceed the common Development interval.")
    numeric_columns = [
        *SPOT_FEATURE_COLUMNS,
        *CONTEXT_FEATURE_COLUMNS,
        "outcome_net_r",
    ]
    numeric = candidate[numeric_columns].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Matched context learning values must be finite.")
    candidate.loc[:, numeric_columns] = numeric.astype(float)
    return candidate.sort_values(
        ["decision_timestamp", "asset"], kind="stable"
    ).reset_index(drop=True)


def _feature_names(variant_id):
    names = list(SPOT_FEATURE_COLUMNS)
    if VARIANT_SPECS[variant_id]["feature_set"] == "SPOT_PLUS_DERIVATIVES_CONTEXT":
        names.extend(CONTEXT_FEATURE_COLUMNS)
    return names


def _preprocessor(feature_names):
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]
    )
    return ColumnTransformer(
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


def _pipeline(variant_id, feature_names):
    objective = VARIANT_SPECS[variant_id]["objective"]
    if objective == "CALIBRATED_THREE_CLASS_UTILITY":
        model = HistGradientBoostingClassifier(**CLASSIFIER_PARAMETERS)
    else:
        model = HistGradientBoostingRegressor(**REGRESSOR_PARAMETERS)
    return Pipeline(
        [("preprocessor", _preprocessor(feature_names)), ("model", model)]
    )


def _class_counts(labels):
    observed = pd.Series(labels).value_counts()
    return {label: int(observed.get(label, 0)) for label in CLASS_ORDER}


def _outer_and_inner_slices(table, fold):
    training_end = _utc(fold["training_end_exclusive_utc"])
    validation_start = _utc(fold["validation_start_utc"])
    validation_end = _utc(fold["validation_end_exclusive_utc"])
    outer_training = table.loc[
        (table["decision_timestamp"] < training_end)
        & (table["event_end_timestamp"] < training_end)
    ].copy()
    validation = table.loc[
        (table["decision_timestamp"] >= validation_start)
        & (table["decision_timestamp"] < validation_end)
        & (table["event_end_timestamp"] < validation_end)
    ].copy()
    unique_times = pd.DatetimeIndex(
        outer_training["decision_timestamp"].drop_duplicates().sort_values()
    )
    if len(unique_times) < 8:
        raise ValueError(f"{fold['fold_id']} has insufficient nested-fit timestamps.")
    split = max(1, min(len(unique_times) - 1, int(len(unique_times) * INNER_FIT_FRACTION)))
    inner_boundary = unique_times[split]
    inner_fit = outer_training.loc[
        (outer_training["decision_timestamp"] < inner_boundary)
        & (outer_training["event_end_timestamp"] < inner_boundary)
    ].copy()
    inner_calibration = outer_training.loc[
        (outer_training["decision_timestamp"] >= inner_boundary)
        & (outer_training["event_end_timestamp"] < training_end)
    ].copy()
    for name, frame in (
        ("inner fit", inner_fit),
        ("inner calibration", inner_calibration),
        ("outer validation", validation),
    ):
        counts = _class_counts(frame["label"])
        if min(counts.values(), default=0) < 1:
            raise ValueError(f"{fold['fold_id']} {name} lacks a frozen label class: {counts}.")
    return inner_fit, inner_calibration, validation, inner_boundary


def _aligned_probabilities(estimator, features):
    observed = estimator.predict_proba(features)
    classes = tuple(estimator.named_steps["model"].classes_)
    aligned = np.zeros((len(features), len(CLASS_ORDER)), dtype=float)
    for source_index, label in enumerate(classes):
        aligned[:, CLASS_ORDER.index(label)] = observed[:, source_index]
    return aligned


def _aligned_calibrated_probabilities(calibrator, probabilities):
    logits = np.log(np.clip(probabilities, 1e-9, 1.0))
    observed = calibrator.predict_proba(logits)
    aligned = np.zeros((len(logits), len(CLASS_ORDER)), dtype=float)
    for source_index, label in enumerate(calibrator.classes_):
        aligned[:, CLASS_ORDER.index(label)] = observed[:, source_index]
    return aligned


def _ordered_multiclass_log_loss(labels, probabilities):
    positions = np.asarray([CLASS_ORDER.index(label) for label in labels], dtype=int)
    selected = np.asarray(probabilities, dtype=float)[
        np.arange(len(positions)), positions
    ]
    return float(-np.log(np.clip(selected, 1e-15, 1.0)).mean())


def _fit_predict_variant(variant_id, inner_fit, inner_calibration, validation):
    numeric_features = _feature_names(variant_id)
    feature_names = [*numeric_features, "asset"]
    estimator = _pipeline(variant_id, numeric_features)
    objective = VARIANT_SPECS[variant_id]["objective"]
    if objective == "CALIBRATED_THREE_CLASS_UTILITY":
        estimator.fit(inner_fit[feature_names], inner_fit["label"])
        calibration_probability = _aligned_probabilities(
            estimator, inner_calibration[feature_names]
        )
        calibrator = LogisticRegression(
            C=1.0,
            class_weight=None,
            max_iter=2000,
            random_state=RANDOM_STATE,
        )
        calibrator.fit(
            np.log(np.clip(calibration_probability, 1e-9, 1.0)),
            inner_calibration["label"],
        )
        probability = _aligned_calibrated_probabilities(
            calibrator, _aligned_probabilities(estimator, validation[feature_names])
        )
        score = 3.0 * probability[:, 0] - probability[:, 1]
        target = (validation["label"].to_numpy() == CLASS_ORDER[0]).astype(int)
        predictive = {
            "multiclass_log_loss": _ordered_multiclass_log_loss(
                validation["label"], probability
            ),
            "target_precision_recall_auc": float(
                average_precision_score(target, probability[:, 0])
            ),
            "target_prevalence": float(target.mean()),
            "mean_predicted_net_r": float(score.mean()),
        }
    else:
        estimator.fit(inner_fit[feature_names], inner_fit["outcome_net_r"])
        calibration_prediction = estimator.predict(inner_calibration[feature_names])
        calibrator = LinearRegression()
        calibrator.fit(
            calibration_prediction.reshape(-1, 1),
            inner_calibration["outcome_net_r"].to_numpy(dtype=float),
        )
        score = calibrator.predict(
            estimator.predict(validation[feature_names]).reshape(-1, 1)
        )
        spearman = pd.Series(score).corr(
            pd.Series(validation["outcome_net_r"].to_numpy(dtype=float)),
            method="spearman",
        )
        predictive = {
            "mean_absolute_error_net_r": float(
                mean_absolute_error(validation["outcome_net_r"], score)
            ),
            "prediction_outcome_spearman": (
                float(spearman) if pd.notna(spearman) else None
            ),
            "mean_predicted_net_r": float(score.mean()),
        }
    prediction = validation[
        ["asset", "decision_timestamp", "event_end_timestamp", "label", "outcome_net_r"]
    ].copy()
    prediction["score"] = np.asarray(score, dtype=float)
    prediction["eligible"] = prediction["score"] > 0.0
    artifact = pickle.dumps(
        {
            "variant_id": variant_id,
            "feature_names": feature_names,
            "estimator": estimator,
            "calibrator": calibrator,
        },
        protocol=5,
    )
    return prediction, predictive, artifact


def _summary(frame):
    values = frame["outcome_net_r"].to_numpy(dtype=float)
    count = int(len(frame))
    return {
        "count": count,
        "label_counts": _class_counts(frame["label"]),
        "cumulative_net_r": float(values.sum()),
        "mean_net_r": float(values.mean()) if count else None,
        "median_net_r": float(np.median(values)) if count else None,
        "positive_outcome_count": int((values > 0.0).sum()),
    }


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


def _absolute_review(variant_id, predictions, fold_metadata):
    eligible = predictions.loc[predictions["eligible"]].copy()
    nonoverlap = _nonoverlapping(eligible)
    folds = []
    for fold in FOLD_PLAN:
        fold_id = fold["fold_id"]
        raw_summary = _summary(eligible.loc[eligible["fold_id"] == fold_id])
        separate_summary = _summary(nonoverlap.loc[nonoverlap["fold_id"] == fold_id])
        folds.append(
            {
                **fold_metadata[fold_id],
                "raw_eligible": raw_summary,
                "nonoverlapping_eligible": separate_summary,
                "raw_support_pass": raw_summary["count"]
                >= MINIMUM_RAW_SELECTIONS_PER_FOLD,
                "nonoverlap_support_pass": separate_summary["count"]
                >= MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
                "positive_net_r_pass": (
                    separate_summary["mean_net_r"] is not None
                    and separate_summary["mean_net_r"] > 0.0
                    and separate_summary["cumulative_net_r"] > 0.0
                ),
            }
        )
    assets = []
    for asset in ASSET_ORDER:
        summary = _summary(nonoverlap.loc[nonoverlap["asset"] == asset])
        assets.append(
            {
                "asset": asset,
                "nonoverlapping_eligible": summary,
                "positive_net_r_pass": summary["cumulative_net_r"] > 0.0,
            }
        )
    overall = _summary(nonoverlap)
    gates = {
        "all_fold_raw_support_pass": all(item["raw_support_pass"] for item in folds),
        "all_fold_nonoverlap_support_pass": all(
            item["nonoverlap_support_pass"] for item in folds
        ),
        "all_fold_positive_net_r_pass": all(
            item["positive_net_r_pass"] for item in folds
        ),
        "positive_asset_count": sum(item["positive_net_r_pass"] for item in assets),
        "asset_breadth_pass": sum(item["positive_net_r_pass"] for item in assets)
        >= MINIMUM_POSITIVE_ASSETS,
        "overall_positive_net_r_pass": (
            overall["mean_net_r"] is not None
            and overall["mean_net_r"] > 0.0
            and overall["cumulative_net_r"] > 0.0
        ),
    }
    absolute_pass = all(
        value for key, value in gates.items() if key.endswith("_pass")
    )
    return {
        "variant_id": variant_id,
        "objective": VARIANT_SPECS[variant_id]["objective"],
        "feature_set": VARIANT_SPECS[variant_id]["feature_set"],
        "candidate_eligible": VARIANT_SPECS[variant_id]["candidate_eligible"],
        "folds": folds,
        "assets": assets,
        "raw_eligible_overall": _summary(eligible),
        "nonoverlapping_eligible_overall": overall,
        "absolute_gates": gates,
        "absolute_gates_passed": absolute_pass,
        "incremental_gates": None,
        "development_viable": False,
        "prediction_row_identity_sha256": hashlib.sha256(
            canonical_json_bytes(
                predictions[
                    [
                        "fold_id",
                        "asset",
                        "decision_timestamp",
                        "event_end_timestamp",
                        "label",
                        "outcome_net_r",
                    ]
                ].to_dict("records")
            )
        ).hexdigest(),
    }


def _economic_mean_or_zero(summary):
    return 0.0 if summary["mean_net_r"] is None else summary["mean_net_r"]


def _apply_incremental_gates(reviews):
    registry = {review["variant_id"]: review for review in reviews}
    for context_id, control_id in MATCHED_CONTROL.items():
        if context_id not in registry and control_id not in registry:
            continue
        if context_id not in registry or control_id not in registry:
            raise RuntimeError(f"Incomplete matched review pair for {context_id}.")
        context = registry[context_id]
        control = registry[control_id]
        if context["prediction_row_identity_sha256"] != control["prediction_row_identity_sha256"]:
            raise RuntimeError(f"Matched prediction rows differ for {context_id}.")
        context_overall = _economic_mean_or_zero(
            context["nonoverlapping_eligible_overall"]
        )
        control_overall = _economic_mean_or_zero(
            control["nonoverlapping_eligible_overall"]
        )
        context_worst = min(
            _economic_mean_or_zero(fold["nonoverlapping_eligible"])
            for fold in context["folds"]
        )
        control_worst = min(
            _economic_mean_or_zero(fold["nonoverlapping_eligible"])
            for fold in control["folds"]
        )
        metric = (
            "multiclass_log_loss"
            if context["objective"] == "CALIBRATED_THREE_CLASS_UTILITY"
            else "mean_absolute_error_net_r"
        )
        predictive_fold_wins = sum(
            context_fold["predictive_metrics"][metric]
            < control_fold["predictive_metrics"][metric]
            for context_fold, control_fold in zip(
                context["folds"], control["folds"], strict=True
            )
        )
        incremental = {
            "matched_control": control_id,
            "primary_predictive_metric": metric,
            "overall_mean_net_r": context_overall,
            "control_overall_mean_net_r": control_overall,
            "higher_overall_mean_net_r_pass": context_overall > control_overall,
            "worst_fold_mean_net_r": context_worst,
            "control_worst_fold_mean_net_r": control_worst,
            "higher_worst_fold_mean_net_r_pass": context_worst > control_worst,
            "predictive_fold_win_count": predictive_fold_wins,
            "predictive_fold_wins_pass": predictive_fold_wins
            >= MINIMUM_PREDICTIVE_FOLD_WINS,
        }
        incremental_pass = all(
            value for key, value in incremental.items() if key.endswith("_pass")
        )
        incremental["all_incremental_gates_passed"] = incremental_pass
        context["incremental_gates"] = incremental
        context["development_viable"] = bool(
            context["candidate_eligible"]
            and context["absolute_gates_passed"]
            and incremental_pass
        )
    return reviews


def run_matched_context_experiment(table):
    candidate = _validate_matched_table(table)
    reviews = []
    artifacts = {}
    prediction_frames = []
    shared_fold_identity = {}
    for variant_id in VARIANT_SPECS:
        fold_predictions = []
        fold_metadata = {}
        for fold in FOLD_PLAN:
            inner_fit, inner_calibration, validation, inner_boundary = (
                _outer_and_inner_slices(candidate, fold)
            )
            fold_id = fold["fold_id"]
            validation_identity = _row_identity_sha256(validation)
            previous = shared_fold_identity.setdefault(fold_id, validation_identity)
            if previous != validation_identity:
                raise RuntimeError("Variant validation-row identity mismatch.")
            prediction, predictive, artifact = _fit_predict_variant(
                variant_id, inner_fit, inner_calibration, validation
            )
            prediction["fold_id"] = fold_id
            prediction["variant_id"] = variant_id
            fold_predictions.append(prediction)
            artifact_id = f"{variant_id}|{fold_id}"
            artifacts[artifact_id] = artifact
            fold_metadata[fold_id] = {
                "fold_id": fold_id,
                "inner_boundary_utc": inner_boundary,
                "inner_fit_rows": int(len(inner_fit)),
                "inner_calibration_rows": int(len(inner_calibration)),
                "outer_validation_rows": int(len(validation)),
                "inner_fit_class_counts": _class_counts(inner_fit["label"]),
                "inner_calibration_class_counts": _class_counts(
                    inner_calibration["label"]
                ),
                "outer_validation_class_counts": _class_counts(validation["label"]),
                "validation_row_identity_sha256": validation_identity,
                "predictive_metrics": predictive,
            }
        predictions = pd.concat(fold_predictions, ignore_index=True)
        prediction_frames.append(predictions)
        reviews.append(_absolute_review(variant_id, predictions, fold_metadata))
    reviews = _apply_incremental_gates(reviews)
    passing = [
        review["variant_id"] for review in reviews if review["development_viable"]
    ]
    all_predictions = pd.concat(prediction_frames, ignore_index=True).sort_values(
        ["variant_id", "fold_id", "decision_timestamp", "asset"], kind="stable"
    ).reset_index(drop=True)
    status = STATUS_PASS if passing else STATUS_HOLD
    return {
        "status": status,
        "action": "REVIEW_PASSING_DEVELOPMENT_HYPOTHESES" if passing else "HOLD_CASH",
        "passing_context_hypotheses": passing,
        "automatic_model_selection": False,
        "candidate_v2_authorized": False,
        "variant_reviews": reviews,
        "shared_fold_validation_row_identity_sha256": shared_fold_identity,
    }, all_predictions, artifacts


def _prediction_payload(predictions):
    columns = (
        "variant_id",
        "fold_id",
        "asset",
        "decision_timestamp",
        "event_end_timestamp",
        "label",
        "outcome_net_r",
        "score",
        "eligible",
    )
    return [
        {column: row[column] for column in columns}
        for _, row in predictions.iterrows()
    ]


def _artifact_filename(artifact_id):
    return artifact_id.lower().replace("|", "__") + ".pkl"


def read_context_learning_evidence(evidence_directory):
    root = Path(evidence_directory).resolve()
    report_path = root / REPORT_FILENAME
    sidecar_path = root / REPORT_SHA256_FILENAME
    if not report_path.is_file() or not sidecar_path.is_file():
        raise RuntimeError("Context-learning report lock is incomplete.")
    report_bytes = report_path.read_bytes()
    digest = hashlib.sha256(report_bytes).hexdigest()
    if sidecar_path.read_bytes() != f"{digest}  {REPORT_FILENAME}\n".encode("ascii"):
        raise RuntimeError("Context-learning report sidecar mismatch.")
    report = json.loads(report_bytes)
    if canonical_json_bytes(report) != report_bytes:
        raise RuntimeError("Context-learning report is not canonical JSON.")
    if report.get("protocol_id") != PROTOCOL_ID or report.get("run_id") != RUN_ID:
        raise RuntimeError("Context-learning report identity mismatch.")
    prediction = report.get("prediction_artifact", {})
    prediction_path = root / prediction.get("path", "")
    prediction_sidecar = root / prediction.get("checksum_path", "")
    if not prediction_path.is_file() or not prediction_sidecar.is_file():
        raise RuntimeError("Context-learning prediction artifact is incomplete.")
    prediction_bytes = prediction_path.read_bytes()
    prediction_digest = hashlib.sha256(prediction_bytes).hexdigest()
    if (
        prediction_digest != prediction.get("sha256")
        or len(prediction_bytes) != prediction.get("bytes")
        or prediction_sidecar.read_bytes()
        != f"{prediction_digest}  {PREDICTIONS_FILENAME}\n".encode("ascii")
    ):
        raise RuntimeError("Context-learning prediction artifact mismatch.")
    for artifact in report.get("model_artifacts", []):
        path = root / artifact["path"]
        if (
            not path.is_file()
            or path.stat().st_size != artifact["bytes"]
            or _sha256(path) != artifact["sha256"]
        ):
            raise RuntimeError(f"Context-learning model artifact mismatch: {artifact['artifact_id']}.")
    if len(report.get("model_artifacts", [])) != len(VARIANT_SPECS) * len(FOLD_PLAN):
        raise RuntimeError("Context-learning model artifact count mismatch.")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": READER_PASS_STATUS,
        "report_sha256": digest,
        "learning_status": report["learning_status"],
        "action": report["action"],
        "trained_model_count": report["trained_model_count"],
        "out_of_fold_prediction_count": report["out_of_fold_prediction_count"],
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "real_orders_submitted": False,
    }


class KrakenAIDrivenV2DerivativesContextDevelopmentLearningRunner:
    @staticmethod
    def _external_paths(archive_path, context_lock, evidence_root):
        project_root = Path(__file__).resolve().parents[1]
        paths = tuple(Path(path).resolve() for path in (archive_path, context_lock, evidence_root))
        for path in paths:
            if path == project_root or path.is_relative_to(project_root):
                raise ValueError("Learning inputs and evidence must remain outside the repository.")
        if paths[0] == paths[1] or paths[2] in paths[:2]:
            raise ValueError("Learning archive, context lock and evidence root must be distinct.")
        return paths

    @staticmethod
    def _assert_one_shot(evidence_root):
        final = evidence_root / FINAL_DIRECTORY_NAME
        staging = evidence_root / STAGING_DIRECTORY_NAME
        if final.exists():
            raise FileExistsError("Context-learning evidence already exists; refusing repeat.")
        if staging.exists():
            raise FileExistsError("Incomplete context-learning staging evidence exists.")
        return final, staging

    def run(self, archive_path, context_lock, evidence_root, authorization_phrase):
        if authorization_phrase != AUTHORIZATION_PHRASE:
            raise PermissionError("Exact one-shot context-learning authorization phrase is required.")
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
        table, label_diagnostics, context_diagnostics = (
            build_matched_context_learning_table(frames, sources)
        )
        experiment, predictions, artifacts = run_matched_context_experiment(table)
        if len(artifacts) != len(VARIANT_SPECS) * len(FOLD_PLAN):
            raise RuntimeError("Frozen context-learning model count mismatch.")

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
            "learning_status": experiment["status"],
            "action": experiment["action"],
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
            "class_order": list(CLASS_ORDER),
            "spot_feature_columns": list(SPOT_FEATURE_COLUMNS),
            "context_feature_columns": list(CONTEXT_FEATURE_COLUMNS),
            "variant_order": list(VARIANT_SPECS),
            "matched_control": dict(MATCHED_CONTROL),
            "fold_plan": [dict(fold) for fold in FOLD_PLAN],
            "matched_learning_table_identity_sha256": _row_identity_sha256(table),
            "labeled_row_count": int(len(table)),
            "spot_label_diagnostics": label_diagnostics,
            "context_completeness_diagnostics": context_diagnostics,
            "shared_fold_validation_row_identity_sha256": experiment[
                "shared_fold_validation_row_identity_sha256"
            ],
            "variant_reviews": experiment["variant_reviews"],
            "passing_context_hypotheses": experiment["passing_context_hypotheses"],
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
            "context_dataset_opened": True,
            "development_data_opened": True,
            "labels_generated": True,
            "model_training_authorized": True,
            "model_training_executed": True,
            "hyperparameter_sweep_executed": False,
            "threshold_sweep_executed": False,
            "automatic_model_selection": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
            "next_stage": "RUN_INDEPENDENT_READ_ONLY_CONTEXT_LEARNING_EVIDENCE_REVIEW",
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
            (staging / artifact["path"]).write_bytes(artifacts[artifact["artifact_id"]])
        os.replace(staging, final)
        locked = read_context_learning_evidence(final)
        return RecordedContextLearningEvidence(
            report_path=final / REPORT_FILENAME,
            checksum_path=final / REPORT_SHA256_FILENAME,
            report_sha256=locked["report_sha256"],
            learning_status=locked["learning_status"],
            labeled_row_count=int(len(table)),
            trained_model_count=len(model_manifest),
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
        "spot_feature_count": len(SPOT_FEATURE_COLUMNS),
        "context_feature_count": len(CONTEXT_FEATURE_COLUMNS),
        "variant_order": list(VARIANT_SPECS),
        "matched_control": dict(MATCHED_CONTROL),
        "maximum_fold_model_fits": len(VARIANT_SPECS) * len(FOLD_PLAN),
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "hypothesis_protocol_sha256": HYPOTHESIS_PROTOCOL_SHA256,
        "hypothesis_component_sha256": HYPOTHESIS_COMPONENT_SHA256,
        "hypothesis_review_sha256": HYPOTHESIS_REVIEW_SHA256,
        "dataset_protocol_sha256": DATASET_PROTOCOL_SHA256,
        "dataset_component_sha256": DATASET_COMPONENT_SHA256,
        "dataset_review_sha256": DATASET_REVIEW_SHA256,
        "dataset_result_document_sha256": DATASET_RESULT_DOCUMENT_SHA256,
        "windows_sidecar_incident_sha256": WINDOWS_SIDECAR_INCIDENT_SHA256,
        "canonical_binary_lf_sidecars_implemented": True,
        "identical_context_complete_rows_implemented": True,
        "absolute_and_incremental_gates_implemented": True,
        "real_model_artifact_persistence_implemented": True,
        "out_of_fold_prediction_artifact_implemented": True,
        "one_shot_atomic_evidence_implemented": True,
        "independent_evidence_reader_implemented": True,
        "network_download_authorized": False,
        "source_archive_opened": False,
        "context_dataset_opened": False,
        "development_data_opened": False,
        "labels_generated": False,
        "model_training_authorized": False,
        "model_training_executed": False,
        "hyperparameter_sweep_authorized": False,
        "threshold_sweep_authorized": False,
        "automatic_model_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_RUNNER_REVIEW_REQUIRED",
        "next_stage": "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_CONTEXT_DEVELOPMENT_LEARNING_RUN",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Execute or review frozen derivatives-context Development learning."
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
        result = read_context_learning_evidence(args.review_evidence)
    elif all(
        (
            args.complete_archive,
            args.context_lock,
            args.evidence_root,
            args.authorization_phrase,
        )
    ):
        recorded = KrakenAIDrivenV2DerivativesContextDevelopmentLearningRunner().run(
            args.complete_archive,
            args.context_lock,
            args.evidence_root,
            args.authorization_phrase,
        )
        result = {
            "status": "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_EVIDENCE_RECORDED",
            "learning_status": recorded.learning_status,
            "report_path": str(recorded.report_path),
            "checksum_path": str(recorded.checksum_path),
            "report_sha256": recorded.report_sha256,
            "labeled_row_count": recorded.labeled_row_count,
            "trained_model_count": recorded.trained_model_count,
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
