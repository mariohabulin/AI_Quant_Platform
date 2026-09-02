"""Frozen causal derivatives-context hypothesis and synthetic-only feature engine."""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from kraken_ai_driven_v2_learning_core import FEATURE_COLUMNS as SPOT_FEATURE_COLUMNS
except ImportError:  # pragma: no cover
    from .kraken_ai_driven_v2_learning_core import FEATURE_COLUMNS as SPOT_FEATURE_COLUMNS


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-v2-derivatives-context-learning-hypothesis-v1"
COMPONENT_ID = "kraken-ai-v2-derivatives-context-hypothesis-v1"
PARENT_COMMIT = "99f62423d19d7684c80ed67ed99666e2f48b0fbc"
FEASIBILITY_REPORT_SHA256 = (
    "3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29"
)
FEASIBILITY_STATUS = (
    "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_SOURCE_FEASIBLE_HYPOTHESIS_DESIGN_REQUIRED"
)
ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
COMMON_START_UTC = "2021-12-01T00:00:00Z"
COMMON_END_EXCLUSIVE_UTC = "2024-04-01T00:00:00Z"
BAR_INTERVAL = pd.Timedelta(hours=12)
PURGE_INTERVAL = pd.Timedelta(days=30)
FUNDING_MAX_AGE = pd.Timedelta(hours=12)
OPEN_INTEREST_MAX_AGE = pd.Timedelta(minutes=30)
CONTEXT_WARMUP_BARS = 60
INNER_FIT_FRACTION = 0.75
MINIMUM_RAW_SELECTIONS_PER_FOLD = 30
MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD = 10
MINIMUM_POSITIVE_ASSETS = 2
MINIMUM_PREDICTIVE_FOLD_WINS = 2
EMPTY_CONTROL_SELECTION_BENCHMARK_NET_R = 0.0

CONTEXT_FEATURE_COLUMNS = (
    "funding_rate_latest",
    "funding_rate_mean_6",
    "funding_rate_zscore_60",
    "open_interest_log_change_1",
    "open_interest_log_change_6",
    "open_interest_log_zscore_60",
    "basis_fraction",
    "basis_change_1",
    "basis_zscore_60",
)

FOLD_PLAN = (
    {
        "fold_id": "FOLD_1",
        "training_end_exclusive_utc": "2022-11-01T00:00:00Z",
        "validation_start_utc": "2022-12-01T00:00:00Z",
        "validation_end_exclusive_utc": "2023-04-01T00:00:00Z",
    },
    {
        "fold_id": "FOLD_2",
        "training_end_exclusive_utc": "2023-04-01T00:00:00Z",
        "validation_start_utc": "2023-05-01T00:00:00Z",
        "validation_end_exclusive_utc": "2023-09-01T00:00:00Z",
    },
    {
        "fold_id": "FOLD_3",
        "training_end_exclusive_utc": "2023-09-01T00:00:00Z",
        "validation_start_utc": "2023-10-01T00:00:00Z",
        "validation_end_exclusive_utc": COMMON_END_EXCLUSIVE_UTC,
    },
)

CLASSIFIER_PARAMETERS = {
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "max_iter": 200,
    "min_samples_leaf": 30,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": 1729,
}
REGRESSOR_PARAMETERS = dict(CLASSIFIER_PARAMETERS)

VARIANT_SPECS = {
    "SPOT_ONLY_HIST_GBT_CLASSIFIER_CONTROL": {
        "objective": "CALIBRATED_THREE_CLASS_UTILITY",
        "feature_set": "SPOT_ONLY_CONTROL",
        "model_family": "HISTOGRAM_GRADIENT_BOOSTING_CLASSIFIER",
        "parameters": CLASSIFIER_PARAMETERS,
        "candidate_eligible": False,
    },
    "SPOT_CONTEXT_HIST_GBT_CLASSIFIER": {
        "objective": "CALIBRATED_THREE_CLASS_UTILITY",
        "feature_set": "SPOT_PLUS_DERIVATIVES_CONTEXT",
        "model_family": "HISTOGRAM_GRADIENT_BOOSTING_CLASSIFIER",
        "parameters": CLASSIFIER_PARAMETERS,
        "candidate_eligible": True,
    },
    "SPOT_ONLY_HIST_GBT_NET_R_CONTROL": {
        "objective": "DIRECT_EXPECTED_NET_R",
        "feature_set": "SPOT_ONLY_CONTROL",
        "model_family": "HISTOGRAM_GRADIENT_BOOSTING_REGRESSOR",
        "parameters": REGRESSOR_PARAMETERS,
        "candidate_eligible": False,
    },
    "SPOT_CONTEXT_HIST_GBT_NET_R": {
        "objective": "DIRECT_EXPECTED_NET_R",
        "feature_set": "SPOT_PLUS_DERIVATIVES_CONTEXT",
        "model_family": "HISTOGRAM_GRADIENT_BOOSTING_REGRESSOR",
        "parameters": REGRESSOR_PARAMETERS,
        "candidate_eligible": True,
    },
}

