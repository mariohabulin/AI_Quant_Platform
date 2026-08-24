"""One-shot nested runner for Alpha Discovery and Calibration Protocol v1."""

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from statistics import median, mean

import numpy as np

try:
    from alpha_development_protocol import (
        VARIANT_ORDER,
        alpha_development_evaluation_configuration,
        alpha_development_protective_exit_policy,
        alpha_development_risk_engine,
        alpha_development_strategy_engines,
    )
    from alpha_discovery_protocol import (
        ALPHA_DISCOVERY_ID,
        ASSET_SCOPE,
        CALIBRATION_PARAMETER_CATALOG,
        PARAMETER_SET_ORDER,
        RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256,
        AlphaCalibrationSelectionPolicy,
        AlphaDiscoveryPreregistration,
        NestedCalibrationPlanner,
        alpha_discovery_configuration,
        parameter_catalog_fingerprint,
    )
    from alpha_discovery_strategy import AlphaDiscoveryStrategy
    from backtest import BacktestingEngine
    from feature_engine import generate_features
    from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from multi_asset import MultiAssetValidator
    from out_of_sample import OutOfSampleValidator
    from protective_exit import ProtectiveExitPolicy
    from research_evidence import canonical_json_bytes
    from research_evidence_compaction import (
        compact_multi_asset_evaluation,
        normalize_profit_factor_evidence,
    )
    from risk_engine import RiskEngine
    from strategy_evaluation_protocol import ExecutionCostProfile
    from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
except ImportError:  # package import when src is not placed directly on sys.path
    from src.alpha_development_protocol import (
        VARIANT_ORDER,
        alpha_development_evaluation_configuration,
        alpha_development_protective_exit_policy,
        alpha_development_risk_engine,
        alpha_development_strategy_engines,
    )
    from src.alpha_discovery_protocol import (
        ALPHA_DISCOVERY_ID,
        ASSET_SCOPE,
        CALIBRATION_PARAMETER_CATALOG,
        PARAMETER_SET_ORDER,
        RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256,
        AlphaCalibrationSelectionPolicy,
        AlphaDiscoveryPreregistration,
        NestedCalibrationPlanner,
        alpha_discovery_configuration,
        parameter_catalog_fingerprint,
    )
    from src.alpha_discovery_strategy import AlphaDiscoveryStrategy
    from src.backtest import BacktestingEngine
    from src.feature_engine import generate_features
    from src.first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from src.multi_asset import MultiAssetValidator
    from src.out_of_sample import OutOfSampleValidator
    from src.protective_exit import ProtectiveExitPolicy
    from src.research_evidence import canonical_json_bytes
    from src.research_evidence_compaction import (
        compact_multi_asset_evaluation,
        normalize_profit_factor_evidence,
    )
    from src.risk_engine import RiskEngine
    from src.strategy_evaluation_protocol import ExecutionCostProfile
    from src.strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256


ALPHA_DISCOVERY_REPORT_SCHEMA_VERSION = 1
DISCOVERY_DIRECTORY_NAME = "discovery_v1"
STAGING_DIRECTORY_NAME = ".discovery_v1.staging"
REPORT_FILENAME = "alpha_discovery_report.json"
CHECKSUM_FILENAME = "alpha_discovery_report.sha256"
DEFAULT_OUTPUT_ROOT = Path("data/research/alpha_discovery_v1")
PROFILE_ORDER = (BASELINE_COSTS.label, STRESSED_COSTS.label)
ZERO_COST_DIAGNOSTIC = ExecutionCostProfile(
    label="alpha_discovery_zero_cost_diagnostic_v1",
    commission_rate=0.0,
    slippage_rate=0.0,
    spread_rate=0.0,
)


