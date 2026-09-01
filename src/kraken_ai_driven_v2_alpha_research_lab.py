"""Bounded six-variant Alpha Research Lab for Kraken AI-driven V2."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesClassifier,
    ExtraTreesRegressor,
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import average_precision_score, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from kraken_ai_driven_v2_learning_core import (
        ASSET_ORDER,
        CLASS_ORDER,
        FEATURE_COLUMNS,
        FOLD_PLAN,
        build_labeled_learning_data,
        _validate_learning_table,
    )
    from kraken_ai_driven_v2_12h_development_learning_runner import (
        FROZEN_COMPLETE_ARCHIVE_SPEC,
        KrakenAIDrivenV212hDevelopmentLearningRunner,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_learning_core import (
        ASSET_ORDER,
        CLASS_ORDER,
        FEATURE_COLUMNS,
        FOLD_PLAN,
        build_labeled_learning_data,
        _validate_learning_table,
    )
    from .kraken_ai_driven_v2_12h_development_learning_runner import (
        FROZEN_COMPLETE_ARCHIVE_SPEC,
        KrakenAIDrivenV212hDevelopmentLearningRunner,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-alpha-research-lab-v1"
COMPONENT_ID = "kraken-ai-v2-alpha-research-lab-v1"
PARENT_COMMIT = "dd7735ffbc3f35999c38f29b7b1cc38a22b3f46e"
V1_LEARNING_REPORT_SHA256 = (
    "30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf"
)
V1_ECONOMIC_STATUS = "KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_REVIEW_HOLD_CASH"
RANDOM_STATE = 1729
INNER_FIT_FRACTION = 0.75
MINIMUM_INNER_FIT_CLASS_COUNT = 30
MINIMUM_INNER_CALIBRATION_CLASS_COUNT = 10
MINIMUM_RAW_SELECTIONS_PER_FOLD = 30
MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD = 10
MINIMUM_POSITIVE_ASSETS = 2
RESULT_STATUS_PASS = "KRAKEN_AI_V2_ALPHA_RESEARCH_LAB_DEVELOPMENT_WINNER_REVIEW_REQUIRED"
RESULT_STATUS_HOLD = "KRAKEN_AI_V2_ALPHA_RESEARCH_LAB_NO_VIABLE_VARIANT_HOLD_CASH"


VARIANT_SPECS = {
    "NATURAL_LOGISTIC_CLASSIFIER": {
        "objective": "CALIBRATED_THREE_CLASS_UTILITY",
        "model_family": "MULTINOMIAL_LOGISTIC_REGRESSION",
        "parameters": {"C": 1.0, "class_weight": None, "max_iter": 2000},
    },
    "HIST_GBT_CLASSIFIER": {
        "objective": "CALIBRATED_THREE_CLASS_UTILITY",
        "model_family": "HISTOGRAM_GRADIENT_BOOSTING_CLASSIFIER",
        "parameters": {
            "learning_rate": 0.05,
            "max_leaf_nodes": 15,
            "max_iter": 200,
            "min_samples_leaf": 30,
            "l2_regularization": 1.0,
        },
    },
    "EXTRA_TREES_CLASSIFIER": {
        "objective": "CALIBRATED_THREE_CLASS_UTILITY",
        "model_family": "EXTRA_TREES_CLASSIFIER",
        "parameters": {
            "n_estimators": 120,
            "min_samples_leaf": 20,
            "max_features": 0.75,
            "class_weight": None,
        },
    },
    "RIDGE_NET_R_REGRESSOR": {
        "objective": "DIRECT_EXPECTED_NET_R",
        "model_family": "RIDGE_REGRESSION",
        "parameters": {"alpha": 10.0},
    },
    "HIST_GBT_NET_R_REGRESSOR": {
        "objective": "DIRECT_EXPECTED_NET_R",
        "model_family": "HISTOGRAM_GRADIENT_BOOSTING_REGRESSOR",
        "parameters": {
            "learning_rate": 0.05,
            "max_leaf_nodes": 15,
            "max_iter": 200,
            "min_samples_leaf": 30,
            "l2_regularization": 1.0,
        },
    },
    "EXTRA_TREES_NET_R_REGRESSOR": {
        "objective": "DIRECT_EXPECTED_NET_R",
        "model_family": "EXTRA_TREES_REGRESSOR",
        "parameters": {
            "n_estimators": 120,
            "min_samples_leaf": 20,
            "max_features": 0.75,
        },
    },
}


def _utc(value):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Alpha Research Lab timestamps must be timezone-aware.")
    return timestamp.tz_convert("UTC")


def _json_ready(value):
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Alpha Research Lab output cannot contain non-finite values.")
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


def _preprocessor():
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, list(FEATURE_COLUMNS)),
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


def _base_model(variant_id):
    parameters = dict(VARIANT_SPECS[variant_id]["parameters"])
    if variant_id == "NATURAL_LOGISTIC_CLASSIFIER":
        return LogisticRegression(random_state=RANDOM_STATE, **parameters)
    if variant_id == "HIST_GBT_CLASSIFIER":
        return HistGradientBoostingClassifier(
            random_state=RANDOM_STATE, early_stopping=False, **parameters
        )
    if variant_id == "EXTRA_TREES_CLASSIFIER":
        return ExtraTreesClassifier(
            random_state=RANDOM_STATE, n_jobs=1, **parameters
        )
    if variant_id == "RIDGE_NET_R_REGRESSOR":
        return Ridge(**parameters)
    if variant_id == "HIST_GBT_NET_R_REGRESSOR":
        return HistGradientBoostingRegressor(
            random_state=RANDOM_STATE, early_stopping=False, **parameters
        )
    if variant_id == "EXTRA_TREES_NET_R_REGRESSOR":
        return ExtraTreesRegressor(
            random_state=RANDOM_STATE, n_jobs=1, **parameters
        )
    raise ValueError(f"Unknown Alpha Research Lab variant: {variant_id}.")


def _pipeline(variant_id):
    return Pipeline([("preprocessor", _preprocessor()), ("model", _base_model(variant_id))])


def _aligned_probabilities(estimator, features):
    observed = estimator.predict_proba(features)
    classes = tuple(estimator.named_steps["model"].classes_)
    aligned = np.zeros((len(features), len(CLASS_ORDER)), dtype=float)
    for source_index, label in enumerate(classes):
        aligned[:, CLASS_ORDER.index(label)] = observed[:, source_index]
    return aligned


def _aligned_calibrated_probabilities(calibrator, base_probabilities):
    logits = np.log(np.clip(base_probabilities, 1e-9, 1.0))
    observed = calibrator.predict_proba(logits)
    aligned = np.zeros((len(logits), len(CLASS_ORDER)), dtype=float)
    for source_index, label in enumerate(calibrator.classes_):
        aligned[:, CLASS_ORDER.index(label)] = observed[:, source_index]
    return aligned


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
    unique_timestamps = pd.DatetimeIndex(
        outer_training["decision_timestamp"].drop_duplicates().sort_values()
    )
    if len(unique_timestamps) < 8:
        raise ValueError(f"{fold['fold_id']} has insufficient timestamps for nested learning.")
    split_index = max(1, min(len(unique_timestamps) - 1, int(len(unique_timestamps) * INNER_FIT_FRACTION)))
    inner_boundary = unique_timestamps[split_index]
    inner_fit = outer_training.loc[
        (outer_training["decision_timestamp"] < inner_boundary)
        & (outer_training["event_end_timestamp"] < inner_boundary)
    ].copy()
    inner_calibration = outer_training.loc[
        (outer_training["decision_timestamp"] >= inner_boundary)
        & (outer_training["event_end_timestamp"] < training_end)
    ].copy()
    for name, frame, minimum in (
        ("inner fit", inner_fit, MINIMUM_INNER_FIT_CLASS_COUNT),
        ("inner calibration", inner_calibration, MINIMUM_INNER_CALIBRATION_CLASS_COUNT),
        ("outer validation", validation, MINIMUM_INNER_CALIBRATION_CLASS_COUNT),
    ):
        counts = _class_counts(frame["label"])
        if min(counts.values(), default=0) < minimum:
            raise ValueError(
                f"{fold['fold_id']} {name} class support is insufficient: {counts}."
            )
    return inner_fit, inner_calibration, validation, inner_boundary


def _fit_predict_variant(variant_id, inner_fit, inner_calibration, validation):
    feature_names = [*FEATURE_COLUMNS, "asset"]
    objective = VARIANT_SPECS[variant_id]["objective"]
    estimator = _pipeline(variant_id)
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
            calibrator,
            _aligned_probabilities(estimator, validation[feature_names]),
        )
        score = 3.0 * probability[:, 0] - probability[:, 1]
        actual_target = (validation["label"].to_numpy() == CLASS_ORDER[0]).astype(int)
        predictive = {
            "target_prevalence": float(actual_target.mean()),
            "target_precision_recall_auc": float(
                average_precision_score(actual_target, probability[:, 0])
            ),
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
            "mean_predicted_net_r": float(score.mean()),
            "prediction_outcome_spearman": (
                float(spearman) if pd.notna(spearman) else None
            ),
        }
    prediction = validation[
        ["asset", "decision_timestamp", "event_end_timestamp", "label", "outcome_net_r"]
    ].copy()
    prediction["score"] = np.asarray(score, dtype=float)
    prediction["eligible"] = prediction["score"] > 0.0
    return prediction, predictive


def _summary(frame):
    values = frame["outcome_net_r"].to_numpy(dtype=float)
    counts = _class_counts(frame["label"])
    count = int(len(frame))
    return {
        "count": count,
        "label_counts": counts,
        "cumulative_net_r": float(values.sum()),
        "mean_net_r": float(values.mean()) if count else None,
        "median_net_r": float(np.median(values)) if count else None,
        "positive_outcome_count": int((values > 0.0).sum()),
    }


def _nonoverlapping(frame):
    selected_indices = []
    busy_until = {}
    ordered = frame.sort_values(["decision_timestamp", "asset"], kind="stable")
    for index, row in ordered.iterrows():
        asset = row["asset"]
        if asset not in busy_until or row["decision_timestamp"] >= busy_until[asset]:
            selected_indices.append(index)
            busy_until[asset] = row["event_end_timestamp"]
    return frame.loc[selected_indices].sort_values(
        ["decision_timestamp", "asset"], kind="stable"
    )


def _variant_review(variant_id, predictions, fold_metadata):
    eligible = predictions.loc[predictions["eligible"]].copy()
    nonoverlap = _nonoverlapping(eligible)
    fold_reviews = []
    for fold in FOLD_PLAN:
        fold_id = fold["fold_id"]
        raw = eligible.loc[eligible["fold_id"] == fold_id]
        separate = nonoverlap.loc[nonoverlap["fold_id"] == fold_id]
        raw_summary = _summary(raw)
        separate_summary = _summary(separate)
        fold_reviews.append(
            {
                **fold_metadata[fold_id],
                "raw_eligible": raw_summary,
                "nonoverlapping_eligible": separate_summary,
                "raw_support_pass": raw_summary["count"] >= MINIMUM_RAW_SELECTIONS_PER_FOLD,
                "nonoverlap_support_pass": separate_summary["count"]
                >= MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
                "positive_net_r_pass": (
                    separate_summary["mean_net_r"] is not None
                    and separate_summary["mean_net_r"] > 0.0
                    and separate_summary["cumulative_net_r"] > 0.0
                ),
            }
        )
    asset_reviews = []
    for asset in ASSET_ORDER:
        summary = _summary(nonoverlap.loc[nonoverlap["asset"] == asset])
        asset_reviews.append(
            {
                "asset": asset,
                "nonoverlapping_eligible": summary,
                "positive_net_r_pass": summary["cumulative_net_r"] > 0.0,
            }
        )
    overall = _summary(nonoverlap)
    gates = {
        "all_fold_raw_support_pass": all(item["raw_support_pass"] for item in fold_reviews),
        "all_fold_nonoverlap_support_pass": all(
            item["nonoverlap_support_pass"] for item in fold_reviews
        ),
        "all_fold_positive_net_r_pass": all(
            item["positive_net_r_pass"] for item in fold_reviews
        ),
        "positive_asset_count": sum(item["positive_net_r_pass"] for item in asset_reviews),
        "asset_breadth_pass": sum(item["positive_net_r_pass"] for item in asset_reviews)
        >= MINIMUM_POSITIVE_ASSETS,
        "overall_positive_net_r_pass": (
            overall["mean_net_r"] is not None
            and overall["mean_net_r"] > 0.0
            and overall["cumulative_net_r"] > 0.0
        ),
    }
    viable = all(value for key, value in gates.items() if key.endswith("_pass"))
    identity_records = [
        {
            "fold_id": row["fold_id"],
            "asset": row["asset"],
            "decision_timestamp": row["decision_timestamp"],
            "event_end_timestamp": row["event_end_timestamp"],
            "score": row["score"],
            "eligible": bool(row["eligible"]),
            "actual_label": row["label"],
            "actual_outcome_net_r": row["outcome_net_r"],
        }
        for _, row in predictions.sort_values(
            ["fold_id", "decision_timestamp", "asset"], kind="stable"
        ).iterrows()
    ]
    return {
        "variant_id": variant_id,
        "objective": VARIANT_SPECS[variant_id]["objective"],
        "model_family": VARIANT_SPECS[variant_id]["model_family"],
        "parameters": VARIANT_SPECS[variant_id]["parameters"],
        "folds": fold_reviews,
        "assets": asset_reviews,
        "raw_eligible_overall": _summary(eligible),
        "nonoverlapping_eligible_overall": overall,
        "gates": gates,
        "development_viable": viable,
        "prediction_identity_sha256": hashlib.sha256(
            canonical_json_bytes(identity_records)
        ).hexdigest(),
    }


def run_alpha_research_lab(table):
    candidate = _validate_learning_table(table)
    variant_reviews = []
    for variant_id in VARIANT_SPECS:
        fold_predictions = []
        fold_metadata = {}
        for fold in FOLD_PLAN:
            inner_fit, inner_calibration, validation, inner_boundary = _outer_and_inner_slices(
                candidate, fold
            )
            prediction, predictive = _fit_predict_variant(
                variant_id, inner_fit, inner_calibration, validation
            )
            fold_id = fold["fold_id"]
            prediction["fold_id"] = fold_id
            fold_predictions.append(prediction)
            fold_metadata[fold_id] = {
                "fold_id": fold_id,
                "inner_boundary_utc": inner_boundary,
                "inner_fit_rows": int(len(inner_fit)),
                "inner_calibration_rows": int(len(inner_calibration)),
                "outer_validation_rows": int(len(validation)),
                "inner_fit_class_counts": _class_counts(inner_fit["label"]),
                "inner_calibration_class_counts": _class_counts(inner_calibration["label"]),
                "outer_validation_class_counts": _class_counts(validation["label"]),
                "predictive_metrics": predictive,
            }
        predictions = pd.concat(fold_predictions, ignore_index=True)
        variant_reviews.append(
            _variant_review(variant_id, predictions, fold_metadata)
        )

    viable = [review for review in variant_reviews if review["development_viable"]]
    selected = None
    if viable:
        registry_order = {variant_id: index for index, variant_id in enumerate(VARIANT_SPECS)}

        def rank_key(review):
            worst_fold = min(
                fold["nonoverlapping_eligible"]["mean_net_r"]
                for fold in review["folds"]
            )
            overall = review["nonoverlapping_eligible_overall"]["mean_net_r"]
            return (worst_fold, overall, -registry_order[review["variant_id"]])

        selected = max(viable, key=rank_key)["variant_id"]
    status = RESULT_STATUS_PASS if selected else RESULT_STATUS_HOLD
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "v1_learning_report_sha256": V1_LEARNING_REPORT_SHA256,
        "v1_economic_status": V1_ECONOMIC_STATUS,
        "status": status,
        "action": "REVIEW_FROZEN_DEVELOPMENT_WINNER" if selected else "HOLD_CASH",
        "experiment_budget": 6,
        "executed_variant_count": len(variant_reviews),
        "variant_order": list(VARIANT_SPECS),
        "selected_development_variant": selected,
        "automatic_candidate_promotion": False,
        "candidate_v2_authorized": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "variant_reviews": variant_reviews,
        "next_stage": (
            "FREEZE_DEVELOPMENT_WINNER_BEFORE_CALIBRATION_DECISION"
            if selected
            else "CLOSE_12H_OHLCV_HYPOTHESIS_HOLD_CASH"
        ),
    }


def alpha_research_lab_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "active_resolution": "12h",
        "partition": "DEVELOPMENT",
        "asset_order": list(ASSET_ORDER),
        "feature_count": len(FEATURE_COLUMNS),
        "objective_order": ["CALIBRATED_THREE_CLASS_UTILITY", "DIRECT_EXPECTED_NET_R"],
        "variant_order": list(VARIANT_SPECS),
        "experiment_budget": 6,
        "inner_fit_fraction": INNER_FIT_FRACTION,
        "v1_learning_report_sha256": V1_LEARNING_REPORT_SHA256,
        "v1_economic_status": V1_ECONOMIC_STATUS,
        "development_data_opened": False,
        "model_training_executed": False,
        "hyperparameter_sweep_authorized": False,
        "threshold_sweep_authorized": False,
        "automatic_candidate_promotion": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": "KRAKEN_AI_V2_ALPHA_RESEARCH_LAB_FROZEN_IMPLEMENTATION_REVIEW_REQUIRED",
    }


class KrakenAIDrivenV2AlphaResearchLab:
    def run_archive(self, archive_path, result_path):
        project_root = Path(__file__).resolve().parents[1]
        archive_path = Path(archive_path).resolve()
        result_path = Path(result_path).resolve()
        if result_path == project_root or result_path.is_relative_to(project_root):
            raise ValueError("Alpha Research Lab result must remain outside the repository.")
        if result_path.exists():
            raise FileExistsError("Alpha Research Lab result path already exists.")
        frames, member_evidence = (
            KrakenAIDrivenV212hDevelopmentLearningRunner()._load_frames(archive_path)
        )
        labeled = build_labeled_learning_data(frames)
        result = run_alpha_research_lab(labeled.table)
        result.update(
            {
                "development_data_opened": True,
                "model_training_executed": True,
                "source_archive_sha256": FROZEN_COMPLETE_ARCHIVE_SPEC["sha256"],
                "source_member_evidence": member_evidence,
                "labeled_row_count": int(len(labeled.table)),
                "label_diagnostics": labeled.diagnostics,
                "calibration_data_opened": False,
                "evaluation_data_opened": False,
                "candidate_v2_authorized": False,
                "bounded_forward_paper_authorized": False,
                "cloud_execution_authorized": False,
                "real_orders_submitted": False,
                "live_execution_authorized": False,
            }
        )
        payload = canonical_json_bytes(result)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        staging = result_path.with_name(result_path.name + ".staging")
        if staging.exists():
            raise FileExistsError("Alpha Research Lab staging result already exists.")
        staging.write_bytes(payload)
        os.replace(staging, result_path)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kraken AI-driven V2 Alpha Research Lab.")
    parser.add_argument("--complete-archive", type=Path)
    parser.add_argument("--result-path", type=Path)
    args = parser.parse_args(argv)
    if bool(args.complete_archive) != bool(args.result_path):
        parser.error("--complete-archive and --result-path must be supplied together.")
    result = (
        KrakenAIDrivenV2AlphaResearchLab().run_archive(
            args.complete_archive, args.result_path
        )
        if args.complete_archive
        else alpha_research_lab_declaration()
    )
    print(json.dumps(_json_ready(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