MATCHED_CONTROL = {
    "SPOT_CONTEXT_HIST_GBT_CLASSIFIER": "SPOT_ONLY_HIST_GBT_CLASSIFIER_CONTROL",
    "SPOT_CONTEXT_HIST_GBT_NET_R": "SPOT_ONLY_HIST_GBT_NET_R_CONTROL",
}


def _utc(value, name):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware.")
    return timestamp.tz_convert("UTC")


def _validate_datetime_index(index, name, *, aligned=False):
    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError(f"{name} index must be a DatetimeIndex.")
    if index.tz is None:
        raise ValueError(f"{name} timestamps must be timezone-aware.")
    normalized = index.tz_convert("UTC")
    if not normalized.is_monotonic_increasing or not normalized.is_unique:
        raise ValueError(f"{name} timestamps must be strictly increasing and unique.")
    if aligned:
        interval_seconds = int(BAR_INTERVAL.total_seconds())
        if any(int(timestamp.timestamp()) % interval_seconds for timestamp in normalized):
            raise ValueError(f"{name} timestamps must align to the 12h grid.")
    return normalized


def _validate_values(frame, name, columns, *, positive=False):
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame.")
    if tuple(frame.columns) != tuple(columns):
        raise ValueError(f"{name} columns must be exactly {tuple(columns)}.")
    normalized = frame.copy()
    normalized.index = _validate_datetime_index(frame.index, name)
    values = normalized.loc[:, columns].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError(f"{name} values must be finite numeric values.")
    if positive and (values <= 0.0).any().any():
        raise ValueError(f"{name} values must be positive.")
    normalized.loc[:, columns] = values.astype(float)
    return normalized


def _validate_decision_index(index):
    normalized = _validate_datetime_index(index, "Decision", aligned=True)
    start = _utc(COMMON_START_UTC, "Common start")
    end = _utc(COMMON_END_EXCLUSIVE_UTC, "Common end")
    if len(normalized) == 0 or normalized.min() < start or normalized.max() >= end:
        raise ValueError("Decision timestamps must stay inside the common Development interval.")
    return normalized


def _asof_value(frame, column, effective_times, maximum_age):
    left = pd.DataFrame({"effective_timestamp": effective_times})
    right = frame.reset_index(names="source_timestamp")
    merged = pd.merge_asof(
        left,
        right,
        left_on="effective_timestamp",
        right_on="source_timestamp",
        direction="backward",
        allow_exact_matches=True,
    )
    age = merged["effective_timestamp"] - merged["source_timestamp"]
    values = merged[column].where(age <= maximum_age)
    return pd.Series(values.to_numpy(dtype=float), index=effective_times - BAR_INTERVAL)


def _rolling_zscore(values, window):
    mean = values.rolling(window, min_periods=window).mean()
    standard_deviation = values.rolling(window, min_periods=window).std(ddof=0)
    score = (values - mean) / standard_deviation.replace(0.0, np.nan)
    return score.where(standard_deviation != 0.0, 0.0)


def build_asset_derivatives_context_features(
    funding,
    open_interest,
    mark_index_12h,
    decision_index,
):
    """Build nine causal features for one asset without reading any archive."""

    decisions = _validate_decision_index(decision_index)
    funding = _validate_values(funding, "Funding", ("funding_rate",))
    open_interest = _validate_values(
        open_interest, "Open interest", ("open_interest",), positive=True
    )
    mark_index_12h = _validate_values(
        mark_index_12h,
        "Mark/index",
        ("mark_close", "index_close"),
        positive=True,
    )
    mark_index_12h.index = _validate_datetime_index(
        mark_index_12h.index, "Mark/index", aligned=True
    )

    effective_times = decisions + BAR_INTERVAL
    sampled_funding = _asof_value(
        funding, "funding_rate", effective_times, FUNDING_MAX_AGE
    )
    sampled_open_interest = _asof_value(
        open_interest,
        "open_interest",
        effective_times,
        OPEN_INTEREST_MAX_AGE,
    )
    exact_mark_index = mark_index_12h.reindex(decisions)
    basis = exact_mark_index["mark_close"] / exact_mark_index["index_close"] - 1.0
    log_open_interest = np.log(sampled_open_interest)

    features = pd.DataFrame(index=decisions)
    features["funding_rate_latest"] = sampled_funding
    features["funding_rate_mean_6"] = sampled_funding.rolling(6, min_periods=6).mean()
    features["funding_rate_zscore_60"] = _rolling_zscore(
        sampled_funding, CONTEXT_WARMUP_BARS
    )
    features["open_interest_log_change_1"] = log_open_interest.diff(1)
    features["open_interest_log_change_6"] = log_open_interest.diff(6)
    features["open_interest_log_zscore_60"] = _rolling_zscore(
        log_open_interest, CONTEXT_WARMUP_BARS
    )
    features["basis_fraction"] = basis
    features["basis_change_1"] = basis.diff(1)
    features["basis_zscore_60"] = _rolling_zscore(basis, CONTEXT_WARMUP_BARS)
    features = features.dropna(subset=list(CONTEXT_FEATURE_COLUMNS))
    if not np.isfinite(features.to_numpy(dtype=float)).all():
        raise RuntimeError("Derivatives-context features contain non-finite values.")
    return features.loc[:, CONTEXT_FEATURE_COLUMNS]


