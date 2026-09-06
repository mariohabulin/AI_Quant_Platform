"""Hash-bound bidirectional Development learning runner V1."""

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
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from kraken_ai_driven_v2_12h_development_learning_runner import (
        FROZEN_COMPLETE_ARCHIVE_SPEC,
        KrakenAIDrivenV212hDevelopmentLearningRunner,
    )
    from kraken_ai_driven_v2_bidirectional_hypothesis import (
        ALL_NUMERIC_FEATURE_COLUMNS,
        ASSET_ORDER,
        CONTEXT_FEATURE_COLUMNS,
        DIRECTION_ORDER,
        FOLD_PLAN,
        MATCHED_CONTROL,
        MINIMUM_CONTEXT_FOLD_WINS,
        MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        MINIMUM_POSITIVE_ASSETS,
        MINIMUM_RAW_SELECTIONS_PER_FOLD,
        REGRESSOR_PARAMETERS,
        SPOT_FEATURE_COLUMNS,
        VARIANT_SPECS,
        build_directional_outcome_pair,
        select_bidirectional_action,
    )
    from kraken_ai_driven_v2_derivatives_context_dataset import (
        ATTEMPT_4_MANIFEST_SHA256,
        read_locked_derivatives_context_dataset,
    )
    from kraken_ai_driven_v2_derivatives_context_hypothesis import (
        COMMON_END_EXCLUSIVE_UTC,
        COMMON_START_UTC,
        build_derivatives_context_feature_table,
    )
    from kraken_ai_driven_v2_learning_core import (
        CLASS_ORDER,
        build_causal_feature_table,
        validate_development_frames,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_12h_development_learning_runner import (
        FROZEN_COMPLETE_ARCHIVE_SPEC,
        KrakenAIDrivenV212hDevelopmentLearningRunner,
    )
    from .kraken_ai_driven_v2_bidirectional_hypothesis import (
        ALL_NUMERIC_FEATURE_COLUMNS,
        ASSET_ORDER,
        CONTEXT_FEATURE_COLUMNS,
        DIRECTION_ORDER,
        FOLD_PLAN,
        MATCHED_CONTROL,
        MINIMUM_CONTEXT_FOLD_WINS,
        MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        MINIMUM_POSITIVE_ASSETS,
        MINIMUM_RAW_SELECTIONS_PER_FOLD,
        REGRESSOR_PARAMETERS,
        SPOT_FEATURE_COLUMNS,
        VARIANT_SPECS,
        build_directional_outcome_pair,
        select_bidirectional_action,
    )
    from .kraken_ai_driven_v2_derivatives_context_dataset import (
        ATTEMPT_4_MANIFEST_SHA256,
        read_locked_derivatives_context_dataset,
    )
    from .kraken_ai_driven_v2_derivatives_context_hypothesis import (
        COMMON_END_EXCLUSIVE_UTC,
        COMMON_START_UTC,
        build_derivatives_context_feature_table,
    )
    from .kraken_ai_driven_v2_learning_core import (
        CLASS_ORDER,
        build_causal_feature_table,
        validate_development_frames,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-v2-bidirectional-development-learning-runner-v1"
)
RUN_ID = "kraken-ai-v2-bidirectional-development-learning-v1"
COMPONENT_ID = "kraken-ai-v2-bidirectional-development-learning-runner-v1"
PARENT_COMMIT = "82ea7f12d8786d6d5ed1d6fa49e57da34d73b9fe"
AUTHORIZATION_PHRASE = (
    "EXECUTE_KRAKEN_AI_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_ONCE"
)

DATASET_MANIFEST_SHA256 = (
    "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916"
)
SOURCE_BINDING_SHA256 = {
    "learning_core_component": (
        "467f2a1913371ef11c9a828770bb6a260708032a9ba2aec142d88cfe7ab79207"
    ),
    "spot_reader_component": (
        "8cbeb478b2d78bccbe33ebb96ab8a1e2838492b10f52e7e42b363c1c9e545082"
    ),
    "context_feature_component": (
        "5355bb5d8e672d539776fc88705f2864b4974a767b12aaabfd4615aeb42288b3"
    ),
    "dataset_protocol": (
        "d440ecf75822dcef6c0517402cf3586ae1006452c51f317eb207e89213d8725b"
    ),
    "dataset_component": (
        "718167d72b229f1e48af3e81a0835cf367003f81ca433b1bb0eb19035ed5eda0"
    ),
    "dataset_review": (
        "63cbf24db6d402f2cc88eec6538690e55f6648a0409edf5f2c0c2caa1a2d4169"
    ),
    "dataset_result": (
        "753ff82a36d93382eed5ead23ecabbd884e850dd6ac72f3e2728df32d8c33922"
    ),
    "bidirectional_protocol": (
        "66e58f29c848f3843b4c07df2d42f194e15aebda4ad1ae9c49b755e6ace199dd"
    ),
    "bidirectional_component": (
        "68e9a61e0614e7159a2f5279e4158bc9a6c781c61061b5458a67ff9dd8d8a80c"
    ),
    "bidirectional_review": (
        "ee091037ca66b286291afcfe729ea543102a2c20a76136da5cb846ed49402c31"
    ),
    "context_forensic_result": (
        "4898f0cd92f54af92047753f3afede8d36031ed4f9d36667cf68c483de7fed6a"
    ),
}

FINAL_DIRECTORY_NAME = "v2_bidirectional_development_learning_v1"
STAGING_DIRECTORY_NAME = FINAL_DIRECTORY_NAME + ".staging"
REPORT_FILENAME = "kraken_ai_v2_bidirectional_development_learning_report.json"
REPORT_SHA256_FILENAME = REPORT_FILENAME + ".sha256"
PREDICTIONS_FILENAME = "out_of_fold_predictions.json"
PREDICTIONS_SHA256_FILENAME = PREDICTIONS_FILENAME + ".sha256"
MODEL_DIRECTORY_NAME = "models"
STATUS_REVIEW_REQUIRED = (
    "KRAKEN_AI_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_COMPLETED_REVIEW_REQUIRED"
)
STATUS_HOLD = "KRAKEN_AI_V2_BIDIRECTIONAL_NO_VIABLE_HYPOTHESIS_HOLD_CASH"
STATUS_PASS = "KRAKEN_AI_V2_BIDIRECTIONAL_HYPOTHESIS_PASS_REVIEW_REQUIRED"
READER_PASS_STATUS = "KRAKEN_AI_V2_BIDIRECTIONAL_LEARNING_EVIDENCE_READER_PASS"


@dataclass(frozen=True)
class RecordedBidirectionalLearningEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    learning_status: str
    labeled_decision_count: int
    trained_model_count: int
    out_of_fold_prediction_count: int


def _utc(value):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Bidirectional timestamps must be timezone-aware.")
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
            raise ValueError("Bidirectional evidence cannot contain non-finite values.")
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


def _identity_records(table):
    columns = (
        "asset",
        "decision_timestamp",
        "entry_timestamp",
        "long_event_end_timestamp",
        "short_event_end_timestamp",
        "long_label",
        "short_label",
        "long_outcome_net_r",
        "short_outcome_net_r",
    )
    ordered = table.sort_values(["decision_timestamp", "asset"], kind="stable")
    return [
        {column: row[column] for column in columns}
        for _, row in ordered.iterrows()
    ]


def _identity_sha256(table):
    return hashlib.sha256(canonical_json_bytes(_identity_records(table))).hexdigest()


def build_bidirectional_context_learning_table(frames, sources_by_asset):
    """Build one paired-outcome, context-complete Development table."""

    validated = validate_development_frames(frames)
    features = build_causal_feature_table(validated)
    start = _utc(COMMON_START_UTC)
    end = _utc(COMMON_END_EXCLUSIVE_UTC)
    features = features.loc[
        (features["decision_timestamp"] >= start)
        & (features["decision_timestamp"] < end)
    ].copy()
    positions = {
        asset: {timestamp: number for number, timestamp in enumerate(frame.index)}
        for asset, frame in validated.items()
    }
    diagnostics = {
        asset: {
            "common_interval_feature_rows": 0,
            "paired_labeled_decisions": 0,
            "context_complete_decisions": 0,
            "invalid_reason_counts": {direction: {} for direction in DIRECTION_ORDER},
            "label_counts": {
                direction: {label: 0 for label in CLASS_ORDER}
                for direction in DIRECTION_ORDER
            },
        }
        for asset in ASSET_ORDER
    }
    rows = []
    for feature_row in features.to_dict("records"):
        asset = feature_row["asset"]
        diagnostics[asset]["common_interval_feature_rows"] += 1
        timestamp = feature_row["decision_timestamp"]
        outcomes = build_directional_outcome_pair(
            validated[asset],
            decision_position=positions[asset][timestamp],
            signal_atr=feature_row["signal_atr_14"],
        )
        invalid = False
        for direction, outcome in outcomes.items():
            if not outcome.valid:
                counts = diagnostics[asset]["invalid_reason_counts"][direction]
                counts[outcome.invalid_reason] = counts.get(outcome.invalid_reason, 0) + 1
                invalid = True
        if invalid:
            continue
        if outcomes["LONG"].entry_timestamp != outcomes["SHORT"].entry_timestamp:
            raise RuntimeError("Directional outcomes do not share one entry timestamp.")
        row = {
            key: feature_row[key]
            for key in ("asset", "decision_timestamp", *SPOT_FEATURE_COLUMNS)
        }
        row["entry_timestamp"] = outcomes["LONG"].entry_timestamp
        for direction, outcome in outcomes.items():
            prefix = direction.lower()
            row[f"{prefix}_event_end_timestamp"] = outcome.event_end_timestamp
            row[f"{prefix}_label"] = outcome.label
            row[f"{prefix}_outcome_net_r"] = outcome.outcome_net_r
            diagnostics[asset]["label_counts"][direction][outcome.label] += 1
        diagnostics[asset]["paired_labeled_decisions"] += 1
        rows.append(row)
    paired = pd.DataFrame(rows)
    if paired.empty:
        raise ValueError("No valid paired bidirectional Development labels were produced.")

    decision_indices = {
        asset: pd.DatetimeIndex(
            paired.loc[paired["asset"] == asset, "decision_timestamp"]
        )
        for asset in ASSET_ORDER
    }
    context = build_derivatives_context_feature_table(
        sources_by_asset, decision_indices
    )
    matched = paired.merge(
        context,
        on=["asset", "decision_timestamp"],
        how="inner",
        validate="one_to_one",
        sort=False,
    )
    matched = _validate_bidirectional_table(matched)
    for asset in ASSET_ORDER:
        diagnostics[asset]["context_complete_decisions"] = int(
            (matched["asset"] == asset).sum()
        )
    return matched, diagnostics


def _validate_bidirectional_table(table):
    if not isinstance(table, pd.DataFrame) or table.empty:
        raise ValueError("Bidirectional learning table must be nonempty.")
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
        raise ValueError(f"Bidirectional learning table schema mismatch: {missing}.")
    candidate = table.copy()
    timestamp_columns = (
        "decision_timestamp",
        "entry_timestamp",
        "long_event_end_timestamp",
        "short_event_end_timestamp",
    )
    for column in timestamp_columns:
        candidate[column] = pd.to_datetime(candidate[column], utc=True)
    if not set(candidate["asset"]).issubset(set(ASSET_ORDER)):
        raise ValueError("Bidirectional learning table asset mismatch.")
    if candidate.duplicated(["asset", "decision_timestamp"]).any():
        raise ValueError("Bidirectional learning table has duplicate decisions.")
    if (candidate["entry_timestamp"] <= candidate["decision_timestamp"]).any():
        raise ValueError("Bidirectional entries are not causal.")
    for direction in DIRECTION_ORDER:
        prefix = direction.lower()
        if set(candidate[f"{prefix}_label"]) - set(CLASS_ORDER):
            raise ValueError(f"{direction} label registry mismatch.")
        if (
            candidate[f"{prefix}_event_end_timestamp"]
            < candidate["entry_timestamp"]
        ).any():
            raise ValueError(f"{direction} outcomes are not causal.")
    start = _utc(COMMON_START_UTC)
    end = _utc(COMMON_END_EXCLUSIVE_UTC)
    if (
        (candidate["decision_timestamp"] < start).any()
        or (candidate["decision_timestamp"] >= end).any()
    ):
        raise ValueError("Bidirectional decisions exceed the common interval.")
    candidate["latest_event_end_timestamp"] = candidate[
        ["long_event_end_timestamp", "short_event_end_timestamp"]
    ].max(axis=1)
    if (candidate["latest_event_end_timestamp"] >= end).any():
        raise ValueError("Bidirectional outcomes exceed the Development boundary.")
    numeric_columns = [
        *ALL_NUMERIC_FEATURE_COLUMNS,
        "long_outcome_net_r",
        "short_outcome_net_r",
    ]
    numeric = candidate[numeric_columns].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Bidirectional features and outcomes must be finite.")
    candidate.loc[:, numeric_columns] = numeric.astype(float)
    return candidate.sort_values(
        ["decision_timestamp", "asset"], kind="stable"
    ).reset_index(drop=True)


def _feature_names(variant_id):
    names = list(SPOT_FEATURE_COLUMNS)
    if VARIANT_SPECS[variant_id]["feature_set"] == "SPOT_PLUS_DERIVATIVES_CONTEXT":
        names.extend(CONTEXT_FEATURE_COLUMNS)
    return names


def _pipeline(feature_names):
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
    model = HistGradientBoostingRegressor(**REGRESSOR_PARAMETERS)
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def _fold_slices(table, fold):
    training_end = _utc(fold["training_end_exclusive_utc"])
    validation_start = _utc(fold["validation_start_utc"])
    validation_end = _utc(fold["validation_end_exclusive_utc"])
    training = table.loc[
        (table["decision_timestamp"] < training_end)
        & (table["latest_event_end_timestamp"] < training_end)
    ].copy()
    validation = table.loc[
        (table["decision_timestamp"] >= validation_start)
        & (table["decision_timestamp"] < validation_end)
        & (table["latest_event_end_timestamp"] < validation_end)
    ].copy()
    if training.empty or validation.empty:
        raise ValueError(f"{fold['fold_id']} has insufficient paired rows.")
    return training, validation


def _fit_direction(variant_id, direction, training, validation):
    numeric_features = _feature_names(variant_id)
    feature_names = [*numeric_features, "asset"]
    target_column = _direction_column(direction, "outcome_net_r")
    estimator = _pipeline(numeric_features)
    estimator.fit(training[feature_names], training[target_column])
    prediction = np.asarray(
        estimator.predict(validation[feature_names]), dtype=float
    )
    actual = validation[target_column].to_numpy(dtype=float)
    spearman = pd.Series(prediction).corr(pd.Series(actual), method="spearman")
    metrics = {
        "training_rows": int(len(training)),
        "validation_rows": int(len(validation)),
        "mean_absolute_error_net_r": float(mean_absolute_error(actual, prediction)),
        "prediction_outcome_spearman": (
            float(spearman) if pd.notna(spearman) else None
        ),
        "mean_predicted_net_r": float(prediction.mean()),
        "mean_actual_net_r": float(actual.mean()),
    }
    artifact = pickle.dumps(
        {
            "variant_id": variant_id,
            "direction": direction,
            "feature_names": feature_names,
            "estimator": estimator,
        },
        protocol=5,
    )
    return prediction, metrics, artifact


def _combine_direction_predictions(validation, long_score, short_score):
    prediction = validation[
        [
            "asset",
            "decision_timestamp",
            "entry_timestamp",
            "long_event_end_timestamp",
            "short_event_end_timestamp",
            "long_label",
            "short_label",
            "long_outcome_net_r",
            "short_outcome_net_r",
        ]
    ].copy()
    prediction["long_predicted_net_r"] = np.asarray(long_score, dtype=float)
    prediction["short_predicted_net_r"] = np.asarray(short_score, dtype=float)
    prediction["action"] = [
        select_bidirectional_action(long_value, short_value)
        for long_value, short_value in zip(long_score, short_score, strict=True)
    ]
    prediction["selected_outcome_net_r"] = np.select(
        [prediction["action"] == "LONG", prediction["action"] == "SHORT"],
        [prediction["long_outcome_net_r"], prediction["short_outcome_net_r"]],
        default=0.0,
    ).astype(float)
    return prediction


def _selected_events(predictions):
    selected = predictions.loc[predictions["action"] != "HOLD_CASH"].copy()
    if selected.empty:
        selected["event_end_timestamp"] = pd.Series(dtype="datetime64[ns, UTC]")
        selected["outcome_net_r"] = pd.Series(dtype=float)
        return selected
    selected["event_end_timestamp"] = selected["long_event_end_timestamp"].where(
        selected["action"] == "LONG", selected["short_event_end_timestamp"]
    )
    selected["outcome_net_r"] = selected["selected_outcome_net_r"]
    return selected


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


def _summary(frame):
    values = frame["outcome_net_r"].to_numpy(dtype=float)
    count = int(len(frame))
    actions = frame["action"].value_counts() if "action" in frame else pd.Series()
    return {
        "count": count,
        "direction_counts": {
            direction: int(actions.get(direction, 0)) for direction in DIRECTION_ORDER
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
        "long_event_end_timestamp",
        "short_event_end_timestamp",
        "long_label",
        "short_label",
        "long_outcome_net_r",
        "short_outcome_net_r",
    )
    return hashlib.sha256(
        canonical_json_bytes(predictions.loc[:, columns].to_dict("records"))
    ).hexdigest()


def _absolute_review(variant_id, predictions, fold_metadata):
    raw_selected = _selected_events(predictions)
    nonoverlap = _nonoverlapping(raw_selected)
    folds = []
    for fold in FOLD_PLAN:
        fold_id = fold["fold_id"]
        raw_summary = _summary(
            raw_selected.loc[raw_selected["fold_id"] == fold_id]
        )
        nonoverlap_summary = _summary(
            nonoverlap.loc[nonoverlap["fold_id"] == fold_id]
        )
        folds.append(
            {
                **fold_metadata[fold_id],
                "raw_selected": raw_summary,
                "nonoverlapping_selected": nonoverlap_summary,
                "raw_support_pass": (
                    raw_summary["count"] >= MINIMUM_RAW_SELECTIONS_PER_FOLD
                ),
                "nonoverlap_support_pass": (
                    nonoverlap_summary["count"]
                    >= MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD
                ),
                "positive_net_r_pass": (
                    nonoverlap_summary["mean_net_r"] is not None
                    and nonoverlap_summary["mean_net_r"] > 0.0
                    and nonoverlap_summary["cumulative_net_r"] > 0.0
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
        "identity_validation_pass": True,
        "all_fold_raw_support_pass": all(item["raw_support_pass"] for item in folds),
        "all_fold_nonoverlap_support_pass": all(
            item["nonoverlap_support_pass"] for item in folds
        ),
        "all_fold_positive_net_r_pass": all(
            item["positive_net_r_pass"] for item in folds
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
        (
            gates["identity_validation_pass"],
            gates["all_fold_raw_support_pass"],
            gates["all_fold_nonoverlap_support_pass"],
            gates["all_fold_positive_net_r_pass"],
            gates["asset_breadth_pass"],
            gates["overall_positive_net_r_pass"],
        )
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
            raise RuntimeError("Bidirectional matched review pair is incomplete.")
        context = registry[context_id]
        control = registry[control_id]
        if (
            context["prediction_row_identity_sha256"]
            != control["prediction_row_identity_sha256"]
        ):
            raise RuntimeError("Bidirectional matched prediction rows differ.")
        context_overall = _mean_or_zero(
            context["nonoverlapping_selected_overall"]
        )
        control_overall = _mean_or_zero(
            control["nonoverlapping_selected_overall"]
        )
        context_fold_means = {
            fold["fold_id"]: _mean_or_zero(fold["nonoverlapping_selected"])
            for fold in context["folds"]
        }
        control_fold_means = {
            fold["fold_id"]: _mean_or_zero(fold["nonoverlapping_selected"])
            for fold in control["folds"]
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


def run_bidirectional_experiment(table):
    candidate = _validate_bidirectional_table(table)
    reviews = []
    artifacts = {}
    prediction_frames = []
    shared_fold_identity = {}
    for variant_id in VARIANT_SPECS:
        fold_predictions = []
        fold_metadata = {}
        for fold in FOLD_PLAN:
            training, validation = _fold_slices(candidate, fold)
            fold_id = fold["fold_id"]
            validation_identity = _identity_sha256(validation)
            previous = shared_fold_identity.setdefault(fold_id, validation_identity)
            if previous != validation_identity:
                raise RuntimeError("Variant validation-row identity mismatch.")
            scores = {}
            direction_metrics = {}
            for direction in DIRECTION_ORDER:
                score, metrics, artifact = _fit_direction(
                    variant_id, direction, training, validation
                )
                scores[direction] = score
                direction_metrics[direction] = metrics
                artifacts[f"{variant_id}|{fold_id}|{direction}"] = artifact
            prediction = _combine_direction_predictions(
                validation, scores["LONG"], scores["SHORT"]
            )
            prediction["fold_id"] = fold_id
            prediction["variant_id"] = variant_id
            fold_predictions.append(prediction)
            fold_metadata[fold_id] = {
                "fold_id": fold_id,
                "training_rows": int(len(training)),
                "validation_rows": int(len(validation)),
                "training_latest_event_end_utc": training[
                    "latest_event_end_timestamp"
                ].max(),
                "validation_latest_event_end_utc": validation[
                    "latest_event_end_timestamp"
                ].max(),
                "validation_row_identity_sha256": validation_identity,
                "direction_predictive_metrics": direction_metrics,
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
    return (
        {
            "status": STATUS_PASS if passing else STATUS_HOLD,
            "action": (
                "REVIEW_PASSING_DEVELOPMENT_HYPOTHESES" if passing else "HOLD_CASH"
            ),
            "passing_development_hypotheses": passing,
            "automatic_model_selection": False,
            "candidate_v2_authorized": False,
            "variant_reviews": reviews,
            "shared_fold_validation_row_identity_sha256": shared_fold_identity,
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
        "long_event_end_timestamp",
        "short_event_end_timestamp",
        "long_label",
        "short_label",
        "long_outcome_net_r",
        "short_outcome_net_r",
        "long_predicted_net_r",
        "short_predicted_net_r",
        "action",
        "selected_outcome_net_r",
    )
    return [
        {column: row[column] for column in columns}
        for _, row in predictions.iterrows()
    ]


def _artifact_filename(artifact_id):
    return artifact_id.lower().replace("|", "__") + ".pkl"


def read_bidirectional_learning_evidence(evidence_directory):
    root = Path(evidence_directory).resolve()
    report_path = root / REPORT_FILENAME
    sidecar_path = root / REPORT_SHA256_FILENAME
    if not report_path.is_file() or not sidecar_path.is_file():
        raise RuntimeError("Bidirectional report lock is incomplete.")
    report_bytes = report_path.read_bytes()
    digest = hashlib.sha256(report_bytes).hexdigest()
    if sidecar_path.read_bytes() != f"{digest}  {REPORT_FILENAME}\n".encode("ascii"):
        raise RuntimeError("Bidirectional report sidecar mismatch.")
    report = json.loads(report_bytes)
    if canonical_json_bytes(report) != report_bytes:
        raise RuntimeError("Bidirectional report is not canonical JSON.")
    if report.get("protocol_id") != PROTOCOL_ID or report.get("run_id") != RUN_ID:
        raise RuntimeError("Bidirectional report identity mismatch.")
    prediction = report.get("prediction_artifact", {})
    prediction_path = root / prediction.get("path", "")
    prediction_sidecar = root / prediction.get("checksum_path", "")
    if not prediction_path.is_file() or not prediction_sidecar.is_file():
        raise RuntimeError("Bidirectional prediction artifact is incomplete.")
    prediction_bytes = prediction_path.read_bytes()
    prediction_digest = hashlib.sha256(prediction_bytes).hexdigest()
    if (
        prediction_digest != prediction.get("sha256")
        or len(prediction_bytes) != prediction.get("bytes")
        or prediction_sidecar.read_bytes()
        != f"{prediction_digest}  {PREDICTIONS_FILENAME}\n".encode("ascii")
    ):
        raise RuntimeError("Bidirectional prediction artifact mismatch.")
    prediction_rows = json.loads(prediction_bytes)
    if canonical_json_bytes(prediction_rows) != prediction_bytes:
        raise RuntimeError("Bidirectional predictions are not canonical JSON.")
    if len(prediction_rows) != report.get("out_of_fold_prediction_count"):
        raise RuntimeError("Bidirectional prediction count mismatch.")
    expected_artifact_ids = {
        f"{variant}|{fold['fold_id']}|{direction}"
        for variant in VARIANT_SPECS
        for fold in FOLD_PLAN
        for direction in DIRECTION_ORDER
    }
    observed_artifact_ids = set()
    for artifact in report.get("model_artifacts", []):
        observed_artifact_ids.add(artifact["artifact_id"])
        path = root / artifact["path"]
        if (
            not path.is_file()
            or path.stat().st_size != artifact["bytes"]
            or _sha256(path) != artifact["sha256"]
        ):
            raise RuntimeError(
                f"Bidirectional model artifact mismatch: {artifact['artifact_id']}."
            )
    if observed_artifact_ids != expected_artifact_ids:
        raise RuntimeError("Bidirectional model artifact registry mismatch.")
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


class KrakenAIDrivenV2BidirectionalDevelopmentLearningRunner:
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
            raise FileExistsError("Bidirectional evidence already exists; refusing repeat.")
        if staging.exists():
            raise FileExistsError("Incomplete bidirectional staging evidence exists.")
        return final, staging

    def run(
        self,
        archive_path,
        context_lock,
        evidence_root,
        authorization_phrase,
    ):
        if authorization_phrase != AUTHORIZATION_PHRASE:
            raise PermissionError("Exact one-shot bidirectional authorization is required.")
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
        table, label_diagnostics = build_bidirectional_context_learning_table(
            frames, sources
        )
        experiment, predictions, artifacts = run_bidirectional_experiment(table)
        expected_models = len(VARIANT_SPECS) * len(FOLD_PLAN) * len(DIRECTION_ORDER)
        if len(artifacts) != expected_models:
            raise RuntimeError("Frozen bidirectional model count mismatch.")

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
            "spot_feature_columns": list(SPOT_FEATURE_COLUMNS),
            "context_feature_columns": list(CONTEXT_FEATURE_COLUMNS),
            "variant_order": list(VARIANT_SPECS),
            "matched_control": dict(MATCHED_CONTROL),
            "fold_plan": [dict(fold) for fold in FOLD_PLAN],
            "matched_learning_table_identity_sha256": _identity_sha256(table),
            "labeled_decision_count": int(len(table)),
            "directional_label_count": int(len(table) * len(DIRECTION_ORDER)),
            "label_diagnostics": label_diagnostics,
            "shared_fold_validation_row_identity_sha256": experiment[
                "shared_fold_validation_row_identity_sha256"
            ],
            "variant_reviews": experiment["variant_reviews"],
            "passing_development_hypotheses": experiment[
                "passing_development_hypotheses"
            ],
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
            "feature_search_executed": False,
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
            "next_stage": "RUN_INDEPENDENT_READ_ONLY_BIDIRECTIONAL_EVIDENCE_REVIEW",
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
        locked = read_bidirectional_learning_evidence(final)
        return RecordedBidirectionalLearningEvidence(
            report_path=final / REPORT_FILENAME,
            checksum_path=final / REPORT_SHA256_FILENAME,
            report_sha256=locked["report_sha256"],
            learning_status=locked["learning_status"],
            labeled_decision_count=int(len(table)),
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
        "direction_order": list(DIRECTION_ORDER),
        "spot_feature_count": len(SPOT_FEATURE_COLUMNS),
        "context_feature_count": len(CONTEXT_FEATURE_COLUMNS),
        "maximum_numeric_feature_count": len(ALL_NUMERIC_FEATURE_COLUMNS),
        "variant_order": list(VARIANT_SPECS),
        "matched_control": dict(MATCHED_CONTROL),
        "maximum_fold_model_fits": (
            len(VARIANT_SPECS) * len(FOLD_PLAN) * len(DIRECTION_ORDER)
        ),
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "source_binding_sha256": dict(SOURCE_BINDING_SHA256),
        "frozen_archive_sha256": FROZEN_COMPLETE_ARCHIVE_SPEC["sha256"],
        "paired_directional_rows_implemented": True,
        "latest_outcome_purge_implemented": True,
        "positive_maximum_action_rule_implemented": True,
        "absolute_and_incremental_gates_implemented": True,
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
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": "KRAKEN_AI_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_RUNNER_REVIEW_REQUIRED",
        "next_stage": "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_BIDIRECTIONAL_RUN",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Execute or review frozen bidirectional Development learning."
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
        result = read_bidirectional_learning_evidence(args.review_evidence)
    elif all(
        (
            args.complete_archive,
            args.context_lock,
            args.evidence_root,
            args.authorization_phrase,
        )
    ):
        recorded = KrakenAIDrivenV2BidirectionalDevelopmentLearningRunner().run(
            args.complete_archive,
            args.context_lock,
            args.evidence_root,
            args.authorization_phrase,
        )
        result = {
            "status": "KRAKEN_AI_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_EVIDENCE_RECORDED",
            "learning_status": recorded.learning_status,
            "report_path": str(recorded.report_path),
            "checksum_path": str(recorded.checksum_path),
            "report_sha256": recorded.report_sha256,
            "labeled_decision_count": recorded.labeled_decision_count,
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