def _finite(value, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def alpha_discovery_risk_engine():
    return RiskEngine(
        risk_per_trade=0.005,
        max_position_fraction=0.50,
        max_drawdown_fraction=0.20,
        daily_loss_limit=0.02,
        weekly_loss_limit=0.05,
        min_reward_risk=3.0,
    )


def alpha_discovery_protective_exit_policy(parameter_set):
    return ProtectiveExitPolicy(
        risk_distance_column="ALPHA_V2_ATR_RISK_DISTANCE",
        reward_risk_ratio=parameter_set.reward_risk_ratio,
        reward_risk_ratio_column="ALPHA_V2_REWARD_RISK_RATIO",
        stop_and_target_same_bar="STOP_FIRST",
        stop_gap_fill="OPEN",
        target_gap_fill="TARGET",
        entry_bar_protection=True,
        breakeven_trigger_r=parameter_set.breakeven_trigger_r,
    )


class _PreparedWindowEngine:
    def __init__(self, strategy_name, prepared):
        self._strategy_name = strategy_name
        self.prepared = prepared.copy(deep=True)

    @property
    def strategy_name(self):
        return self._strategy_name

    def run(self, data):
        if not data.index.equals(self.prepared.index):
            raise ValueError("Prepared evaluation window index changed.")
        return self.prepared.copy(deep=True)


class AlphaDiscoveryWindowEvaluator:
    """Evaluate one catalog member on one exact window and cost profile."""

    def __init__(
        self,
        strategy_factory=AlphaDiscoveryStrategy,
        feature_generator=generate_features,
        risk_engine_factory=alpha_discovery_risk_engine,
        protective_policy_factory=alpha_discovery_protective_exit_policy,
        partition_validator_factory=OutOfSampleValidator,
    ):
        for factory, name in (
            (strategy_factory, "Strategy factory"),
            (feature_generator, "Feature generator"),
            (risk_engine_factory, "Risk Engine factory"),
            (protective_policy_factory, "Protective-policy factory"),
            (partition_validator_factory, "Partition-validator factory"),
        ):
            if not callable(factory):
                raise TypeError(f"{name} must be callable.")
        self.strategy_factory = strategy_factory
        self.feature_generator = feature_generator
        self.risk_engine_factory = risk_engine_factory
        self.protective_policy_factory = protective_policy_factory
        self.partition_validator_factory = partition_validator_factory

    @staticmethod
    def _validate_request(assets, start_position, end_position, phase, window_id):
        if not isinstance(assets, dict) or tuple(sorted(assets)) != ASSET_SCOPE:
            raise ValueError("Window evaluation requires exact BTC/ETH assets.")
        lengths = {len(frame) for frame in assets.values()}
        if len(lengths) != 1:
            raise ValueError("Window evaluation assets must have equal row counts.")
        total_rows = next(iter(lengths))
        for value, name in (
            (start_position, "Window start"),
            (end_position, "Window end"),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be an integer.")
        if not 0 <= start_position < end_position <= total_rows:
            raise ValueError("Window positions are outside the locked dataset.")
        if phase not in ("INNER", "OUTER"):
            raise ValueError("Window phase must be INNER or OUTER.")
        if not isinstance(window_id, str) or not window_id:
            raise ValueError("Window ID is required.")

    @staticmethod
    def _summary(partition, policy, start_position, end_position):
        trades = partition.get("trade_history")
        equity = partition.get("equity_curve")
        if not isinstance(trades, list) or not isinstance(equity, list):
            raise ValueError("Raw window trade/equity evidence is incomplete.")
        initial_capital = _finite(partition.get("initial_capital"), "Initial capital")
        if initial_capital <= 0.0:
            raise ValueError("Initial capital must be positive.")
        rows = end_position - start_position
        years = rows * 21600.0 / (365.25 * 24.0 * 3600.0)
        round_trip_notional = 0.0
        total_costs = 0.0
        for trade in trades:
            shares = _finite(trade.get("shares"), "Trade shares")
            entry_price = _finite(trade.get("entry_price"), "Trade entry price")
            exit_price = _finite(trade.get("exit_price"), "Trade exit price")
            costs = _finite(trade.get("total_costs"), "Trade costs")
            if min(shares, entry_price, exit_price) <= 0.0 or costs < 0.0:
                raise ValueError("Window trade execution evidence is invalid.")
            round_trip_notional += shares * (entry_price + exit_price)
            total_costs += costs
        normalized, _ = normalize_profit_factor_evidence(partition)
        raw_bytes = canonical_json_bytes(normalized)
        performance = partition.get("performance", {})
        comparison = partition.get("comparison", {})
        return {
            "window_start_position": start_position,
            "window_end_position": end_position,
            "window_rows": rows,
            "strategy_return": _finite(
                comparison.get("strategy_return"), "Window strategy return"
            ),
            "maximum_drawdown_percent": _finite(
                performance.get("max_drawdown"), "Window drawdown"
            ),
            "completed_trades": len(trades),
            "annualized_turnover_multiple": (
                round_trip_notional / initial_capital / years
            ),
            "annualized_cost_fraction": total_costs / initial_capital / years,
            "protective_policy_active": (
                partition.get("protective_exit_policy") == policy.as_dict()
            ),
            "raw_partition_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "raw_partition_canonical_bytes": len(raw_bytes),
            "raw_trade_level_evidence_persisted": False,
        }

    def evaluate(
        self,
        parameter_set,
        assets,
        start_position,
        end_position,
        cost_profile,
        phase,
        window_id,
    ):
        self._validate_request(
            assets, start_position, end_position, phase, window_id
        )
        if not isinstance(cost_profile, ExecutionCostProfile):
            raise TypeError("Cost profile must be an ExecutionCostProfile.")
        result = {}
        for asset_name in ASSET_SCOPE:
            full_data = assets[asset_name]
            history = full_data.iloc[:end_position].copy()
            strategy = self.strategy_factory(parameter_set)
            featured = self.feature_generator(
                history,
                required_features=strategy.required_features,
            )
            signaled = strategy.generate_signals(
                featured,
                evaluation_start_position=start_position,
            )
            prepared = signaled.iloc[start_position:end_position].copy()
            market_window = full_data.iloc[start_position:end_position].copy()
            engine = _PreparedWindowEngine(strategy.name, prepared)
            policy = self.protective_policy_factory(parameter_set)
            validator = self.partition_validator_factory(
                engine,
                initial_capital=5000.0,
                commission_rate=cost_profile.commission_rate,
                slippage_rate=cost_profile.slippage_rate,
                spread_rate=cost_profile.spread_rate,
                execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
                risk_engine=self.risk_engine_factory(),
                protective_exit_policy=policy,
            )
            partition = validator._evaluate_partition(market_window)
            summary = self._summary(
                partition, policy, start_position, end_position
            )
            summary.update(
                {
                    "asset": asset_name,
                    "phase": phase,
                    "window_id": window_id,
                    "parameter_set_id": parameter_set.parameter_set_id,
                    "cost_profile": cost_profile.as_dict(),
                }
            )
            result[asset_name] = summary
        return result


class AlphaDiscoveryDiagnosticEvaluator:
    """Replay exact closed v2 variants at zero cost for path attribution only."""

    def __init__(self, validator_factory=MultiAssetValidator):
        if not callable(validator_factory):
            raise TypeError("Validator factory must be callable.")
        self.validator_factory = validator_factory

    @staticmethod
    def _trade_path_summary(trades):
        if not isinstance(trades, list):
            raise ValueError("Diagnostic trade history must be a list.")
        fields = (
            "maximum_favorable_excursion_r",
            "maximum_adverse_excursion_r",
            "realized_r",
            "holding_bars",
            "bars_to_maximum_favorable_excursion",
        )
        values = {field: [] for field in fields}
        exits = {}
        for trade in trades:
            for field in fields:
                value = _finite(trade.get(field), f"Diagnostic {field}")
                if field != "realized_r" and value < 0.0:
                    raise ValueError("Diagnostic path metrics cannot be negative.")
                values[field].append(value)
            reason = trade.get("exit_reason")
            if reason not in (
                "SIGNAL",
                "PROTECTIVE_STOP",
                "PROTECTIVE_TARGET",
                "TERMINAL_FORCE_CLOSE",
            ):
                raise ValueError("Diagnostic exit reason is invalid.")
            exits[reason] = exits.get(reason, 0) + 1

        def median_or_none(items):
            return float(np.median(items)) if items else None

        return {
            "trade_count": len(trades),
            "median_maximum_favorable_excursion_r": median_or_none(
                values["maximum_favorable_excursion_r"]
            ),
            "median_maximum_adverse_excursion_r": median_or_none(
                values["maximum_adverse_excursion_r"]
            ),
            "median_realized_r": median_or_none(values["realized_r"]),
            "median_holding_bars": median_or_none(values["holding_bars"]),
            "median_bars_to_maximum_favorable_excursion": median_or_none(
                values["bars_to_maximum_favorable_excursion"]
            ),
            "exit_reason_counts": {
                reason: exits.get(reason, 0)
                for reason in (
                    "SIGNAL",
                    "PROTECTIVE_STOP",
                    "PROTECTIVE_TARGET",
                    "TERMINAL_FORCE_CLOSE",
                )
            },
            "raw_trade_paths_persisted": False,
        }

    def run(self, locked):
        configuration = alpha_development_evaluation_configuration()
        variants = {}
        for variant_id, engine in alpha_development_strategy_engines().items():
            policy = alpha_development_protective_exit_policy()
            kwargs = configuration.validator_kwargs(ZERO_COST_DIAGNOSTIC)
            kwargs.update(
                {
                    "risk_engine": alpha_development_risk_engine(),
                    "protective_exit_policy": policy,
                }
            )
            raw = self.validator_factory(engine, **kwargs).run(locked.assets)
            if tuple(sorted(raw.get("assets", {}))) != ASSET_SCOPE:
                raise ValueError("Diagnostic replay asset scope is invalid.")
            summaries = {}
            for asset_name in ASSET_SCOPE:
                partition = raw["assets"][asset_name]["out_of_sample"][
                    "out_of_sample"
                ]
                if partition.get("protective_exit_policy") != policy.as_dict():
                    raise ValueError("Diagnostic replay lost protective policy.")
                summaries[asset_name] = self._trade_path_summary(
                    partition["trade_history"]
                )
            variants[variant_id] = {
                "strategy_name": engine.strategy_name,
                "assets": summaries,
                "evaluation": compact_multi_asset_evaluation(raw),
            }
        return {
            "status": "ZERO_COST_TRADE_PATH_DIAGNOSTIC_COMPLETED",
            "variant_order": list(VARIANT_ORDER),
            "multi_asset_replays": len(VARIANT_ORDER),
            "cost_profile": ZERO_COST_DIAGNOSTIC.as_dict(),
            "zero_cost_may_select_parameters": False,
            "raw_trade_paths_persisted": False,
            "variants": variants,
        }


@dataclass(frozen=True)
class RecordedAlphaDiscovery:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    outer_window_count: int
    selected_outer_windows: int
    hold_cash_outer_windows: int
    status: str = "ALPHA_DISCOVERY_RECORDED"

    def as_dict(self):
        return {
            "status": self.status,
            "report_path": str(self.report_path),
            "checksum_path": str(self.checksum_path),
            "report_sha256": self.report_sha256,
            "outer_window_count": self.outer_window_count,
            "selected_outer_windows": self.selected_outer_windows,
            "hold_cash_outer_windows": self.hold_cash_outer_windows,
            "zero_cost_diagnostic_executed": True,
            "trade_path_analysis_executed": True,
            "nested_calibration_executed": True,
            "outer_development_test_executed": True,
            "parameter_selection_executed": True,
            "global_hindsight_leaderboard_generated": False,
            "formal_candidate_evaluation": False,
            "candidate_v2_authorized": False,
            "optimization_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }


class AlphaDiscoveryCalibrationRunner:
    """Execute the exact diagnostic and nested adaptive procedure once."""

    def __init__(
        self,
        output_root=DEFAULT_OUTPUT_ROOT,
        preregistration=None,
        diagnostic_evaluator=None,
        window_evaluator=None,
        planner=None,
        selection_policy=None,
    ):
        self.output_root = Path(output_root)
        self.output_directory = self.output_root / DISCOVERY_DIRECTORY_NAME
        self.staging_directory = self.output_root / STAGING_DIRECTORY_NAME
        self.preregistration = preregistration or AlphaDiscoveryPreregistration()
        self.diagnostic_evaluator = (
            diagnostic_evaluator or AlphaDiscoveryDiagnosticEvaluator()
        )
        self.window_evaluator = window_evaluator or AlphaDiscoveryWindowEvaluator()
        self.planner = planner or NestedCalibrationPlanner()
        self.selection_policy = selection_policy or AlphaCalibrationSelectionPolicy()
        for item, method, name in (
            (self.preregistration, "lock", "Preregistration"),
            (self.diagnostic_evaluator, "run", "Diagnostic evaluator"),
            (self.window_evaluator, "evaluate", "Window evaluator"),
            (self.planner, "plan", "Nested planner"),
            (self.selection_policy, "select", "Selection policy"),
        ):
            if not callable(getattr(item, method, None)):
                raise TypeError(f"{name} must implement {method}().")

    def _assert_not_previously_executed(self):
        if self.output_directory.exists():
            raise FileExistsError(
                "Alpha Discovery evidence already exists; refusing to repeat."
            )
        if self.staging_directory.exists():
            raise FileExistsError(
                "Alpha Discovery staging evidence exists; review it first."
            )

    @staticmethod
    def _validate_locked(locked):
        if locked.manifest_sha256 != DEVELOPMENT_MANIFEST_SHA256:
            raise ValueError("Alpha Discovery manifest SHA-256 is invalid.")
        if (
            locked.alpha_development_report_sha256
            != RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256
        ):
            raise ValueError("Alpha Development report SHA-256 is invalid.")
        if locked.configuration != alpha_discovery_configuration():
            raise ValueError("Locked Alpha Discovery configuration changed.")
        if tuple(sorted(locked.assets)) != ASSET_SCOPE:
            raise ValueError("Locked Alpha Discovery asset scope changed.")
        lengths = {len(frame) for frame in locked.assets.values()}
        if len(lengths) != 1:
            raise ValueError("Locked Alpha Discovery assets have unequal rows.")
        if (
            locked.contract.timeframe != "6h"
            or tuple(locked.contract.products) != ASSET_SCOPE
        ):
            raise ValueError("Locked Alpha Discovery contract changed.")

    @staticmethod
    def _validate_diagnostic(diagnostic):
        if not isinstance(diagnostic, dict):
            raise TypeError("Alpha Discovery diagnostic must be a dictionary.")
        if (
            diagnostic.get("status")
            != "ZERO_COST_TRADE_PATH_DIAGNOSTIC_COMPLETED"
            or diagnostic.get("variant_order") != list(VARIANT_ORDER)
            or diagnostic.get("multi_asset_replays") != len(VARIANT_ORDER)
            or diagnostic.get("zero_cost_may_select_parameters") is not False
            or diagnostic.get("raw_trade_paths_persisted") is not False
            or not isinstance(diagnostic.get("variants"), dict)
        ):
            raise ValueError("Alpha Discovery diagnostic evidence is invalid.")

    @staticmethod
    def _validate_window_evidence(
        evidence,
        parameter_set,
        start_position,
        end_position,
        cost_profile,
        phase,
        window_id,
    ):
        if not isinstance(evidence, dict) or tuple(sorted(evidence)) != ASSET_SCOPE:
            raise ValueError("Window evidence asset scope is invalid.")
        required = {
            "asset",
            "phase",
            "window_id",
            "window_start_position",
            "window_end_position",
            "window_rows",
            "parameter_set_id",
            "cost_profile",
            "strategy_return",
            "maximum_drawdown_percent",
            "completed_trades",
            "annualized_turnover_multiple",
            "annualized_cost_fraction",
            "protective_policy_active",
            "raw_partition_sha256",
            "raw_partition_canonical_bytes",
            "raw_trade_level_evidence_persisted",
        }
        for asset in ASSET_SCOPE:
            item = evidence[asset]
            if not required.issubset(item):
                raise ValueError("Window evidence fields are incomplete.")
            for name in (
                "strategy_return",
                "maximum_drawdown_percent",
                "annualized_turnover_multiple",
                "annualized_cost_fraction",
            ):
                _finite(item[name], f"Window {name}")
            if (
                item["asset"] != asset
                or item["phase"] != phase
                or item["window_id"] != window_id
                or item["window_start_position"] != start_position
                or item["window_end_position"] != end_position
                or item["window_rows"] != end_position - start_position
                or item["parameter_set_id"] != parameter_set.parameter_set_id
                or item["cost_profile"] != cost_profile.as_dict()
                or not isinstance(item["completed_trades"], int)
                or isinstance(item["completed_trades"], bool)
                or item["completed_trades"] < 0
                or item["maximum_drawdown_percent"] < 0.0
                or item["annualized_turnover_multiple"] < 0.0
                or item["annualized_cost_fraction"] < 0.0
                or item["protective_policy_active"] is not True
                or item["raw_trade_level_evidence_persisted"] is not False
                or not isinstance(item["raw_partition_sha256"], str)
                or len(item["raw_partition_sha256"]) != 64
                or not isinstance(item["raw_partition_canonical_bytes"], int)
                or isinstance(item["raw_partition_canonical_bytes"], bool)
                or item["raw_partition_canonical_bytes"] <= 0
            ):
                raise ValueError("Window evidence failed safety validation.")

    def _evaluate_inner_cache(self, plan, locked):
        unique_windows = {}
        for outer in plan["windows"]:
            for inner in outer["inner_windows"]:
                key = (
                    inner["inner_validation_start"],
                    inner["inner_validation_end"],
                )
                unique_windows.setdefault(key, inner)
        cache = {}
        profiles = (BASELINE_COSTS, STRESSED_COSTS)
        for window_number, (key, inner) in enumerate(unique_windows.items()):
            start, end = key
            window_id = f"inner-{window_number}-{start}-{end}"
            parameter_results = {}
            for parameter in CALIBRATION_PARAMETER_CATALOG:
                profile_results = {}
                for profile in profiles:
                    evidence = self.window_evaluator.evaluate(
                        parameter,
                        locked.assets,
                        start,
                        end,
                        profile,
                        "INNER",
                        window_id,
                    )
                    self._validate_window_evidence(
                        evidence,
                        parameter,
                        start,
                        end,
                        profile,
                        "INNER",
                        window_id,
                    )
                    profile_results[profile.label] = evidence
                parameter_results[parameter.parameter_set_id] = profile_results
            cache[key] = {
                "window_id": window_id,
                "inner_train_start": inner["inner_train_start"],
                "inner_train_end": inner["inner_train_end"],
                "inner_validation_start": start,
                "inner_validation_end": end,
                "parameters": parameter_results,
            }
        return cache

    @staticmethod
    def _selection_evidence(inner_windows, cache):
        result = {}
        for parameter_id in PARAMETER_SET_ORDER:
            assets = {}
            for asset in ASSET_SCOPE:
                baseline = []
                stress = []
                drawdowns = []
                trades = {label: 0 for label in PROFILE_ORDER}
                turnovers = {label: [] for label in PROFILE_ORDER}
                baseline_costs = []
                protective = []
                for inner in inner_windows:
                    key = (
                        inner["inner_validation_start"],
                        inner["inner_validation_end"],
                    )
                    profiles = cache[key]["parameters"][parameter_id]
                    baseline_item = profiles[BASELINE_COSTS.label][asset]
                    stress_item = profiles[STRESSED_COSTS.label][asset]
                    baseline.append(baseline_item["strategy_return"])
                    stress.append(stress_item["strategy_return"])
                    for label, item in (
                        (BASELINE_COSTS.label, baseline_item),
                        (STRESSED_COSTS.label, stress_item),
                    ):
                        drawdowns.append(item["maximum_drawdown_percent"])
                        trades[label] += int(item["completed_trades"])
                        turnovers[label].append(
                            item["annualized_turnover_multiple"]
                        )
                        protective.append(item["protective_policy_active"])
                    baseline_costs.append(
                        baseline_item["annualized_cost_fraction"]
                    )
                assets[asset] = {
                    "baseline_median_net_return": float(median(baseline)),
                    "stress_median_net_return": float(median(stress)),
                    "baseline_positive_window_rate": (
                        sum(value > 0.0 for value in baseline) / len(baseline)
                    ),
                    "stress_positive_window_rate": (
                        sum(value > 0.0 for value in stress) / len(stress)
                    ),
                    "maximum_drawdown_percent": max(drawdowns),
                    "completed_trades": min(trades.values()),
                    "annualized_turnover_multiple": max(
                        mean(values) for values in turnovers.values()
                    ),
                    "annualized_baseline_cost_fraction": float(
                        mean(baseline_costs)
                    ),
                    "protective_policy_active": all(protective),
                }
            result[parameter_id] = assets
        return result

    def _outer_evaluation(self, outer, selection, locked):
        parameter_id = selection["selected_parameter_set_id"]
        if parameter_id is None:
            return {
                "action": "HOLD_CASH",
                "parameter_set_id": None,
                "profiles": {},
            }
        parameter = next(
            item
            for item in CALIBRATION_PARAMETER_CATALOG
            if item.parameter_set_id == parameter_id
        )
        profiles = {}
        for profile in (BASELINE_COSTS, STRESSED_COSTS):
            evidence = self.window_evaluator.evaluate(
                parameter,
                locked.assets,
                outer["outer_test_start"],
                outer["outer_test_end"],
                profile,
                "OUTER",
                f"outer-{outer['outer_window']}",
            )
            self._validate_window_evidence(
                evidence,
                parameter,
                outer["outer_test_start"],
                outer["outer_test_end"],
                profile,
                "OUTER",
                f"outer-{outer['outer_window']}",
            )
            profiles[profile.label] = evidence
        return {
            "action": "EXECUTE_SELECTED",
            "parameter_set_id": parameter_id,
            "profiles": profiles,
        }

    @staticmethod
    def _review_outer(outer_windows):
        selected = sum(
            window["outer_evaluation"]["action"] == "EXECUTE_SELECTED"
            for window in outer_windows
        )
        hold = len(outer_windows) - selected
        profiles = {}
        for profile_label in PROFILE_ORDER:
            assets = {}
            for asset in ASSET_SCOPE:
                values = []
                drawdowns = []
                trades = 0
                turnovers = []
                costs = []
                for window in outer_windows:
                    evaluation = window["outer_evaluation"]
                    if evaluation["action"] == "HOLD_CASH":
                        values.append(0.0)
                        drawdowns.append(0.0)
                        turnovers.append(0.0)
                        costs.append(0.0)
                    else:
                        item = evaluation["profiles"][profile_label][asset]
                        values.append(item["strategy_return"])
                        drawdowns.append(item["maximum_drawdown_percent"])
                        trades += int(item["completed_trades"])
                        turnovers.append(item["annualized_turnover_multiple"])
                        costs.append(item["annualized_cost_fraction"])
                assets[asset] = {
                    "median_strategy_return": float(median(values)),
                    "positive_window_rate": (
                        sum(value > 0.0 for value in values) / len(values)
                    ),
                    "maximum_window_drawdown_percent": max(drawdowns),
                    "completed_trades": trades,
                    "mean_annualized_turnover_multiple": float(mean(turnovers)),
                    "mean_annualized_cost_fraction": float(mean(costs)),
                }
            profiles[profile_label] = assets
        config = alpha_discovery_configuration()["calibration_phase"]
        baseline = profiles[BASELINE_COSTS.label]
        stress = profiles[STRESSED_COSTS.label]
        gates = {
            "minimum_outer_windows": len(outer_windows)
            >= config["minimum_outer_windows"],
            "at_least_one_selected_window": selected > 0,
            "positive_baseline_median_return_both_assets": all(
                baseline[asset]["median_strategy_return"] > 0.0
                for asset in ASSET_SCOPE
            ),
            "nonnegative_stress_median_return_both_assets": all(
                stress[asset]["median_strategy_return"] >= 0.0
                for asset in ASSET_SCOPE
            ),
            "baseline_outer_persistence": all(
                baseline[asset]["positive_window_rate"]
                >= config["minimum_positive_inner_window_rate"]
                for asset in ASSET_SCOPE
            ),
            "stress_outer_persistence": all(
                stress[asset]["positive_window_rate"]
                >= config["minimum_positive_inner_window_rate"]
                for asset in ASSET_SCOPE
            ),
            "outer_drawdown_within_limit": all(
                profiles[label][asset]["maximum_window_drawdown_percent"]
                <= config["maximum_drawdown_percent"]
                for label in PROFILE_ORDER
                for asset in ASSET_SCOPE
            ),
            "outer_turnover_within_budget": all(
                profiles[label][asset]["mean_annualized_turnover_multiple"]
                <= config["maximum_annual_turnover_multiple"]
                for label in PROFILE_ORDER
                for asset in ASSET_SCOPE
            ),
            "outer_baseline_cost_within_budget": all(
                baseline[asset]["mean_annualized_cost_fraction"]
                <= config["maximum_annual_baseline_cost_fraction"]
                for asset in ASSET_SCOPE
            ),
        }
        outcome = (
            "ADAPTIVE_PROCEDURE_RETAINS_DEVELOPMENT_INTEREST"
            if all(gates.values())
            else "SCREEN_OUT"
        )
        return {
            "outcome": outcome,
            "gates": gates,
            "failed_gates": [name for name, passed in gates.items() if not passed],
            "selected_outer_windows": selected,
            "hold_cash_outer_windows": hold,
            "profiles": profiles,
            "development_interest_is_formal_validation": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }

    @staticmethod
    def _inner_index(cache):
        return [cache[key] for key in cache]

    def run(self, manifest_path, alpha_report_path):
        self._assert_not_previously_executed()
        locked = self.preregistration.lock(manifest_path, alpha_report_path)
        self._validate_locked(locked)
        total_rows = len(locked.assets[ASSET_SCOPE[0]])
        plan = self.planner.plan(total_rows)
        diagnostic = self.diagnostic_evaluator.run(locked)
        self._validate_diagnostic(diagnostic)
        inner_cache = self._evaluate_inner_cache(plan, locked)

        outer_windows = []
        for outer in plan["windows"]:
            if any(
                inner["inner_validation_end"] > outer["selection_cutoff"]
                for inner in outer["inner_windows"]
            ):
                raise ValueError("Inner evidence crosses the selection cutoff.")
            selection_input = self._selection_evidence(
                outer["inner_windows"], inner_cache
            )
            selection = self.selection_policy.select(selection_input)
            outer_evaluation = self._outer_evaluation(
                outer, selection, locked
            )
            outer_windows.append(
                {
                    **{
                        key: value
                        for key, value in outer.items()
                        if key != "inner_windows"
                    },
                    "inner_windows": [
                        {
                            **inner,
                            "window_id": inner_cache[
                                (
                                    inner["inner_validation_start"],
                                    inner["inner_validation_end"],
                                )
                            ]["window_id"],
                        }
                        for inner in outer["inner_windows"]
                    ],
                    "selection": selection,
                    "outer_evaluation": outer_evaluation,
                }
            )

        review = self._review_outer(outer_windows)
        payload = {
            "schema_version": ALPHA_DISCOVERY_REPORT_SCHEMA_VERSION,
            "status": "ALPHA_DISCOVERY_COMPLETED",
            "alpha_discovery_id": ALPHA_DISCOVERY_ID,
            "discovery_type": "BOUNDED_NESTED_ADAPTIVE_DEVELOPMENT",
            "manifest_sha256": locked.manifest_sha256,
            "alpha_development_report_sha256": (
                locked.alpha_development_report_sha256
            ),
            "dataset_contract": locked.contract.as_dict(),
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "development_data_only": True,
            "parameter_set_order": list(PARAMETER_SET_ORDER),
            "parameter_catalog_sha256": parameter_catalog_fingerprint(),
            "profile_order": list(PROFILE_ORDER),
            "configuration": alpha_discovery_configuration(),
            "diagnostic": diagnostic,
            "nested_calibration": {
                "plan": {
                    key: value for key, value in plan.items() if key != "windows"
                },
                "inner_evaluation_index": self._inner_index(inner_cache),
                "outer_windows": outer_windows,
            },
            "adaptive_review": review,
            "zero_cost_diagnostic_executed": True,
            "trade_path_analysis_executed": True,
            "nested_calibration_executed": True,
            "outer_development_test_executed": True,
            "parameter_selection_executed": True,
            "global_hindsight_leaderboard_generated": False,
            "formal_candidate_evaluation": False,
            "candidate_v2_authorized": False,
            "optimization_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }
        report_bytes = canonical_json_bytes(payload)
        digest = hashlib.sha256(report_bytes).hexdigest()
        checksum_bytes = f"{digest}  {REPORT_FILENAME}\n".encode("ascii")

        self.output_root.mkdir(parents=True, exist_ok=True)
        self.staging_directory.mkdir(exist_ok=False)
        (self.staging_directory / REPORT_FILENAME).write_bytes(report_bytes)
        (self.staging_directory / CHECKSUM_FILENAME).write_bytes(checksum_bytes)
        self.staging_directory.rename(self.output_directory)

        return RecordedAlphaDiscovery(
            report_path=self.output_directory / REPORT_FILENAME,
            checksum_path=self.output_directory / CHECKSUM_FILENAME,
            report_sha256=digest,
            outer_window_count=len(outer_windows),
            selected_outer_windows=review["selected_outer_windows"],
            hold_cash_outer_windows=review["hold_cash_outer_windows"],
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Execute and atomically record Alpha Discovery nested calibration once."
        )
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--alpha-report", required=True)
    args = parser.parse_args(argv)
    recorded = AlphaDiscoveryCalibrationRunner().run(
        args.manifest, args.alpha_report
    )
    print(json.dumps(recorded.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
