"""Executable causal learning core for Kraken BTC/ETH/XRP AI-driven V2.

This module is deliberately independent from real-data authorization.  It can
validate already supplied Development frames, build causal features, create
cost-aware three-class labels and fit deterministic walk-forward learners.  It
does not open an archive, Calibration or Evaluation, and it cannot promote a
Candidate or submit an order.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import pickle
from numbers import Integral, Real

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SCHEMA_VERSION = 1
COMPONENT_ID = "kraken-ai-v2-learning-core-v1"
STATUS = "KRAKEN_AI_V2_LEARNING_CORE_IMPLEMENTED_REAL_DEVELOPMENT_RUN_REQUIRED"
ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
ACTIVE_RESOLUTION = "12h"
BAR_INTERVAL = pd.Timedelta(hours=12)
DEVELOPMENT_START_UTC = "2019-01-01T00:00:00Z"
DEVELOPMENT_END_EXCLUSIVE_UTC = "2024-04-01T00:00:00Z"
CLASS_ORDER = (
    "TARGET_3R_FIRST",
    "STOP_1R_FIRST",
    "TIMEOUT_NO_BARRIER",
)

FEATURE_COLUMNS = (
    "return_1",
    "return_2",
    "return_6",
    "return_14",
    "atr_fraction_14",
    "realized_volatility_14",
    "ema_12_distance",
    "ema_48_distance",
    "ema_12_48_spread",
    "ema_180_distance",
    "volume_ratio_20",
    "distance_to_high_20",
    "distance_to_low_20",
    "rsi_14",
    "market_return_1",
    "btc_return_1",
)

MODEL_SPECS = {
    "LOGISTIC_BASELINE": {
        "family": "MULTINOMIAL_LOGISTIC_REGRESSION",
        "parameters": {
            "C": 1.0,
            "class_weight": "balanced",
            "solver": "lbfgs",
            "max_iter": 2000,
            "random_state": 1729,
        },
        "learns_parameters": True,
        "automatic_promotion": False,
    },
    "HIST_GBT_CHALLENGER": {
        "family": "HISTOGRAM_GRADIENT_BOOSTING",
        "parameters": {
            "learning_rate": 0.08,
            "max_leaf_nodes": 15,
            "max_iter": 300,
            "min_samples_leaf": 20,
            "l2_regularization": 1.0,
            "early_stopping": False,
            "random_state": 1729,
        },
        "learns_parameters": True,
        "automatic_promotion": False,
    },
}

FOLD_PLAN = (
    {
        "fold_id": "FOLD_1",
        "training_end_exclusive_utc": "2021-03-02T00:00:00Z",
        "validation_start_utc": "2021-04-01T00:00:00Z",
        "validation_end_exclusive_utc": "2022-04-01T00:00:00Z",
    },
    {
        "fold_id": "FOLD_2",
        "training_end_exclusive_utc": "2022-04-01T00:00:00Z",
        "validation_start_utc": "2022-05-01T00:00:00Z",
        "validation_end_exclusive_utc": "2023-05-01T00:00:00Z",
    },
    {
        "fold_id": "FOLD_3",
        "training_end_exclusive_utc": "2023-05-01T00:00:00Z",
        "validation_start_utc": "2023-05-31T00:00:00Z",
        "validation_end_exclusive_utc": DEVELOPMENT_END_EXCLUSIVE_UTC,
    },
)


@dataclass(frozen=True)
class LearningCostProfile:
    profile_id: str
    commission_rate: float
    slippage_rate: float
    full_spread_rate: float

    def __post_init__(self):
        if not isinstance(self.profile_id, str) or not self.profile_id:
            raise ValueError("Cost profile ID is required.")
        for value, name in (
            (self.commission_rate, "Commission"),
            (self.slippage_rate, "Slippage"),
            (self.full_spread_rate, "Spread"),
        ):
            if not isinstance(value, Real) or isinstance(value, bool):
                raise TypeError(f"{name} must be numeric.")
            if not math.isfinite(float(value)) or not 0.0 <= float(value) < 1.0:
                raise ValueError(f"{name} must be a finite fraction.")

    @property
    def adverse_price_rate(self):
        return float(self.slippage_rate) + float(self.full_spread_rate) / 2.0

    def buy_fill(self, reference):
        return _positive(reference, "Buy reference") * (1.0 + self.adverse_price_rate)

    def sell_fill(self, reference):
        return _positive(reference, "Sell reference") * (1.0 - self.adverse_price_rate)

    def buy_cash_per_unit(self, reference):
        fill = self.buy_fill(reference)
        return fill * (1.0 + float(self.commission_rate))

    def sell_cash_per_unit(self, reference):
        fill = self.sell_fill(reference)
        return fill * (1.0 - float(self.commission_rate))


BASELINE_COST_PROFILE = LearningCostProfile(
    profile_id="kraken-tier1-taker-adverse-20260829-v1",
    commission_rate=0.008,
    slippage_rate=0.0015,
    full_spread_rate=0.003,
)
ZERO_COST_PROFILE = LearningCostProfile(
    profile_id="synthetic-zero-cost-test-v1",
    commission_rate=0.0,
    slippage_rate=0.0,
    full_spread_rate=0.0,
)


@dataclass(frozen=True)
class LabelOutcome:
    valid: bool
    label: str | None
    invalid_reason: str | None
    decision_timestamp: pd.Timestamp
    entry_timestamp: pd.Timestamp | None = None
    event_end_timestamp: pd.Timestamp | None = None
    entry_cash_per_unit: float | None = None
    stop_trigger_price: float | None = None
    target_trigger_price: float | None = None
    exit_cash_per_unit: float | None = None
    outcome_net_r: float | None = None


@dataclass(frozen=True)
class WalkForwardLearningResult:
    predictions: pd.DataFrame
    metrics: dict
    model_artifact_sha256: dict
    trained_model_count: int
    parameters_learned_from_labels: bool
    automatic_model_selected: bool = False
    calibration_data_opened: bool = False
    evaluation_data_opened: bool = False
    candidate_v2_authorized: bool = False


def _positive(value, label):
    if not isinstance(value, Real) or isinstance(value, bool):
        raise TypeError(f"{label} must be numeric.")
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be positive and finite.")
    return value


def _utc(value, label):
    try:
        timestamp = pd.Timestamp(value)
    except Exception as exc:  # pragma: no cover - defensive normalization
        raise TypeError(f"{label} must be datetime-like.") from exc
    if pd.isna(timestamp) or timestamp.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware.")
    return timestamp.tz_convert("UTC")


def _canonical_sha256(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def learning_core_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "component_id": COMPONENT_ID,
        "status": STATUS,
        "active_resolution": ACTIVE_RESOLUTION,
        "asset_order": list(ASSET_ORDER),
        "class_order": list(CLASS_ORDER),
        "feature_columns": list(FEATURE_COLUMNS),
        "model_specs": json.loads(json.dumps(MODEL_SPECS)),
        "rule_discovery_rounds_active": False,
        "causal_features_implemented": True,
        "triple_barrier_labels_implemented": True,
        "walk_forward_training_implemented": True,
        "parameters_learned_from_labels": True,
        "automatic_model_selection": False,
        "real_development_training_executed": False,
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "paper_authorized": False,
        "live_execution_authorized": False,
        "next_stage": "IMPLEMENT_HASH_BOUND_12H_DEVELOPMENT_LEARNING_RUNNER",
    }


def _validate_frame(frame, asset):
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{asset} frame must be a pandas DataFrame.")
    required = ("Open", "High", "Low", "Close", "Volume")
    missing = [column for column in required if column not in frame]
    if missing:
        raise ValueError(f"{asset} missing OHLCV columns: {missing}.")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError(f"{asset} index must be a DatetimeIndex.")
    if frame.index.tz is None:
        raise ValueError(f"{asset} timestamps must be timezone-aware.")
    index = frame.index.tz_convert("UTC")
    if not index.is_monotonic_increasing or not index.is_unique:
        raise ValueError(f"{asset} timestamps must be strictly increasing and unique.")
    start = _utc(DEVELOPMENT_START_UTC, "Development start")
    end = _utc(DEVELOPMENT_END_EXCLUSIVE_UTC, "Development end")
    if len(index) == 0 or index.min() < start or index.max() >= end:
        raise ValueError(f"{asset} must remain inside the Development boundary.")
    interval_seconds = int(BAR_INTERVAL.total_seconds())
    if any(int(timestamp.timestamp()) % interval_seconds for timestamp in index):
        raise ValueError(f"{asset} timestamps must align to the continuous 12h grid.")

    values = frame.loc[:, required].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError(f"{asset} OHLCV values must be finite numeric values.")
    if (values[["Open", "High", "Low", "Close"]] <= 0.0).any().any():
        raise ValueError(f"{asset} OHLC prices must be positive.")
    if (values["Volume"] < 0.0).any():
        raise ValueError(f"{asset} volume must be nonnegative.")
    if (values["High"] < values[["Open", "Close", "Low"]].max(axis=1)).any():
        raise ValueError(f"{asset} High violates OHLC geometry.")
    if (values["Low"] > values[["Open", "Close", "High"]].min(axis=1)).any():
        raise ValueError(f"{asset} Low violates OHLC geometry.")

    normalized = values.copy()
    normalized.index = index
    return normalized


def validate_development_frames(frames):
    if not isinstance(frames, dict) or set(frames) != set(ASSET_ORDER):
        raise ValueError("Development frames must contain exactly BTC-USD, ETH-USD and XRP-USD.")
    return {asset: _validate_frame(frames[asset], asset) for asset in ASSET_ORDER}


def _asset_features(frame):
    close = frame["Close"].astype(float)
    high = frame["High"].astype(float)
    low = frame["Low"].astype(float)
    volume = frame["Volume"].astype(float)
    previous_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    atr_14 = true_range.rolling(14, min_periods=14).mean()
    return_1 = close.pct_change(fill_method=None)
    ema_12 = close.ewm(span=12, adjust=False, min_periods=12).mean()
    ema_48 = close.ewm(span=48, adjust=False, min_periods=48).mean()
    ema_180 = close.ewm(span=180, adjust=False, min_periods=180).mean()
    delta = close.diff()
    average_gain = delta.clip(lower=0.0).rolling(14, min_periods=14).mean()
    average_loss = -delta.clip(upper=0.0).rolling(14, min_periods=14).mean()
    relative_strength = average_gain / average_loss.replace(0.0, np.nan)
    rsi_14 = 100.0 - 100.0 / (1.0 + relative_strength)
    rsi_14 = rsi_14.where(~((average_gain == 0.0) & (average_loss == 0.0)), 50.0)

    features = pd.DataFrame(index=frame.index)
    features["return_1"] = return_1
    for periods in (2, 6, 14):
        features[f"return_{periods}"] = close.pct_change(periods, fill_method=None)
    features["atr_fraction_14"] = atr_14 / close
    features["realized_volatility_14"] = return_1.rolling(14, min_periods=14).std(ddof=0)
    features["ema_12_distance"] = close / ema_12 - 1.0
    features["ema_48_distance"] = close / ema_48 - 1.0
    features["ema_12_48_spread"] = ema_12 / ema_48 - 1.0
    features["ema_180_distance"] = close / ema_180 - 1.0
    features["volume_ratio_20"] = volume / volume.rolling(20, min_periods=20).median() - 1.0
    prior_high = high.shift(1).rolling(20, min_periods=20).max()
    prior_low = low.shift(1).rolling(20, min_periods=20).min()
    features["distance_to_high_20"] = close / prior_high - 1.0
    features["distance_to_low_20"] = close / prior_low - 1.0
    features["rsi_14"] = rsi_14 / 100.0
    features["signal_atr_14"] = atr_14
    return features


def build_causal_feature_table(frames):
    validated = validate_development_frames(frames)
    by_asset = {asset: _asset_features(frame) for asset, frame in validated.items()}
    common_returns = pd.concat(
        {asset: feature["return_1"] for asset, feature in by_asset.items()}, axis=1
    )
    market_return = common_returns.mean(axis=1, skipna=False)
    btc_return = common_returns["BTC-USD"]

    rows = []
    for asset in ASSET_ORDER:
        feature = by_asset[asset].copy()
        feature["market_return_1"] = market_return.reindex(feature.index)
        feature["btc_return_1"] = btc_return.reindex(feature.index)
        feature["asset"] = asset
        feature["decision_timestamp"] = feature.index
        feature = feature.dropna(subset=[*FEATURE_COLUMNS, "signal_atr_14"])
        rows.append(feature.reset_index(drop=True))
    result = pd.concat(rows, ignore_index=True)
    result["asset"] = pd.Categorical(result["asset"], categories=ASSET_ORDER, ordered=True)
    result = result.sort_values(["decision_timestamp", "asset"], kind="stable").reset_index(drop=True)
    result["asset"] = result["asset"].astype("object")
    if not np.isfinite(result[[*FEATURE_COLUMNS, "signal_atr_14"]].to_numpy(dtype=float)).all():
        raise RuntimeError("Causal feature table contains non-finite values.")
    return result


def _invalid_label(frame, decision_position, reason):
    return LabelOutcome(
        valid=False,
        label=None,
        invalid_reason=reason,
        decision_timestamp=frame.index[decision_position],
    )


def triple_barrier_label(
    frame,
    *,
    decision_position,
    signal_atr,
    horizon_bars=60,
    cost_profile=BASELINE_COST_PROFILE,
):
    if not isinstance(frame, pd.DataFrame) or not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("Label frame must use a DatetimeIndex.")
    if not isinstance(decision_position, Integral) or isinstance(decision_position, bool):
        raise TypeError("Decision position must be an integer.")
    decision_position = int(decision_position)
    if not 0 <= decision_position < len(frame):
        raise IndexError("Decision position is outside the frame.")
    if not isinstance(horizon_bars, Integral) or isinstance(horizon_bars, bool) or horizon_bars < 2:
        raise ValueError("Label horizon must contain at least two bars.")
    if not isinstance(cost_profile, LearningCostProfile):
        raise TypeError("Learning cost profile is invalid.")
    signal_atr = _positive(signal_atr, "Signal ATR")
    boundary_position = decision_position + int(horizon_bars)
    if boundary_position >= len(frame):
        return _invalid_label(frame, decision_position, "RIGHT_EDGE_CENSORED")

    path_index = frame.index[decision_position : boundary_position + 1]
    if path_index.tz is None:
        raise ValueError("Label timestamps must be timezone-aware.")
    path_index = path_index.tz_convert("UTC")
    if not (path_index.to_series().diff().dropna() == BAR_INTERVAL).all():
        return _invalid_label(frame, decision_position, "PROVIDER_GAP_CENSORED")

    entry_position = decision_position + 1
    entry_open = _positive(frame.iloc[entry_position]["Open"], "Entry open")
    entry_cash = cost_profile.buy_cash_per_unit(entry_open)
    risk_unit = 1.5 * signal_atr
    net_sell_multiplier = (1.0 - cost_profile.adverse_price_rate) * (
        1.0 - cost_profile.commission_rate
    )
    stop_trigger = (entry_cash - risk_unit) / net_sell_multiplier
    target_trigger = (entry_cash + 3.0 * risk_unit) / net_sell_multiplier
    if stop_trigger <= 0.0:
        return _invalid_label(frame, decision_position, "NONPOSITIVE_STOP_BARRIER")

    label = None
    event_position = None
    exit_cash = None
    for position in range(entry_position, boundary_position):
        row = frame.iloc[position]
        open_price = _positive(row["Open"], "Path open")
        high_price = _positive(row["High"], "Path high")
        low_price = _positive(row["Low"], "Path low")
        if open_price <= stop_trigger:
            label = "STOP_1R_FIRST"
            event_position = position
            exit_cash = cost_profile.sell_cash_per_unit(open_price)
            break
        if open_price >= target_trigger:
            label = "TARGET_3R_FIRST"
            event_position = position
            exit_cash = cost_profile.sell_cash_per_unit(open_price)
            break
        stop_touched = low_price <= stop_trigger
        target_touched = high_price >= target_trigger
        if stop_touched:
            label = "STOP_1R_FIRST"
            event_position = position
            exit_cash = cost_profile.sell_cash_per_unit(stop_trigger)
            break
        if target_touched:
            label = "TARGET_3R_FIRST"
            event_position = position
            exit_cash = cost_profile.sell_cash_per_unit(target_trigger)
            break

    if label is None:
        label = "TIMEOUT_NO_BARRIER"
        event_position = boundary_position
        exit_cash = cost_profile.sell_cash_per_unit(frame.iloc[event_position]["Open"])

    return LabelOutcome(
        valid=True,
        label=label,
        invalid_reason=None,
        decision_timestamp=frame.index[decision_position],
        entry_timestamp=frame.index[entry_position],
        event_end_timestamp=frame.index[event_position],
        entry_cash_per_unit=entry_cash,
        stop_trigger_price=stop_trigger,
        target_trigger_price=target_trigger,
        exit_cash_per_unit=exit_cash,
        outcome_net_r=(exit_cash - entry_cash) / risk_unit,
    )


def build_labeled_learning_table(frames):
    validated = validate_development_frames(frames)
    features = build_causal_feature_table(validated)
    rows = []
    positions = {asset: {timestamp: number for number, timestamp in enumerate(frame.index)} for asset, frame in validated.items()}
    for feature_row in features.to_dict("records"):
        asset = feature_row["asset"]
        decision_timestamp = feature_row["decision_timestamp"]
        outcome = triple_barrier_label(
            validated[asset],
            decision_position=positions[asset][decision_timestamp],
            signal_atr=feature_row["signal_atr_14"],
        )
        if not outcome.valid:
            continue
        row = {key: feature_row[key] for key in ("asset", "decision_timestamp", *FEATURE_COLUMNS)}
        row.update(
            {
                "entry_timestamp": outcome.entry_timestamp,
                "event_end_timestamp": outcome.event_end_timestamp,
                "label": outcome.label,
                "outcome_net_r": outcome.outcome_net_r,
            }
        )
        rows.append(row)
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError("No valid labeled Development examples were produced.")
    return result.sort_values(["decision_timestamp", "asset"], kind="stable").reset_index(drop=True)


def _model(model_id):
    spec = MODEL_SPECS[model_id]
    if model_id == "LOGISTIC_BASELINE":
        return LogisticRegression(**spec["parameters"])
    if model_id == "HIST_GBT_CHALLENGER":
        return HistGradientBoostingClassifier(**spec["parameters"])
    raise ValueError(f"Unknown model ID: {model_id}.")


def _pipeline(model_id):
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]
    )
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric, list(FEATURE_COLUMNS)),
            (
                "asset",
                OneHotEncoder(categories=[list(ASSET_ORDER)], handle_unknown="error", sparse_output=False),
                ["asset"],
            ),
        ],
        sparse_threshold=0.0,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", _model(model_id))])


def _class_counts(labels):
    counts = pd.Series(labels).value_counts()
    return {label: int(counts.get(label, 0)) for label in CLASS_ORDER}


def _validate_learning_table(table):
    if not isinstance(table, pd.DataFrame):
        raise TypeError("Learning table must be a pandas DataFrame.")
    required = {"asset", "decision_timestamp", "event_end_timestamp", "label", "outcome_net_r", *FEATURE_COLUMNS}
    missing = sorted(required - set(table.columns))
    if missing:
        raise ValueError(f"Learning table is missing columns: {missing}.")
    candidate = table.copy()
    candidate["decision_timestamp"] = pd.to_datetime(candidate["decision_timestamp"], utc=True)
    candidate["event_end_timestamp"] = pd.to_datetime(candidate["event_end_timestamp"], utc=True)
    start = _utc(DEVELOPMENT_START_UTC, "Development start")
    end = _utc(DEVELOPMENT_END_EXCLUSIVE_UTC, "Development end")
    if (
        (candidate["decision_timestamp"] < start).any()
        or (candidate["decision_timestamp"] >= end).any()
        or (candidate["event_end_timestamp"] >= end).any()
    ):
        raise ValueError("Learning rows must stay inside the Development partition.")
    if (candidate["event_end_timestamp"] <= candidate["decision_timestamp"]).any():
        raise ValueError("Every label event must end after its decision timestamp.")
    if not set(candidate["asset"]).issubset(set(ASSET_ORDER)):
        raise ValueError("Learning table contains an unregistered asset.")
    if not set(candidate["label"]).issubset(set(CLASS_ORDER)):
        raise ValueError("Learning table contains an unregistered label.")
    numeric = candidate[list(FEATURE_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Learning features must be finite numeric values.")
    candidate[list(FEATURE_COLUMNS)] = numeric
    return candidate.sort_values(["decision_timestamp", "asset"], kind="stable").reset_index(drop=True)


def _aligned_probabilities(model, feature_rows):
    observed = model.predict_proba(feature_rows)
    model_classes = tuple(model.named_steps["model"].classes_)
    aligned = np.zeros((len(feature_rows), len(CLASS_ORDER)), dtype=float)
    for source_column, label in enumerate(model_classes):
        aligned[:, CLASS_ORDER.index(label)] = observed[:, source_column]
    return aligned


def _expected_calibration_error(actual_target, predicted_target, bins=10):
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(predicted_target)
    error = 0.0
    for lower, upper in zip(edges[:-1], edges[1:], strict=True):
        if upper == 1.0:
            selected = (predicted_target >= lower) & (predicted_target <= upper)
        else:
            selected = (predicted_target >= lower) & (predicted_target < upper)
        if selected.any():
            error += selected.mean() * abs(actual_target[selected].mean() - predicted_target[selected].mean())
    return float(error if total else math.nan)


def _ordered_multiclass_log_loss(labels, probabilities):
    indices = np.array([CLASS_ORDER.index(label) for label in labels], dtype=int)
    selected = probabilities[np.arange(len(indices)), indices]
    selected = np.clip(selected, np.finfo(float).eps, 1.0)
    return float(-np.log(selected).mean())


def train_walk_forward(
    table,
    *,
    model_ids=("LOGISTIC_BASELINE", "HIST_GBT_CHALLENGER"),
    minimum_training_class_count=30,
    minimum_validation_class_count=10,
):
    candidate = _validate_learning_table(table)
    if not model_ids or len(set(model_ids)) != len(model_ids):
        raise ValueError("Model IDs must be a nonempty unique sequence.")
    if any(model_id not in MODEL_SPECS for model_id in model_ids):
        raise ValueError("Walk-forward request contains an unknown model ID.")
    for value, label in (
        (minimum_training_class_count, "Training class minimum"),
        (minimum_validation_class_count, "Validation class minimum"),
    ):
        if not isinstance(value, Integral) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")

    feature_names = [*FEATURE_COLUMNS, "asset"]
    prediction_frames = []
    metrics = {}
    artifact_hashes = {}
    for fold in FOLD_PLAN:
        fold_id = fold["fold_id"]
        training_end = _utc(fold["training_end_exclusive_utc"], "Training end")
        validation_start = _utc(fold["validation_start_utc"], "Validation start")
        validation_end = _utc(fold["validation_end_exclusive_utc"], "Validation end")
        training = candidate.loc[
            (candidate["decision_timestamp"] < training_end)
            & (candidate["event_end_timestamp"] < training_end)
        ].copy()
        validation = candidate.loc[
            (candidate["decision_timestamp"] >= validation_start)
            & (candidate["decision_timestamp"] < validation_end)
            & (candidate["event_end_timestamp"] < validation_end)
        ].copy()
        training_counts = _class_counts(training["label"])
        validation_counts = _class_counts(validation["label"])
        if min(training_counts.values(), default=0) < minimum_training_class_count:
            raise ValueError(f"{fold_id} training class support is insufficient: {training_counts}.")
        if min(validation_counts.values(), default=0) < minimum_validation_class_count:
            raise ValueError(f"{fold_id} validation class support is insufficient: {validation_counts}.")

        for model_id in model_ids:
            estimator = _pipeline(model_id)
            estimator.fit(training[feature_names], training["label"])
            probability = _aligned_probabilities(estimator, validation[feature_names])
            actual_target = (validation["label"].to_numpy() == CLASS_ORDER[0]).astype(float)
            target_probability = probability[:, 0]
            key = f"{fold_id}|{model_id}"
            metrics[key] = {
                "fold_id": fold_id,
                "model_id": model_id,
                "training_rows": int(len(training)),
                "validation_rows": int(len(validation)),
                "training_class_counts": training_counts,
                "validation_class_counts": validation_counts,
                "multiclass_log_loss": _ordered_multiclass_log_loss(
                    validation["label"], probability
                ),
                "target_brier_score": float(np.mean((actual_target - target_probability) ** 2)),
                "target_precision_recall_auc": float(average_precision_score(actual_target, target_probability)),
                "expected_calibration_error": _expected_calibration_error(actual_target, target_probability),
            }
            model_bytes = pickle.dumps(estimator, protocol=5)
            artifact_hashes[key] = hashlib.sha256(model_bytes).hexdigest()
            prediction_frames.append(
                pd.DataFrame(
                    {
                        "fold_id": fold_id,
                        "model_id": model_id,
                        "asset": validation["asset"].to_numpy(),
                        "decision_timestamp": validation["decision_timestamp"].to_numpy(),
                        "event_end_timestamp": validation["event_end_timestamp"].to_numpy(),
                        "training_end_timestamp": training_end,
                        "actual_label": validation["label"].to_numpy(),
                        "actual_outcome_net_r": validation["outcome_net_r"].to_numpy(dtype=float),
                        "p_target_3r_first": probability[:, 0],
                        "p_stop_1r_first": probability[:, 1],
                        "p_timeout_no_barrier": probability[:, 2],
                    }
                )
            )

    predictions = pd.concat(prediction_frames, ignore_index=True)
    predictions = predictions.sort_values(
        ["fold_id", "model_id", "decision_timestamp", "asset"], kind="stable"
    ).reset_index(drop=True)
    return WalkForwardLearningResult(
        predictions=predictions,
        metrics=metrics,
        model_artifact_sha256=artifact_hashes,
        trained_model_count=len(artifact_hashes),
        parameters_learned_from_labels=True,
    )


LEARNING_CORE_CONFIGURATION_SHA256 = _canonical_sha256(learning_core_declaration())
