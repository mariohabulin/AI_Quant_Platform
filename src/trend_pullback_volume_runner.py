"""One-shot nested development runner for Trend Pullback Volume Protocol v1."""

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

try:
    from alpha_discovery_protocol import (
        ASSET_SCOPE,
        INNER_ASSET_METRICS,
        NestedCalibrationConfig,
        NestedCalibrationPlanner,
    )
    from alpha_discovery_runner import AlphaDiscoveryWindowEvaluator
    from feature_engine import generate_features
    from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from out_of_sample import OutOfSampleValidator
    from protective_exit import ProtectiveExitPolicy
    from research_evidence import canonical_json_bytes
    from risk_engine import RiskEngine
    from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
    from trend_pullback_volume_protocol import (
        RECORDED_ALPHA_DISCOVERY_REPORT_SHA256,
        TREND_PULLBACK_DEVELOPMENT_ID,
        TREND_PULLBACK_PARAMETER_CATALOG,
        TREND_PULLBACK_PARAMETER_CATALOG_SHA256,
        TREND_PULLBACK_PARAMETER_ORDER,
        TrendPullbackVolumeParameterSet,
        TrendPullbackVolumePreregistration,
        trend_pullback_configuration,
    )
    from trend_pullback_volume_strategy import TrendPullbackVolumeStrategy
except ImportError:  # package import when src is not placed directly on sys.path
    from src.alpha_discovery_protocol import (
        ASSET_SCOPE,
        INNER_ASSET_METRICS,
        NestedCalibrationConfig,
        NestedCalibrationPlanner,
    )
    from src.alpha_discovery_runner import AlphaDiscoveryWindowEvaluator
    from src.feature_engine import generate_features
    from src.first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from src.out_of_sample import OutOfSampleValidator
    from src.protective_exit import ProtectiveExitPolicy
    from src.research_evidence import canonical_json_bytes
    from src.risk_engine import RiskEngine
    from src.strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
    from src.trend_pullback_volume_protocol import (
        RECORDED_ALPHA_DISCOVERY_REPORT_SHA256,
        TREND_PULLBACK_DEVELOPMENT_ID,
        TREND_PULLBACK_PARAMETER_CATALOG,
        TREND_PULLBACK_PARAMETER_CATALOG_SHA256,
        TREND_PULLBACK_PARAMETER_ORDER,
        TrendPullbackVolumeParameterSet,
        TrendPullbackVolumePreregistration,
        trend_pullback_configuration,
    )
    from src.trend_pullback_volume_strategy import TrendPullbackVolumeStrategy


TREND_PULLBACK_REPORT_SCHEMA_VERSION = 1
DEVELOPMENT_DIRECTORY_NAME = "development_v1"
STAGING_DIRECTORY_NAME = ".development_v1.staging"
REPORT_FILENAME = "trend_pullback_volume_report.json"
CHECKSUM_FILENAME = "trend_pullback_volume_report.sha256"
DEFAULT_OUTPUT_ROOT = Path("data/research/trend_pullback_volume_v1")
PROFILE_ORDER = (BASELINE_COSTS.label, STRESSED_COSTS.label)


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


def trend_pullback_risk_engine():
    return RiskEngine(
        risk_per_trade=0.005,
        max_position_fraction=0.50,
        max_drawdown_fraction=0.20,
        daily_loss_limit=0.02,
        weekly_loss_limit=0.05,
        min_reward_risk=3.0,
    )


def trend_pullback_protective_exit_policy(parameter_set):
    if not isinstance(parameter_set, TrendPullbackVolumeParameterSet):
        raise TypeError(
            "Parameter set must be a TrendPullbackVolumeParameterSet."
        )
    return ProtectiveExitPolicy(
        risk_distance_column="ALPHA_V2_ATR_RISK_DISTANCE",
        reward_risk_ratio=parameter_set.reward_risk_ratio,
        reward_risk_ratio_column="ALPHA_V2_REWARD_RISK_RATIO",
        stop_and_target_same_bar="STOP_FIRST",
        stop_gap_fill="OPEN",
        target_gap_fill="TARGET",
        entry_bar_protection=True,
        breakeven_trigger_r=None,
    )


