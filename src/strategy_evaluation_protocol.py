"""Versioned research protocol for promoting a strategy to forward PAPER.

The protocol composes the existing multi-asset validation stack.  It does not
generate signals, alter strategy parameters, execute orders, or authorize live
trading.  Its job is to freeze the candidate declaration and turn baseline and
cost-stressed research evidence into one deterministic promotion decision.
"""

from dataclasses import dataclass
import math

from multi_asset import MultiAssetValidator
from validation_pipeline import StrategyValidationPipeline, ValidationPolicy


def _validated_text(value, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} cannot be empty.")
    return value


def _validated_rate(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a number.")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    if value < 0.0:
        raise ValueError(f"{name} cannot be negative.")
    if value >= 1.0:
        raise ValueError(f"{name} must be less than 1.0.")
    return value


def _validated_positive_integer(value, name):
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer.")
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value


def _validated_fraction(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a number.")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1.")
    return value


@dataclass(frozen=True)
class StrategyCandidate:
    """Immutable pre-registration for one strategy research candidate."""

    candidate_id: str
    strategy_name: str
    hypothesis: str
    parameter_set_id: str
    data_version: str
    timeframe: str
    assets: tuple

    def __post_init__(self):
        for field_name, display_name in (
            ("candidate_id", "Candidate ID"),
            ("strategy_name", "Strategy name"),
            ("hypothesis", "Hypothesis"),
            ("parameter_set_id", "Parameter-set ID"),
            ("data_version", "Data version"),
            ("timeframe", "Timeframe"),
        ):
            object.__setattr__(
                self,
                field_name,
                _validated_text(getattr(self, field_name), display_name),
            )

        if not isinstance(self.assets, tuple):
            raise TypeError("Assets must be a tuple so the declared scope is immutable.")
        if not self.assets:
            raise ValueError("Assets cannot be empty.")

        normalized = tuple(
            sorted(_validated_text(asset, "Asset name") for asset in self.assets)
        )
        if len(set(normalized)) != len(normalized):
            raise ValueError("Assets must not contain duplicates.")
        object.__setattr__(self, "assets", normalized)

    def as_dict(self):
        return {
            "candidate_id": self.candidate_id,
            "strategy_name": self.strategy_name,
            "hypothesis": self.hypothesis,
            "parameter_set_id": self.parameter_set_id,
            "data_version": self.data_version,
            "timeframe": self.timeframe,
            "assets": list(self.assets),
        }


@dataclass(frozen=True)
class ExecutionCostProfile:
    """Explicit execution-cost assumptions expressed as decimal rates."""

    label: str
    commission_rate: float
    slippage_rate: float
    spread_rate: float

    def __post_init__(self):
        object.__setattr__(self, "label", _validated_text(self.label, "Cost-profile label"))
        for field_name, display_name in (
            ("commission_rate", "Commission rate"),
            ("slippage_rate", "Slippage rate"),
            ("spread_rate", "Spread rate"),
        ):
            object.__setattr__(
                self,
                field_name,
                _validated_rate(getattr(self, field_name), display_name),
            )

    @property
    def total_rate(self):
        return self.commission_rate + self.slippage_rate + self.spread_rate

    def as_dict(self):
        return {
            "label": self.label,
            "commission_rate": self.commission_rate,
            "slippage_rate": self.slippage_rate,
            "spread_rate": self.spread_rate,
            "total_rate": self.total_rate,
        }


@dataclass(frozen=True)
class StrategyEvaluationConfig:
    """Frozen, reviewable configuration for Strategy Evaluation Protocol v1."""

    train_size: int
    test_size: int
    baseline_costs: ExecutionCostProfile
    stressed_costs: ExecutionCostProfile
    step_size: int | None = None
    expanding: bool = True
    in_sample_fraction: float = 0.70
    initial_capital: float = 10000.0
    simulations: int = 1000
    confidence_level: float = 0.95
    random_seed: int | None = 42
    min_positive_walk_forward_excess_rate: float = 0.60
    min_assets: int = 2
    min_validated_asset_rate: float = 0.60
    max_rejected_asset_rate: float = 0.20
    min_walk_forward_windows: int = 5
    min_unseen_trades_per_asset: int = 30
    max_oos_drawdown_percent: float = 20.0

    def __post_init__(self):
        for field_name, display_name in (
            ("train_size", "Train size"),
            ("test_size", "Test size"),
            ("simulations", "Simulations"),
            ("min_assets", "Minimum assets"),
            ("min_walk_forward_windows", "Minimum walk-forward windows"),
            ("min_unseen_trades_per_asset", "Minimum unseen trades per asset"),
        ):
            object.__setattr__(
                self,
                field_name,
                _validated_positive_integer(getattr(self, field_name), display_name),
            )

        if self.min_assets < 2:
            raise ValueError("Minimum assets must be at least 2.")

        resolved_step = self.test_size if self.step_size is None else self.step_size
        resolved_step = _validated_positive_integer(resolved_step, "Step size")
        if resolved_step < self.test_size:
            raise ValueError(
                "Walk-forward test windows must not overlap in the evaluation protocol."
            )
        object.__setattr__(self, "step_size", resolved_step)

        if not isinstance(self.expanding, bool):
            raise TypeError("Expanding must be a boolean.")
        if not isinstance(self.baseline_costs, ExecutionCostProfile):
            raise TypeError("Baseline costs must be an ExecutionCostProfile.")
        if not isinstance(self.stressed_costs, ExecutionCostProfile):
            raise TypeError("Stressed costs must be an ExecutionCostProfile.")
        if self.baseline_costs.total_rate <= 0.0:
            raise ValueError("Baseline costs must be non-zero and explicitly reviewed.")

        baseline_rates = (
            self.baseline_costs.commission_rate,
            self.baseline_costs.slippage_rate,
            self.baseline_costs.spread_rate,
        )
        stressed_rates = (
            self.stressed_costs.commission_rate,
            self.stressed_costs.slippage_rate,
            self.stressed_costs.spread_rate,
        )
        if any(stressed < baseline for baseline, stressed in zip(baseline_rates, stressed_rates)):
            raise ValueError(
                "Every stressed cost component must be at least as high as baseline."
            )
        if not any(stressed > baseline for baseline, stressed in zip(baseline_rates, stressed_rates)):
            raise ValueError("At least one stressed cost component must be strictly higher.")

        if not isinstance(self.initial_capital, (int, float)) or isinstance(
            self.initial_capital, bool
        ):
            raise TypeError("Initial capital must be a number.")
        initial_capital = float(self.initial_capital)
        if not math.isfinite(initial_capital) or initial_capital <= 0.0:
            raise ValueError("Initial capital must be finite and greater than zero.")
        object.__setattr__(self, "initial_capital", initial_capital)

        in_sample_fraction = _validated_fraction(
            self.in_sample_fraction, "In-sample fraction"
        )
        if in_sample_fraction in {0.0, 1.0}:
            raise ValueError("In-sample fraction must be between 0 and 1.")
        object.__setattr__(self, "in_sample_fraction", in_sample_fraction)

        for field_name, display_name in (
            (
                "min_positive_walk_forward_excess_rate",
                "Minimum positive walk-forward excess rate",
            ),
            ("min_validated_asset_rate", "Minimum validated asset rate"),
            ("max_rejected_asset_rate", "Maximum rejected asset rate"),
        ):
            object.__setattr__(
                self,
                field_name,
                _validated_fraction(getattr(self, field_name), display_name),
            )

        confidence_level = _validated_fraction(self.confidence_level, "Confidence level")
        if confidence_level in {0.0, 1.0}:
            raise ValueError("Confidence level must be between 0 and 1.")
        object.__setattr__(self, "confidence_level", confidence_level)

        if self.random_seed is not None and (
            not isinstance(self.random_seed, int) or isinstance(self.random_seed, bool)
        ):
            raise TypeError("Random seed must be an integer or None.")

        if not isinstance(self.max_oos_drawdown_percent, (int, float)) or isinstance(
            self.max_oos_drawdown_percent, bool
        ):
            raise TypeError("Maximum OOS drawdown percent must be a number.")
        max_drawdown = float(self.max_oos_drawdown_percent)
        if not math.isfinite(max_drawdown) or not 0.0 < max_drawdown <= 100.0:
            raise ValueError(
                "Maximum OOS drawdown percent must be greater than 0 and at most 100."
            )
        object.__setattr__(self, "max_oos_drawdown_percent", max_drawdown)

    def validator_kwargs(self, costs):
        return {
            "train_size": self.train_size,
            "test_size": self.test_size,
            "step_size": self.step_size,
            "expanding": self.expanding,
            "in_sample_fraction": self.in_sample_fraction,
            "initial_capital": self.initial_capital,
            "commission_rate": costs.commission_rate,
            "slippage_rate": costs.slippage_rate,
            "spread_rate": costs.spread_rate,
            "simulations": self.simulations,
            "confidence_level": self.confidence_level,
            "random_seed": self.random_seed,
            "min_positive_walk_forward_excess_rate": (
                self.min_positive_walk_forward_excess_rate
            ),
            "min_assets": self.min_assets,
            "min_validated_asset_rate": self.min_validated_asset_rate,
            "max_rejected_asset_rate": self.max_rejected_asset_rate,
        }

    def as_dict(self):
        return {
            "train_size": self.train_size,
            "test_size": self.test_size,
            "step_size": self.step_size,
            "expanding": self.expanding,
            "in_sample_fraction": self.in_sample_fraction,
            "initial_capital": self.initial_capital,
            "simulations": self.simulations,
            "confidence_level": self.confidence_level,
            "random_seed": self.random_seed,
            "min_positive_walk_forward_excess_rate": (
                self.min_positive_walk_forward_excess_rate
            ),
            "min_assets": self.min_assets,
            "min_validated_asset_rate": self.min_validated_asset_rate,
            "max_rejected_asset_rate": self.max_rejected_asset_rate,
            "min_walk_forward_windows": self.min_walk_forward_windows,
            "min_unseen_trades_per_asset": self.min_unseen_trades_per_asset,
            "max_oos_drawdown_percent": self.max_oos_drawdown_percent,
            "baseline_costs": self.baseline_costs.as_dict(),
            "stressed_costs": self.stressed_costs.as_dict(),
        }


class StrategyEvaluationPolicy:
    """Classify frozen baseline and cost-stress research evidence."""

    PROTOCOL_VERSION = "1.0"
    PAPER_CANDIDATE = "PAPER_CANDIDATE"
    RESEARCH_HOLD = "RESEARCH_HOLD"
    REJECTED = "REJECTED"

    def __init__(self, configuration):
        if not isinstance(configuration, StrategyEvaluationConfig):
            raise TypeError("Configuration must be a StrategyEvaluationConfig.")
        self.configuration = configuration

    @staticmethod
    def _status(result, label):
        try:
            status = result["classification"]["status"]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"{label} evidence is missing classification status.") from exc
        allowed = {
            ValidationPolicy.VALIDATED,
            ValidationPolicy.CONDITIONAL,
            ValidationPolicy.REJECTED,
        }
        if status not in allowed:
            raise ValueError(f"{label} evidence has unknown classification status '{status}'.")
        return status

    @staticmethod
    def _strategy_name(result):
        return result.get("strategy") if isinstance(result, dict) else None

    @staticmethod
    def _asset_names(result):
        assets = result.get("assets") if isinstance(result, dict) else None
        if not isinstance(assets, dict):
            return ()
        return tuple(sorted(assets))

    @staticmethod
    def _asset_metrics(result):
        windows = result["walk_forward"]["windows"]
        if not isinstance(windows, list):
            raise ValueError("Walk-forward windows must be a list.")
        unseen_trade_count = 0
        for window in windows:
            trades = window["test"]["trade_history"]
            if not isinstance(trades, list):
                raise ValueError("Walk-forward test trade history must be a list.")
            unseen_trade_count += len(trades)

        drawdown = result["out_of_sample"]["out_of_sample"]["performance"][
            "max_drawdown"
        ]
        if not isinstance(drawdown, (int, float)) or isinstance(drawdown, bool):
            raise TypeError("OOS maximum drawdown must be a number.")
        drawdown = float(drawdown)
        if not math.isfinite(drawdown) or drawdown < 0.0:
            raise ValueError("OOS maximum drawdown must be finite and non-negative.")

        return {
            "walk_forward_windows": len(windows),
            "unseen_trade_count": unseen_trade_count,
            "oos_max_drawdown_percent": drawdown,
            "classification": StrategyEvaluationPolicy._status(result, "Asset"),
        }

    def review(self, candidate, baseline_result, stressed_result):
        if not isinstance(candidate, StrategyCandidate):
            raise TypeError("Candidate must be a StrategyCandidate.")
        if not isinstance(baseline_result, dict) or not isinstance(stressed_result, dict):
            raise TypeError("Baseline and stressed evidence must be dictionaries.")

        baseline_status = self._status(baseline_result, "Baseline")
        stressed_status = self._status(stressed_result, "Cost-stress")
        expected_assets = candidate.assets
        baseline_assets = self._asset_names(baseline_result)
        stressed_assets = self._asset_names(stressed_result)

        identity_frozen = (
            self._strategy_name(baseline_result) == candidate.strategy_name
            and self._strategy_name(stressed_result) == candidate.strategy_name
        )
        scope_frozen = (
            baseline_assets == expected_assets
            and stressed_assets == expected_assets
        )

        asset_evidence = {}
        complete_asset_evidence = scope_frozen
        for asset_name in expected_assets:
            baseline_asset = baseline_result.get("assets", {}).get(asset_name)
            stressed_asset = stressed_result.get("assets", {}).get(asset_name)
            if baseline_asset is None or stressed_asset is None:
                complete_asset_evidence = False
                continue

            baseline_metrics = self._asset_metrics(baseline_asset)
            stressed_metrics = self._asset_metrics(stressed_asset)
            asset_evidence[asset_name] = {
                "baseline_classification": baseline_metrics["classification"],
                "stressed_classification": stressed_metrics["classification"],
                "walk_forward_windows": min(
                    baseline_metrics["walk_forward_windows"],
                    stressed_metrics["walk_forward_windows"],
                ),
                "unseen_trade_count": min(
                    baseline_metrics["unseen_trade_count"],
                    stressed_metrics["unseen_trade_count"],
                ),
                "baseline_oos_max_drawdown_percent": baseline_metrics[
                    "oos_max_drawdown_percent"
                ],
                "stressed_oos_max_drawdown_percent": stressed_metrics[
                    "oos_max_drawdown_percent"
                ],
            }

        enough_windows = complete_asset_evidence and all(
            item["walk_forward_windows"]
            >= self.configuration.min_walk_forward_windows
            for item in asset_evidence.values()
        )
        enough_trades = complete_asset_evidence and all(
            item["unseen_trade_count"]
            >= self.configuration.min_unseen_trades_per_asset
            for item in asset_evidence.values()
        )
        drawdown_within_limit = complete_asset_evidence and all(
            max(
                item["baseline_oos_max_drawdown_percent"],
                item["stressed_oos_max_drawdown_percent"],
            )
            <= self.configuration.max_oos_drawdown_percent
            for item in asset_evidence.values()
        )

        gates = {
            "strategy_identity_frozen": identity_frozen,
            "asset_scope_frozen": scope_frozen,
            "baseline_validated": baseline_status == ValidationPolicy.VALIDATED,
            "cost_stress_validated": stressed_status == ValidationPolicy.VALIDATED,
            "minimum_walk_forward_windows": enough_windows,
            "minimum_unseen_trades_per_asset": enough_trades,
            "oos_drawdown_within_limit": drawdown_within_limit,
        }

        integrity_failure = not identity_frozen or not scope_frozen
        rejected_edge = (
            baseline_status == ValidationPolicy.REJECTED
            or stressed_status == ValidationPolicy.REJECTED
        )
        if integrity_failure or rejected_edge:
            status = self.REJECTED
        elif all(gates.values()):
            status = self.PAPER_CANDIDATE
        else:
            status = self.RESEARCH_HOLD

        return {
            "protocol": "Strategy Evaluation Protocol",
            "protocol_version": self.PROTOCOL_VERSION,
            "candidate": candidate.as_dict(),
            "configuration": self.configuration.as_dict(),
            "status": status,
            "gates": gates,
            "failed_gates": [name for name, passed in gates.items() if not passed],
            "thresholds": {
                "required_baseline_classification": ValidationPolicy.VALIDATED,
                "required_cost_stress_classification": ValidationPolicy.VALIDATED,
                "min_walk_forward_windows": (
                    self.configuration.min_walk_forward_windows
                ),
                "min_unseen_trades_per_asset": (
                    self.configuration.min_unseen_trades_per_asset
                ),
                "max_oos_drawdown_percent": (
                    self.configuration.max_oos_drawdown_percent
                ),
            },
            "evidence": {
                "baseline_classification": baseline_status,
                "cost_stress_classification": stressed_status,
                "assets": asset_evidence,
            },
            "next_stage": (
                "BOUNDED_FORWARD_PAPER"
                if status == self.PAPER_CANDIDATE
                else "RESEARCH"
            ),
            "live_execution_authorized": False,
        }