def build_derivatives_context_feature_table(sources_by_asset, decision_indices):
    if not isinstance(sources_by_asset, dict) or set(sources_by_asset) != set(ASSET_ORDER):
        raise ValueError("Context sources must contain exactly BTC-USD, ETH-USD and XRP-USD.")
    if not isinstance(decision_indices, dict) or set(decision_indices) != set(ASSET_ORDER):
        raise ValueError("Decision indices must contain exactly BTC-USD, ETH-USD and XRP-USD.")
    rows = []
    for asset in ASSET_ORDER:
        sources = sources_by_asset[asset]
        if not isinstance(sources, dict) or set(sources) != {
            "funding",
            "open_interest",
            "mark_index_12h",
        }:
            raise ValueError(f"{asset} context source registry mismatch.")
        features = build_asset_derivatives_context_features(
            sources["funding"],
            sources["open_interest"],
            sources["mark_index_12h"],
            decision_indices[asset],
        ).copy()
        features["asset"] = asset
        features["decision_timestamp"] = features.index
        rows.append(features.reset_index(drop=True))
    result = pd.concat(rows, ignore_index=True)
    return result.sort_values(["decision_timestamp", "asset"], kind="stable").reset_index(
        drop=True
    )


def fold_plan_is_causal():
    common_start = _utc(COMMON_START_UTC, "Common start")
    common_end = _utc(COMMON_END_EXCLUSIVE_UTC, "Common end")
    previous_validation_end = None
    for fold in FOLD_PLAN:
        training_end = _utc(fold["training_end_exclusive_utc"], "Training end")
        validation_start = _utc(fold["validation_start_utc"], "Validation start")
        validation_end = _utc(
            fold["validation_end_exclusive_utc"], "Validation end"
        )
        if not common_start < training_end < validation_start < validation_end <= common_end:
            return False
        if validation_start - training_end < PURGE_INTERVAL:
            return False
        if previous_validation_end is not None and validation_start < previous_validation_end:
            return False
        previous_validation_end = validation_end
    return previous_validation_end == common_end


def derivatives_context_hypothesis_declaration():
    if not fold_plan_is_causal():
        raise RuntimeError("Frozen derivatives-context fold plan is not causal.")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "feasibility_report_sha256": FEASIBILITY_REPORT_SHA256,
        "feasibility_status": FEASIBILITY_STATUS,
        "source_feasible": True,
        "active_resolution": "12h",
        "asset_order": list(ASSET_ORDER),
        "common_start_utc": COMMON_START_UTC,
        "common_end_exclusive_utc": COMMON_END_EXCLUSIVE_UTC,
        "context_warmup_bars": CONTEXT_WARMUP_BARS,
        "spot_feature_count": len(SPOT_FEATURE_COLUMNS),
        "context_feature_count": len(CONTEXT_FEATURE_COLUMNS),
        "total_context_model_numeric_feature_count": len(SPOT_FEATURE_COLUMNS)
        + len(CONTEXT_FEATURE_COLUMNS),
        "context_feature_order": list(CONTEXT_FEATURE_COLUMNS),
        "fold_plan": [dict(fold) for fold in FOLD_PLAN],
        "variant_order": list(VARIANT_SPECS),
        "matched_control": dict(MATCHED_CONTROL),
        "experiment_budget": len(VARIANT_SPECS),
        "maximum_fold_model_fits": len(VARIANT_SPECS) * len(FOLD_PLAN),
        "minimum_raw_selections_per_fold": MINIMUM_RAW_SELECTIONS_PER_FOLD,
        "minimum_nonoverlapping_selections_per_fold": MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        "minimum_positive_assets": MINIMUM_POSITIVE_ASSETS,
        "minimum_predictive_fold_wins": MINIMUM_PREDICTIVE_FOLD_WINS,
        "empty_control_selection_benchmark_net_r": EMPTY_CONTROL_SELECTION_BENCHMARK_NET_R,
        "control_variants_candidate_eligible": False,
        "market_values_opened": False,
        "labels_generated": False,
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
        "status": "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_HYPOTHESIS_PRE_REGISTERED_REVIEW_REQUIRED",
        "next_stage": "IMPLEMENT_HASH_BOUND_DERIVATIVES_CONTEXT_DATASET_LOCK_AND_READER",
    }