class TrendPullbackWindowEvaluator(AlphaDiscoveryWindowEvaluator):
    """Evaluate one exact pullback member on one bounded window."""

    def __init__(
        self,
        strategy_factory=TrendPullbackVolumeStrategy,
        feature_generator=generate_features,
        risk_engine_factory=trend_pullback_risk_engine,
        protective_policy_factory=trend_pullback_protective_exit_policy,
        partition_validator_factory=OutOfSampleValidator,
    ):
        super().__init__(
            strategy_factory=strategy_factory,
            feature_generator=feature_generator,
            risk_engine_factory=risk_engine_factory,
            protective_policy_factory=protective_policy_factory,
            partition_validator_factory=partition_validator_factory,
        )


class TrendPullbackSelectionPolicy:
    """Select from complete prior-inner evidence or explicitly hold cash."""

    def __init__(self, catalog=None, configuration=None):
        self.catalog = tuple(catalog or TREND_PULLBACK_PARAMETER_CATALOG)
        if not self.catalog or any(
            not isinstance(item, TrendPullbackVolumeParameterSet)
            for item in self.catalog
        ):
            raise TypeError("Catalog must contain pullback parameter sets.")
        ids = tuple(item.parameter_set_id for item in self.catalog)
        if len(set(ids)) != len(ids):
            raise ValueError("Pullback parameter-set IDs must be unique.")
        self.parameter_order = ids
        self.configuration = configuration or NestedCalibrationConfig()
        if not isinstance(self.configuration, NestedCalibrationConfig):
            raise TypeError("Configuration must be NestedCalibrationConfig.")

    @staticmethod
    def _validated_asset_metrics(metrics):
        if not isinstance(metrics, dict) or set(metrics) != INNER_ASSET_METRICS:
            raise ValueError("Inner asset evidence fields are not exact.")
        result = {}
        for name in INNER_ASSET_METRICS - {"protective_policy_active"}:
            result[name] = _finite(metrics[name], name)
        result["protective_policy_active"] = (
            metrics["protective_policy_active"] is True
        )
        for name in (
            "baseline_positive_window_rate",
            "stress_positive_window_rate",
            "annualized_baseline_cost_fraction",
        ):
            if not 0.0 <= result[name] <= 1.0:
                raise ValueError(f"{name} must be a fraction from zero to one.")
        if result["completed_trades"] < 0.0:
            raise ValueError("Completed trades cannot be negative.")
        return result

    def select(self, inner_evidence):
        if not isinstance(inner_evidence, dict):
            raise TypeError("Inner evidence must be a dictionary.")
        if tuple(inner_evidence) != self.parameter_order:
            raise ValueError(
                "Inner evidence must match the complete frozen catalog order."
            )
        config = self.configuration
        records = {}
        eligible = []
        for order, parameter_id in enumerate(self.parameter_order):
            evidence = inner_evidence[parameter_id]
            if not isinstance(evidence, dict) or tuple(sorted(evidence)) != ASSET_SCOPE:
                raise ValueError("Every parameter set requires exact asset evidence.")
            assets = {
                asset: self._validated_asset_metrics(evidence[asset])
                for asset in ASSET_SCOPE
            }
            gates = {
                "positive_baseline_median_return_both_assets": all(
                    item["baseline_median_net_return"] > 0.0
                    for item in assets.values()
                ),
                "nonnegative_stress_median_return_both_assets": all(
                    item["stress_median_net_return"] >= 0.0
                    for item in assets.values()
                ),
                "baseline_inner_persistence": all(
                    item["baseline_positive_window_rate"]
                    >= config.minimum_positive_inner_window_rate
                    for item in assets.values()
                ),
                "stress_inner_persistence": all(
                    item["stress_positive_window_rate"]
                    >= config.minimum_positive_inner_window_rate
                    for item in assets.values()
                ),
                "minimum_inner_trades": all(
                    item["completed_trades"]
                    >= config.minimum_inner_trades_per_asset
                    for item in assets.values()
                ),
                "drawdown_within_limit": all(
                    item["maximum_drawdown_percent"]
                    <= config.maximum_drawdown_percent
                    for item in assets.values()
                ),
                "annual_turnover_within_budget": all(
                    item["annualized_turnover_multiple"]
                    <= config.maximum_annual_turnover_multiple
                    for item in assets.values()
                ),
                "annual_baseline_cost_within_budget": all(
                    item["annualized_baseline_cost_fraction"]
                    <= config.maximum_annual_baseline_cost_fraction
                    for item in assets.values()
                ),
                "protective_policy_active": all(
                    item["protective_policy_active"] for item in assets.values()
                ),
            }
            worst_stress = min(
                item["stress_median_net_return"] for item in assets.values()
            )
            worst_baseline = min(
                item["baseline_median_net_return"] for item in assets.values()
            )
            mean_turnover = mean(
                item["annualized_turnover_multiple"] for item in assets.values()
            )
            record = {
                "eligible": all(gates.values()),
                "gates": gates,
                "failed_gates": [
                    name for name, passed in gates.items() if not passed
                ],
                "selection_metrics": {
                    "worst_asset_stress_median_net_return": worst_stress,
                    "worst_asset_baseline_median_net_return": worst_baseline,
                    "mean_annualized_turnover_multiple": mean_turnover,
                },
            }
            records[parameter_id] = record
            if record["eligible"]:
                eligible.append(
                    (
                        -worst_stress,
                        -worst_baseline,
                        mean_turnover,
                        order,
                        parameter_id,
                    )
                )
        selected = min(eligible)[-1] if eligible else None
        return {
            "status": (
                "DEVELOPMENT_CONFIGURATION_SELECTED"
                if selected is not None
                else "NO_ELIGIBLE_CONFIGURATION_HOLD_CASH"
            ),
            "selected_parameter_set_id": selected,
            "hold_cash": selected is None,
            "selection_scope": "INNER_VALIDATION_ONLY",
            "outer_test_evidence_used": False,
            "global_hindsight_leaderboard_generated": False,
            "records": records,
        }


