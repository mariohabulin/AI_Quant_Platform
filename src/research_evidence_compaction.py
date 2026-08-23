"""Bounded canonical evidence shared by exploratory research runners."""

import hashlib
import math
from numbers import Real

try:
    from research_evidence import canonical_json_bytes
except ImportError:  # package import when src is not placed directly on sys.path
    from src.research_evidence import canonical_json_bytes


POSITIVE_INFINITY_PROFIT_FACTOR = "POSITIVE_INFINITY_NO_LOSING_TRADES"


def compact_backtest_run(result):
    retained = {}
    for key in (
        "initial_capital",
        "final_capital",
        "performance",
        "comparison",
        "benchmark",
        "execution_timing",
    ):
        if key in result:
            retained[key] = result[key]
    return retained


def compact_oos_evidence(result):
    retained = {}
    for key in ("split", "generalization"):
        if key in result:
            retained[key] = result[key]
    for key in ("in_sample", "out_of_sample"):
        if key in result:
            retained[key] = compact_backtest_run(result[key])
    return retained


def compact_walk_forward_evidence(result):
    windows = []
    unseen_trade_count = 0
    for window in result["windows"]:
        compact_window = {
            key: value
            for key, value in window.items()
            if key not in {"train", "test"}
        }
        for segment in ("train", "test"):
            if segment in window:
                compact_window[segment] = compact_backtest_run(window[segment])
        unseen_trade_count += len(window.get("test", {}).get("trade_history", []))
        windows.append(compact_window)
    return {
        "configuration": result.get("configuration"),
        "summary": result["summary"],
        "unseen_trade_count": unseen_trade_count,
        "windows": windows,
    }


def normalize_profit_factor_evidence(value):
    """Encode only the defined positive-infinite no-losing-trades state."""

    if isinstance(value, dict):
        normalized = {}
        encoded_count = 0
        for key, item in value.items():
            if (
                key == "profit_factor"
                and isinstance(item, Real)
                and not isinstance(item, bool)
                and math.isinf(float(item))
                and item > 0
            ):
                normalized[key] = POSITIVE_INFINITY_PROFIT_FACTOR
                encoded_count += 1
                continue
            normalized_item, item_count = normalize_profit_factor_evidence(item)
            normalized[key] = normalized_item
            encoded_count += item_count
        return normalized, encoded_count
    if isinstance(value, list):
        normalized = []
        encoded_count = 0
        for item in value:
            normalized_item, item_count = normalize_profit_factor_evidence(item)
            normalized.append(normalized_item)
            encoded_count += item_count
        return normalized, encoded_count
    if isinstance(value, tuple):
        normalized, encoded_count = normalize_profit_factor_evidence(list(value))
        return tuple(normalized), encoded_count
    return value, 0


def compact_multi_asset_evaluation(result):
    """Hash complete evidence while persisting a bounded deterministic subset."""

    normalized_result, encoded_count = normalize_profit_factor_evidence(result)
    raw_bytes = canonical_json_bytes(normalized_result)
    assets = {}
    for asset_name, asset_result in sorted(normalized_result["assets"].items()):
        assets[asset_name] = {
            "strategy": asset_result["strategy"],
            "classification": asset_result["classification"],
            "out_of_sample": compact_oos_evidence(asset_result["out_of_sample"]),
            "walk_forward": compact_walk_forward_evidence(
                asset_result["walk_forward"]
            ),
            "falsification": asset_result["falsification"],
        }
    return {
        "strategy": normalized_result["strategy"],
        "asset_count": normalized_result["asset_count"],
        "summary": normalized_result["summary"],
        "classification": normalized_result["classification"],
        "assets": assets,
        "raw_evaluation_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "raw_evaluation_canonical_bytes": len(raw_bytes),
        "raw_evaluation_encoding": {
            "positive_infinite_profit_factor_count": encoded_count,
            "positive_infinite_profit_factor_value": (
                POSITIVE_INFINITY_PROFIT_FACTOR
            ),
        },
        "raw_trade_level_evidence_persisted": False,
    }


def profile_summary(asset_result):
    out_of_sample = asset_result["out_of_sample"]["out_of_sample"]
    comparison = out_of_sample["comparison"]
    performance = out_of_sample["performance"]
    walk_forward = asset_result["walk_forward"]
    falsification = asset_result["falsification"]
    return {
        "validation_classification": asset_result["classification"]["status"],
        "oos_strategy_return": comparison["strategy_return"],
        "oos_benchmark_return": comparison["benchmark_return"],
        "oos_excess_return": comparison["excess_return"],
        "oos_max_drawdown_percent": performance["max_drawdown"],
        "oos_trade_count": performance["number_of_trades"],
        "walk_forward_window_count": walk_forward["summary"]["window_count"],
        "unseen_walk_forward_trade_count": walk_forward["unseen_trade_count"],
        "positive_walk_forward_excess_rate": walk_forward["summary"][
            "positive_test_excess_rate"
        ],
        "passes_statistical_falsification": falsification[
            "passes_statistical_falsification"
        ],
        "bootstrap_ci_lower": falsification["bootstrap"]["ci_lower"],
        "bootstrap_ci_upper": falsification["bootstrap"]["ci_upper"],
        "permutation_p_value": falsification["permutation"]["p_value"],
    }
