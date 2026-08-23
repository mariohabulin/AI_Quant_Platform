"""Non-evaluating inventory and failure-mode boundary for strategy research."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from research_evidence import canonical_json_bytes
    from strategy_engine import StrategyEngine
    from strategy_library import StrategyLibrary
    from strategies.adx_strategy import ADXStrategy
    from strategies.atr_strategy import ATRStrategy
    from strategies.bollinger_strategy import BollingerStrategy
    from strategies.donchian_strategy import DonchianStrategy
    from strategies.ema_strategy import EMAStrategy
    from strategies.macd_strategy import MACDStrategy
    from strategies.rsi_strategy import RSIStrategy
    from strategies.stochastic_strategy import StochasticStrategy
    from strategies.supertrend_strategy import SupertrendStrategy
except ImportError:  # package import when src is not placed directly on sys.path
    from src.research_evidence import canonical_json_bytes
    from src.strategy_engine import StrategyEngine
    from src.strategy_library import StrategyLibrary
    from src.strategies.adx_strategy import ADXStrategy
    from src.strategies.atr_strategy import ATRStrategy
    from src.strategies.bollinger_strategy import BollingerStrategy
    from src.strategies.donchian_strategy import DonchianStrategy
    from src.strategies.ema_strategy import EMAStrategy
    from src.strategies.macd_strategy import MACDStrategy
    from src.strategies.rsi_strategy import RSIStrategy
    from src.strategies.stochastic_strategy import StochasticStrategy
    from src.strategies.supertrend_strategy import SupertrendStrategy


STRATEGY_RESEARCH_INVENTORY_SCHEMA_VERSION = 1
STRATEGY_RESEARCH_INVENTORY_ID = "strategy-research-inventory-v1"
RECORDED_TIMEFRAME_STUDY_SHA256 = (
    "505bd5b40a38d7e5b8b4538e1d7ac9cb459cd40f46108dc1a33a42c1647b64ab"
)
RECORDED_TIMEFRAME_STUDY_ID = "ema-20-50-btc-eth-timeframe-sensitivity-v1"
RECORDED_TIMEFRAME_ORDER = ("1h", "6h", "1d")
RECORDED_ASSET_SCOPE = ("BTC-USD", "ETH-USD")
PROFILE_ORDER = ("baseline", "stress")


@dataclass(frozen=True)
class StrategyResearchSpec:
    strategy_name: str
    factory: object
    family: str
    mechanism: str
    signal_behavior: str
    default_parameters: tuple
    research_status: str

    def as_dict(self):
        return {
            "strategy_name": self.strategy_name,
            "family": self.family,
            "mechanism": self.mechanism,
            "signal_behavior": self.signal_behavior,
            "default_parameters": dict(self.default_parameters),
            "research_status": self.research_status,
            "standalone_implementation": True,
            "combination_authorized": False,
            "formal_candidate_authorized": False,
        }


STRATEGY_SPECS = (
    StrategyResearchSpec(
        "adx",
        ADXStrategy,
        "TREND",
        "TREND_STRENGTH_AND_DIRECTION",
        "STATE_TRANSITION",
        (("period", 14), ("threshold", 25.0)),
        "UNEVALUATED_RESEARCH_COMPONENT",
    ),
    StrategyResearchSpec(
        "atr",
        ATRStrategy,
        "BREAKOUT",
        "VOLATILITY_BREAKOUT",
        "STATE_CONDITION",
        (("period", 14), ("multiplier", 1.0)),
        "UNEVALUATED_RESEARCH_COMPONENT",
    ),
    StrategyResearchSpec(
        "bollinger",
        BollingerStrategy,
        "MEAN_REVERSION",
        "VOLATILITY_BAND_EXTREME",
        "STATE_CONDITION",
        (("period", 20), ("standard_deviations", 2.0)),
        "UNEVALUATED_RESEARCH_COMPONENT",
    ),
    StrategyResearchSpec(
        "donchian",
        DonchianStrategy,
        "BREAKOUT",
        "PRIOR_CHANNEL_BREAKOUT",
        "STATE_CONDITION",
        (("period", 20),),
        "UNEVALUATED_RESEARCH_COMPONENT",
    ),
    StrategyResearchSpec(
        "ema_crossover",
        EMAStrategy,
        "TREND",
        "MOVING_AVERAGE_CROSSOVER",
        "STATE_TRANSITION",
        (("fast_period", 20), ("slow_period", 50)),
        "CLOSED_REJECTED_CANDIDATE_V1",
    ),
    StrategyResearchSpec(
        "macd",
        MACDStrategy,
        "TREND",
        "MOMENTUM_TREND_CROSSOVER",
        "STATE_TRANSITION",
        (("fast_period", 12), ("slow_period", 26), ("signal_period", 9)),
        "UNEVALUATED_RESEARCH_COMPONENT",
    ),
    StrategyResearchSpec(
        "rsi",
        RSIStrategy,
        "MEAN_REVERSION",
        "MOMENTUM_EXTREME",
        "STATE_CONDITION",
        (("period", 14), ("oversold", 30), ("overbought", 70)),
        "UNEVALUATED_RESEARCH_COMPONENT",
    ),
    StrategyResearchSpec(
        "stochastic",
        StochasticStrategy,
        "MEAN_REVERSION",
        "EXTREME_ZONE_CROSSOVER",
        "STATE_TRANSITION",
        (
            ("k_period", 14),
            ("d_period", 3),
            ("oversold", 20.0),
            ("overbought", 80.0),
        ),
        "UNEVALUATED_RESEARCH_COMPONENT",
    ),
    StrategyResearchSpec(
        "supertrend",
        SupertrendStrategy,
        "TREND",
        "VOLATILITY_ADJUSTED_TREND_DIRECTION",
        "STATE_TRANSITION",
        (("period", 10), ("multiplier", 3.0)),
        "UNEVALUATED_RESEARCH_COMPONENT",
    ),
)


def inventory_declaration():
    strategies = [spec.as_dict() for spec in STRATEGY_SPECS]
    return {
        "schema_version": STRATEGY_RESEARCH_INVENTORY_SCHEMA_VERSION,
        "status": "STRATEGY_RESEARCH_INVENTORY_DECLARED",
        "inventory_id": STRATEGY_RESEARCH_INVENTORY_ID,
        "strategy_count": len(strategies),
        "remaining_unevaluated_strategy_count": sum(
            item["research_status"] == "UNEVALUATED_RESEARCH_COMPONENT"
            for item in strategies
        ),
        "strategies": strategies,
        "inventory_order": [item["strategy_name"] for item in strategies],
        "selection_policy": "NONE_INVENTORY_ONLY",
        "strategy_screening_executed": False,
        "performance_evaluation_executed": False,
        "automatic_ranking_authorized": False,
        "parameter_sweep_authorized": False,
        "strategy_combination_authorized": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


def _diagnostic_market_frame(rows=720):
    if not isinstance(rows, int) or isinstance(rows, bool):
        raise TypeError("Diagnostic row count must be an integer.")
    if rows < 600:
        raise ValueError("Diagnostic row count must be at least 600.")

    positions = np.arange(rows, dtype=float)
    close = (
        100.0
        + 0.015 * positions
        + 12.0 * np.sin(positions / 13.0)
        + 5.0 * np.sin(positions / 3.7)
    )
    for position, magnitude in (
        (150, 35.0),
        (151, -25.0),
        (350, -40.0),
        (351, 30.0),
        (550, 45.0),
        (551, -35.0),
    ):
        close[position:] += magnitude

    open_price = np.concatenate(([close[0]], close[:-1]))
    high = np.maximum(open_price, close) + 1.0
    low = np.minimum(open_price, close) - 1.0
    volume = 100.0 + 20.0 * np.square(np.sin(positions / 11.0))
    index = pd.date_range(
        "2024-01-01T00:00:00Z",
        periods=rows,
        freq="h",
    )
    return pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def _strategy_engine(strategy):
    library = StrategyLibrary()
    library.register(strategy)
    return StrategyEngine(library, strategy.name)


def _prefix_checkpoints(result):
    length = len(result)
    checkpoints = set(
        np.linspace(0, length - 1, num=16, dtype=int).tolist()
    )
    for signal in (1, -1):
        positions = np.flatnonzero(result["Signal"].to_numpy() == signal)
        checkpoints.update(positions[:8].tolist())
        checkpoints.update(positions[-8:].tolist())
    return sorted(checkpoints)


def _audit_strategy(spec, data):
    strategy = spec.factory()
    engine = _strategy_engine(strategy)
    original = data.copy(deep=True)
    first = engine.run(data)
    second = engine.run(data)
    signals = first["Signal"]

    prefix_causal = True
    for position in _prefix_checkpoints(first):
        prefix = data.iloc[: position + 1]
        prefix_result = engine.run(prefix)
        if prefix_result["Signal"].iloc[-1] != signals.iloc[position]:
            prefix_causal = False
            break

    checks = {
        "strategy_name_matches_inventory": strategy.name == spec.strategy_name,
        "required_features_declared": bool(strategy.required_features),
        "input_preserved": data.equals(original),
        "deterministic": first.equals(second),
        "signal_domain_valid": set(signals.unique()).issubset({-1, 0, 1}),
        "buy_signal_observed": bool(signals.eq(1).any()),
        "sell_signal_observed": bool(signals.eq(-1).any()),
        "prefix_causal": prefix_causal,
    }
    return {
        "strategy_name": spec.strategy_name,
        "family": spec.family,
        "default_parameters": dict(spec.default_parameters),
        "research_status": spec.research_status,
        "checks": checks,
        "signal_counts": {
            "buy": int(signals.eq(1).sum()),
            "sell": int(signals.eq(-1).sum()),
            "neutral": int(signals.eq(0).sum()),
        },
        "integration_ready": all(checks.values()),
        "performance_evaluated": False,
    }


def audit_strategy_integrations(data=None):
    diagnostic_data = _diagnostic_market_frame() if data is None else data
    if not isinstance(diagnostic_data, pd.DataFrame):
        raise TypeError("Diagnostic data must be a pandas DataFrame.")
    strategies = [
        _audit_strategy(spec, diagnostic_data)
        for spec in STRATEGY_SPECS
    ]
    passed = all(item["integration_ready"] for item in strategies)
    return {
        "status": (
            "STRATEGY_INTEGRATION_AUDIT_PASS"
            if passed
            else "STRATEGY_INTEGRATION_AUDIT_BLOCKED"
        ),
        "strategy_count": len(strategies),
        "diagnostic_rows": len(diagnostic_data),
        "diagnostic_purpose": "SYNTHETIC_CAUSAL_INTEGRATION_ONLY",
        "market_dataset_used": False,
        "performance_evaluation_executed": False,
        "automatic_ranking_generated": False,
        "candidate_v2_authorized": False,
        "live_execution_authorized": False,
        "strategies": strategies,
    }


def load_recorded_study_report(
    report_path,
    expected_sha256=RECORDED_TIMEFRAME_STUDY_SHA256,
):
    path = Path(report_path)
    if not path.is_file():
        raise FileNotFoundError(f"Recorded study report does not exist: {path}")
    report_bytes = path.read_bytes()
    digest = hashlib.sha256(report_bytes).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Recorded study report does not match the frozen hash.")

    checksum_path = path.with_name("timeframe_sensitivity_report.sha256")
    if not checksum_path.is_file():
        raise FileNotFoundError("Recorded study checksum sidecar is missing.")
    expected_sidecar = f"{digest}  {path.name}\n".encode("ascii")
    if checksum_path.read_bytes() != expected_sidecar:
        raise ValueError("Recorded study checksum sidecar is invalid.")

    try:
        payload = json.loads(report_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError("Recorded study report is not valid JSON.") from exc
    if canonical_json_bytes(payload) != report_bytes:
        raise ValueError("Recorded study report is not canonical JSON.")
    if (
        payload.get("schema_version") != 3
        or payload.get("status") != "TIMEFRAME_SENSITIVITY_COMPLETED"
        or payload.get("study_id") != RECORDED_TIMEFRAME_STUDY_ID
    ):
        raise ValueError("Recorded study identity is invalid.")

    false_flags = (
        "candidate_v1_reopened",
        "automatic_timeframe_selection",
        "formal_candidate_evaluation",
        "candidate_v2_authorized",
        "optimization_authorized",
        "bounded_forward_paper_review_eligible",
        "bounded_forward_paper_authorized",
        "live_execution_authorized",
    )
    if any(payload.get(flag) is not False for flag in false_flags):
        raise ValueError("Recorded study authorization boundary is invalid.")
    comparison = payload.get("comparison", {})
    if (
        comparison.get("timeframe_order") != list(RECORDED_TIMEFRAME_ORDER)
        or comparison.get("selection_policy") != "NONE_EXPLORATORY_ONLY"
        or comparison.get("automatic_ranking_generated") is not False
    ):
        raise ValueError("Recorded study comparison boundary is invalid.")
    return payload, digest


def _recorded_profile(comparison, timeframe, asset, profile):
    try:
        return comparison["timeframes"][timeframe]["assets"][asset][profile]
    except (KeyError, TypeError) as exc:
        raise ValueError("Recorded study profile scope is incomplete.") from exc


def analyze_recorded_study(payload, digest):
    comparison = payload.get("comparison", {})
    if comparison.get("timeframe_order") != list(RECORDED_TIMEFRAME_ORDER):
        raise ValueError("Recorded study timeframe order is invalid.")

    observations = {}
    flat_profiles = []
    aggregate_statuses = []
    for timeframe in RECORDED_TIMEFRAME_ORDER:
        timeframe_result = comparison.get("timeframes", {}).get(timeframe)
        if not isinstance(timeframe_result, dict):
            raise ValueError("Recorded study timeframe evidence is incomplete.")
        aggregate_statuses.extend(
            [
                timeframe_result.get("baseline_aggregate_classification"),
                timeframe_result.get("cost_stress_aggregate_classification"),
            ]
        )
        observations[timeframe] = {}
        for asset in RECORDED_ASSET_SCOPE:
            observations[timeframe][asset] = {}
            for profile in PROFILE_ORDER:
                item = _recorded_profile(
                    comparison,
                    timeframe,
                    asset,
                    profile,
                )
                required = (
                    "validation_classification",
                    "oos_strategy_return",
                    "oos_benchmark_return",
                    "oos_excess_return",
                    "oos_max_drawdown_percent",
                    "oos_trade_count",
                    "walk_forward_window_count",
                    "unseen_walk_forward_trade_count",
                    "positive_walk_forward_excess_rate",
                    "passes_statistical_falsification",
                )
                if any(key not in item for key in required):
                    raise ValueError("Recorded study profile evidence is incomplete.")
                retained = {key: item[key] for key in required}
                observations[timeframe][asset][profile] = retained
                flat_profiles.append(retained)

    return {
        "status": "RECORDED_FAILURE_MODES_ANALYZED",
        "source_report_sha256": digest,
        "profile_count": len(flat_profiles),
        "all_aggregate_profiles_rejected": all(
            status == "REJECTED" for status in aggregate_statuses
        ),
        "all_asset_profiles_rejected": all(
            item["validation_classification"] == "REJECTED"
            for item in flat_profiles
        ),
        "all_statistical_falsification_failed": all(
            item["passes_statistical_falsification"] is False
            for item in flat_profiles
        ),
        "observations": observations,
        "next_hypothesis_constraints": [
            "REDUCE_TURNOVER_OR_PROVE_COST_SURVIVAL",
            "BOUND_DRAWDOWN",
            "STATE_A_FALSIFIABLE_MARKET_REGIME_HYPOTHESIS",
            "RETAIN_BASELINE_AND_STRESS_COSTS",
            "RESERVE_GENUINELY_UNSEEN_VALIDATION_DATA",
            "NO_AUTOMATIC_RANKING_OR_PARAMETER_SWEEP",
        ],
        "selected_strategy": None,
        "selected_timeframe": None,
        "automatic_ranking_generated": False,
        "strategy_screening_executed": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Declare strategy inventory, run synthetic integration checks, "
            "or summarize exact recorded development evidence."
        )
    )
    parser.add_argument(
        "--audit-integrations",
        action="store_true",
        help="Run synthetic causal/integration checks without performance data.",
    )
    parser.add_argument(
        "--study-report",
        help="Analyze only the exact frozen Timeframe Study report.",
    )
    args = parser.parse_args(argv)

    output = inventory_declaration()
    if args.audit_integrations:
        output["integration_audit"] = audit_strategy_integrations()
        output["integration_audit_executed"] = True
    else:
        output["integration_audit_executed"] = False
    if args.study_report:
        payload, digest = load_recorded_study_report(
            args.study_report,
            expected_sha256=RECORDED_TIMEFRAME_STUDY_SHA256,
        )
        output["failure_mode_analysis"] = analyze_recorded_study(
            payload,
            digest,
        )
        output["recorded_evidence_analysis_executed"] = True
    else:
        output["recorded_evidence_analysis_executed"] = False
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