@dataclass(frozen=True)
class RecordedTrendPullbackDevelopment:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    outer_window_count: int
    selected_outer_windows: int
    hold_cash_outer_windows: int
    status: str = "TREND_PULLBACK_VOLUME_DEVELOPMENT_RECORDED"

    def as_dict(self):
        return {
            "status": self.status,
            "report_path": str(self.report_path),
            "checksum_path": str(self.checksum_path),
            "report_sha256": self.report_sha256,
            "outer_window_count": self.outer_window_count,
            "selected_outer_windows": self.selected_outer_windows,
            "hold_cash_outer_windows": self.hold_cash_outer_windows,
            "nested_development_evaluation_executed": True,
            "inner_calibration_executed": True,
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


class TrendPullbackVolumeDevelopmentRunner:
    """Execute the exact four-member nested development procedure once."""

    def __init__(
        self,
        output_root=DEFAULT_OUTPUT_ROOT,
        preregistration=None,
        window_evaluator=None,
        planner=None,
        selection_policy=None,
    ):
        self.output_root = Path(output_root)
        self.output_directory = self.output_root / DEVELOPMENT_DIRECTORY_NAME
        self.staging_directory = self.output_root / STAGING_DIRECTORY_NAME
        self.preregistration = (
            preregistration or TrendPullbackVolumePreregistration()
        )
        self.window_evaluator = window_evaluator or TrendPullbackWindowEvaluator()
        self.planner = planner or NestedCalibrationPlanner()
        self.selection_policy = selection_policy or TrendPullbackSelectionPolicy()
        for item, method, name in (
            (self.preregistration, "lock", "Preregistration"),
            (self.window_evaluator, "evaluate", "Window evaluator"),
            (self.planner, "plan", "Nested planner"),
            (self.selection_policy, "select", "Selection policy"),
        ):
            if not callable(getattr(item, method, None)):
                raise TypeError(f"{name} must implement {method}().")

    def _assert_not_previously_executed(self):
        if self.output_directory.exists():
            raise FileExistsError(
                "Trend Pullback evidence already exists; refusing to repeat."
            )
        if self.staging_directory.exists():
            raise FileExistsError(
                "Trend Pullback staging evidence exists; review it first."
            )

    @staticmethod
    def _validate_locked(locked):
        if locked.manifest_sha256 != DEVELOPMENT_MANIFEST_SHA256:
            raise ValueError("Trend Pullback manifest SHA-256 is invalid.")
        if (
            locked.alpha_discovery_report_sha256
            != RECORDED_ALPHA_DISCOVERY_REPORT_SHA256
        ):
            raise ValueError("Alpha Discovery report SHA-256 is invalid.")
        if locked.configuration != trend_pullback_configuration():
            raise ValueError("Locked Trend Pullback configuration changed.")
        if tuple(sorted(locked.assets)) != ASSET_SCOPE:
            raise ValueError("Locked Trend Pullback asset scope changed.")
        lengths = {len(frame) for frame in locked.assets.values()}
        if len(lengths) != 1:
            raise ValueError("Locked Trend Pullback assets have unequal rows.")
        if (
            locked.contract.timeframe != "6h"
            or tuple(locked.contract.products) != ASSET_SCOPE
        ):
            raise ValueError("Locked Trend Pullback contract changed.")

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
        for window_number, (key, inner) in enumerate(unique_windows.items()):
            start, end = key
            window_id = f"inner-{window_number}-{start}-{end}"
            parameter_results = {}
            for parameter in TREND_PULLBACK_PARAMETER_CATALOG:
                profile_results = {}
                for profile in (BASELINE_COSTS, STRESSED_COSTS):
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
        for parameter_id in TREND_PULLBACK_PARAMETER_ORDER:
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
            for item in TREND_PULLBACK_PARAMETER_CATALOG
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
        config = trend_pullback_configuration()["future_runner_boundary"]
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
            "DEVELOPMENT_PROCEDURE_RETAINS_INTEREST"
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

    def run(self, manifest_path, discovery_report_path):
        self._assert_not_previously_executed()
        locked = self.preregistration.lock(manifest_path, discovery_report_path)
        self._validate_locked(locked)
        total_rows = len(locked.assets[ASSET_SCOPE[0]])
        plan = self.planner.plan(total_rows)
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
            outer_evaluation = self._outer_evaluation(outer, selection, locked)
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
            "schema_version": TREND_PULLBACK_REPORT_SCHEMA_VERSION,
            "status": "TREND_PULLBACK_VOLUME_DEVELOPMENT_COMPLETED",
            "development_id": TREND_PULLBACK_DEVELOPMENT_ID,
            "development_type": "BOUNDED_NESTED_ADAPTIVE_DEVELOPMENT",
            "manifest_sha256": locked.manifest_sha256,
            "alpha_discovery_report_sha256": (
                locked.alpha_discovery_report_sha256
            ),
            "dataset_contract": locked.contract.as_dict(),
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "development_data_only": True,
            "parameter_set_order": list(TREND_PULLBACK_PARAMETER_ORDER),
            "parameter_catalog_sha256": (
                TREND_PULLBACK_PARAMETER_CATALOG_SHA256
            ),
            "profile_order": list(PROFILE_ORDER),
            "configuration": trend_pullback_configuration(),
            "nested_development": {
                "plan": {
                    key: value for key, value in plan.items() if key != "windows"
                },
                "inner_evaluation_index": self._inner_index(inner_cache),
                "outer_windows": outer_windows,
            },
            "adaptive_review": review,
            "nested_development_evaluation_executed": True,
            "inner_calibration_executed": True,
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

        return RecordedTrendPullbackDevelopment(
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
            "Execute and atomically record Trend Pullback nested development once."
        )
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--discovery-report", required=True)
    args = parser.parse_args(argv)
    recorded = TrendPullbackVolumeDevelopmentRunner().run(
        args.manifest, args.discovery_report
    )
    print(json.dumps(recorded.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