class StrategyEvaluationProtocol:
    """Run one frozen candidate under baseline and stressed execution costs."""

    def __init__(self, strategy_engine, candidate, configuration):
        if not isinstance(candidate, StrategyCandidate):
            raise TypeError("Candidate must be a StrategyCandidate.")
        if not isinstance(configuration, StrategyEvaluationConfig):
            raise TypeError("Configuration must be a StrategyEvaluationConfig.")

        actual_name = StrategyValidationPipeline._strategy_name(strategy_engine)
        if actual_name != candidate.strategy_name:
            raise ValueError(
                f"Strategy engine '{actual_name}' does not match declared strategy "
                f"'{candidate.strategy_name}'."
            )
        if len(candidate.assets) < configuration.min_assets:
            raise ValueError(
                f"Candidate declares {len(candidate.assets)} assets but the protocol "
                f"requires at least {configuration.min_assets}."
            )

        self.strategy_engine = strategy_engine
        self.candidate = candidate
        self.configuration = configuration
        self.policy = StrategyEvaluationPolicy(configuration)

    def _validator(self, costs):
        return MultiAssetValidator(
            self.strategy_engine,
            **self.configuration.validator_kwargs(costs),
        )

    def run(self, assets):
        if not isinstance(assets, dict):
            raise TypeError("Assets must be a dictionary mapping names to DataFrames.")
        if any(not isinstance(name, str) or not name.strip() for name in assets):
            raise ValueError("Every evaluation asset must have a non-empty string name.")
        observed_scope = tuple(sorted(assets))
        if observed_scope != self.candidate.assets:
            raise ValueError(
                "Evaluation asset names must exactly match the pre-registered candidate scope."
            )

        baseline = self._validator(self.configuration.baseline_costs).run(assets)
        stressed = self._validator(self.configuration.stressed_costs).run(assets)
        report = self.policy.review(self.candidate, baseline, stressed)
        report["execution_assumptions"] = {
            "baseline": self.configuration.baseline_costs.as_dict(),
            "stress": self.configuration.stressed_costs.as_dict(),
        }
        report["baseline_evaluation"] = baseline
        report["cost_stress_evaluation"] = stressed
        return report
